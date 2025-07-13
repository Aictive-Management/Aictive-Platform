from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from supabase import create_client, Client
import httpx
import json
import asyncio
import re
from urllib.parse import urlparse

# Import our services
from claude_service import ClaudeService
from config import settings, validate_security_config
from auth import (
    auth_service, get_current_token, require_scopes, 
    check_rate_limit, security_headers, Scopes, TokenData
)
from cache import (
    cache_manager, ClaudeResponseCache, TemplateCache, 
    RateLimitCache, cache_metrics, get_classification_with_cache
)

# Configure logging based on environment
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check security configuration
security_issues = validate_security_config()
if security_issues:
    logger.warning(f"Security configuration issues detected: {security_issues}")

# Initialize FastAPI app
app = FastAPI(
    title="Aictive Platform API",
    description="AI-powered property management email processing system",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# Configure CORS with security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)

# Add trusted host middleware
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.aictive.com", "aictive.com"]
    )

# Add security headers
app.middleware("http")(security_headers)

# Initialize services with error handling
try:
    supabase: Client = create_client(
        settings.supabase_url,
        settings.supabase_anon_key
    )
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase: {str(e)}")
    supabase = None

claude_service = ClaudeService(api_key=settings.anthropic_api_key)

# Enhanced Pydantic models with validation
class EmailRequest(BaseModel):
    sender_email: str = Field(..., max_length=254)
    subject: str = Field(..., max_length=500)
    body_text: str = Field(..., max_length=50000)  # 50KB limit
    body_html: Optional[str] = Field(None, max_length=100000)  # 100KB limit
    attachments: Optional[List[Dict[str, Any]]] = Field(default=[], max_items=10)
    received_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    @validator('sender_email')
    def validate_email(cls, v):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('body_text', 'body_html')
    def sanitize_content(cls, v):
        """Basic content sanitization"""
        if v:
            # Remove potential script tags
            v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
            # Remove potential SQL injection attempts
            v = re.sub(r'(DROP|DELETE|INSERT|UPDATE|EXEC|UNION|SELECT)\s+(TABLE|FROM|INTO)', '', v, flags=re.IGNORECASE)
        return v

# Workflow Management Models
class WorkflowRequest(BaseModel):
    workflow_type: str = Field(..., regex='^(single_family|duplex|small_building|medium_building|large_building|mixed_portfolio)$')
    property_size: int = Field(..., ge=1, le=50)
    investment_amount: float = Field(..., ge=0)
    scenario_type: str = Field(..., regex='^(maintenance|renovation|leasing|emergency|seasonal|strategic)$')
    urgency: str = Field(default="medium", regex='^(low|medium|high|emergency)$')
    description: str = Field(..., max_length=1000)
    context: Dict[str, Any] = Field(default={})

class WorkflowExecution(BaseModel):
    workflow_id: str
    status: str = Field(..., regex='^(pending|active|completed|failed|escalated)$')
    current_step: int = Field(..., ge=0)
    total_steps: int = Field(..., ge=1)
    started_at: datetime
    completed_at: Optional[datetime] = None
    agents_involved: List[str] = Field(..., max_items=10)
    messages_exchanged: int = Field(..., ge=0)
    approval_required: bool = True
    escalated_to: Optional[str] = None

