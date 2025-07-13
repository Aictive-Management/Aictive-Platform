"""
RentVine Webhook Handler
Production-ready webhook receiver with signature verification
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import asyncio
from fastapi import Request, HTTPException, Header, BackgroundTasks
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# RentVine webhook signing key (store in environment variable in production)
RENTVINE_SIGNING_KEY = "dszqtymvoxttkw35yrvisaimwhczpsa0-t3qpw5sz-f5ybqa4c"


class WebhookEventType(Enum):
    """RentVine webhook event types"""
    # Property events
    PROPERTY_CREATED = "property.created"
    PROPERTY_UPDATED = "property.updated"
    PROPERTY_DELETED = "property.deleted"
    
    # Tenant events
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_MOVED_OUT = "tenant.moved_out"
    
    # Lease events
    LEASE_CREATED = "lease.created"
    LEASE_UPDATED = "lease.updated"
    LEASE_EXPIRED = "lease.expired"
    LEASE_RENEWED = "lease.renewed"
    
    # Work order events
    WORK_ORDER_CREATED = "work_order.created"
    WORK_ORDER_UPDATED = "work_order.updated"
    WORK_ORDER_COMPLETED = "work_order.completed"
    WORK_ORDER_CANCELLED = "work_order.cancelled"
    
    # Financial events
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
    
    # Maintenance events
    MAINTENANCE_REQUEST = "maintenance.request"
    MAINTENANCE_SCHEDULED = "maintenance.scheduled"
    MAINTENANCE_COMPLETED = "maintenance.completed"


@dataclass
class WebhookEvent:
    """Parsed webhook event"""
    event_id: str
    event_type: WebhookEventType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class WebhookSignatureVerifier:
    """Verify webhook signatures from RentVine"""
    
    def __init__(self, signing_key: str):
        self.signing_key = signing_key.encode('utf-8')
    
    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """Verify webhook signature"""
        try:
            # RentVine signature format: "sha256=<signature>"
            if signature.startswith("sha256="):
                signature = signature[7:]
            
            # Create HMAC signature
            if timestamp:
                # Include timestamp in signature to prevent replay attacks
                message = f"{timestamp}.{payload.decode('utf-8')}".encode('utf-8')
            else:
                message = payload
            
            expected_signature = hmac.new(
                self.signing_key,
                message,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant time comparison)
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False


class WebhookHandler:
    """Handle RentVine webhook events"""
    
    def __init__(self, signing_key: str):
        self.verifier = WebhookSignatureVerifier(signing_key)
        self.event_handlers: Dict[WebhookEventType, List[Callable]] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        # Property events
        self.register_handler(WebhookEventType.PROPERTY_CREATED, self._handle_property_created)
        self.register_handler(WebhookEventType.PROPERTY_UPDATED, self._handle_property_updated)
        
        # Tenant events
        self.register_handler(WebhookEventType.TENANT_CREATED, self._handle_tenant_created)
        self.register_handler(WebhookEventType.TENANT_MOVED_OUT, self._handle_tenant_moved_out)
        
        # Work order events
        self.register_handler(WebhookEventType.WORK_ORDER_CREATED, self._handle_work_order_created)
        self.register_handler(WebhookEventType.WORK_ORDER_COMPLETED, self._handle_work_order_completed)
        
        # Payment events
        self.register_handler(WebhookEventType.PAYMENT_RECEIVED, self._handle_payment_received)
        self.register_handler(WebhookEventType.PAYMENT_FAILED, self._handle_payment_failed)
    
    def register_handler(self, event_type: WebhookEventType, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def handle_webhook(
        self,
        request: Request,
        signature: str,
        timestamp: Optional[str] = None
    ) -> JSONResponse:
        """Main webhook handler"""
        try:
            # Get raw body
            body = await request.body()
            
            # Verify signature
            if not self.verifier.verify_signature(body, signature, timestamp):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Parse payload
            payload = json.loads(body)
            
            # Extract event details
            event = self._parse_event(payload)
            
            # Log event
            logger.info(
                f"Webhook received: {event.event_type.value}",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat()
                }
            )
            
            # Process event asynchronously
            asyncio.create_task(self._process_event(event))
            
            # Return immediate response
            return JSONResponse(
                status_code=200,
                content={
                    "status": "accepted",
                    "event_id": event.event_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def _parse_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Parse webhook payload into event object"""
        try:
            event_type = WebhookEventType(payload.get("event_type"))
        except ValueError:
            logger.warning(f"Unknown event type: {payload.get('event_type')}")
            event_type = WebhookEventType.PROPERTY_UPDATED  # Default
        
        return WebhookEvent(
            event_id=payload.get("event_id", str(datetime.utcnow().timestamp())),
            event_type=event_type,
            timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.utcnow().isoformat())),
            data=payload.get("data", {}),
            metadata=payload.get("metadata", {})
        )
    
    async def _process_event(self, event: WebhookEvent):
        """Process event with registered handlers"""
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler: {e}",
                    extra={
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "handler": handler.__name__
                    }
                )
    
    # Default event handlers
    
    async def _handle_property_created(self, event: WebhookEvent):
        """Handle property created event"""
        property_data = event.data
        logger.info(f"New property created: {property_data.get('name')} (ID: {property_data.get('id')})")
        
        # TODO: Sync to local database
        # TODO: Create default workflows for property
        # TODO: Notify property manager
    
    async def _handle_property_updated(self, event: WebhookEvent):
        """Handle property updated event"""
        property_data = event.data
        logger.info(f"Property updated: {property_data.get('id')}")
        
        # TODO: Update local cache
        # TODO: Check if critical fields changed
    
    async def _handle_tenant_created(self, event: WebhookEvent):
        """Handle tenant created event"""
        tenant_data = event.data
        logger.info(f"New tenant created: {tenant_data.get('first_name')} {tenant_data.get('last_name')}")
        
        # TODO: Create welcome workflow
        # TODO: Schedule move-in inspection
        # TODO: Send welcome email
    
    async def _handle_tenant_moved_out(self, event: WebhookEvent):
        """Handle tenant moved out event"""
        tenant_data = event.data
        logger.info(f"Tenant moved out: {tenant_data.get('id')}")
        
        # TODO: Create move-out workflow
        # TODO: Schedule final inspection
        # TODO: Process security deposit
    
    async def _handle_work_order_created(self, event: WebhookEvent):
        """Handle work order created event"""
        work_order = event.data
        priority = work_order.get('priority', 'medium')
        
        logger.info(
            f"New work order: {work_order.get('description')} "
            f"(Priority: {priority}, Property: {work_order.get('property_id')})"
        )
        
        # TODO: Create maintenance workflow
        # TODO: Assign to technician based on priority
        # TODO: Send notifications
        
        # If emergency, trigger immediate response
        if priority == 'emergency':
            logger.warning(f"Emergency work order created: {work_order.get('id')}")
            # TODO: Trigger emergency workflow
    
    async def _handle_work_order_completed(self, event: WebhookEvent):
        """Handle work order completed event"""
        work_order = event.data
        logger.info(f"Work order completed: {work_order.get('id')}")
        
        # TODO: Update workflow status
        # TODO: Send completion notification
        # TODO: Request tenant feedback
    
    async def _handle_payment_received(self, event: WebhookEvent):
        """Handle payment received event"""
        payment = event.data
        logger.info(
            f"Payment received: ${payment.get('amount')} "
            f"from tenant {payment.get('tenant_id')} "
            f"for property {payment.get('property_id')}"
        )
        
        # TODO: Update tenant balance
        # TODO: Send receipt
        # TODO: Update financial reports
    
    async def _handle_payment_failed(self, event: WebhookEvent):
        """Handle payment failed event"""
        payment = event.data
        logger.warning(
            f"Payment failed: ${payment.get('amount')} "
            f"from tenant {payment.get('tenant_id')} "
            f"Reason: {payment.get('failure_reason')}"
        )
        
        # TODO: Create collection workflow
        # TODO: Send payment failure notification
        # TODO: Update tenant account status


