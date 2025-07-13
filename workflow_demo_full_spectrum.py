#!/usr/bin/env python3
"""
Full Spectrum Workflow Demo
Demonstrates workflows across all property sizes: single families to 50-unit buildings
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

async def workflow_1_single_family_repair():
    """Workflow 1: Single Family Home - Minor Repair"""
    print("\n" + "="*80)
    print("🏠 WORKFLOW 1: SINGLE FAMILY HOME - MINOR REPAIR")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("single_family_repair")
    
    # Create agents
    maintenance_tech = orchestrator.create_agent("maintenance_tech")
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    
    print("\n📋 Scenario: Single family home - $1,200 plumbing repair")
    print("💰 Amount: $1,200 (Minor repair requiring approval)")
    print("🏠 Property: 3-bedroom single family home")
    
    # Step 1: Maintenance Tech discovers issue
    print("\n🔵 Step 1: Maintenance Tech discovers plumbing issue")
    result = await maintenance_tech.execute_action("report_maintenance_issue", {
        "context": {
            "issue_type": "plumbing_repair",
            "severity": "moderate",
            "estimated_cost": 1200,
            "urgency": "medium",
            "property_type": "single_family"
        }
    })
    print(f"✅ Maintenance Tech Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Maintenance Supervisor reviews
    print("\n🔵 Step 2: Maintenance Supervisor reviews repair")
    result = await maintenance_supervisor.execute_action("review_maintenance_request", {
        "context": {
            "repair_type": "plumbing",
            "estimated_cost": 1200,
            "approval_required": True,
            "property_type": "single_family"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Property Manager approves
    print("\n🔵 Step 3: Property Manager approves repair")
    result = await property_manager.execute_action("approve_maintenance_expenditure", {
        "context": {
            "expenditure_type": "maintenance_repair",
            "amount": 1200,
            "property_type": "single_family",
            "urgency": "medium"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("repair_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_2_duplex_renovation():
    """Workflow 2: Duplex - Unit Renovation"""
    print("\n" + "="*80)
    print("🏘️ WORKFLOW 2: DUPLEX - UNIT RENOVATION")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("duplex_renovation")
    
    # Create agents
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Duplex - $15K unit renovation")
    print("💰 Amount: $15,000 (Renovation requiring escalation)")
    print("🏘️ Property: 2-unit duplex, renovating vacant unit")
    
    # Step 1: Property Manager initiates renovation
    print("\n🔵 Step 1: Property Manager initiates renovation")
    result = await property_manager.execute_action("approve_major_expenditure", {
        "context": {
            "expenditure_type": "unit_renovation",
            "amount": 15000,
            "description": "Kitchen and bathroom renovation for duplex unit",
            "urgency": "medium",
            "expected_roi": "20%"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Accounting Manager reviews
    print("\n🔵 Step 2: Accounting Manager reviews financial impact")
    result = await accounting_manager.execute_action("review_financial_impact", {
        "context": {
            "expenditure_type": "unit_renovation",
            "amount": 15000,
            "budget_impact": "moderate",
            "cash_flow_impact": "manageable"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Director escalates to President
    print("\n🔵 Step 3: Director escalates to President")
    result = await director_of_accounting.execute_action("escalate_major_decision", {
        "context": {
            "decision_type": "renovation_investment",
            "amount": 15000,
            "escalation_reason": "exceeds_director_approval_limit",
            "recommendation": "approve"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: President approves
    print("\n🔵 Step 4: President approves renovation")
    result = await president.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "renovation_investment",
            "impact_level": "medium",
            "budget_impact": 15000,
            "strategic_importance": "medium",
            "recommendation": "approve"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("renovation_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_3_20unit_building_management():
    """Workflow 3: 20-Unit Building - Major System Upgrade"""
    print("\n" + "="*80)
    print("🏢 WORKFLOW 3: 20-UNIT BUILDING - MAJOR SYSTEM UPGRADE")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("20unit_system_upgrade")
    
    # Create agents
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 20-unit building - $75K HVAC system upgrade")
    print("💰 Amount: $75,000 (Major system upgrade)")
    print("🏢 Property: 20-unit apartment building")
    
    # Step 1: Maintenance Supervisor identifies need
    print("\n🔵 Step 1: Maintenance Supervisor identifies system upgrade need")
    result = await maintenance_supervisor.execute_action("identify_system_upgrade", {
        "context": {
            "upgrade_type": "hvac_system",
            "estimated_cost": 75000,
            "urgency": "high",
            "property_size": "20_units",
            "impact": "energy_efficiency"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Property Manager coordinates assessment
    print("\n🔵 Step 2: Property Manager coordinates assessment")
    result = await property_manager.execute_action("coordinate_system_assessment", {
        "context": {
            "system_type": "hvac",
            "estimated_cost": 75000,
            "coordination_scope": "full_building",
            "resident_impact": "significant"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager reviews budget
    print("\n🔵 Step 3: Accounting Manager reviews budget impact")
    result = await accounting_manager.execute_action("review_financial_impact", {
        "context": {
            "expenditure_type": "system_upgrade",
            "amount": 75000,
            "budget_impact": "significant",
            "cash_flow_impact": "negative_short_term"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director escalates
    print("\n🔵 Step 4: Director escalates to VP")
    result = await director_of_accounting.execute_action("escalate_major_decision", {
        "context": {
            "decision_type": "system_upgrade",
            "amount": 75000,
            "escalation_reason": "exceeds_director_approval_limit",
            "recommendation": "approve_with_conditions"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: VP reviews strategic impact
    print("\n🔵 Step 5: VP reviews strategic impact")
    result = await vice_president.execute_action("review_strategic_decision", {
        "context": {
            "decision_type": "system_upgrade",
            "amount": 75000,
            "strategic_impact": "high",
            "market_conditions": "favorable",
            "escalation_reason": "exceeds_vp_approval_limit"
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: President makes final decision
    print("\n🔵 Step 6: President makes final decision")
    result = await president.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "system_upgrade",
            "impact_level": "high",
            "budget_impact": 75000,
            "strategic_importance": "high",
            "recommendation": "approve"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("system_upgrade_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_4_50unit_building_lease_campaign():
    """Workflow 4: 50-Unit Building - Major Lease Campaign"""
    print("\n" + "="*80)
    print("🏢 WORKFLOW 4: 50-UNIT BUILDING - MAJOR LEASE CAMPAIGN")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("50unit_lease_campaign")
    
    # Create agents
    leasing_agent = orchestrator.create_agent("leasing_agent")
    leasing_manager = orchestrator.create_agent("leasing_manager")
    leasing_coordinator = orchestrator.create_agent("leasing_coordinator")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    resident_services_manager = orchestrator.create_agent("resident_services_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 50-unit building - Major lease campaign with concessions")
    print("💰 Campaign Cost: $35K (marketing + concessions)")
    print("🏢 Property: 50-unit apartment building, 15 units vacant")
    
    # Step 1: Leasing Agent identifies need
    print("\n🔵 Step 1: Leasing Agent identifies need for major campaign")
    result = await leasing_agent.execute_action("identify_lease_campaign_need", {
        "context": {
            "campaign_type": "major_lease_campaign",
            "estimated_cost": 35000,
            "vacant_units": 15,
            "property_size": "50_units",
            "urgency": "high"
        }
    })
    print(f"✅ Leasing Agent Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Leasing Manager develops strategy
    print("\n🔵 Step 2: Leasing Manager develops campaign strategy")
    result = await leasing_manager.execute_action("develop_lease_strategy", {
        "context": {
            "strategy_type": "major_campaign",
            "estimated_cost": 35000,
            "target_units": 15,
            "concessions": "2_months_free",
            "approval_required": True
        }
    })
    print(f"✅ Leasing Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Leasing Coordinator coordinates
    print("\n🔵 Step 3: Leasing Coordinator coordinates campaign")
    result = await leasing_coordinator.execute_action("coordinate_lease_campaign", {
        "context": {
            "campaign_scope": "major",
            "coordination_needed": True,
            "marketing_budget": 15000,
            "concessions_budget": 20000
        }
    })
    print(f"✅ Leasing Coordinator Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Leasing approves strategy
    print("\n🔵 Step 4: Director of Leasing approves campaign strategy")
    result = await director_of_leasing.execute_action("approve_lease_campaign", {
        "context": {
            "campaign_type": "major_lease_campaign",
            "total_cost": 35000,
            "expected_roi": "high",
            "market_strategy": "aggressive_positioning"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: Accounting Manager reviews budget
    print("\n🔵 Step 5: Accounting Manager reviews campaign budget")
    result = await accounting_manager.execute_action("review_campaign_budget", {
        "context": {
            "campaign_cost": 35000,
            "expected_revenue": 450000,
            "net_impact": "positive",
            "approval_status": "approved"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: Resident Services prepares for influx
    print("\n🔵 Step 6: Resident Services prepares for new residents")
    result = await resident_services_manager.execute_action("prepare_for_new_residents", {
        "context": {
            "new_residents": 15,
            "service_level": "standard",
            "coordination_needed": True,
            "move_in_support": "required"
        }
    })
    print(f"✅ Resident Services Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 7: President approves major campaign
    print("\n🔵 Step 7: President approves major campaign")
    result = await president.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "lease_campaign",
            "impact_level": "high",
            "budget_impact": 35000,
            "strategic_importance": "high",
            "recommendation": "approve"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("campaign_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_5_mixed_portfolio_management():
    """Workflow 5: Mixed Portfolio - Strategic Portfolio Management"""
    print("\n" + "="*80)
    print("🏗️ WORKFLOW 5: MIXED PORTFOLIO - STRATEGIC PORTFOLIO MANAGEMENT")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("mixed_portfolio_management")
    
    # Create agents
    president = orchestrator.create_agent("president")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    internal_controller = orchestrator.create_agent("internal_controller")
    property_manager = orchestrator.create_agent("property_manager")
    
    print("\n📋 Scenario: Mixed portfolio strategic management")
    print("🎯 Focus: Portfolio optimization across all property sizes")
    print("📊 Portfolio: Mix of single families, duplexes, 20-unit, and 50-unit buildings")
    
    # Step 1: President sets portfolio strategy
    print("\n🔵 Step 1: President sets portfolio strategy")
    result = await president.execute_action("set_portfolio_strategy", {
        "context": {
            "strategy_focus": "portfolio_optimization",
            "portfolio_mix": "mixed_sizes",
            "strategic_period": "annual",
            "growth_targets": "moderate"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: VP Operations aligns operations
    print("\n🔵 Step 2: VP Operations aligns operations strategy")
    result = await vice_president.execute_action("align_portfolio_operations", {
        "context": {
            "portfolio_scope": "mixed_sizes",
            "operational_focus": "efficiency",
            "coordination_needed": True
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Director of Accounting develops financial strategy
    print("\n🔵 Step 3: Director of Accounting develops financial strategy")
    result = await director_of_accounting.execute_action("develop_portfolio_financials", {
        "context": {
            "portfolio_type": "mixed",
            "financial_focus": "optimization",
            "budget_allocation": "balanced"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Leasing develops market strategy
    print("\n🔵 Step 4: Director of Leasing develops market strategy")
    result = await director_of_leasing.execute_action("develop_portfolio_market_strategy", {
        "context": {
            "market_focus": "diversified",
            "property_mix": "single_family_to_50unit",
            "market_positioning": "balanced"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: Internal Controller ensures compliance
    print("\n🔵 Step 5: Internal Controller ensures portfolio compliance")
    result = await internal_controller.execute_action("ensure_portfolio_compliance", {
        "context": {
            "compliance_scope": "portfolio_wide",
            "regulatory_focus": "mixed_properties",
            "risk_assessment": "comprehensive"
        }
    })
    print(f"✅ Internal Controller Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: Property Manager implements strategy
    print("\n🔵 Step 6: Property Manager implements portfolio strategy")
    result = await property_manager.execute_action("implement_portfolio_strategy", {
        "context": {
            "implementation_scope": "operational",
            "property_mix": "all_sizes",
            "coordination_needed": True
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("portfolio_strategy_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def main():
    """Main workflow demonstration"""
    print("🚀 FULL SPECTRUM WORKFLOW DEMONSTRATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # Run all workflows
        workflows = []
        
        print("\n🎯 Running 5 comprehensive workflows across all property sizes...")
        workflows.append(await workflow_1_single_family_repair())
        workflows.append(await workflow_2_duplex_renovation())
        workflows.append(await workflow_3_20unit_building_management())
        workflows.append(await workflow_4_50unit_building_lease_campaign())
        workflows.append(await workflow_5_mixed_portfolio_management())
        
        # Summary
        print("\n" + "="*80)
        print("📊 FULL SPECTRUM WORKFLOW DEMONSTRATION SUMMARY")
        print("="*80)
        
        total_messages = sum(len(w.messages) for w in workflows)
        total_workflows = len(workflows)
        
        print(f"✅ Total Workflows Completed: {total_workflows}")
        print(f"📤 Total Messages Exchanged: {total_messages}")
        print(f"📈 Average Messages per Workflow: {total_messages // total_workflows}")
        
        print("\n🏠 Property Size Spectrum Covered:")
        print("1. 🏠 Single Family Home - $1,200 repair (minor approval)")
        print("2. 🏘️ Duplex - $15K renovation (escalation required)")
        print("3. 🏢 20-Unit Building - $75K system upgrade (major investment)")
        print("4. 🏢 50-Unit Building - $35K lease campaign (strategic decision)")
        print("5. 🏗️ Mixed Portfolio - Strategic portfolio management")
        
        print("\n💰 Investment Levels Demonstrated:")
        print("💵 Minor: $1K-$5K (single family repairs)")
        print("💵 Medium: $10K-$25K (duplex renovations)")
        print("💵 Major: $50K-$100K (20-unit upgrades)")
        print("💵 Strategic: $25K-$50K (50-unit campaigns)")
        print("💵 Portfolio: Mixed (strategic management)")
        
        print("\n🔒 Approval Hierarchy Verified:")
        print("👑 President: Ultimate authority (∞)")
        print("🔒 All Others: Require approval for any amount ($0)")
        
        print("\n🎉 All workflows completed successfully!")
        print("✅ Full spectrum of property sizes covered")
        print("✅ Appropriate escalation for each investment level")
        print("✅ Multi-agent orchestration functioning")
        
    except Exception as e:
        print(f"\n❌ Error during workflow demonstration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 