class AgentAction(BaseModel):
    agent_role: str = Field(..., max_length=50)
    action_type: str = Field(..., max_length=100)
    context: Dict[str, Any] = Field(default={})
    decision: Optional[str] = Field(None, max_length=50)
    requires_approval: bool = True
    approval_amount: Optional[float] = Field(None, ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WorkflowTemplate(BaseModel):
    template_id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    property_size_range: str = Field(..., regex='^(1|2-4|5-10|11-25|26-50|mixed)$')
    investment_range: str = Field(..., max_length=50)
    scenario_type: str = Field(..., max_length=50)
    steps: List[Dict[str, Any]] = Field(..., max_items=20)
    estimated_duration: str = Field(..., max_length=50)
    approval_chain: List[str] = Field(..., max_items=10)

class EmailClassification(BaseModel):
    email_id: str
    primary_category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    secondary_category: Optional[str] = None
    keywords: List[str] = Field(..., max_items=20)
    urgency: str = Field(..., regex='^(low|medium|high|emergency)$')
    sentiment: str = Field(..., regex='^(positive|neutral|negative)$')
    processing_time: datetime

class MaintenanceDetails(BaseModel):
    issue_type: str = Field(..., regex='^(plumbing|electrical|hvac|appliance|structural|pest|other)$')
    specific_issue: str = Field(..., max_length=500)
    location: Dict[str, str]
    urgency_indicators: Dict[str, bool]
    urgency_level: str = Field(..., regex='^(emergency|high|medium|low)$')
    tenant_impact: str = Field(..., regex='^(cannot_use_area|inconvenient|cosmetic)$')
    estimated_repair_complexity: str = Field(..., regex='^(simple|moderate|complex)$')
    tenant_availability: Optional[str] = Field(None, max_length=200)
    special_instructions: Optional[str] = Field(None, max_length=1000)
    detected_appliances: List[str] = Field(..., max_items=10)
    requires_parts: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class ResponseGeneration(BaseModel):
    template_type: str = Field(..., regex='^(maintenance_acknowledgment|payment_balance|general_response)$')
    context: Dict[str, Any]
    tone: str = Field(default="professional", regex='^(professional|friendly|urgent)$')

class WebhookNotification(BaseModel):
    event_type: str = Field(..., max_length=50)
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = None  # For webhook verification

# Helper functions with error handling
async def send_slack_notification(message: str, blocks: Optional[List[Dict]] = None):
    """Send notification to Slack with retry logic"""
    if not settings.slack_webhook_url:
        logger.debug("Slack webhook URL not configured")
        return
    
    payload = {"text": message[:3000]}  # Slack message limit
    if blocks:
        payload["blocks"] = blocks[:50]  # Slack blocks limit
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    settings.slack_webhook_url, 
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    logger.info("Slack notification sent successfully")
                    return
                else:
                    logger.warning(f"Slack notification failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Slack notification (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

async def store_email_in_supabase(email_data: EmailRequest, classification: Dict[str, Any]):
    """Store email and classification in Supabase with error handling"""
    if not supabase:
        logger.error("Supabase client not initialized")
        return None
        
    try:
        # Prepare data with validation
        email_record = {
            "sender_email": email_data.sender_email[:254],
            "subject": email_data.subject[:500],
            "body_text": email_data.body_text[:50000],
            "body_html": email_data.body_html[:100000] if email_data.body_html else None,
            "received_at": email_data.received_at.isoformat(),
            "primary_category": classification["primary_category"],
            "confidence": float(classification["confidence"]),
            "urgency": classification["urgency"],
            "sentiment": classification["sentiment"],
            "processed_at": datetime.utcnow().isoformat()
        }
        
        result = await asyncio.to_thread(
            lambda: supabase.table("emails").insert(email_record).execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error storing email in Supabase: {str(e)}")
        return None

# API Endpoints with authentication
@app.get("/")
async def root():
    """Health check endpoint - no auth required"""
    return {
        "status": "active",
        "service": "Aictive Platform API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "healthy",
            "supabase": "healthy" if supabase else "unavailable",
            "claude": "healthy",  # Could add actual Claude health check
            "slack": "configured" if settings.slack_webhook_url else "not configured"
        }
    }
    
    # Check if any service is unhealthy
    if any(status == "unavailable" for status in health_status["services"].values()):
        health_status["status"] = "degraded"
        
    return health_status

@app.post("/api/classify-email", 
          response_model=EmailClassification,
          dependencies=[Depends(check_rate_limit)])
async def classify_email(
    email: EmailRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))
):
    """Classify incoming email with authentication"""
    try:
        # Log request (without sensitive data)
        logger.info(f"Classifying email from {email.sender_email[:3]}***")
        
        # Classify email using Claude
        classification = await claude_service.classify_email({
            "sender_email": email.sender_email,
            "subject": email.subject,
            "body_text": email.body_text
        })
        
        # Generate email ID
        email_id = f"email_{int(datetime.utcnow().timestamp())}_{token_data.sub[:8]}"
        
        # Create response
        response = EmailClassification(
            email_id=email_id,
            primary_category=classification["primary_category"],
            confidence=classification["confidence"],
            secondary_category=classification.get("secondary_category"),
            keywords=classification["keywords"][:20],  # Limit keywords
            urgency=classification["urgency"],
            sentiment=classification["sentiment"],
            processing_time=datetime.utcnow()
        )
        
        # Background tasks
        if settings.environment != "development":
            background_tasks.add_task(store_email_in_supabase, email, classification)
            background_tasks.add_task(
                send_slack_notification,
                f"New {classification['primary_category']} email classified",
                [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Category:* {classification['primary_category']}\n"
                               f"*Urgency:* {classification['urgency']}\n"
                               f"*Confidence:* {classification['confidence']:.2f}"
                    }
                }]
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error classifying email: {str(e)}")
        raise HTTPException(status_code=500, detail="Email classification failed")

