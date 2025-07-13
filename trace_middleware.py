"""
FastAPI Middleware for Distributed Tracing
Provides automatic tracing for all HTTP requests, webhooks, and operations
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime
import traceback
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Send, Scope

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.propagate import extract, inject
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from distributed_tracing import get_tracer, init_tracing

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Main tracing middleware for FastAPI"""
    
    def __init__(
        self,
        app: ASGIApp,
        service_name: str = "aictive-platform",
        excluded_paths: Optional[List[str]] = None,
        sensitive_headers: Optional[List[str]] = None,
        trace_all_requests: bool = True
    ):
        super().__init__(app)
        self.service_name = service_name
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.sensitive_headers = sensitive_headers or ["authorization", "x-api-key", "cookie"]
        self.trace_all_requests = trace_all_requests
        
        # Initialize tracing if not already done
        try:
            self.tracer = get_tracer()
        except RuntimeError:
            self.tracer = init_tracing(service_name=service_name)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing"""
        # Skip tracing for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Extract trace context from headers
        trace_context = extract(dict(request.headers))
        
        # Start span
        with self.tracer.trace_span(
            name=f"{request.method} {request.url.path}",
            kind=SpanKind.SERVER,
            attributes=self._get_request_attributes(request)
        ) as span:
            # Store span in request state for use in endpoints
            request.state.trace_span = span
            request.state.trace_context = self.tracer.correlate_with_logs(span)
            
            # Add trace headers to response
            response_headers = {}
            inject(response_headers)
            
            try:
                # Time the request
                start_time = time.time()
                
                # Process request
                response = await call_next(request)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Add response attributes
                span.set_attributes({
                    "http.status_code": response.status_code,
                    "http.response.size": response.headers.get("content-length", 0),
                    "http.duration_ms": duration * 1000
                })
                
                # Set status based on HTTP status code
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                # Add trace headers to response
                for key, value in response_headers.items():
                    response.headers[key] = value
                
                # Add trace ID to response for client correlation
                response.headers["X-Trace-ID"] = request.state.trace_context["trace_id"]
                
                return response
                
            except Exception as e:
                # Record exception
                self.tracer.record_error(span, e, {"middleware.error": True})
                
                # Return error response
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "trace_id": request.state.trace_context["trace_id"]
                    },
                    headers=response_headers
                )
    
    def _get_request_attributes(self, request: Request) -> Dict[str, Any]:
        """Extract attributes from request"""
        attributes = {
            "http.method": request.method,
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "http.target": request.url.path,
            "http.url": str(request.url),
            "http.user_agent": request.headers.get("user-agent", ""),
            "net.peer.ip": request.client.host if request.client else "",
            "net.peer.port": request.client.port if request.client else 0,
        }
        
        # Add non-sensitive headers
        for key, value in request.headers.items():
            if key.lower() not in self.sensitive_headers:
                attributes[f"http.request.header.{key}"] = value
        
        # Add query parameters
        if request.query_params:
            attributes["http.query"] = str(request.query_params)
        
        return attributes


class WebhookTracingMiddleware:
    """Specialized middleware for webhook tracing"""
    
    def __init__(self, tracer: Optional[Any] = None):
        self.tracer = tracer or get_tracer()
    
    async def trace_webhook(
        self,
        webhook_type: str,
        webhook_data: Dict[str, Any],
        source: str = "rentvine"
    ) -> Dict[str, Any]:
        """Trace webhook processing"""
        with self.tracer.trace_span(
            name=f"webhook.{source}.{webhook_type}",
            kind=SpanKind.CONSUMER,
            attributes={
                "webhook.type": webhook_type,
                "webhook.source": source,
                "webhook.timestamp": datetime.utcnow().isoformat()
            }
        ) as span:
            # Extract trace context if provided in webhook
            if "trace_context" in webhook_data:
                parent_context = extract(webhook_data["trace_context"])
                span.add_link(trace.Link(parent_context))
            
            # Add webhook-specific attributes
            if "event_id" in webhook_data:
                span.set_attribute("webhook.event_id", webhook_data["event_id"])
            if "entity_type" in webhook_data:
                span.set_attribute("webhook.entity_type", webhook_data["entity_type"])
            if "entity_id" in webhook_data:
                span.set_attribute("webhook.entity_id", webhook_data["entity_id"])
            
            # Return trace context for correlation
            return self.tracer.correlate_with_logs(span)


class DatabaseTracingMiddleware:
    """Middleware for database query tracing"""
    
    def __init__(self, tracer: Optional[Any] = None):
        self.tracer = tracer or get_tracer()
        
        # Instrument SQLAlchemy if available
        try:
            SQLAlchemyInstrumentor().instrument()
            logger.info("SQLAlchemy instrumentation enabled")
        except Exception as e:
            logger.warning(f"Could not instrument SQLAlchemy: {e}")
        
        # Instrument Redis if available
        try:
            RedisInstrumentor().instrument()
            logger.info("Redis instrumentation enabled")
        except Exception as e:
            logger.warning(f"Could not instrument Redis: {e}")
    
    @asynccontextmanager
    async def trace_query(
        self,
        query_type: str,
        table_name: str,
        operation: str,
        query_params: Optional[Dict[str, Any]] = None
    ):
        """Trace database query execution"""
        with self.tracer.trace_span(
            name=f"db.{operation}.{table_name}",
            kind=SpanKind.CLIENT,
            attributes={
                "db.system": "postgresql",  # or your database system
                "db.operation": operation,
                "db.table": table_name,
                "db.query_type": query_type
            }
        ) as span:
            start_time = time.time()
            
            try:
                yield span
                
                # Add success metrics
                duration = time.time() - start_time
                span.set_attributes({
                    "db.duration_ms": duration * 1000,
                    "db.success": True
                })
                
            except Exception as e:
                # Record database error
                self.tracer.record_error(span, e, {
                    "db.error": True,
                    "db.error_type": type(e).__name__
                })
                raise
    
    def create_query_span(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        db_name: Optional[str] = None
    ) -> trace.Span:
        """Create span for raw SQL query"""
        # Parse query to extract operation and table
        query_lower = query.lower().strip()
        operation = query_lower.split()[0]
        
        # Try to extract table name
        table_name = "unknown"
        if operation in ["select", "insert", "update", "delete"]:
            parts = query_lower.split()
            for i, part in enumerate(parts):
                if part == "from" and i + 1 < len(parts):
                    table_name = parts[i + 1].strip("()")
                    break
                elif part == "into" and i + 1 < len(parts):
                    table_name = parts[i + 1].strip("()")
                    break
        
        return self.tracer.tracer.start_span(
            name=f"db.query.{operation}",
            kind=SpanKind.CLIENT,
            attributes={
                "db.system": "postgresql",
                "db.statement": query[:1000],  # Truncate long queries
                "db.operation": operation,
                "db.table": table_name,
                "db.name": db_name or "default"
            }
        )


class ExternalAPITracingMiddleware:
    """Middleware for tracing external API calls"""
    
    def __init__(self, tracer: Optional[Any] = None):
        self.tracer = tracer or get_tracer()
        
        # Instrument requests library
        RequestsInstrumentor().instrument()
    
    @asynccontextmanager
    async def trace_api_call(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        request_data: Optional[Dict[str, Any]] = None
    ):
        """Trace external API call"""
        with self.tracer.trace_span(
            name=f"external_api.{service_name}.{method}",
            kind=SpanKind.CLIENT,
            attributes={
                "api.service": service_name,
                "api.endpoint": endpoint,
                "api.method": method,
                "api.has_request_body": request_data is not None
            }
        ) as span:
            start_time = time.time()
            
            try:
                yield span
                
                # Success metrics
                duration = time.time() - start_time
                span.set_attributes({
                    "api.duration_ms": duration * 1000,
                    "api.success": True
                })
                
            except Exception as e:
                # Record API error
                self.tracer.record_error(span, e, {
                    "api.error": True,
                    "api.error_type": type(e).__name__
                })
                raise
    
    def trace_rentvine_api(self, operation: str):
        """Decorator for tracing RentVine API calls"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract relevant information from arguments
                attributes = {
                    "api.service": "rentvine",
                    "api.operation": operation
                }
                
                # Try to extract entity information
                if args and hasattr(args[0], "__dict__"):
                    instance = args[0]
                    if hasattr(instance, "config"):
                        attributes["api.tenant_id"] = getattr(instance.config, "tenant_id", "unknown")
                
                with self.tracer.trace_span(
                    name=f"rentvine.{operation}",
                    kind=SpanKind.CLIENT,
                    attributes=attributes
                ) as span:
                    try:
                        result = await func(*args, **kwargs)
                        
                        # Add result metrics
                        if hasattr(result, "success"):
                            span.set_attribute("api.response.success", result.success)
                        if hasattr(result, "data") and isinstance(result.data, list):
                            span.set_attribute("api.response.count", len(result.data))
                        
                        return result
                        
                    except Exception as e:
                        self.tracer.record_error(span, e)
                        raise
            
            return wrapper
        return decorator


