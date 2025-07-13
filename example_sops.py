"""
Example SOPs for the Aictive Platform
Demonstrates complete workflow definitions
"""
import json
from typing import Dict, List, Any

# Emergency Maintenance SOP
EMERGENCY_MAINTENANCE_SOP = {
    "name": "Emergency Maintenance Response",
    "description": "Handle emergency maintenance requests within 30 minutes",
    "department": "Maintenance",
    "category": "Emergency Response",
    "version": 1,
    "is_active": True,
    "steps": [
        {
            "step_id": "acknowledge_request",
            "name": "Acknowledge Emergency Request",
            "description": "Send immediate acknowledgment to tenant",
            "type": "automated",
            "assigned_role": "maintenance_supervisor",
            "actions": ["send_acknowledgment", "create_work_order"],
            "completion_criteria": {
                "all_actions_completed": True
            },
            "timeout_minutes": 5,
            "next_steps": ["assess_severity"]
        },
        {
            "step_id": "assess_severity",
            "name": "Assess Severity and Safety",
            "description": "Determine if issue poses immediate safety risk",
            "type": "decision",
            "assigned_role": "maintenance_supervisor",
            "actions": ["evaluate_safety_risk", "determine_response_level"],
            "completion_criteria": {
                "decision_made": True
            },
            "timeout_minutes": 10,
            "conditions": {
                "safety_risk": "dispatch_immediate",
                "no_safety_risk": "schedule_emergency"
            },
            "next_steps": []
        },
        {
            "step_id": "dispatch_immediate",
            "name": "Immediate Dispatch",
            "description": "Dispatch technician immediately for safety issues",
            "type": "parallel",
            "assigned_role": "maintenance_supervisor",
            "actions": ["assign_emergency_tech", "notify_property_manager"],
            "completion_criteria": {
                "all_actions_completed": True
            },
            "timeout_minutes": 15,
            "next_steps": ["notify_tenant_eta", "arrange_temporary_solution"]
        },
        {
            "step_id": "schedule_emergency",
            "name": "Schedule Emergency Repair",
            "description": "Schedule repair within 2 hours",
            "type": "automated",
            "assigned_role": "maintenance_supervisor",
            "actions": ["find_available_tech", "schedule_repair"],
            "completion_criteria": {
                "technician_assigned": True
            },
            "timeout_minutes": 20,
            "next_steps": ["notify_tenant_eta"]
        },
        {
            "step_id": "notify_tenant_eta",
            "name": "Notify Tenant of ETA",
            "description": "Send ETA to tenant via RentVine or email",
            "type": "automated",
            "assigned_role": "maintenance_supervisor",
            "actions": ["send_eta_notification"],
            "completion_criteria": {
                "notification_sent": True
            },
            "timeout_minutes": 5,
            "next_steps": ["perform_repair"]
        },
        {
            "step_id": "arrange_temporary_solution",
            "name": "Arrange Temporary Solution",
            "description": "Provide temporary accommodation if needed",
            "type": "human_action",
            "assigned_role": "assistant_manager",
            "actions": ["assess_habitability", "arrange_alternative"],
            "completion_criteria": {
                "solution_provided": True
            },
            "timeout_minutes": 30,
            "next_steps": ["perform_repair"]
        },
        {
            "step_id": "perform_repair",
            "name": "Perform Emergency Repair",
            "description": "Technician performs the emergency repair",
            "type": "human_action",
            "assigned_role": "maintenance_tech",
            "actions": ["complete_repair", "document_work", "take_photos"],
            "completion_criteria": {
                "repair_completed": True,
                "documentation_complete": True
            },
            "timeout_minutes": 180,
            "next_steps": ["quality_check"]
        },
        {
            "step_id": "quality_check",
            "name": "Quality Assurance Check",
            "description": "Supervisor verifies repair quality",
            "type": "human_action",
            "assigned_role": "maintenance_supervisor",
            "actions": ["inspect_repair", "approve_completion"],
            "completion_criteria": {
                "quality_approved": True
            },
            "timeout_minutes": 30,
            "next_steps": ["close_work_order"]
        },
        {
            "step_id": "close_work_order",
            "name": "Close Work Order",
            "description": "Complete work order and notify tenant",
            "type": "automated",
            "assigned_role": "maintenance_supervisor",
            "actions": ["update_work_order_status", "send_completion_notice", "request_feedback"],
            "completion_criteria": {
                "all_actions_completed": True
            },
            "timeout_minutes": 10,
            "next_steps": []
        }
    ],
    "required_roles": ["maintenance_supervisor", "maintenance_tech", "assistant_manager"],
    "escalation_path": ["maintenance_supervisor", "assistant_manager", "property_manager"],
    "time_limit_hours": 4,
    "priority": "emergency"
}

