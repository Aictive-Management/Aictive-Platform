"""
Example Integration of Distributed Tracing with Existing Services
Shows how to add tracing to RentVine API Client and Webhook Workflow Engine
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from distributed_tracing import init_tracing, get_tracer, RentVineTracing
from trace_middleware import setup_tracing_middleware, trace_endpoint
from rentvine_api_client import RentVineAPIClient, RentVineConfig, APIResponse
from webhook_workflow_engine import WebhookWorkflowEngine, WebhookEvent, WebhookEventType
from opentelemetry.trace import SpanKind, Status, StatusCode
import json

# Initialize FastAPI app with tracing
app = FastAPI(title="Aictive Platform with Tracing")

# Setup comprehensive tracing
tracer = setup_tracing_middleware(
    app,
    service_name="aictive-platform",
    service_version="2.0.0",
    environment="production"
)


class TracedRentVineAPIClient(RentVineAPIClient):
    """Extended RentVine API Client with comprehensive tracing"""
    
    def __init__(self, config: RentVineConfig):
        super().__init__(config)
        self.tracer = get_tracer()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """Enhanced request method with detailed tracing"""
        
        # Create span for API request
        with self.tracer.trace_span(
            name=f"rentvine.api.{method.lower()}",
            kind=SpanKind.CLIENT,
            attributes={
                "http.method": method,
                "http.url": f"{self.config.base_url}{endpoint}",
                "rentvine.tenant_id": self.config.tenant_id,
                "rentvine.endpoint": endpoint,
                "api.has_params": params is not None,
                "api.has_body": json_data is not None
            }
        ) as span:
            # Add request details
            if params:
                span.set_attribute("api.params", json.dumps(params)[:500])
            
            # Perform actual request with parent's implementation
            try:
                response = await super()._make_request(
                    method, endpoint, params, json_data, correlation_id
                )
                
                # Add response attributes
                span.set_attributes({
                    "api.response.success": response.success,
                    "api.response.has_data": response.data is not None,
                    "api.response.correlation_id": response.correlation_id
                })
                
                # Add specific metrics based on endpoint
                if endpoint.startswith("/properties") and response.data:
                    if isinstance(response.data, list):
                        span.set_attribute("rentvine.properties.count", len(response.data))
                    elif isinstance(response.data, dict):
                        span.set_attribute("rentvine.property.id", response.data.get("id"))
                
                return response
                
            except Exception as e:
                self.tracer.record_error(span, e, {"api.endpoint": endpoint})
                raise
    
    @RentVineTracing.trace_work_order_operation("create")
    async def create_work_order(self, work_order_data: Dict) -> APIResponse[Dict]:
        """Create work order with specialized tracing"""
        # Add work order specific attributes to current span
        span = self.tracer.tracer.get_current_span()
        if span:
            span.set_attributes({
                "rentvine.work_order.priority": work_order_data.get("priority", "normal"),
                "rentvine.work_order.type": work_order_data.get("type"),
                "rentvine.work_order.property_id": work_order_data.get("property_id")
            })
        
        return await super().create_work_order(work_order_data)
    
    @RentVineTracing.trace_payment_operation("process")
    async def process_payment(self, payment_data: Dict) -> APIResponse[Dict]:
        """Process payment with enhanced tracing"""
        # Sensitive data handling - only log safe attributes
        span = self.tracer.tracer.get_current_span()
        if span:
            span.set_attributes({
                "rentvine.payment.amount": payment_data.get("amount"),
                "rentvine.payment.method": payment_data.get("method"),
                "rentvine.payment.tenant_id": payment_data.get("tenant_id"),
                # Don't log full card numbers, only last 4 digits
                "rentvine.payment.card_last4": payment_data.get("card_number", "")[-4:] if payment_data.get("card_number") else None
            })
        
        return await self._make_request("POST", "/payments", json_data=payment_data)


class TracedWebhookWorkflowEngine(WebhookWorkflowEngine):
    """Extended Webhook Workflow Engine with comprehensive tracing"""
    
    def __init__(self, rentvine_client, orchestration_engine, swarm_orchestrator):
        super().__init__(rentvine_client, orchestration_engine, swarm_orchestrator)
        self.tracer = get_tracer()
    
    async def process_webhook_event(self, event: WebhookEvent):
        """Process webhook with distributed tracing"""
        
        # Extract trace context if provided in webhook headers
        trace_context = {}
        if hasattr(event, 'headers'):
            trace_context = dict(event.headers)
        
        # Create main span for webhook processing
        with self.tracer.trace_span(
            name=f"webhook.process.{event.event_type.value}",
            kind=SpanKind.CONSUMER,
            attributes={
                "webhook.event_id": event.event_id,
                "webhook.event_type": event.event_type.value,
                "webhook.timestamp": event.timestamp.isoformat(),
                "webhook.has_metadata": bool(event.metadata)
            }
        ) as span:
            # Add webhook-specific attributes
            self._add_webhook_attributes(span, event)
            
            # Process with parent's implementation
            try:
                workflow = await super().process_webhook_event(event)
                
                # Add workflow result attributes
                span.set_attributes({
                    "workflow.id": workflow.workflow_id,
                    "workflow.status": workflow.status,
                    "workflow.priority": workflow.priority.value,
                    "workflow.duration_ms": (datetime.utcnow() - workflow.created_at).total_seconds() * 1000
                })
                
                return workflow
                
            except Exception as e:
                self.tracer.record_error(span, e, {
                    "webhook.failed": True,
                    "webhook.event_type": event.event_type.value
                })
                raise
    
    def _add_webhook_attributes(self, span, event: WebhookEvent):
        """Add detailed webhook attributes to span"""
        # Entity-specific attributes based on event type
        if event.event_type in [WebhookEventType.WORK_ORDER_CREATED, 
                               WebhookEventType.WORK_ORDER_UPDATED,
                               WebhookEventType.WORK_ORDER_COMPLETED]:
            span.set_attributes({
                "rentvine.entity_type": "work_order",
                "rentvine.work_order_id": event.data.get("id"),
                "rentvine.work_order_priority": event.data.get("priority"),
                "rentvine.property_id": event.data.get("property_id")
            })
        
        elif event.event_type in [WebhookEventType.LEASE_CREATED,
                                 WebhookEventType.LEASE_UPDATED,
                                 WebhookEventType.LEASE_EXPIRED]:
            span.set_attributes({
                "rentvine.entity_type": "lease",
                "rentvine.lease_id": event.data.get("id"),
                "rentvine.property_id": event.data.get("property_id"),
                "rentvine.tenant_id": event.data.get("tenant_id")
            })
        
        elif event.event_type in [WebhookEventType.PAYMENT_RECEIVED,
                                 WebhookEventType.PAYMENT_FAILED]:
            span.set_attributes({
                "rentvine.entity_type": "payment",
                "rentvine.payment_id": event.data.get("id"),
                "rentvine.payment_amount": event.data.get("amount"),
                "rentvine.payment_status": event.data.get("status")
            })
    
    async def _handle_emergency_work_order(self, work_order: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency work order with detailed tracing"""
        with self.tracer.trace_span(
            name="workflow.emergency_work_order",
            attributes={
                "workflow.type": "emergency",
                "rentvine.work_order_id": work_order.get("id"),
                "rentvine.priority": "emergency"
            }
        ) as span:
            # Trace each step of emergency handling
            
            # Step 1: Dispatch technician
            with self.tracer.trace_span("dispatch_emergency_technician") as dispatch_span:
                dispatch_result = await self._dispatch_emergency_technician(work_order)
                dispatch_span.set_attributes({
                    "dispatch.technician": dispatch_result.get("technician_name"),
                    "dispatch.eta": dispatch_result.get("eta")
                })
            
            # Step 2: Notify stakeholders
            with self.tracer.trace_span("notify_stakeholders") as notify_span:
                notifications = await self._notify_emergency_stakeholders(work_order)
                notify_span.set_attribute("notifications.count", len(notifications))
            
            # Step 3: Get approval if needed
            if work_order.get("estimated_cost", 0) > 1000:
                with self.tracer.trace_span("get_emergency_approval") as approval_span:
                    approval = await self._get_emergency_approval(work_order)
                    approval_span.set_attributes({
                        "approval.granted": approval.get("approved"),
                        "approval.amount": approval.get("approval_amount")
                    })
            
            # Complete the parent implementation
            result = await super()._handle_emergency_work_order(work_order)
            
            # Add final metrics
            span.set_attributes({
                "workflow.steps_completed": result.get("steps_executed", 0),
                "workflow.success": True
            })
            
            return result


