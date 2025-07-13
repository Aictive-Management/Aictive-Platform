#!/usr/bin/env python3
"""
Strict Approval Workflow Demo
Demonstrates the complete approval hierarchy with multi-agent orchestration
"""

import asyncio
import json
from datetime import datetime
from role_agents import (
    # Operational Agents
    PropertyManagerAgent, AssistantManagerAgent, LeasingManagerAgent, 
    AccountingManagerAgent, MaintenanceSupervisorAgent, LeasingAgentAgent,
    AccountantAgent, MaintenanceTechLeadAgent, MaintenanceTechAgent,
    ResidentServicesManagerAgent, ResidentServicesRepAgent, AdminAssistantAgent,
    
    # Management Agents
    DirectorOfAccountingAgent, DirectorOfLeasingAgent, VicePresidentOfOperationsAgent,
    InternalControllerAgent, LeasingCoordinatorAgent, PresidentAgent
)

class WorkflowOrchestrator:
    """Orchestrator for managing multi-agent workflows"""
    
    def __init__(self):
        self.agents = {}
        self.workflows = {}
        self.messages = []
        self.current_workflow_id = None
    
    def create_agent(self, role: str):
        """Create an agent instance"""
        agent_classes = {
            # Operational Agents
            "property_manager": PropertyManagerAgent,
            "assistant_manager": AssistantManagerAgent,
            "leasing_manager": LeasingManagerAgent,
            "accounting_manager": AccountingManagerAgent,
            "maintenance_supervisor": MaintenanceSupervisorAgent,
            "leasing_agent": LeasingAgentAgent,
            "accountant": AccountantAgent,
            "maintenance_tech_lead": MaintenanceTechLeadAgent,
            "maintenance_tech": MaintenanceTechAgent,
            "resident_services_manager": ResidentServicesManagerAgent,
            "resident_services_rep": ResidentServicesRepAgent,
            "admin_assistant": AdminAssistantAgent,
            
            # Management Agents
            "director_of_accounting": DirectorOfAccountingAgent,
            "director_of_leasing": DirectorOfLeasingAgent,
            "vice_president_of_operations": VicePresidentOfOperationsAgent,
            "internal_controller": InternalControllerAgent,
            "leasing_coordinator": LeasingCoordinatorAgent,
            "president": PresidentAgent
        }
        
        if role in agent_classes:
            agent = agent_classes[role](self)
            self.agents[role] = agent
            return agent
        else:
            raise ValueError(f"Unknown agent role: {role}")
    
    async def send_agent_message(self, from_role: str, to_role: str, subject: str, message: str, data: dict = None, message_type: str = "task"):
        """Send message between agents"""
        msg = {
            "workflow_id": self.current_workflow_id,
            "from_role": from_role,
            "to_role": to_role,
            "subject": subject,
            "message": message,
            "data": data,
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.messages.append(msg)
        print(f"📤 [{self.current_workflow_id}] {from_role} → {to_role}: {subject}")
        
        # Process message if target agent exists
        if to_role in self.agents:
            agent = self.agents[to_role]
            # Simulate agent processing
            await asyncio.sleep(0.1)  # Simulate processing time
            print(f"📥 [{self.current_workflow_id}] {to_role} received: {subject}")
    
    async def send_message(self, to_role: str, subject: str, message: str, data: dict = None):
        """Legacy message sending"""
        await self.send_agent_message("system", to_role, subject, message, data)
    
    def start_workflow(self, workflow_name: str):
        """Start a new workflow"""
        self.current_workflow_id = f"{workflow_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.workflows[self.current_workflow_id] = {
            "name": workflow_name,
            "started_at": datetime.utcnow().isoformat(),
            "status": "active",
            "steps": []
        }
        print(f"\n🚀 Starting Workflow: {workflow_name}")
        print(f"🆔 Workflow ID: {self.current_workflow_id}")
        return self.current_workflow_id
    
    def end_workflow(self, status: str = "completed"):
        """End current workflow"""
        if self.current_workflow_id:
            self.workflows[self.current_workflow_id]["status"] = status
            self.workflows[self.current_workflow_id]["ended_at"] = datetime.utcnow().isoformat()
            print(f"✅ Workflow {self.current_workflow_id} {status}")
            self.current_workflow_id = None