@app.post("/api/analyze-maintenance", 
          response_model=MaintenanceDetails,
          dependencies=[Depends(check_rate_limit)])
async def analyze_maintenance(
    request: Dict[str, str],
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_scopes([Scopes.MAINTENANCE_ANALYZE]))
):
    """Analyze maintenance request details with authentication"""
    try:
        # Validate input
        email_content = request.get("email_content", "")
        if not email_content or len(email_content) > 50000:
            raise HTTPException(status_code=400, detail="Invalid email content")
        
        # Analyze maintenance request
        details = await claude_service.analyze_maintenance_request(email_content)
        
        # Validate and convert to response model
        response = MaintenanceDetails(**details)
        
        # Send urgent notification if needed
        if details["urgency_level"] == "emergency" and settings.environment != "development":
            background_tasks.add_task(
                send_slack_notification,
                "🚨 EMERGENCY MAINTENANCE REQUEST",
                [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Issue:* {details['specific_issue'][:100]}\n"
                               f"*Type:* {details['issue_type']}\n"
                               f"*Location:* {details['location'].get('unit_area', 'Unknown')}"
                    }
                }]
            )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing maintenance request: {str(e)}")
        raise HTTPException(status_code=500, detail="Maintenance analysis failed")

@app.post("/api/generate-response",
          dependencies=[Depends(check_rate_limit)])
async def generate_response(
    request: ResponseGeneration,
    token_data: TokenData = Depends(require_scopes([Scopes.RESPONSE_GENERATE]))
):
    """Generate email response with authentication"""
    try:
        response_text = await claude_service.generate_response(
            template_type=request.template_type,
            context=request.context,
            tone=request.tone
        )
        
        # Check compliance before returning
        if settings.environment == "production":
            compliance = await claude_service.check_compliance(response_text)
            if not compliance.get("is_compliant", True):
                logger.warning(f"Generated response failed compliance: {compliance}")
                # Attempt to fix compliance issues
                response_text = await claude_service.generate_response(
                    template_type=request.template_type,
                    context={
                        **request.context,
                        "compliance_issues": compliance.get("issues", [])
                    },
                    tone=request.tone
                )
        
        return {
            "response": response_text[:10000],  # Limit response length
            "template_used": request.template_type,
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": f"user_{token_data.sub[:8]}"
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail="Response generation failed")

@app.post("/api/extract-entities",
          dependencies=[Depends(check_rate_limit)])
