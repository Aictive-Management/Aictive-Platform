from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx
import json
import asyncio

# Import our claude service
from claude_service import ClaudeService

# Import distributed tracing (optional - only if tracing dependencies are installed)
try:
    from trace_middleware import setup_tracing_middleware
    from distributed_tracing import get_tracer
    TRACING_ENABLED = True
    print("🔍 Distributed tracing enabled")
except ImportError:
    TRACING_ENABLED = False
    print("⚠️ Distributed tracing not available - install tracing dependencies to enable")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Aictive Platform API",
    description="AI-powered property management email processing system",
    version="1.0.0"
)

# Setup distributed tracing if available
if TRACING_ENABLED:
    tracer = setup_tracing_middleware(
        app,
        service_name=os.getenv("SERVICE_NAME", "aictive-platform"),
        service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
        environment=os.getenv("ENVIRONMENT", "development"),
        excluded_paths=["/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico"]
    )
    logger.info("Distributed tracing middleware configured")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)
claude_service = ClaudeService()

# Pydantic models
class EmailRequest(BaseModel):
    sender_email: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    received_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class EmailClassification(BaseModel):
    email_id: str
    primary_category: str
    confidence: float
    secondary_category: Optional[str] = None
    keywords: List[str]
    urgency: str
    sentiment: str
    processing_time: datetime

class MaintenanceDetails(BaseModel):
    issue_type: str
    specific_issue: str
    location: Dict[str, str]
    urgency_indicators: Dict[str, bool]
    urgency_level: str
    tenant_impact: str
    estimated_repair_complexity: str
    tenant_availability: Optional[str] = None
    special_instructions: Optional[str] = None
    detected_appliances: List[str]
    requires_parts: bool
    confidence_score: float

class ResponseGeneration(BaseModel):
    template_type: str
    context: Dict[str, Any]
    tone: str = "professional"

class WebhookNotification(BaseModel):
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Helper functions
async def send_slack_notification(message: str, blocks: Optional[List[Dict]] = None):
    """Send notification to Slack"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("Slack webhook URL not configured")
        return
    
    payload = {"text": message}
    if blocks:
        payload["blocks"] = blocks
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Slack notification failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")

async def store_email_in_supabase(email_data: EmailRequest, classification: Dict[str, Any]):
    """Store email and classification in Supabase"""
    try:
        # Store email
        email_record = {
            "sender_email": email_data.sender_email,
            "subject": email_data.subject,
            "body_text": email_data.body_text,
            "body_html": email_data.body_html,
            "received_at": email_data.received_at.isoformat(),
            "primary_category": classification["primary_category"],
            "confidence": classification["confidence"],
            "urgency": classification["urgency"],
            "sentiment": classification["sentiment"],
            "processed_at": datetime.utcnow().isoformat()
        }
        
        result = await asyncio.to_thread(
            lambda: supabase.table("emails").insert(email_record).execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error storing email in Supabase: {e}")
        return None

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "active",
        "service": "Aictive Platform API",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/classify-email", response_model=EmailClassification)
async def classify_email(
    email: EmailRequest,
    background_tasks: BackgroundTasks
):
    """Classify incoming email"""
    try:
        # Classify email using Claude
        classification = await claude_service.classify_email({
            "sender_email": email.sender_email,
            "subject": email.subject,
            "body_text": email.body_text
        })
        
        # Generate email ID
        email_id = f"email_{datetime.utcnow().timestamp()}"
        
        # Create response
        response = EmailClassification(
            email_id=email_id,
            primary_category=classification["primary_category"],
            confidence=classification["confidence"],
            secondary_category=classification.get("secondary_category"),
            keywords=classification["keywords"],
            urgency=classification["urgency"],
            sentiment=classification["sentiment"],
            processing_time=datetime.utcnow()
        )
        
        # Background tasks
        background_tasks.add_task(store_email_in_supabase, email, classification)
        background_tasks.add_task(
            send_slack_notification,
            f"New {classification['primary_category']} email from {email.sender_email}",
            [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Category:* {classification['primary_category']}\n"
                           f"*Urgency:* {classification['urgency']}\n"
                           f"*Subject:* {email.subject}"
                }
            }]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error classifying email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-maintenance", response_model=MaintenanceDetails)
async def analyze_maintenance(
    email_content: str,
    background_tasks: BackgroundTasks
):
    """Analyze maintenance request details"""
    try:
        # Analyze maintenance request
        details = await claude_service.analyze_maintenance_request(email_content)
        
        # Convert to response model
        response = MaintenanceDetails(**details)
        
        # Send urgent notification if needed
        if details["urgency_level"] == "emergency":
            background_tasks.add_task(
                send_slack_notification,
                "🚨 EMERGENCY MAINTENANCE REQUEST",
                [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Issue:* {details['specific_issue']}\n"
                               f"*Type:* {details['issue_type']}\n"
                               f"*Location:* {details['location']['unit_area']}"
                    }
                }]
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing maintenance request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-response")
async def generate_response(request: ResponseGeneration):
    """Generate email response"""
    try:
        response_text = await claude_service.generate_response(
            template_type=request.template_type,
            context=request.context,
            tone=request.tone
        )
        
        return {
            "response": response_text,
            "template_used": request.template_type,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract-entities")
async def extract_entities(text: str):
    """Extract entities from text"""
    try:
        entities = await claude_service.extract_entities(text)
        return {
            "entities": entities,
            "extracted_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-compliance")
async def check_compliance(
    message: str,
    state: str = "CA"
):
    """Check message compliance"""
    try:
        compliance = await claude_service.check_compliance(message, state)
        return {
            "compliance": compliance,
            "state": state,
            "checked_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhook/n8n")
async def n8n_webhook(
    notification: WebhookNotification,
    background_tasks: BackgroundTasks
):
    """Handle n8n webhook notifications"""
    try:
        # Process webhook based on event type
        if notification.event_type == "email_received":
            # Process new email
            email_data = EmailRequest(**notification.payload)
            classification = await claude_service.classify_email(notification.payload)
            
            # Store and notify
            background_tasks.add_task(store_email_in_supabase, email_data, classification)
            
        return {
            "status": "received",
            "event_type": notification.event_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get platform statistics"""
    try:
        # Get email count by category from Supabase
        result = await asyncio.to_thread(
            lambda: supabase.table("emails")
            .select("primary_category", count="exact")
            .execute()
        )
        
        # Group by category
        stats = {}
        if result.data:
            for email in result.data:
                category = email["primary_category"]
                stats[category] = stats.get(category, 0) + 1
        
        return {
            "total_emails": sum(stats.values()),
            "by_category": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "total_emails": 0,
            "by_category": {},
            "error": str(e)
        }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)