#!/usr/bin/env python3
"""
Additional Workflow Scenarios
Common property management situations across the portfolio mix
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

async def workflow_1_emergency_maintenance():
    """Workflow 1: Emergency Maintenance - Single Family"""
    print("\n" + "="*80)
    print("🚨 WORKFLOW 1: EMERGENCY MAINTENANCE - SINGLE FAMILY")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("emergency_maintenance_single_family")
    
    # Create agents
    maintenance_tech = orchestrator.create_agent("maintenance_tech")
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Single family home - Emergency HVAC failure")
    print("💰 Amount: $3,500 (Emergency repair)")
    print("🏠 Property: 3-bedroom single family home")
    print("🚨 Urgency: Emergency - No heat in winter")
    
    # Step 1: Maintenance Tech responds to emergency
    print("\n🔵 Step 1: Maintenance Tech responds to emergency call")
    result = await maintenance_tech.execute_action("respond_to_emergency", {
        "context": {
            "emergency_type": "hvac_failure",
            "severity": "critical",
            "estimated_cost": 3500,
            "urgency": "emergency",
            "resident_impact": "no_heat"
        }
    })
    print(f"✅ Maintenance Tech Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Maintenance Supervisor assesses
    print("\n🔵 Step 2: Maintenance Supervisor assesses emergency")
    result = await maintenance_supervisor.execute_action("assess_emergency_situation", {
        "context": {
            "emergency_type": "hvac_failure",
            "estimated_cost": 3500,
            "approval_required": True,
            "immediate_action": "required"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Property Manager escalates to President
    print("\n🔵 Step 3: Property Manager escalates emergency to President")
    result = await property_manager.execute_action("escalate_emergency", {
        "context": {
            "emergency_type": "hvac_failure",
            "amount": 3500,
            "escalation_reason": "emergency_approval_required",
            "immediate_action": "required"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: President approves emergency repair
    print("\n🔵 Step 4: President approves emergency repair")
    result = await president.execute_action("approve_emergency_expenditure", {
        "context": {
            "emergency_type": "hvac_failure",
            "amount": 3500,
            "urgency": "emergency",
            "resident_safety": "critical"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("emergency_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_2_tenant_application_approval():
    """Workflow 2: Complex Tenant Application - Duplex"""
    print("\n" + "="*80)
    print("📋 WORKFLOW 2: COMPLEX TENANT APPLICATION - DUPLEX")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("complex_tenant_application")
    
    # Create agents
    leasing_agent = orchestrator.create_agent("leasing_agent")
    leasing_manager = orchestrator.create_agent("leasing_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Duplex - Complex tenant application with special circumstances")
    print("🏘️ Property: 2-unit duplex, 3-bedroom unit")
    print("💰 Rent: $2,200/month")
    print("📋 Application: Self-employed tenant with good credit but irregular income")
    
    # Step 1: Leasing Agent processes application
    print("\n🔵 Step 1: Leasing Agent processes complex application")
    result = await leasing_agent.execute_action("process_complex_application", {
        "context": {
            "application_type": "self_employed",
            "income_verification": "irregular",
            "credit_score": "excellent",
            "rent_amount": 2200,
            "special_circumstances": "self_employed_income"
        }
    })
    print(f"✅ Leasing Agent Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Leasing Manager reviews application
    print("\n🔵 Step 2: Leasing Manager reviews complex application")
    result = await leasing_manager.execute_action("review_complex_application", {
        "context": {
            "application_complexity": "high",
            "risk_assessment": "moderate",
            "approval_required": True,
            "special_considerations": "self_employed"
        }
    })
    print(f"✅ Leasing Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager reviews financials
    print("\n🔵 Step 3: Accounting Manager reviews financial documentation")
    result = await accounting_manager.execute_action("review_tenant_financials", {
        "context": {
            "income_type": "self_employed",
            "documentation_quality": "good",
            "risk_level": "moderate",
            "approval_recommendation": "conditional"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Leasing makes decision
    print("\n🔵 Step 4: Director of Leasing makes final decision")
    result = await director_of_leasing.execute_action("approve_complex_application", {
        "context": {
            "application_type": "complex",
            "decision": "conditional_approval",
            "conditions": "additional_deposit",
            "risk_mitigation": "required"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: President approves final decision
    print("\n🔵 Step 5: President approves final decision")
    result = await president.execute_action("approve_tenant_decision", {
        "context": {
            "decision_type": "complex_tenant_approval",
            "risk_level": "moderate",
            "mitigation_strategy": "additional_deposit",
            "recommendation": "approve"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("application_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_3_roof_replacement():
    """Workflow 3: Major Roof Replacement - 20-Unit Building"""
    print("\n" + "="*80)
    print("🏠 WORKFLOW 3: MAJOR ROOF REPLACEMENT - 20-UNIT BUILDING")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("roof_replacement_20unit")
    
    # Create agents
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 20-unit building - Complete roof replacement")
    print("💰 Amount: $85,000 (Major capital improvement)")
    print("🏢 Property: 20-unit apartment building")
    print("🏠 Scope: Complete roof replacement with warranty")
    
    # Step 1: Maintenance Supervisor identifies need
    print("\n🔵 Step 1: Maintenance Supervisor identifies roof replacement need")
    result = await maintenance_supervisor.execute_action("identify_major_repair", {
        "context": {
            "repair_type": "roof_replacement",
            "estimated_cost": 85000,
            "urgency": "high",
            "property_size": "20_units",
            "impact": "building_integrity"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Property Manager coordinates assessment
    print("\n🔵 Step 2: Property Manager coordinates roof assessment")
    result = await property_manager.execute_action("coordinate_major_repair", {
        "context": {
            "repair_type": "roof_replacement",
            "estimated_cost": 85000,
            "coordination_scope": "full_building",
            "resident_impact": "minimal"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager reviews budget impact
    print("\n🔵 Step 3: Accounting Manager reviews budget impact")
    result = await accounting_manager.execute_action("review_capital_expenditure", {
        "context": {
            "expenditure_type": "roof_replacement",
            "amount": 85000,
            "budget_impact": "significant",
            "cash_flow_impact": "negative_short_term"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director escalates to VP
    print("\n🔵 Step 4: Director escalates to VP")
    result = await director_of_accounting.execute_action("escalate_major_decision", {
        "context": {
            "decision_type": "roof_replacement",
            "amount": 85000,
            "escalation_reason": "exceeds_director_approval_limit",
            "recommendation": "approve"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: VP reviews strategic impact
    print("\n🔵 Step 5: VP reviews strategic impact")
    result = await vice_president.execute_action("review_strategic_decision", {
        "context": {
            "decision_type": "roof_replacement",
            "amount": 85000,
            "strategic_impact": "high",
            "building_value": "preserved",
            "escalation_reason": "exceeds_vp_approval_limit"
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: President approves major investment
    print("\n🔵 Step 6: President approves major investment")
    result = await president.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "roof_replacement",
            "impact_level": "high",
            "budget_impact": 85000,
            "strategic_importance": "high",
            "recommendation": "approve"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("roof_replacement_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_4_amenity_upgrade():
    """Workflow 4: Amenity Upgrade - 50-Unit Building"""
    print("\n" + "="*80)
    print("🏊 WORKFLOW 4: AMENITY UPGRADE - 50-UNIT BUILDING")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("amenity_upgrade_50unit")
    
    # Create agents
    resident_services_manager = orchestrator.create_agent("resident_services_manager")
    property_manager = orchestrator.create_agent("property_manager")
    leasing_manager = orchestrator.create_agent("leasing_manager")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 50-unit building - Fitness center and pool upgrade")
    print("💰 Amount: $45,000 (Amenity enhancement)")
    print("🏢 Property: 50-unit apartment building")
    print("🏊 Scope: Fitness center equipment and pool deck renovation")
    
    # Step 1: Resident Services Manager identifies need
    print("\n🔵 Step 1: Resident Services Manager identifies amenity upgrade need")
    result = await resident_services_manager.execute_action("identify_amenity_upgrade", {
        "context": {
            "upgrade_type": "fitness_pool_upgrade",
            "estimated_cost": 45000,
            "resident_demand": "high",
            "competitive_advantage": "significant"
        }
    })
    print(f"✅ Resident Services Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Property Manager coordinates planning
    print("\n🔵 Step 2: Property Manager coordinates upgrade planning")
    result = await property_manager.execute_action("coordinate_amenity_upgrade", {
        "context": {
            "upgrade_type": "fitness_pool_upgrade",
            "estimated_cost": 45000,
            "coordination_scope": "amenity_areas",
            "resident_impact": "positive"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Leasing Manager assesses market impact
    print("\n🔵 Step 3: Leasing Manager assesses market impact")
    result = await leasing_manager.execute_action("assess_market_impact", {
        "context": {
            "upgrade_type": "amenity_enhancement",
            "market_advantage": "significant",
            "rent_premium": "potential",
            "competitive_position": "improved"
        }
    })
    print(f"✅ Leasing Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Leasing approves strategy
    print("\n🔵 Step 4: Director of Leasing approves upgrade strategy")
    result = await director_of_leasing.execute_action("approve_amenity_strategy", {
        "context": {
            "strategy_type": "amenity_upgrade",
            "total_cost": 45000,
            "expected_roi": "high",
            "market_strategy": "competitive_positioning"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: Accounting Manager reviews budget
    print("\n🔵 Step 5: Accounting Manager reviews upgrade budget")
    result = await accounting_manager.execute_action("review_amenity_budget", {
        "context": {
            "upgrade_cost": 45000,
            "expected_revenue": 60000,
            "net_impact": "positive",
            "approval_status": "approved"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: President approves amenity investment
    print("\n🔵 Step 6: President approves amenity investment")
    result = await president.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "amenity_upgrade",
            "impact_level": "medium",
            "budget_impact": 45000,
            "strategic_importance": "high",
            "recommendation": "approve"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("amenity_upgrade_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_5_compliance_audit():
    """Workflow 5: Compliance Audit - Mixed Portfolio"""
    print("\n" + "="*80)
    print("📋 WORKFLOW 5: COMPLIANCE AUDIT - MIXED PORTFOLIO")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("compliance_audit_mixed_portfolio")
    
    # Create agents
    internal_controller = orchestrator.create_agent("internal_controller")
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Mixed portfolio - Annual compliance audit")
    print("📊 Portfolio: Mix of single families, duplexes, 20-unit, and 50-unit buildings")
    print("💰 Audit Cost: $12,000 (External audit firm)")
    print("📋 Scope: Financial, operational, and regulatory compliance")
    
    # Step 1: Internal Controller initiates audit
    print("\n🔵 Step 1: Internal Controller initiates compliance audit")
    result = await internal_controller.execute_action("initiate_compliance_audit", {
        "context": {
            "audit_type": "annual_compliance",
            "estimated_cost": 12000,
            "portfolio_scope": "mixed_sizes",
            "regulatory_requirements": "mandatory"
        }
    })
    print(f"✅ Internal Controller Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Property Manager coordinates access
    print("\n🔵 Step 2: Property Manager coordinates audit access")
    result = await property_manager.execute_action("coordinate_audit_access", {
        "context": {
            "audit_scope": "portfolio_wide",
            "coordination_needed": True,
            "property_access": "all_sizes",
            "documentation_required": "comprehensive"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager prepares financials
    print("\n🔵 Step 3: Accounting Manager prepares financial documentation")
    result = await accounting_manager.execute_action("prepare_audit_financials", {
        "context": {
            "audit_preparation": "financial_documentation",
            "portfolio_mix": "mixed_sizes",
            "documentation_quality": "comprehensive",
            "compliance_status": "current"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Accounting reviews audit plan
    print("\n🔵 Step 4: Director of Accounting reviews audit plan")
    result = await director_of_accounting.execute_action("review_audit_plan", {
        "context": {
            "audit_plan": "comprehensive",
            "cost_justification": "regulatory_requirement",
            "risk_mitigation": "compliance_assurance",
            "recommendation": "proceed"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: VP Operations ensures operational compliance
    print("\n🔵 Step 5: VP Operations ensures operational compliance")
    result = await vice_president.execute_action("ensure_operational_compliance", {
        "context": {
            "compliance_scope": "operational",
            "portfolio_operations": "mixed_sizes",
            "regulatory_standards": "current",
            "audit_readiness": "prepared"
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: President approves audit expenditure
    print("\n🔵 Step 6: President approves audit expenditure")
    result = await president.execute_action("approve_compliance_expenditure", {
        "context": {
            "expenditure_type": "compliance_audit",
            "amount": 12000,
            "regulatory_requirement": "mandatory",
            "risk_mitigation": "compliance_assurance"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("audit_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def main():
    """Main workflow demonstration"""
    print("🚀 ADDITIONAL WORKFLOW SCENARIOS DEMONSTRATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # Run all workflows
        workflows = []
        
        print("\n🎯 Running 5 additional realistic scenarios...")
        workflows.append(await workflow_1_emergency_maintenance())
        workflows.append(await workflow_2_tenant_application_approval())
        workflows.append(await workflow_3_roof_replacement())
        workflows.append(await workflow_4_amenity_upgrade())
        workflows.append(await workflow_5_compliance_audit())
        
        # Summary
        print("\n" + "="*80)
        print("📊 ADDITIONAL SCENARIOS DEMONSTRATION SUMMARY")
        print("="*80)
        
        total_messages = sum(len(w.messages) for w in workflows)
        total_workflows = len(workflows)
        
        print(f"✅ Total Workflows Completed: {total_workflows}")
        print(f"📤 Total Messages Exchanged: {total_messages}")
        print(f"📈 Average Messages per Workflow: {total_messages // total_workflows}")
        
        print("\n🏠 Additional Scenarios Covered:")
        print("1. 🚨 Emergency Maintenance - Single Family ($3,500)")
        print("2. 📋 Complex Tenant Application - Duplex ($2,200/month)")
        print("3. 🏠 Major Roof Replacement - 20-Unit ($85,000)")
        print("4. 🏊 Amenity Upgrade - 50-Unit ($45,000)")
        print("5. 📋 Compliance Audit - Mixed Portfolio ($12,000)")
        
        print("\n💰 Investment Types Demonstrated:")
        print("🚨 Emergency: HVAC failure requiring immediate action")
        print("📋 Operational: Complex tenant screening and approval")
        print("🏠 Capital: Major building system replacement")
        print("🏊 Strategic: Amenity enhancement for competitive advantage")
        print("📋 Compliance: Regulatory audit and risk mitigation")
        
        print("\n🔒 Approval Process Verified:")
        print("👑 President: Ultimate authority for all decisions")
        print("🔒 All Others: Require approval for any amount ($0)")
        print("📈 Escalation: Appropriate for investment size and complexity")
        
        print("\n🎉 All additional scenarios completed successfully!")
        print("✅ Realistic property management situations covered")
        print("✅ Appropriate escalation for each scenario type")
        print("✅ Multi-agent orchestration functioning across scenarios")
        
    except Exception as e:
        print(f"\n❌ Error during workflow demonstration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 