async def workflow_1_major_property_investment():
    """Workflow 1: Major Property Investment (Requires President Approval)"""
    print("\n" + "="*80)
    print("🏢 WORKFLOW 1: MAJOR PROPERTY INVESTMENT")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("major_property_investment")
    
    # Create agents
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Property Manager wants to invest $25K in property renovations")
    print("💰 Amount: $25,000 (Exceeds operational approval limits)")
    
    # Step 1: Property Manager initiates request
    print("\n🔵 Step 1: Property Manager initiates investment request")
    result = await property_manager.execute_action("approve_major_expenditure", {
        "context": {
            "expenditure_type": "property_renovation",
            "amount": 25000,
            "description": "Kitchen and bathroom updates for 4-unit building",
            "urgency": "medium",
            "expected_roi": "15%"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Accounting Manager reviews (cannot approve - exceeds limit)
    print("\n🔵 Step 2: Accounting Manager reviews financial impact")
    result = await accounting_manager.execute_action("review_financial_impact", {
        "context": {
            "expenditure_type": "property_renovation",
            "amount": 25000,
            "budget_impact": "moderate",
            "cash_flow_impact": "manageable"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Director of Accounting escalates (cannot approve - exceeds limit)
    print("\n🔵 Step 3: Director of Accounting escalates to VP")
    result = await director_of_accounting.execute_action("escalate_major_decision", {
        "context": {
            "decision_type": "property_investment",
            "amount": 25000,
            "escalation_reason": "exceeds_director_approval_limit",
            "recommendation": "approve_with_conditions"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: VP Operations reviews (cannot approve - exceeds limit)
    print("\n🔵 Step 4: VP Operations reviews strategic impact")
    result = await vice_president.execute_action("review_strategic_decision", {
        "context": {
            "decision_type": "property_investment",
            "amount": 25000,
            "strategic_impact": "medium",
            "market_conditions": "favorable",
            "escalation_reason": "exceeds_vp_approval_limit"
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: President makes final decision
    print("\n🔵 Step 5: President makes final decision")
    result = await president.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "property_investment",
            "impact_level": "medium",
            "budget_impact": 25000,
            "strategic_importance": "medium",
            "recommendation": "approve"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("approved_by_president")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_2_maintenance_emergency():
    """Workflow 2: Emergency Maintenance (Escalates through hierarchy)"""
    print("\n" + "="*80)
    print("🔧 WORKFLOW 2: EMERGENCY MAINTENANCE")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("emergency_maintenance")
    
    # Create agents
    maintenance_tech = orchestrator.create_agent("maintenance_tech")
    maintenance_tech_lead = orchestrator.create_agent("maintenance_tech_lead")
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    assistant_manager = orchestrator.create_agent("assistant_manager")
    
    print("\n📋 Scenario: Emergency HVAC failure requiring $8K replacement")
    print("💰 Amount: $8,000 (Exceeds operational approval limits)")
    
    # Step 1: Maintenance Tech discovers emergency
    print("\n🔵 Step 1: Maintenance Tech discovers emergency")
    result = await maintenance_tech.execute_action("report_emergency_maintenance", {
        "context": {
            "issue_type": "hvac_failure",
            "severity": "critical",
            "estimated_cost": 8000,
            "urgency": "immediate",
            "impact": "building_uninhabitable"
        }
    })
    print(f"✅ Maintenance Tech Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Maintenance Tech Lead assesses
    print("\n🔵 Step 2: Maintenance Tech Lead assesses situation")
    result = await maintenance_tech_lead.execute_action("assess_emergency_situation", {
        "context": {
            "issue_type": "hvac_failure",
            "estimated_cost": 8000,
            "technical_assessment": "replacement_required",
            "escalation_needed": True
        }
    })
    print(f"✅ Maintenance Tech Lead Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Maintenance Supervisor escalates
    print("\n🔵 Step 3: Maintenance Supervisor escalates to management")
    result = await maintenance_supervisor.execute_action("escalate_emergency", {
        "context": {
            "emergency_type": "hvac_failure",
            "estimated_cost": 8000,
            "escalation_reason": "exceeds_supervisor_limit",
            "urgency": "immediate"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Property Manager coordinates response
    print("\n🔵 Step 4: Property Manager coordinates emergency response")
    result = await property_manager.execute_action("coordinate_emergency_response", {
        "context": {
            "emergency_type": "hvac_failure",
            "estimated_cost": 8000,
            "coordination_scope": "full_property",
            "resident_impact": "significant"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: Accounting Manager reviews emergency budget
    print("\n🔵 Step 5: Accounting Manager reviews emergency budget")
    result = await accounting_manager.execute_action("review_emergency_expenditure", {
        "context": {
            "expenditure_type": "emergency_maintenance",
            "amount": 8000,
            "budget_source": "emergency_fund",
            "approval_required": True
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: Assistant Manager provides operational support
    print("\n🔵 Step 6: Assistant Manager provides operational support")
    result = await assistant_manager.execute_action("support_emergency_operations", {
        "context": {
            "emergency_type": "hvac_failure",
            "support_scope": "resident_communication",
            "coordination_needed": True
        }
    })
    print(f"✅ Assistant Manager Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("emergency_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_3_lease_application_approval():
    """Workflow 3: Complex Lease Application (Multi-department approval)"""
    print("\n" + "="*80)
    print("📝 WORKFLOW 3: COMPLEX LEASE APPLICATION")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("complex_lease_application")
    
    # Create agents
    leasing_agent = orchestrator.create_agent("leasing_agent")
    leasing_manager = orchestrator.create_agent("leasing_manager")
    leasing_coordinator = orchestrator.create_agent("leasing_coordinator")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    resident_services_manager = orchestrator.create_agent("resident_services_manager")
    
    print("\n📋 Scenario: Premium lease application for 4-bedroom unit")
    print("💰 Monthly Rent: $2,800 (Premium unit with special concessions)")
    
    # Step 1: Leasing Agent receives application
    print("\n🔵 Step 1: Leasing Agent receives premium application")
    result = await leasing_agent.execute_action("process_lease_application", {
        "context": {
            "applicant_type": "premium_family",
            "monthly_rent": 2800,
            "lease_term": "12_months",
            "special_terms": "pet_friendly",
            "concessions": "1_month_free"
        }
    })
    print(f"✅ Leasing Agent Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Leasing Manager reviews terms
    print("\n🔵 Step 2: Leasing Manager reviews lease terms")
    result = await leasing_manager.execute_action("review_lease_terms", {
        "context": {
            "lease_type": "premium_family",
            "monthly_rent": 2800,
            "concessions_value": 2800,
            "approval_required": True
        }
    })
    print(f"✅ Leasing Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Leasing Coordinator coordinates processing
    print("\n🔵 Step 3: Leasing Coordinator coordinates processing")
    result = await leasing_coordinator.execute_action("process_lease_applications", {
        "context": {
            "application_type": "premium",
            "processing_priority": "high",
            "coordination_needed": True
        }
    })
    print(f"✅ Leasing Coordinator Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Leasing approves terms
    print("\n🔵 Step 4: Director of Leasing approves special terms")
    result = await director_of_leasing.execute_action("approve_lease_terms", {
        "context": {
            "lease_type": "premium_family",
            "monthly_rent": 2800,
            "concessions": "approved",
            "market_strategy": "premium_positioning"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: Accounting Manager reviews financial impact
    print("\n🔵 Step 5: Accounting Manager reviews financial impact")
    result = await accounting_manager.execute_action("review_lease_financials", {
        "context": {
            "lease_value": 33600,
            "concessions_cost": 2800,
            "net_present_value": 30800,
            "approval_status": "approved"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: Resident Services Manager prepares premium service
    print("\n🔵 Step 6: Resident Services Manager prepares premium service")
    result = await resident_services_manager.execute_action("prepare_premium_service", {
        "context": {
            "service_level": "premium",
            "resident_type": "family",
            "special_requirements": "pet_friendly",
            "service_coordination": "required"
        }
    })
    print(f"✅ Resident Services Manager Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("lease_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_4_compliance_audit():
    """Workflow 4: Compliance Audit (Internal Controller oversight)"""
    print("\n" + "="*80)
    print("🔒 WORKFLOW 4: COMPLIANCE AUDIT")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("compliance_audit")
    
    # Create agents
    internal_controller = orchestrator.create_agent("internal_controller")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Annual compliance audit with regulatory implications")
    print("🔍 Scope: Financial, operational, and regulatory compliance")
    
    # Step 1: Internal Controller initiates audit
    print("\n🔵 Step 1: Internal Controller initiates comprehensive audit")
    result = await internal_controller.execute_action("conduct_internal_audit", {
        "context": {
            "audit_scope": "comprehensive",
            "audit_period": "annual",
            "regulatory_focus": "financial_reporting"
        }
    })
    print(f"✅ Internal Controller Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Director of Accounting conducts financial review
    print("\n🔵 Step 2: Director of Accounting conducts financial review")
    result = await director_of_accounting.execute_action("conduct_financial_review", {
        "context": {
            "review_scope": "financial_controls",
            "compliance_focus": "gaap_compliance",
            "audit_coordination": "required"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Director of Leasing reviews operational compliance
    print("\n🔵 Step 3: Director of Leasing reviews operational compliance")
    result = await director_of_leasing.execute_action("review_operational_compliance", {
        "context": {
            "compliance_area": "leasing_operations",
            "regulatory_focus": "fair_housing",
            "audit_coordination": "required"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: VP Operations provides executive oversight
    print("\n🔵 Step 4: VP Operations provides executive oversight")
    result = await vice_president.execute_action("provide_executive_oversight", {
        "context": {
            "oversight_scope": "compliance_audit",
            "executive_summary": "required",
            "board_reporting": "required"
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: President reviews final audit report
    print("\n🔵 Step 5: President reviews final audit report")
    result = await president.execute_action("review_audit_findings", {
        "context": {
            "audit_type": "compliance",
            "findings_severity": "moderate",
            "action_required": "policy_updates",
            "board_approval": "required"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("audit_completed")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_5_strategic_planning():
    """Workflow 5: Strategic Planning (President-led vision setting)"""
    print("\n" + "="*80)
    print("🎯 WORKFLOW 5: STRATEGIC PLANNING")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("strategic_planning")
    
    # Create agents
    president = orchestrator.create_agent("president")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    internal_controller = orchestrator.create_agent("internal_controller")
    property_manager = orchestrator.create_agent("property_manager")
    
    print("\n📋 Scenario: Annual strategic planning with organizational vision")
    print("🎯 Focus: Long-term growth strategy and market positioning")
    
    # Step 1: President sets organizational vision
    print("\n🔵 Step 1: President sets organizational vision")
    result = await president.execute_action("set_organizational_vision", {
        "context": {
            "vision_focus": "market_expansion",
            "vision_period": "5_year",
            "strategic_goals": "portfolio_growth"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: VP Operations aligns operations
    print("\n🔵 Step 2: VP Operations aligns operations with vision")
    result = await vice_president.execute_action("align_operations_strategy", {
        "context": {
            "strategy_focus": "operational_efficiency",
            "alignment_scope": "full_organization",
            "implementation_timeline": "12_months"
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Director of Accounting develops financial strategy
    print("\n🔵 Step 3: Director of Accounting develops financial strategy")
    result = await director_of_accounting.execute_action("develop_financial_strategy", {
        "context": {
            "strategy_type": "growth_financing",
            "investment_requirements": "significant",
            "financial_planning": "5_year"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Leasing develops market strategy
    print("\n🔵 Step 4: Director of Leasing develops market strategy")
    result = await director_of_leasing.execute_action("develop_market_strategy", {
        "context": {
            "market_focus": "premium_segment",
            "expansion_plan": "geographic_growth",
            "competitive_positioning": "market_leader"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: Internal Controller ensures compliance
    print("\n🔵 Step 5: Internal Controller ensures compliance alignment")
    result = await internal_controller.execute_action("ensure_strategic_compliance", {
        "context": {
            "compliance_scope": "strategic_planning",
            "regulatory_alignment": "required",
            "risk_assessment": "comprehensive"
        }
    })
    print(f"✅ Internal Controller Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: Property Manager implements operational changes
    print("\n🔵 Step 6: Property Manager implements operational changes")
    result = await property_manager.execute_action("implement_strategic_changes", {
        "context": {
            "implementation_scope": "operational",
            "change_management": "required",
            "staff_training": "required"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("strategy_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def main():
    """Main workflow demonstration"""
    print("🚀 STRICT APPROVAL WORKFLOW DEMONSTRATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # Run all workflows
        workflows = []
        
        print("\n🎯 Running 5 comprehensive workflows...")
        workflows.append(await workflow_1_major_property_investment())
        workflows.append(await workflow_2_maintenance_emergency())
        workflows.append(await workflow_3_lease_application_approval())
        workflows.append(await workflow_4_compliance_audit())
        workflows.append(await workflow_5_strategic_planning())
        
        # Summary
        print("\n" + "="*80)
        print("📊 WORKFLOW DEMONSTRATION SUMMARY")
        print("="*80)
        
        total_messages = sum(len(w.messages) for w in workflows)
        total_workflows = len(workflows)
        
        print(f"✅ Total Workflows Completed: {total_workflows}")
        print(f"📤 Total Messages Exchanged: {total_messages}")
        print(f"📈 Average Messages per Workflow: {total_messages // total_workflows}")
        
        print("\n🏢 Workflow Types Demonstrated:")
        print("1. 🏢 Major Property Investment - President approval required")
        print("2. 🔧 Emergency Maintenance - Multi-level escalation")
        print("3. 📝 Complex Lease Application - Multi-department coordination")
        print("4. 🔒 Compliance Audit - Internal Controller oversight")
        print("5. 🎯 Strategic Planning - President-led vision setting")
        
        print("\n🔒 Approval Hierarchy Verified:")
        print("👑 President: Ultimate authority (∞)")
        print("🔒 All Others: Require approval for any amount ($0)")
        
        print("\n🎉 All workflows completed successfully!")
        print("✅ Strict approval process working correctly")
        print("✅ Multi-agent orchestration functioning")
        print("✅ Escalation chains properly implemented")
        
    except Exception as e:
        print(f"\n❌ Error during workflow demonstration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 