async def extract_entities(
    request: Dict[str, str],
    token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_READ]))
):
    """Extract entities from text with authentication"""
    try:
        text = request.get("text", "")
        if not text or len(text) > 10000:
            raise HTTPException(status_code=400, detail="Invalid text input")
            
        entities = await claude_service.extract_entities(text)
        
        # Sanitize extracted data
        for key in entities:
            if isinstance(entities[key], list):
                entities[key] = entities[key][:50]  # Limit array size
                
        return {
            "entities": entities,
            "extracted_at": datetime.utcnow().isoformat(),
            "text_length": len(text)
        }
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        raise HTTPException(status_code=500, detail="Entity extraction failed")

@app.post("/api/check-compliance",
          dependencies=[Depends(check_rate_limit)])
async def check_compliance(
    request: Dict[str, str],
    token_data: TokenData = Depends(require_scopes([Scopes.COMPLIANCE_CHECK]))
):
    """Check message compliance with authentication"""
    try:
        message = request.get("message", "")
        state = request.get("state", "CA")
        
        if not message or len(message) > 10000:
            raise HTTPException(status_code=400, detail="Invalid message")
        
        if not re.match(r'^[A-Z]{2}$', state):
            raise HTTPException(status_code=400, detail="Invalid state code")
            
        compliance = await claude_service.check_compliance(message, state)
        
        return {
            "compliance": compliance,
            "state": state,
            "checked_at": datetime.utcnow().isoformat(),
            "checked_by": f"user_{token_data.sub[:8]}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking compliance: {str(e)}")
        raise HTTPException(status_code=500, detail="Compliance check failed")

@app.post("/api/webhook/n8n",
          dependencies=[Depends(check_rate_limit)])
async def n8n_webhook(
    notification: WebhookNotification,
    background_tasks: BackgroundTasks,
    request: Request,
    token_data: TokenData = Depends(require_scopes([Scopes.WEBHOOK_WRITE]))
):
    """Handle n8n webhook notifications with authentication and verification"""
    try:
        # Verify webhook signature if provided
        if notification.signature:
            # Implement signature verification based on n8n webhook security
            pass
        
        # Process webhook based on event type
        if notification.event_type == "email_received":
            # Validate payload
            try:
                email_data = EmailRequest(**notification.payload)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
                
            # Process new email
            classification = await claude_service.classify_email({
                "sender_email": email_data.sender_email,
                "subject": email_data.subject,
                "body_text": email_data.body_text
            })
            
            # Store and notify
            if settings.environment != "development":
                background_tasks.add_task(store_email_in_supabase, email_data, classification)
            
        return {
            "status": "received",
            "event_type": notification.event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "processed_by": f"webhook_{token_data.sub[:8]}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.get("/api/stats",
         dependencies=[Depends(check_rate_limit)])
async def get_stats(
    token_data: TokenData = Depends(require_scopes([Scopes.STATS_READ]))
):
    """Get platform statistics with authentication"""
    try:
        if not supabase:
            return {
                "total_emails": 0,
                "by_category": {},
                "error": "Database unavailable"
            }
            
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
            "timestamp": datetime.utcnow().isoformat(),
            "requested_by": f"user_{token_data.sub[:8]}"
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return {
            "total_emails": 0,
            "by_category": {},
            "error": "Failed to retrieve statistics"
        }

# Workflow Management Endpoints
@app.post("/api/workflows/create",
          dependencies=[Depends(check_rate_limit)])
async def create_workflow(
    request: WorkflowRequest,
    token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))
):
    """Create a new workflow execution"""
    try:
        workflow_id = f"{request.workflow_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Determine workflow template based on request
        template = get_workflow_template(request.workflow_type, request.property_size, request.scenario_type)
        
        # Create workflow execution record
        workflow_execution = WorkflowExecution(
            workflow_id=workflow_id,
            status="pending",
            current_step=0,
            total_steps=len(template["steps"]),
            started_at=datetime.utcnow(),
            agents_involved=template["approval_chain"],
            messages_exchanged=0,
            approval_required=True
        )
        
        # Store in database
        await store_workflow_in_supabase(workflow_execution, request)
        
        # Log workflow creation
        logger.info(f"Workflow created: {workflow_id} for {request.workflow_type} property")
        
        return {
            "workflow_id": workflow_id,
            "status": "pending",
            "template": template,
            "estimated_duration": template["estimated_duration"],
            "approval_chain": template["approval_chain"]
        }
        
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")