# Payment Plan Request SOP
PAYMENT_PLAN_SOP = {
    "name": "Payment Plan Request Processing",
    "description": "Process tenant requests for payment arrangements",
    "department": "Accounting",
    "category": "Financial",
    "version": 1,
    "is_active": True,
    "steps": [
        {
            "step_id": "receive_request",
            "name": "Receive Payment Plan Request",
            "description": "Log and acknowledge payment plan request",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["log_request", "send_acknowledgment"],
            "completion_criteria": {
                "request_logged": True
            },
            "timeout_minutes": 30,
            "next_steps": ["review_payment_history"]
        },
        {
            "step_id": "review_payment_history",
            "name": "Review Payment History",
            "description": "Check tenant's payment history and current balance",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["pull_payment_history", "calculate_balance", "check_previous_plans"],
            "completion_criteria": {
                "history_reviewed": True
            },
            "timeout_minutes": 60,
            "next_steps": ["assess_eligibility"]
        },
        {
            "step_id": "assess_eligibility",
            "name": "Assess Plan Eligibility",
            "description": "Determine if tenant qualifies for payment plan",
            "type": "decision",
            "assigned_role": "accountant",
            "actions": ["check_criteria", "calculate_risk_score"],
            "completion_criteria": {
                "eligibility_determined": True
            },
            "timeout_minutes": 120,
            "conditions": {
                "eligible": "create_plan_proposal",
                "not_eligible": "send_denial",
                "needs_review": "manager_review"
            },
            "next_steps": []
        },
        {
            "step_id": "create_plan_proposal",
            "name": "Create Payment Plan Proposal",
            "description": "Generate payment plan terms and schedule",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["calculate_installments", "set_due_dates", "add_terms"],
            "completion_criteria": {
                "proposal_created": True
            },
            "timeout_minutes": 60,
            "next_steps": ["send_proposal"]
        },
        {
            "step_id": "manager_review",
            "name": "Manager Review Required",
            "description": "Accounting manager reviews special cases",
            "type": "human_action",
            "assigned_role": "accounting_manager",
            "actions": ["review_case", "make_decision", "set_special_terms"],
            "completion_criteria": {
                "decision_made": True
            },
            "timeout_minutes": 1440,
            "conditions": {
                "approved": "create_plan_proposal",
                "denied": "send_denial"
            },
            "next_steps": []
        },
        {
            "step_id": "send_proposal",
            "name": "Send Plan Proposal",
            "description": "Send payment plan proposal to tenant",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["generate_agreement", "send_via_rentvine", "set_response_deadline"],
            "completion_criteria": {
                "proposal_sent": True
            },
            "timeout_minutes": 30,
            "next_steps": ["await_response"]
        },
        {
            "step_id": "await_response",
            "name": "Await Tenant Response",
            "description": "Wait for tenant to accept or reject plan",
            "type": "human_action",
            "assigned_role": "accountant",
            "actions": ["monitor_response", "send_reminder"],
            "completion_criteria": {
                "response_received": True
            },
            "timeout_minutes": 4320,
            "conditions": {
                "accepted": "finalize_agreement",
                "rejected": "close_request",
                "no_response": "send_final_notice"
            },
            "next_steps": []
        },
        {
            "step_id": "finalize_agreement",
            "name": "Finalize Payment Agreement",
            "description": "Execute payment plan agreement",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["activate_plan", "schedule_payments", "send_confirmation"],
            "completion_criteria": {
                "plan_activated": True
            },
            "timeout_minutes": 60,
            "next_steps": ["setup_monitoring"]
        },
        {
            "step_id": "setup_monitoring",
            "name": "Setup Payment Monitoring",
            "description": "Configure automatic payment tracking",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["create_payment_schedule", "set_alerts", "notify_management"],
            "completion_criteria": {
                "monitoring_active": True
            },
            "timeout_minutes": 30,
            "next_steps": []
        },
        {
            "step_id": "send_denial",
            "name": "Send Denial Notice",
            "description": "Notify tenant of payment plan denial",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["generate_denial_letter", "provide_alternatives", "send_notice"],
            "completion_criteria": {
                "notice_sent": True
            },
            "timeout_minutes": 60,
            "next_steps": ["close_request"]
        },
        {
            "step_id": "send_final_notice",
            "name": "Send Final Notice",
            "description": "Send final notice for no response",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["send_expiration_notice"],
            "completion_criteria": {
                "notice_sent": True
            },
            "timeout_minutes": 30,
            "next_steps": ["close_request"]
        },
        {
            "step_id": "close_request",
            "name": "Close Request",
            "description": "Close the payment plan request",
            "type": "automated",
            "assigned_role": "accountant",
            "actions": ["update_status", "archive_documents"],
            "completion_criteria": {
                "request_closed": True
            },
            "timeout_minutes": 30,
            "next_steps": []
        }
    ],
    "required_roles": ["accountant", "accounting_manager"],
    "escalation_path": ["accountant", "accounting_manager", "property_manager"],
    "time_limit_hours": 96,
    "priority": "medium"
}

