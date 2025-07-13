"""
Position-based logic and department routing system
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class Department(str, Enum):
    """Available departments in property management"""
    MAINTENANCE = "maintenance"
    LEASING = "leasing"
    ACCOUNTING = "accounting"
    MANAGEMENT = "management"
    SECURITY = "security"
    CUSTOMER_SERVICE = "customer_service"

class Position(str, Enum):
    """Staff positions with different permissions"""
    # Management
    PROPERTY_MANAGER = "property_manager"
    ASSISTANT_MANAGER = "assistant_manager"
    
    # Department heads
    MAINTENANCE_SUPERVISOR = "maintenance_supervisor"
    LEASING_MANAGER = "leasing_manager"
    ACCOUNTING_MANAGER = "accounting_manager"
    
    # Staff
    MAINTENANCE_TECH = "maintenance_tech"
    LEASING_AGENT = "leasing_agent"
    ACCOUNTANT = "accountant"
    CUSTOMER_SERVICE_REP = "customer_service_rep"
    SECURITY_OFFICER = "security_officer"

class ResponsePermission(BaseModel):
    """Defines what a position can do"""
    can_approve_maintenance: bool = False
    can_approve_payments: bool = False
    can_modify_lease: bool = False
    can_send_legal_notices: bool = False
    can_waive_fees: bool = False
    can_schedule_repairs: bool = False
    can_access_financial_data: bool = False
    max_approval_amount: float = 0.0
    requires_approval_from: Optional[Position] = None

# Position permissions matrix
POSITION_PERMISSIONS = {
    Position.PROPERTY_MANAGER: ResponsePermission(
        can_approve_maintenance=True,
        can_approve_payments=True,
        can_modify_lease=True,
        can_send_legal_notices=True,
        can_waive_fees=True,
        can_schedule_repairs=True,
        can_access_financial_data=True,
        max_approval_amount=10000.0
    ),
    Position.ASSISTANT_MANAGER: ResponsePermission(
        can_approve_maintenance=True,
        can_approve_payments=True,
        can_modify_lease=False,
        can_send_legal_notices=False,
        can_waive_fees=True,
        can_schedule_repairs=True,
        can_access_financial_data=True,
        max_approval_amount=5000.0,
        requires_approval_from=Position.PROPERTY_MANAGER
    ),
    Position.MAINTENANCE_SUPERVISOR: ResponsePermission(
        can_approve_maintenance=True,
        can_schedule_repairs=True,
        max_approval_amount=2000.0
    ),
    Position.LEASING_MANAGER: ResponsePermission(
        can_modify_lease=True,
        can_access_financial_data=True,
        max_approval_amount=1000.0
    ),
    Position.MAINTENANCE_TECH: ResponsePermission(
        can_schedule_repairs=True,
        max_approval_amount=500.0,
        requires_approval_from=Position.MAINTENANCE_SUPERVISOR
    ),
    Position.LEASING_AGENT: ResponsePermission(
        can_access_financial_data=False,
        requires_approval_from=Position.LEASING_MANAGER
    ),
    Position.CUSTOMER_SERVICE_REP: ResponsePermission(
        requires_approval_from=Position.ASSISTANT_MANAGER
    )
}

class FormTemplate(BaseModel):
    """Form templates for different scenarios"""
    id: str
    name: str
    category: str
    required_fields: List[str]
    file_path: Optional[str] = None
    content: Optional[str] = None
    positions_can_use: List[Position]

# Standard forms library
STANDARD_FORMS = {
    "maintenance_request": FormTemplate(
        id="form_maint_001",
        name="Maintenance Request Form",
        category="maintenance",
        required_fields=["unit_number", "issue_description", "urgency", "contact_info"],
        positions_can_use=[Position.MAINTENANCE_SUPERVISOR, Position.MAINTENANCE_TECH]
    ),
    "payment_plan": FormTemplate(
        id="form_pay_001",
        name="Payment Plan Agreement",
        category="payment",
        required_fields=["tenant_name", "amount_owed", "payment_schedule", "signatures"],
        positions_can_use=[Position.PROPERTY_MANAGER, Position.ASSISTANT_MANAGER, Position.ACCOUNTING_MANAGER]
    ),
    "lease_renewal": FormTemplate(
        id="form_lease_001",
        name="Lease Renewal Form",
        category="lease",
        required_fields=["tenant_name", "unit_number", "new_terms", "rent_amount", "lease_duration"],
        positions_can_use=[Position.PROPERTY_MANAGER, Position.LEASING_MANAGER]
    ),
    "notice_to_cure": FormTemplate(
        id="form_legal_001",
        name="Notice to Cure or Quit",
        category="legal",
        required_fields=["tenant_name", "violation", "cure_period", "date"],
        positions_can_use=[Position.PROPERTY_MANAGER]
    ),
    "work_order": FormTemplate(
        id="form_work_001",
        name="Maintenance Work Order",
        category="maintenance",
        required_fields=["work_description", "assigned_to", "priority", "estimated_time"],
        positions_can_use=[Position.MAINTENANCE_SUPERVISOR, Position.MAINTENANCE_TECH]
    )
}

class SOP(BaseModel):
    """Standard Operating Procedure"""
    id: str
    department: Department
    scenario: str
    steps: List[str]
    required_forms: List[str]
    escalation_path: List[Position]
    time_limit_hours: Optional[int] = None

# Department SOPs
DEPARTMENT_SOPS = {
    "emergency_maintenance": SOP(
        id="sop_maint_emergency",
        department=Department.MAINTENANCE,
        scenario="Emergency maintenance request (flooding, no heat, etc.)",
        steps=[
            "1. Acknowledge receipt within 15 minutes",
            "2. Dispatch emergency maintenance immediately",
            "3. Contact tenant with ETA",
            "4. Document issue with photos",
            "5. Complete emergency work order",
            "6. Follow up within 24 hours"
        ],
        required_forms=["work_order"],
        escalation_path=[Position.MAINTENANCE_TECH, Position.MAINTENANCE_SUPERVISOR, Position.PROPERTY_MANAGER],
        time_limit_hours=4
    ),
    "rent_payment_late": SOP(
        id="sop_acct_late_payment",
        department=Department.ACCOUNTING,
        scenario="Late rent payment",
        steps=[
            "1. Send friendly reminder on day 3",
            "2. Call tenant on day 5",
            "3. Send formal notice on day 7",
            "4. Offer payment plan if needed",
            "5. Begin eviction process on day 15 (if no response)"
        ],
        required_forms=["payment_plan", "notice_to_cure"],
        escalation_path=[Position.ACCOUNTANT, Position.ACCOUNTING_MANAGER, Position.PROPERTY_MANAGER],
        time_limit_hours=24
    ),
    "lease_renewal_request": SOP(
        id="sop_lease_renewal",
        department=Department.LEASING,
        scenario="Tenant requests lease renewal",
        steps=[
            "1. Check tenant payment history",
            "2. Review current market rates",
            "3. Prepare renewal offer",
            "4. Send renewal form",
            "5. Schedule signing appointment"
        ],
        required_forms=["lease_renewal"],
        escalation_path=[Position.LEASING_AGENT, Position.LEASING_MANAGER],
        time_limit_hours=48
    )
}

class ResponseRouter:
    """Routes emails to appropriate department and generates responses based on position"""
    
    @staticmethod
    def route_to_department(email_category: str, urgency: str) -> Dict[str, Any]:
        """Determine which department should handle the email"""
        routing_rules = {
            "maintenance": {
                "department": Department.MAINTENANCE,
                "positions": [Position.MAINTENANCE_TECH, Position.MAINTENANCE_SUPERVISOR],
                "sop": "emergency_maintenance" if urgency == "emergency" else "standard_maintenance"
            },
            "payment": {
                "department": Department.ACCOUNTING,
                "positions": [Position.ACCOUNTANT, Position.ACCOUNTING_MANAGER],
                "sop": "rent_payment_late"
            },
            "lease": {
                "department": Department.LEASING,
                "positions": [Position.LEASING_AGENT, Position.LEASING_MANAGER],
                "sop": "lease_renewal_request"
            },
            "general": {
                "department": Department.CUSTOMER_SERVICE,
                "positions": [Position.CUSTOMER_SERVICE_REP],
                "sop": "general_inquiry"
            }
        }
        
        return routing_rules.get(email_category, routing_rules["general"])
    
    @staticmethod
    def get_position_response_options(position: Position, email_category: str) -> Dict[str, Any]:
        """Get available response options based on position"""
        permissions = POSITION_PERMISSIONS.get(position)
        available_forms = []
        available_actions = []
        
        # Determine available forms
        for form_id, form in STANDARD_FORMS.items():
            if position in form.positions_can_use and form.category == email_category:
                available_forms.append(form)
        
        # Determine available actions based on permissions
        if permissions.can_approve_maintenance and email_category == "maintenance":
            available_actions.extend([
                "Approve repair",
                "Schedule maintenance",
                "Request quote",
                "Dispatch technician"
            ])
        
        if permissions.can_approve_payments and email_category == "payment":
            available_actions.extend([
                "Approve payment plan",
                "Waive late fee",
                "Send payment reminder",
                "Process refund"
            ])
        
        if permissions.can_modify_lease and email_category == "lease":
            available_actions.extend([
                "Approve renewal",
                "Modify terms",
                "Schedule viewing",
                "Send renewal offer"
            ])
        
        return {
            "position": position,
            "permissions": permissions,
            "available_forms": available_forms,
            "available_actions": available_actions,
            "requires_approval": permissions.requires_approval_from is not None,
            "approval_from": permissions.requires_approval_from
        }
    
    @staticmethod
    def generate_response_template(
        position: Position,
        email_category: str,
        email_context: Dict[str, Any],
        selected_action: str,
        selected_forms: List[str]
    ) -> Dict[str, Any]:
        """Generate a response template based on position and selected action"""
        
        permissions = POSITION_PERMISSIONS.get(position)
        routing = ResponseRouter.route_to_department(email_category, email_context.get("urgency", "medium"))
        sop = DEPARTMENT_SOPS.get(routing["sop"])
        
        # Build response
        response = {
            "from_position": position.value,
            "from_department": routing["department"].value,
            "action": selected_action,
            "attachments": selected_forms,
            "requires_approval": permissions.requires_approval_from is not None,
            "approval_position": permissions.requires_approval_from.value if permissions.requires_approval_from else None,
            "sop_reference": sop.id if sop else None,
            "response_template": "",
            "next_steps": []
        }
        
        # Generate appropriate response template
        if email_category == "maintenance":
            if selected_action == "Approve repair":
                response["response_template"] = f"""