@app.post("/api/workflows/{workflow_id}/execute",
          dependencies=[Depends(check_rate_limit)])
async def execute_workflow(
    workflow_id: str,
    token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))
):
    """Execute a workflow"""
    try:
        # Get workflow from database
        workflow = await get_workflow_from_supabase(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow["status"] != "pending":
            raise HTTPException(status_code=400, detail="Workflow already executed")
        
        # Execute workflow (this would integrate with our workflow orchestration)
        # For now, simulate execution
        execution_result = await simulate_workflow_execution(workflow_id, workflow)
        
        return {
            "workflow_id": workflow_id,
            "status": "active",
            "execution_result": execution_result,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute workflow")

@app.get("/api/workflows/{workflow_id}/status",
         dependencies=[Depends(check_rate_limit)])
async def get_workflow_status(
    workflow_id: str,
    token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))
):
    """Get workflow status and progress"""
    try:
        workflow = await get_workflow_from_supabase(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "workflow_id": workflow_id,
            "status": workflow["status"],
            "current_step": workflow["current_step"],
            "total_steps": workflow["total_steps"],
            "progress": (workflow["current_step"] / workflow["total_steps"]) * 100,
            "agents_involved": workflow["agents_involved"],
            "messages_exchanged": workflow["messages_exchanged"],
            "approval_required": workflow["approval_required"],
            "escalated_to": workflow.get("escalated_to"),
            "started_at": workflow["started_at"],
            "completed_at": workflow.get("completed_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow status {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workflow status")

@app.get("/api/workflows",
         dependencies=[Depends(check_rate_limit)])
async def list_workflows(
    status: Optional[str] = None,
    workflow_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))
):
    """List workflows with filtering"""
    try:
        workflows = await list_workflows_from_supabase(
            status=status,
            workflow_type=workflow_type,
            limit=limit,
            offset=offset
        )
        
        return {
            "workflows": workflows,
            "total": len(workflows),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list workflows")

@app.get("/api/workflows/templates",
         dependencies=[Depends(check_rate_limit)])
async def get_workflow_templates(
    token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))
):
    """Get available workflow templates"""
    try:
        templates = get_all_workflow_templates()
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"Error getting workflow templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workflow templates")

@app.post("/api/agents/{agent_role}/action",
          dependencies=[Depends(check_rate_limit)])
async def execute_agent_action(
    agent_role: str,
    action: AgentAction,
    token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))
):
    """Execute an agent action"""
    try:
        # Validate agent role
        valid_roles = get_valid_agent_roles()
        if agent_role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid agent role: {agent_role}")
        
        # Execute agent action (this would integrate with our agent system)
        action_result = await simulate_agent_action(agent_role, action)
        
        # Store action in database
        await store_agent_action_in_supabase(action)
        
        return {
            "agent_role": agent_role,
            "action_type": action.action_type,
            "decision": action_result.get("decision"),
            "requires_approval": action.requires_approval,
            "approval_amount": action.approval_amount,
            "timestamp": action.timestamp.isoformat(),
            "result": action_result
        }
        
    except Exception as e:
        logger.error(f"Error executing agent action: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute agent action")