class ErrorTracingMiddleware:
    """Enhanced error tracking with stack traces"""
    
    def __init__(self, tracer: Optional[Any] = None):
        self.tracer = tracer or get_tracer()
    
    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Capture exception with full context"""
        current_span = trace.get_current_span()
        
        if current_span:
            # Create error attributes
            error_attrs = {
                "error.type": type(exception).__name__,
                "error.message": str(exception),
                "error.stack_trace": traceback.format_exc(),
                "error.timestamp": datetime.utcnow().isoformat()
            }
            
            # Add context
            if context:
                for key, value in context.items():
                    error_attrs[f"error.context.{key}"] = str(value)
            
            # Add user information
            if user_id:
                error_attrs["error.user_id"] = user_id
            
            # Add request information
            if request:
                error_attrs.update({
                    "error.request.method": request.method,
                    "error.request.path": request.url.path,
                    "error.request.url": str(request.url)
                })
            
            # Record exception
            current_span.record_exception(exception, attributes=error_attrs)
            current_span.set_status(Status(StatusCode.ERROR, str(exception)))
    
    @asynccontextmanager
    async def trace_with_error_handling(
        self,
        operation_name: str,
        reraise: bool = True,
        fallback_result: Any = None
    ):
        """Context manager for operations with error handling"""
        with self.tracer.trace_span(name=operation_name) as span:
            try:
                yield span
            except Exception as e:
                # Capture detailed error information
                self.capture_exception(e, {"operation": operation_name})
                
                if reraise:
                    raise
                else:
                    # Return fallback result
                    span.set_attribute("error.handled", True)
                    span.set_attribute("error.fallback_used", True)
                    return fallback_result


class PerformanceTracingMiddleware:
    """Middleware for performance monitoring"""
    
    def __init__(self, tracer: Optional[Any] = None):
        self.tracer = tracer or get_tracer()
        self.slow_query_threshold_ms = 1000  # 1 second
        self.slow_api_threshold_ms = 5000    # 5 seconds
    
    def check_slow_operation(
        self,
        span: trace.Span,
        duration_ms: float,
        operation_type: str
    ):
        """Check if operation is slow and add appropriate tags"""
        threshold = {
            "query": self.slow_query_threshold_ms,
            "api": self.slow_api_threshold_ms,
            "webhook": 10000,  # 10 seconds for webhooks
            "workflow": 30000  # 30 seconds for workflows
        }.get(operation_type, 5000)
        
        if duration_ms > threshold:
            span.set_attributes({
                "performance.slow": True,
                "performance.threshold_ms": threshold,
                "performance.duration_ms": duration_ms,
                "performance.exceeded_by_ms": duration_ms - threshold
            })
            
            # Add event for slow operation
            span.add_event(
                name="slow_operation_detected",
                attributes={
                    "operation_type": operation_type,
                    "duration_ms": duration_ms,
                    "threshold_ms": threshold
                }
            )
    
    async def measure_operation(
        self,
        operation_name: str,
        operation_type: str,
        operation_func: Callable,
        *args,
        **kwargs
    ):
        """Measure operation performance"""
        with self.tracer.trace_span(
            name=operation_name,
            attributes={"operation.type": operation_type}
        ) as span:
            start_time = time.time()
            
            try:
                # Execute operation
                result = await operation_func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Check for slow operation
                self.check_slow_operation(span, duration_ms, operation_type)
                
                # Add performance metrics
                span.set_attributes({
                    "performance.duration_ms": duration_ms,
                    "performance.success": True
                })
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                span.set_attributes({
                    "performance.duration_ms": duration_ms,
                    "performance.success": False,
                    "performance.error": str(e)
                })
                raise


def setup_tracing_middleware(app: FastAPI, **kwargs):
    """Setup all tracing middleware for FastAPI app"""
    # Initialize tracing
    tracer = init_tracing(**kwargs)
    
    # Add HTTP tracing middleware
    app.add_middleware(TracingMiddleware, **kwargs)
    
    # Initialize specialized middleware
    webhook_tracer = WebhookTracingMiddleware(tracer)
    db_tracer = DatabaseTracingMiddleware(tracer)
    api_tracer = ExternalAPITracingMiddleware(tracer)
    error_tracer = ErrorTracingMiddleware(tracer)
    perf_tracer = PerformanceTracingMiddleware(tracer)
    
    # Store middleware instances in app state for use in endpoints
    app.state.webhook_tracer = webhook_tracer
    app.state.db_tracer = db_tracer
    app.state.api_tracer = api_tracer
    app.state.error_tracer = error_tracer
    app.state.perf_tracer = perf_tracer
    
    logger.info("Tracing middleware setup complete")
    
    return tracer


# Decorators for easy use in endpoints
def trace_endpoint(name: Optional[str] = None, **kwargs):
    """Decorator to trace FastAPI endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs_inner):
            tracer = get_tracer()
            span_name = name or f"endpoint.{func.__name__}"
            
            with tracer.trace_span(name=span_name, **kwargs) as span:
                # Extract request if available
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if request:
                    # Add request context
                    span.set_attributes({
                        "endpoint.path": request.url.path,
                        "endpoint.method": request.method
                    })
                
                return await func(*args, **kwargs_inner)
        
        return wrapper
    return decorator