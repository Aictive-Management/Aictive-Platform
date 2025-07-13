"""
Complete email response system with 13-role integration
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from claude_service import ClaudeService
from integrations import ResponseOrchestrator, RentVineAPI, SlackApprovalFlow
from auth import get_current_token, TokenData, require_scopes, Scopes

logger = logging.getLogger(__name__)

# Models for the response system
class RoleConfig(BaseModel):
    """Configuration for each of the 13 roles"""
    role_id: str
    role_name: str
    department: str
    permissions: List[str]
    can_approve_up_to: float
    requires_approval_from: Optional[str] = None
    sop_access: List[str]
    form_access: List[str]
    kra: List[str]  # Key Result Areas

class EmailResponseRequest(BaseModel):
    """Request to generate and send email response"""
    email_id: str
    tenant_email: str
    tenant_id: Optional[str] = None  # RentVine tenant ID if available
    subject: str
    original_message: str
    classification: Dict[str, Any]
    
    # Response details
    selected_action: str
    response_template: str
    custom_message: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    
    # Staff details
    staff_id: str
    staff_role: str
    staff_name: str
    
    # Options
    send_via_rentvine: bool = True
    require_approval: bool = True
    create_work_order: bool = False
    work_order_details: Optional[Dict[str, Any]] = None

class ResponseStatus(BaseModel):
    """Status of a sent response"""
    response_id: str
    status: str  # pending_approval, approved, sent, failed
    method: str  # rentvine, email
    approval_status: Optional[str] = None
    sent_at: Optional[datetime] = None
    error: Optional[str] = None

# Load role configurations (in production, from database)
ROLE_CONFIGS = {
    "property_manager": RoleConfig(
        role_id="pm",
        role_name="Property Manager",
        department="Management",
        permissions=["all"],
        can_approve_up_to=10000,
        sop_access=["all"],
        form_access=["all"],
        kra=["Overall property performance", "Tenant satisfaction", "Financial targets"]
    ),
    "assistant_manager": RoleConfig(
        role_id="am",
        role_name="Assistant Manager",
        department="Management",
        permissions=["approve_maintenance", "approve_payments", "tenant_communication"],
        can_approve_up_to=5000,
        requires_approval_from="property_manager",
        sop_access=["maintenance", "tenant_relations", "payments"],
        form_access=["maintenance", "payment_plans", "notices"],
        kra=["Operational efficiency", "Response times", "Tenant issues resolution"]
    ),
    "maintenance_supervisor": RoleConfig(
        role_id="ms",
        role_name="Maintenance Supervisor",
        department="Maintenance",
        permissions=["approve_work_orders", "assign_technicians", "order_parts"],
        can_approve_up_to=2000,
        sop_access=["maintenance", "emergency_response", "vendor_management"],
        form_access=["work_orders", "vendor_forms", "inspection_reports"],
        kra=["Work order completion rate", "Response time", "Cost control"]
    ),
    "leasing_agent": RoleConfig(
        role_id="la",
        role_name="Leasing Agent",
        department="Leasing",
        permissions=["show_units", "process_applications", "send_lease_info"],
        can_approve_up_to=0,
        requires_approval_from="leasing_manager",
        sop_access=["leasing", "showings", "applications"],
        form_access=["applications", "lease_agreements", "move_in_forms"],
        kra=["Occupancy rate", "Lease renewals", "Prospect conversion"]
    ),
    # Add remaining 9 roles...
}

class EmailResponseSystem:
    """Main system for processing email responses with role-based logic"""
    
    def __init__(self):
        self.claude = ClaudeService()
        self.orchestrator = ResponseOrchestrator()
        self.rentvine = RentVineAPI()
        self.slack = SlackApprovalFlow()
        
    async def generate_role_based_response(
        self,
        request: EmailResponseRequest
    ) -> Dict[str, Any]:
        """Generate response based on role and context"""
        
        # Get role configuration
        role_config = ROLE_CONFIGS.get(request.staff_role)
        if not role_config:
            raise ValueError(f"Unknown role: {request.staff_role}")
        
        # Check permissions for the action
        if not self._check_permission(role_config, request.selected_action, request.classification):
            return {
                "error": "Permission denied",
                "message": f"Role {role_config.role_name} cannot perform {request.selected_action}",
                "escalate_to": role_config.requires_approval_from
            }
        
        # Generate contextual response
        context = {
            "tenant_name": await self._get_tenant_name(request.tenant_id, request.tenant_email),
            "issue": request.classification.get("specific_issue", "your concern"),
            "category": request.classification.get("primary_category"),
            "urgency": request.classification.get("urgency"),
            "staff_name": request.staff_name,
            "staff_title": role_config.role_name,
            "department": role_config.department,
            "action": request.selected_action,
            "original_message": request.original_message[:500]  # First 500 chars
        }
        
        # Use Claude to enhance the response
        enhanced_response = await self.claude.generate_response(
            template_type=request.response_template,
            context=context,
            tone="professional"
        )
        
        # Apply role-specific modifications
        final_response = self._apply_role_modifications(
            enhanced_response,
            role_config,
            request.classification
        )
        
        # Check if approval is needed
        needs_approval = (
            role_config.requires_approval_from is not None or
            request.require_approval or
            self._is_high_risk_action(request.selected_action)
        )
        
        return {
            "response_text": final_response,
            "needs_approval": needs_approval,
            "approval_from": role_config.requires_approval_from,
            "attachments": self._get_required_forms(role_config, request.selected_action),
            "metadata": {
                "role": role_config.role_name,
                "department": role_config.department,
                "action": request.selected_action,
                "category": request.classification.get("primary_category")
            }
        }
    
    async def send_response(
        self,
        request: EmailResponseRequest,
        response_data: Dict[str, Any]
    ) -> ResponseStatus:
        """Send the response through appropriate channel"""
        
        # Prepare response payload
        payload = {
            "staff_name": request.staff_name,
            "tenant_email": request.tenant_email,
            "tenant_id": request.tenant_id,
            "subject": f"Re: {request.subject}",
            "message": response_data["response_text"],
            "attachments": response_data.get("attachments", []),
            "metadata": response_data.get("metadata", {}),
            "original_message_id": request.email_id,
            "create_work_order": request.create_work_order,
            "work_order_details": request.work_order_details
        }
        
        # Send through orchestrator
        result = await self.orchestrator.send_response(
            response_data=payload,
            approval_required=response_data.get("needs_approval", True),
            use_rentvine=request.send_via_rentvine
        )
        
        # Create status response
        return ResponseStatus(
            response_id=result.get("response_id"),
            status=result.get("status", "failed"),
            method=result.get("method", "unknown"),
            approval_status="pending" if response_data.get("needs_approval") else "not_required",
            sent_at=datetime.utcnow() if result.get("status") == "sent" else None,
            error=result.get("error")
        )
    
    def _check_permission(
        self,
        role: RoleConfig,
        action: str,
        classification: Dict[str, Any]
    ) -> bool:
        """Check if role has permission for action"""
        if "all" in role.permissions:
            return True
            
        # Map actions to permissions
        action_permissions = {
            "approve_repair": "approve_maintenance",
            "schedule_maintenance": "approve_maintenance",
            "approve_payment_plan": "approve_payments",
            "send_notice": "tenant_communication",
            "create_work_order": "approve_work_orders"
        }
        
        required_permission = action_permissions.get(action, "tenant_communication")
        return required_permission in role.permissions
    
    def _apply_role_modifications(
        self,
        response: str,
        role: RoleConfig,
        classification: Dict[str, Any]
    ) -> str:
        """Apply role-specific modifications to response"""
        
        # Add approval limits if mentioned
        if "approval" in response.lower() and role.can_approve_up_to > 0:
            response += f"\n\n*Note: My approval authority is limited to ${role.can_approve_up_to}. Higher amounts require {role.requires_approval_from or 'senior management'} approval."
        
        # Add escalation notice for urgent issues
        if classification.get("urgency") == "emergency" and role.requires_approval_from:
            response += f"\n\n*This emergency issue has been escalated to {role.requires_approval_from} for immediate attention."
        
        # Add department signature
        response += f"\n\nBest regards,\n{role.department} Department"
        
        return response
    
    def _is_high_risk_action(self, action: str) -> bool:
        """Determine if action is high risk and needs approval"""
        high_risk_actions = [
            "send_legal_notice",
            "approve_large_refund",
            "terminate_lease",
            "waive_significant_fees"
        ]
        return action in high_risk_actions
    
    def _get_required_forms(self, role: RoleConfig, action: str) -> List[str]:
        """Get forms required for the action based on role"""
        form_mapping = {
            "approve_repair": ["work_order_form.pdf"],
            "approve_payment_plan": ["payment_agreement.pdf", "payment_schedule.xlsx"],
            "schedule_maintenance": ["maintenance_notice.pdf", "access_request.pdf"],
            "send_notice": ["official_notice.pdf"]
        }
        
        forms = form_mapping.get(action, [])
        # Filter based on role's form access
        return [f for f in forms if any(allowed in f for allowed in role.form_access)]
    
    async def _get_tenant_name(self, tenant_id: Optional[str], email: str) -> str:
        """Get tenant name from RentVine or use email"""
        if tenant_id:
            tenant_info = await self.rentvine.get_tenant_info(tenant_id)
            if "error" not in tenant_info:
                return tenant_info.get("name", email.split("@")[0])
        
        # Fallback to email prefix
        return email.split("@")[0].replace(".", " ").title()

# API Endpoints
app = FastAPI(title="Aictive Response System")

response_system = EmailResponseSystem()

@app.post("/api/responses/generate")
async def generate_response(
    request: EmailResponseRequest,
    token_data: TokenData = Depends(get_current_token)
) -> Dict[str, Any]:
    """Generate email response based on role and context"""
    try:
        response = await response_system.generate_role_based_response(request)
        return response
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/responses/send")
async def send_response(
    request: EmailResponseRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(get_current_token)
) -> ResponseStatus:
    """Send email response with approval flow"""
    try:
        # First generate the response
        response_data = await response_system.generate_role_based_response(request)
        
        if "error" in response_data:
            raise HTTPException(status_code=403, detail=response_data["error"])
        
        # Send it
        status = await response_system.send_response(request, response_data)
        
        # Log in background
        background_tasks.add_task(
            log_response,
            request.email_id,
            status.response_id,
            request.staff_id
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error sending response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/slack/actions")
async def handle_slack_actions(
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle Slack button actions for approvals"""
    from integrations import handle_slack_action
    return await handle_slack_action(payload)

async def log_response(email_id: str, response_id: str, staff_id: str):
    """Log response in database"""
    logger.info(f"Response {response_id} logged for email {email_id} by staff {staff_id}")