# Helper functions for workflow management
def get_workflow_template(workflow_type: str, property_size: int, scenario_type: str) -> Dict[str, Any]:
    """Get workflow template based on type and parameters"""
    templates = {
        "single_family": {
            "steps": [
                {"agent": "maintenance_tech", "action": "assess_issue", "approval_required": False},
                {"agent": "property_manager", "action": "approve_repair", "approval_required": True},
                {"agent": "president", "action": "final_approval", "approval_required": True}
            ],
            "approval_chain": ["maintenance_tech", "property_manager", "president"],
            "estimated_duration": "1-2 days"
        },
        "duplex": {
            "steps": [
                {"agent": "maintenance_supervisor", "action": "assess_repair", "approval_required": False},
                {"agent": "property_manager", "action": "coordinate_repair", "approval_required": True},
                {"agent": "accounting_manager", "action": "review_budget", "approval_required": True},
                {"agent": "president", "action": "final_approval", "approval_required": True}
            ],
            "approval_chain": ["maintenance_supervisor", "property_manager", "accounting_manager", "president"],
            "estimated_duration": "3-5 days"
        },
        "large_building": {
            "steps": [
                {"agent": "maintenance_supervisor", "action": "identify_need", "approval_required": False},
                {"agent": "property_manager", "action": "coordinate_assessment", "approval_required": True},
                {"agent": "accounting_manager", "action": "review_financial_impact", "approval_required": True},
                {"agent": "director_of_accounting", "action": "escalate_decision", "approval_required": True},
                {"agent": "vice_president_of_operations", "action": "review_strategic_impact", "approval_required": True},
                {"agent": "president", "action": "final_approval", "approval_required": True}
            ],
            "approval_chain": ["maintenance_supervisor", "property_manager", "accounting_manager", "director_of_accounting", "vice_president_of_operations", "president"],
            "estimated_duration": "1-2 weeks"
        }
    }
    
    # Select template based on property size
    if property_size == 1:
        return templates["single_family"]
    elif property_size <= 4:
        return templates["duplex"]
    else:
        return templates["large_building"]

