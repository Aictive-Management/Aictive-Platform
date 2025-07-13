"""
Distributed Tracing System with OpenTelemetry
Provides comprehensive tracing for the Aictive platform with Jaeger backend
"""

import os
import logging
from typing import Dict, Any, Optional, Callable, List, Union
from functools import wraps
from contextlib import contextmanager
import json
from datetime import datetime
import asyncio

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.propagate import set_global_textmap, extract, inject
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.trace.sampling import (
    TraceIdRatioBased, 
    ParentBased, 
    AlwaysOn, 
    AlwaysOff,
    StaticSampler
)

# Metrics
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader

logger = logging.getLogger(__name__)


class SamplingStrategy:
    """Custom sampling strategies for performance optimization"""
    
    @staticmethod
    def create_rentvine_sampler() -> ParentBased:
        """Create a sampler optimized for RentVine operations"""
        # Always sample critical operations
        critical_operations = [
            "emergency_work_order",
            "payment_processing",
            "lease_creation",
            "tenant_screening"
        ]
        
        # Sample 10% of routine operations
        routine_sampler = TraceIdRatioBased(0.1)
        
        # Sample 100% of critical operations
        critical_sampler = AlwaysOn()
        
        # Sample 50% of webhook operations
        webhook_sampler = TraceIdRatioBased(0.5)
        
        # Sample 1% of health checks
        health_check_sampler = TraceIdRatioBased(0.01)
        
        # Create composite sampler
        return ParentBased(
            root=routine_sampler,
            remote_parent_sampled=AlwaysOn(),
            remote_parent_not_sampled=AlwaysOff(),
            local_parent_sampled=AlwaysOn(),
            local_parent_not_sampled=AlwaysOff()
        )