Dear {email_context.get('tenant_name', 'Tenant')},

Thank you for reporting the {email_context.get('issue', 'maintenance issue')}. 

I have approved the repair request and our maintenance team will address this issue.

Work Order #: {email_context.get('work_order_id', 'WO-' + datetime.now().strftime('%Y%m%d%H%M'))}
Scheduled Time: {email_context.get('scheduled_time', 'Within 24-48 hours')}
Technician: {email_context.get('technician', 'Will be assigned')}

Please ensure someone is available to provide access to the unit.

Best regards,
{position.value.replace('_', ' ').title()}
{routing['department'].value.replace('_', ' ').title()} Department
"""
            
        elif email_category == "payment":
            if selected_action == "Approve payment plan":
                response["response_template"] = f"""
Dear {email_context.get('tenant_name', 'Tenant')},

I understand your current situation regarding the rent payment.

I'm pleased to inform you that we can offer you a payment plan for the outstanding balance.

Current Balance: ${email_context.get('balance', '0.00')}
Payment Plan: {email_context.get('plan_details', 'To be discussed')}

Please find the attached payment plan agreement. Kindly review, sign, and return it within 48 hours.

Best regards,
{position.value.replace('_', ' ').title()}
{routing['department'].value.replace('_', ' ').title()} Department
"""
        
        # Add next steps from SOP
        if sop:
            response["next_steps"] = sop.steps[:3]  # First 3 steps
        
        return response

# Example usage function
def process_email_with_position(
    email_category: str,
    email_urgency: str,
    staff_position: Position,
    email_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Process an email based on staff position"""
    
    # Route to department
    routing = ResponseRouter.route_to_department(email_category, email_urgency)
    
    # Get position options
    options = ResponseRouter.get_position_response_options(staff_position, email_category)
    
    # Check if position can handle this category
    if not options["available_actions"]:
        return {
            "error": "You don't have permission to handle this type of request",
            "escalate_to": routing["positions"][0].value
        }
    
    return {
        "routing": routing,
        "options": options,
        "can_respond": True
    }