# FastAPI webhook endpoints
from fastapi import FastAPI

app = FastAPI()
webhook_handler = WebhookHandler(RENTVINE_SIGNING_KEY)


@app.post("/webhooks/rentvine")
async def receive_rentvine_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_rentvine_signature: str = Header(...),
    x_rentvine_timestamp: Optional[str] = Header(None)
):
    """Receive webhook from RentVine"""
    return await webhook_handler.handle_webhook(
        request=request,
        signature=x_rentvine_signature,
        timestamp=x_rentvine_timestamp
    )


@app.get("/webhooks/health")
async def webhook_health():
    """Health check for webhook endpoint"""
    return {
        "status": "healthy",
        "endpoint": "/webhooks/rentvine",
        "timestamp": datetime.utcnow().isoformat()
    }


# Webhook testing utilities
class WebhookTester:
    """Test webhook functionality"""
    
    @staticmethod
    def create_test_signature(payload: str, signing_key: str) -> str:
        """Create a test signature for webhook testing"""
        signature = hmac.new(
            signing_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    @staticmethod
    def create_test_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test webhook event"""
        return {
            "event_id": f"test_{datetime.utcnow().timestamp()}",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": {
                "source": "test",
                "version": "1.0"
            }
        }


# Example: How to test webhooks locally
if __name__ == "__main__":
    import uvicorn
    
    # Test signature generation
    test_payload = json.dumps(WebhookTester.create_test_event(
        "property.created",
        {
            "id": "prop_123",
            "name": "Test Property",
            "address": "123 Main St",
            "units": 10
        }
    ))
    
    test_signature = WebhookTester.create_test_signature(test_payload, RENTVINE_SIGNING_KEY)
    
    print("🪝 RentVine Webhook Handler")
    print("=" * 50)
    print(f"Signing Key: {RENTVINE_SIGNING_KEY[:20]}...")
    print(f"Test Signature: {test_signature}")
    print("\nWebhook endpoint: POST /webhooks/rentvine")
    print("Health endpoint: GET /webhooks/health")
    print("\nStarting webhook server on http://localhost:8001")
    print("\nTest with curl:")
    print(f'curl -X POST http://localhost:8001/webhooks/rentvine \\')
    print(f'  -H "X-RentVine-Signature: {test_signature}" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f"  -d '{test_payload}'")
    
    # Run the webhook server
    uvicorn.run(app, host="0.0.0.0", port=8001)