# API Endpoints with Tracing

@app.post("/api/v1/webhook")
@trace_endpoint(name="webhook_receiver")
async def receive_webhook(request: Request):
    """Receive and process webhook with tracing"""
    tracer = get_tracer()
    
    # Extract webhook data
    webhook_data = await request.json()
    
    # Get trace span from request
    span = request.state.trace_span
    
    # Add webhook attributes
    span.set_attributes({
        "webhook.source": request.headers.get("X-Webhook-Source", "unknown"),
        "webhook.signature": bool(request.headers.get("X-Webhook-Signature")),
        "webhook.event_type": webhook_data.get("event_type")
    })
    
    try:
        # Create webhook event
        event = WebhookEvent(
            event_id=webhook_data.get("id"),
            event_type=WebhookEventType(webhook_data.get("event_type")),
            timestamp=datetime.fromisoformat(webhook_data.get("timestamp")),
            data=webhook_data.get("data"),
            metadata=webhook_data.get("metadata", {})
        )
        
        # Process with workflow engine
        workflow_result = await app.state.workflow_engine.process_webhook_event(event)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "processed",
                "workflow_id": workflow_result.workflow_id,
                "trace_id": request.state.trace_context["trace_id"]
            }
        )
        
    except Exception as e:
        tracer.record_error(span, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/properties/{property_id}")
@trace_endpoint(name="get_property")
async def get_property(property_id: str, request: Request):
    """Get property with tracing"""
    span = request.state.trace_span
    span.set_attribute("rentvine.property_id", property_id)
    
    try:
        # Use traced RentVine client
        response = await app.state.rentvine_client.get_property(property_id)
        
        if response.success:
            return response.data
        else:
            raise HTTPException(status_code=404, detail=response.error)
            
    except Exception as e:
        app.state.error_tracer.capture_exception(
            e,
            context={"property_id": property_id},
            request=request
        )
        raise


@app.post("/api/v1/work-orders")
@trace_endpoint(name="create_work_order")
async def create_work_order(work_order_data: Dict[str, Any], request: Request):
    """Create work order with comprehensive tracing"""
    tracer = get_tracer()
    span = request.state.trace_span
    
    # Add work order attributes
    span.set_attributes({
        "rentvine.work_order.priority": work_order_data.get("priority", "normal"),
        "rentvine.work_order.type": work_order_data.get("type"),
        "rentvine.property_id": work_order_data.get("property_id")
    })
    
    # Check if emergency
    if work_order_data.get("priority") == "emergency":
        span.set_attribute("workflow.emergency", True)
        
        # Create child span for emergency validation
        with tracer.trace_span("validate_emergency") as validation_span:
            # Validate emergency criteria
            is_valid_emergency = await validate_emergency_criteria(work_order_data)
            validation_span.set_attribute("validation.passed", is_valid_emergency)
    
    try:
        # Create work order with traced client
        response = await app.state.rentvine_client.create_work_order(work_order_data)
        
        if response.success:
            # Trigger workflow if needed
            if work_order_data.get("priority") == "emergency":
                webhook_event = WebhookEvent(
                    event_id=f"manual_{response.data['id']}",
                    event_type=WebhookEventType.WORK_ORDER_CREATED,
                    timestamp=datetime.utcnow(),
                    data=response.data,
                    metadata={"source": "api", "triggered_by": "manual"}
                )
                
                workflow = await app.state.workflow_engine.process_webhook_event(webhook_event)
                span.set_attribute("workflow.triggered", True)
                span.set_attribute("workflow.id", workflow.workflow_id)
            
            return response.data
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        tracer.record_error(span, e)
        raise


# Performance monitoring endpoint
@app.get("/api/v1/performance/traces")
async def get_performance_metrics(request: Request):
    """Get performance metrics from traces"""
    perf_tracer = request.app.state.perf_tracer
    
    # This would typically query Jaeger or your metrics backend
    return {
        "slow_operations": {
            "threshold_ms": perf_tracer.slow_api_threshold_ms,
            "count_last_hour": 42  # Would query actual metrics
        },
        "error_rate": {
            "last_hour": 0.02,  # 2% error rate
            "last_24h": 0.015
        },
        "trace_sampling": {
            "current_rate": 0.1,
            "emergency_rate": 1.0
        }
    }


# Helper functions

async def validate_emergency_criteria(work_order_data: Dict[str, Any]) -> bool:
    """Validate if work order qualifies as emergency"""
    emergency_keywords = ["flood", "fire", "gas leak", "no heat", "no water", "electrical hazard"]
    description = work_order_data.get("description", "").lower()
    
    return any(keyword in description for keyword in emergency_keywords)


# Application startup
@app.on_event("startup")
async def startup_event():
    """Initialize traced services"""
    # Initialize RentVine client with tracing
    rentvine_config = RentVineConfig(
        base_url="https://api.rentvine.com/v2",
        api_key="your_api_key",
        api_secret="your_api_secret",
        tenant_id="your_tenant_id"
    )
    
    app.state.rentvine_client = TracedRentVineAPIClient(rentvine_config)
    
    # Initialize other services...
    # app.state.workflow_engine = TracedWebhookWorkflowEngine(...)
    
    logger.info("Application started with distributed tracing enabled")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)