class DistributedTracing:
    """Main distributed tracing system for Aictive platform"""
    
    def __init__(
        self,
        service_name: str = "aictive-platform",
        service_version: str = "2.0.0",
        jaeger_endpoint: Optional[str] = None,
        environment: str = "production",
        enable_metrics: bool = True
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.jaeger_endpoint = jaeger_endpoint or os.getenv(
            "JAEGER_ENDPOINT", 
            "http://localhost:14268/api/traces"
        )
        
        # Initialize tracer provider
        self._init_tracer_provider()
        
        # Initialize metrics if enabled
        if enable_metrics:
            self._init_metrics_provider()
        
        # Set up propagator for distributed context
        set_global_textmap(TraceContextTextMapPropagator())
        
        # Get tracer
        self.tracer = trace.get_tracer(
            instrumenting_module_name=__name__,
            instrumenting_library_version=service_version
        )
        
        # Instrument HTTP client
        HTTPXClientInstrumentor().instrument()
        
        # Instrument asyncio for async operations
        AsyncioInstrumentor().instrument()
        
        logger.info(f"Distributed tracing initialized for {service_name} v{service_version}")
    
    def _init_tracer_provider(self):
        """Initialize the tracer provider with Jaeger exporter"""
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            "environment": self.environment,
            "platform": "aictive",
            "component": "backend"
        })
        
        # Create Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
            collector_endpoint=self.jaeger_endpoint,
            username=os.getenv("JAEGER_USERNAME"),
            password=os.getenv("JAEGER_PASSWORD"),
            max_tag_value_length=256
        )
        
        # Create tracer provider with custom sampler
        provider = TracerProvider(
            resource=resource,
            sampler=SamplingStrategy.create_rentvine_sampler()
        )
        
        # Add batch processor
        processor = BatchSpanProcessor(
            jaeger_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            max_export_timeout_millis=30000
        )
        provider.add_span_processor(processor)
        
        # Set as global provider
        trace.set_tracer_provider(provider)
    
    def _init_metrics_provider(self):
        """Initialize metrics provider for performance monitoring"""
        # Create Prometheus metric reader
        prometheus_reader = PrometheusMetricReader()
        
        # Create meter provider
        provider = MeterProvider(metric_readers=[prometheus_reader])
        metrics.set_meter_provider(provider)
        
        # Create meters for tracking
        self.meter = metrics.get_meter(self.service_name, self.service_version)
        
        # Create common metrics
        self.request_counter = self.meter.create_counter(
            name="aictive_requests_total",
            description="Total number of requests",
            unit="1"
        )
        
        self.request_duration = self.meter.create_histogram(
            name="aictive_request_duration_seconds",
            description="Request duration in seconds",
            unit="s"
        )
        
        self.active_requests = self.meter.create_up_down_counter(
            name="aictive_active_requests",
            description="Number of active requests",
            unit="1"
        )
    
    @contextmanager
    def trace_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        links: Optional[List] = None
    ):
        """Context manager for creating trace spans"""
        with self.tracer.start_as_current_span(
            name=name,
            kind=kind,
            attributes=attributes or {},
            links=links or []
        ) as span:
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            finally:
                # Add final attributes
                span.set_attribute("span.duration_ms", 
                    (datetime.utcnow().timestamp() * 1000) - 
                    (span.start_time / 1_000_000)  # Convert nanoseconds to milliseconds
                )
    
    def trace_async(
        self,
        name: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True
    ):
        """Decorator for tracing async functions"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"
                
                with self.trace_span(
                    name=span_name,
                    kind=kind,
                    attributes=attributes or {}
                ) as span:
                    # Add function metadata
                    span.set_attribute("function.module", func.__module__)
                    span.set_attribute("function.name", func.__name__)
                    
                    # Add arguments (be careful with sensitive data)
                    if args:
                        span.set_attribute("function.args_count", len(args))
                    if kwargs:
                        span.set_attribute("function.kwargs_keys", 
                                         json.dumps(list(kwargs.keys())))
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        if record_exception:
                            span.record_exception(e)
                        if set_status_on_exception:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            
            return wrapper
        return decorator
    
    def trace_sync(
        self,
        name: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True
    ):
        """Decorator for tracing synchronous functions"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"
                
                with self.trace_span(
                    name=span_name,
                    kind=kind,
                    attributes=attributes or {}
                ) as span:
                    # Add function metadata
                    span.set_attribute("function.module", func.__module__)
                    span.set_attribute("function.name", func.__name__)
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        if record_exception:
                            span.record_exception(e)
                        if set_status_on_exception:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            
            return wrapper
        return decorator
    
    def add_rentvine_attributes(self, span: trace.Span, operation_data: Dict[str, Any]):
        """Add RentVine-specific attributes to span"""
        # Property information
        if "property_id" in operation_data:
            span.set_attribute("rentvine.property_id", operation_data["property_id"])
        if "property_name" in operation_data:
            span.set_attribute("rentvine.property_name", operation_data["property_name"])
        
        # Tenant information
        if "tenant_id" in operation_data:
            span.set_attribute("rentvine.tenant_id", operation_data["tenant_id"])
        if "tenant_name" in operation_data:
            span.set_attribute("rentvine.tenant_name", operation_data["tenant_name"])
        
        # Work order information
        if "work_order_id" in operation_data:
            span.set_attribute("rentvine.work_order_id", operation_data["work_order_id"])
        if "work_order_priority" in operation_data:
            span.set_attribute("rentvine.work_order_priority", 
                             operation_data["work_order_priority"])
        
        # Lease information
        if "lease_id" in operation_data:
            span.set_attribute("rentvine.lease_id", operation_data["lease_id"])
        if "lease_status" in operation_data:
            span.set_attribute("rentvine.lease_status", operation_data["lease_status"])
        
        # Financial information (be careful with sensitive data)
        if "transaction_type" in operation_data:
            span.set_attribute("rentvine.transaction_type", 
                             operation_data["transaction_type"])
        if "payment_status" in operation_data:
            span.set_attribute("rentvine.payment_status", 
                             operation_data["payment_status"])
        
        # Workflow information
        if "workflow_id" in operation_data:
            span.set_attribute("rentvine.workflow_id", operation_data["workflow_id"])
        if "workflow_type" in operation_data:
            span.set_attribute("rentvine.workflow_type", operation_data["workflow_type"])
        
        # AI/Swarm information
        if "swarm_confidence" in operation_data:
            span.set_attribute("ai.swarm_confidence", operation_data["swarm_confidence"])
        if "ai_model" in operation_data:
            span.set_attribute("ai.model", operation_data["ai_model"])
    
    def create_trace_context(self) -> Dict[str, str]:
        """Create trace context for propagation"""
        carrier = {}
        inject(carrier)
        return carrier
    
    def extract_trace_context(self, carrier: Dict[str, str]):
        """Extract trace context from carrier"""
        return extract(carrier)
    
    def correlate_with_logs(self, span: trace.Span) -> Dict[str, str]:
        """Get correlation IDs for log correlation"""
        span_context = span.get_span_context()
        return {
            "trace_id": format(span_context.trace_id, "032x"),
            "span_id": format(span_context.span_id, "016x"),
            "trace_flags": format(span_context.trace_flags, "02x")
        }
    
    def record_error(
        self,
        span: trace.Span,
        error: Exception,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Record error with additional context"""
        span.record_exception(error, attributes=attributes)
        span.set_status(Status(StatusCode.ERROR, str(error)))
        
        # Add error classification
        error_attrs = {
            "error.type": type(error).__name__,
            "error.message": str(error),
            "error.handled": attributes.get("handled", False) if attributes else False
        }
        
        # Add stack trace for unhandled errors
        if not error_attrs["error.handled"]:
            import traceback
            error_attrs["error.stack_trace"] = traceback.format_exc()
        
        span.set_attributes(error_attrs)
    
    def create_span_link(
        self,
        target_span_context: trace.SpanContext,
        attributes: Optional[Dict[str, Any]] = None
    ) -> trace.Link:
        """Create a link to another span"""
        return trace.Link(target_span_context, attributes or {})
    
    async def trace_batch_operation(
        self,
        operation_name: str,
        items: List[Any],
        process_func: Callable,
        batch_size: int = 10,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Trace batch operations with child spans"""
        with self.trace_span(
            name=f"batch_{operation_name}",
            attributes={
                "batch.total_items": len(items),
                "batch.size": batch_size,
                **(attributes or {})
            }
        ) as parent_span:
            results = []
            errors = []
            
            # Process items in batches
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                with self.trace_span(
                    name=f"{operation_name}_batch_{i//batch_size}",
                    attributes={
                        "batch.index": i // batch_size,
                        "batch.items_count": len(batch)
                    }
                ) as batch_span:
                    try:
                        # Process batch concurrently
                        batch_results = await asyncio.gather(
                            *[process_func(item) for item in batch],
                            return_exceptions=True
                        )
                        
                        # Separate results and errors
                        for idx, result in enumerate(batch_results):
                            if isinstance(result, Exception):
                                errors.append((batch[idx], result))
                                self.record_error(batch_span, result, 
                                                {"batch.item_index": idx})
                            else:
                                results.append(result)
                        
                    except Exception as e:
                        batch_span.record_exception(e)
                        batch_span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            
            # Set final attributes
            parent_span.set_attributes({
                "batch.successful_items": len(results),
                "batch.failed_items": len(errors)
            })
            
            return results, errors


# Global tracing instance
_tracing_instance: Optional[DistributedTracing] = None


def init_tracing(
    service_name: str = "aictive-platform",
    service_version: str = "2.0.0",
    **kwargs
) -> DistributedTracing:
    """Initialize global tracing instance"""
    global _tracing_instance
    _tracing_instance = DistributedTracing(
        service_name=service_name,
        service_version=service_version,
        **kwargs
    )
    return _tracing_instance


def get_tracer() -> DistributedTracing:
    """Get global tracing instance"""
    if _tracing_instance is None:
        raise RuntimeError("Tracing not initialized. Call init_tracing() first.")
    return _tracing_instance


# Convenience decorators
def trace_async_operation(name: Optional[str] = None, **kwargs):
    """Convenience decorator for async operations"""
    tracer = get_tracer()
    return tracer.trace_async(name=name, **kwargs)


def trace_sync_operation(name: Optional[str] = None, **kwargs):
    """Convenience decorator for sync operations"""
    tracer = get_tracer()
    return tracer.trace_sync(name=name, **kwargs)


# Example usage for RentVine operations
class RentVineTracing:
    """Specialized tracing for RentVine operations"""
    
    @staticmethod
    def trace_work_order_operation(operation_type: str):
        """Trace work order operations"""
        def decorator(func):
            @wraps(func)
            async def wrapper(work_order_id: str, *args, **kwargs):
                tracer = get_tracer()
                
                with tracer.trace_span(
                    name=f"work_order.{operation_type}",
                    kind=SpanKind.INTERNAL,
                    attributes={
                        "rentvine.entity_type": "work_order",
                        "rentvine.operation": operation_type,
                        "rentvine.work_order_id": work_order_id
                    }
                ) as span:
                    try:
                        result = await func(work_order_id, *args, **kwargs)
                        
                        # Add result attributes
                        if isinstance(result, dict):
                            if "priority" in result:
                                span.set_attribute("rentvine.work_order_priority", 
                                                 result["priority"])
                            if "status" in result:
                                span.set_attribute("rentvine.work_order_status", 
                                                 result["status"])
                        
                        return result
                    except Exception as e:
                        tracer.record_error(span, e)
                        raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def trace_payment_operation(operation_type: str):
        """Trace payment operations"""
        def decorator(func):
            @wraps(func)
            async def wrapper(payment_data: Dict[str, Any], *args, **kwargs):
                tracer = get_tracer()
                
                with tracer.trace_span(
                    name=f"payment.{operation_type}",
                    kind=SpanKind.INTERNAL,
                    attributes={
                        "rentvine.entity_type": "payment",
                        "rentvine.operation": operation_type,
                        "rentvine.payment_amount": payment_data.get("amount", 0),
                        "rentvine.payment_method": payment_data.get("method", "unknown")
                    }
                ) as span:
                    try:
                        result = await func(payment_data, *args, **kwargs)
                        
                        # Add result attributes
                        if isinstance(result, dict) and "status" in result:
                            span.set_attribute("rentvine.payment_status", result["status"])
                        
                        return result
                    except Exception as e:
                        tracer.record_error(span, e, {"payment.failed": True})
                        raise
            
            return wrapper
        return decorator