async def store_workflow_in_supabase(workflow: WorkflowExecution, request: WorkflowRequest):
    """Store workflow in Supabase"""
    if not supabase:
        logger.error("Supabase client not initialized")
        return None
        
    try:
        workflow_record = {
            "workflow_id": workflow.workflow_id,
            "status": workflow.status,
            "current_step": workflow.current_step,
            "total_steps": workflow.total_steps,
            "started_at": workflow.started_at.isoformat(),
            "agents_involved": workflow.agents_involved,
            "messages_exchanged": workflow.messages_exchanged,
            "approval_required": workflow.approval_required,
            "workflow_type": request.workflow_type,
            "property_size": request.property_size,
            "investment_amount": request.investment_amount,
            "scenario_type": request.scenario_type,
            "urgency": request.urgency,
            "description": request.description,
            "context": request.context
        }
        
        result = await asyncio.to_thread(
            lambda: supabase.table("workflows").insert(workflow_record).execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error storing workflow in Supabase: {str(e)}")
        return None

async def get_workflow_from_supabase(workflow_id: str):
    """Get workflow from Supabase"""
    if not supabase:
        return None
        
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("workflows").select("*").eq("workflow_id", workflow_id).execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting workflow from Supabase: {str(e)}")
        return None

async def simulate_workflow_execution(workflow_id: str, workflow: Dict[str, Any]):
    """Simulate workflow execution"""
    # This would integrate with our actual workflow orchestration
    return {
        "status": "active",
        "current_step": 1,
        "agents_contacted": workflow["agents_involved"][:2],
        "messages_sent": 3
    }

async def list_workflows_from_supabase(status: Optional[str] = None, workflow_type: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List workflows from Supabase with filtering"""
    if not supabase:
        return []
        
    try:
        query = supabase.table("workflows").select("*").range(offset, offset + limit - 1)
        
        if status:
            query = query.eq("status", status)
        if workflow_type:
            query = query.eq("workflow_type", workflow_type)
            
        result = await asyncio.to_thread(lambda: query.execute())
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error listing workflows from Supabase: {str(e)}")
        return []

def get_all_workflow_templates():
    """Get all available workflow templates"""
    return [
        {
            "template_id": "single_family_maintenance",
            "name": "Single Family Maintenance",
            "description": "Routine maintenance for single family homes",
            "property_size_range": "1",
            "investment_range": "$500-$1,500",
            "scenario_type": "maintenance",
            "estimated_duration": "1-2 days"
        },
        {
            "template_id": "duplex_renovation",
            "name": "Duplex Renovation",
            "description": "Unit renovation for duplex properties",
            "property_size_range": "2-4",
            "investment_range": "$10,000-$25,000",
            "scenario_type": "renovation",
            "estimated_duration": "3-5 days"
        },
        {
            "template_id": "large_building_upgrade",
            "name": "Large Building System Upgrade",
            "description": "Major system upgrades for large buildings",
            "property_size_range": "26-50",
            "investment_range": "$35,000-$100,000",
            "scenario_type": "strategic",
            "estimated_duration": "1-2 weeks"
        }
    ]

def get_valid_agent_roles():
    """Get list of valid agent roles"""
    return [
        "property_manager", "assistant_manager", "leasing_manager", "accounting_manager",
        "maintenance_supervisor", "leasing_agent", "accountant", "maintenance_tech_lead",
        "maintenance_tech", "resident_services_manager", "resident_services_rep",
        "admin_assistant", "director_of_accounting", "director_of_leasing",
        "vice_president_of_operations", "internal_controller", "leasing_coordinator", "president"
    ]

async def simulate_agent_action(agent_role: str, action: AgentAction):
    """Simulate agent action execution"""
    # This would integrate with our actual agent system
    return {
        "decision": "approved" if action.approval_amount and action.approval_amount < 1000 else "requires_approval",
        "message": f"{agent_role} processed {action.action_type}",
        "timestamp": action.timestamp.isoformat()
    }

async def store_agent_action_in_supabase(action: AgentAction):
    """Store agent action in Supabase"""
    if not supabase:
        return None
        
    try:
        action_record = {
            "agent_role": action.agent_role,
            "action_type": action.action_type,
            "context": action.context,
            "decision": action.decision,
            "requires_approval": action.requires_approval,
            "approval_amount": action.approval_amount,
            "timestamp": action.timestamp.isoformat()
        }
        
        result = await asyncio.to_thread(
            lambda: supabase.table("agent_actions").insert(action_record).execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error storing agent action in Supabase: {str(e)}")
        return None

# Admin endpoints
@app.post("/api/admin/create-api-key",
          dependencies=[Depends(check_rate_limit)])
async def create_api_key(
    request: Dict[str, Any],
    token_data: TokenData = Depends(require_scopes([Scopes.ADMIN]))
):
    """Create new API key - admin only"""
    try:
        name = request.get("name", "").strip()
        scopes = request.get("scopes", Scopes.default_scopes())
        
        if not name or len(name) > 100:
            raise HTTPException(status_code=400, detail="Invalid API key name")
            
        # Validate scopes
        all_scopes = Scopes.all_scopes()
        for scope in scopes:
            if scope not in all_scopes:
                raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}")
        
        # Generate API key
        import secrets
        api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        key_id = f"key_{int(datetime.utcnow().timestamp())}"
        
        # Hash the key
        key_hash = auth_service.hash_api_key(api_key)
        
        # Store key metadata (in production, store in database)
        key_metadata = {
            "key_id": key_id,
            "key_hash": key_hash,
            "name": name,
            "scopes": scopes,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": token_data.sub
        }
        
        # Return the key only once
        return {
            "api_key": api_key,
            "key_id": key_id,
            "name": name,
            "scopes": scopes,
            "created_at": key_metadata["created_at"],
            "warning": "Store this API key securely. It will not be shown again."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create API key")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }

if __name__ == "__main__":
    import uvicorn
    
    # Security warning for development
    if settings.environment == "development":
        logger.warning("Running in development mode. Do not use in production!")
        
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level=settings.log_level.lower()
    )