# New Lease Application SOP
LEASE_APPLICATION_SOP = {
    "name": "New Lease Application Processing",
    "description": "Process new rental applications from start to move-in",
    "department": "Leasing",
    "category": "Applications",
    "version": 1,
    "is_active": True,
    "steps": [
        {
            "step_id": "receive_application",
            "name": "Receive Application",
            "description": "Log new rental application",
            "type": "automated",
            "assigned_role": "leasing_agent",
            "actions": ["create_application_record", "send_confirmation"],
            "completion_criteria": {
                "application_logged": True
            },
            "timeout_minutes": 30,
            "next_steps": ["initial_screening"]
        },
        {
            "step_id": "initial_screening",
            "name": "Initial Application Screening",
            "description": "Verify application completeness and basic requirements",
            "type": "automated",
            "assigned_role": "leasing_agent",
            "actions": ["check_completeness", "verify_income_docs", "check_id"],
            "completion_criteria": {
                "screening_complete": True
            },
            "timeout_minutes": 120,
            "conditions": {
                "complete": "background_check",
                "incomplete": "request_documents"
            },
            "next_steps": []
        },
        {
            "step_id": "request_documents",
            "name": "Request Missing Documents",
            "description": "Request any missing application documents",
            "type": "automated",
            "assigned_role": "leasing_agent",
            "actions": ["identify_missing_docs", "send_document_request"],
            "completion_criteria": {
                "request_sent": True
            },
            "timeout_minutes": 60,
            "next_steps": ["await_documents"]
        },
        {
            "step_id": "await_documents",
            "name": "Await Document Submission",
            "description": "Wait for applicant to submit documents",
            "type": "human_action",
            "assigned_role": "leasing_agent",
            "actions": ["monitor_submission", "send_reminders"],
            "completion_criteria": {
                "documents_received": True
            },
            "timeout_minutes": 4320,
            "conditions": {
                "received": "initial_screening",
                "not_received": "cancel_application"
            },
            "next_steps": []
        },
        {
            "step_id": "background_check",
            "name": "Run Background Check",
            "description": "Conduct credit and criminal background check",
            "type": "automated",
            "assigned_role": "senior_leasing_agent",
            "actions": ["run_credit_check", "run_criminal_check", "verify_employment"],
            "completion_criteria": {
                "all_checks_complete": True
            },
            "timeout_minutes": 1440,
            "next_steps": ["review_results"]
        },
        {
            "step_id": "review_results",
            "name": "Review Application Results",
            "description": "Review all screening results and make decision",
            "type": "decision",
            "assigned_role": "leasing_manager",
            "actions": ["analyze_credit_score", "review_criminal_history", "calculate_income_ratio"],
            "completion_criteria": {
                "decision_made": True
            },
            "timeout_minutes": 480,
            "conditions": {
                "approved": "send_approval",
                "denied": "send_denial",
                "conditional": "request_additional_info"
            },
            "next_steps": []
        },
        {
            "step_id": "request_additional_info",
            "name": "Request Additional Information",
            "description": "Request co-signer or additional deposit",
            "type": "automated",
            "assigned_role": "leasing_manager",
            "actions": ["determine_requirements", "send_conditional_approval"],
            "completion_criteria": {
                "request_sent": True
            },
            "timeout_minutes": 120,
            "next_steps": ["await_additional_info"]
        },
        {
            "step_id": "await_additional_info",
            "name": "Await Additional Information",
            "description": "Wait for applicant response to conditions",
            "type": "human_action",
            "assigned_role": "senior_leasing_agent",
            "actions": ["monitor_response", "follow_up"],
            "completion_criteria": {
                "response_received": True
            },
            "timeout_minutes": 2880,
            "conditions": {
                "conditions_met": "send_approval",
                "conditions_not_met": "send_denial"
            },
            "next_steps": []
        },
        {
            "step_id": "send_approval",
            "name": "Send Approval Notice",
            "description": "Notify applicant of approval and next steps",
            "type": "automated",
            "assigned_role": "leasing_manager",
            "actions": ["generate_approval_letter", "prepare_lease", "send_notification"],
            "completion_criteria": {
                "approval_sent": True
            },
            "timeout_minutes": 120,
            "next_steps": ["schedule_lease_signing"]
        },
        {
            "step_id": "schedule_lease_signing",
            "name": "Schedule Lease Signing",
            "description": "Coordinate lease signing appointment",
            "type": "human_action",
            "assigned_role": "leasing_agent",
            "actions": ["contact_applicant", "schedule_appointment", "send_reminder"],
            "completion_criteria": {
                "appointment_scheduled": True
            },
            "timeout_minutes": 1440,
            "next_steps": ["lease_signing"]
        },
        {
            "step_id": "lease_signing",
            "name": "Execute Lease Agreement",
            "description": "Complete lease signing and collect deposits",
            "type": "human_action",
            "assigned_role": "leasing_manager",
            "actions": ["review_lease_terms", "collect_signatures", "process_deposits"],
            "completion_criteria": {
                "lease_executed": True,
                "deposits_collected": True
            },
            "timeout_minutes": 120,
            "next_steps": ["schedule_move_in"]
        },
        {
            "step_id": "schedule_move_in",
            "name": "Schedule Move-In",
            "description": "Coordinate move-in date and walkthrough",
            "type": "parallel",
            "assigned_role": "leasing_agent",
            "actions": ["schedule_walkthrough", "order_keys", "prepare_welcome_packet"],
            "completion_criteria": {
                "all_actions_completed": True
            },
            "timeout_minutes": 1440,
            "next_steps": ["notify_maintenance", "update_systems"]
        },
        {
            "step_id": "notify_maintenance",
            "name": "Notify Maintenance",
            "description": "Alert maintenance to prepare unit",
            "type": "automated",
            "assigned_role": "leasing_agent",
            "actions": ["send_move_in_notice", "request_final_inspection"],
            "completion_criteria": {
                "maintenance_notified": True
            },
            "timeout_minutes": 60,
            "next_steps": []
        },
        {
            "step_id": "update_systems",
            "name": "Update Property Systems",
            "description": "Update all systems with new tenant info",
            "type": "automated",
            "assigned_role": "admin_assistant",
            "actions": ["update_tenant_database", "setup_rent_collection", "activate_portal_access"],
            "completion_criteria": {
                "all_systems_updated": True
            },
            "timeout_minutes": 240,
            "next_steps": []
        },
        {
            "step_id": "send_denial",
            "name": "Send Denial Notice",
            "description": "Notify applicant of application denial",
            "type": "automated",
            "assigned_role": "leasing_manager",
            "actions": ["generate_adverse_action_notice", "include_rights_info", "send_notification"],
            "completion_criteria": {
                "denial_sent": True
            },
            "timeout_minutes": 120,
            "next_steps": ["close_application"]
        },
        {
            "step_id": "cancel_application",
            "name": "Cancel Application",
            "description": "Cancel incomplete application",
            "type": "automated",
            "assigned_role": "leasing_agent",
            "actions": ["update_status", "send_cancellation_notice"],
            "completion_criteria": {
                "application_cancelled": True
            },
            "timeout_minutes": 60,
            "next_steps": ["close_application"]
        },
        {
            "step_id": "close_application",
            "name": "Close Application",
            "description": "Archive application and documents",
            "type": "automated",
            "assigned_role": "admin_assistant",
            "actions": ["archive_documents", "update_metrics", "cleanup_temp_data"],
            "completion_criteria": {
                "application_closed": True
            },
            "timeout_minutes": 120,
            "next_steps": []
        }
    ],
    "required_roles": ["leasing_agent", "senior_leasing_agent", "leasing_manager", "admin_assistant"],
    "escalation_path": ["leasing_agent", "senior_leasing_agent", "leasing_manager", "property_manager"],
    "time_limit_hours": 120,
    "priority": "high"
}

# Function to convert Python dict to JSON for database insertion
def export_sop_for_database(sop: Dict[str, Any]) -> str:
    """Export SOP in format ready for database insertion"""
    return json.dumps(sop, indent=2)

# Example usage
if __name__ == "__main__":
    print("Emergency Maintenance SOP:")
    print(export_sop_for_database(EMERGENCY_MAINTENANCE_SOP))
    print("\n" + "="*60 + "\n")
    
    print("Payment Plan SOP:")
    print(export_sop_for_database(PAYMENT_PLAN_SOP))
    print("\n" + "="*60 + "\n")
    
    print("Lease Application SOP:")
    print(export_sop_for_database(LEASE_APPLICATION_SOP))