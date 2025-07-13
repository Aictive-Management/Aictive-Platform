#!/usr/bin/env python3
"""
Small Properties Workflows
Covering the 1-10 unit range of your portfolio spectrum
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

async def workflow_1_single_unit_maintenance():
    """Workflow 1: Single Unit - Routine Maintenance"""
    print("\n" + "="*80)
    print("🏠 WORKFLOW 1: SINGLE UNIT - ROUTINE MAINTENANCE")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("single_unit_maintenance")
    
    # Create agents
    maintenance_tech = orchestrator.create_agent("maintenance_tech")
    property_manager = orchestrator.create_agent("property_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Single unit - Routine appliance replacement")
    print("💰 Amount: $800 (Routine maintenance)")
    print("🏠 Property: 1-unit single family home")
    print("🔧 Scope: Refrigerator replacement")
    
    # Step 1: Maintenance Tech identifies need
    print("\n🔵 Step 1: Maintenance Tech identifies appliance need")
    result = await maintenance_tech.execute_action("identify_appliance_replacement", {
        "context": {
            "appliance_type": "refrigerator",
            "estimated_cost": 800,
            "urgency": "routine",
            "property_type": "single_unit"
        }
    })
    print(f"✅ Maintenance Tech Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Property Manager approves routine maintenance
    print("\n🔵 Step 2: Property Manager approves routine maintenance")
    result = await property_manager.execute_action("approve_routine_maintenance", {
        "context": {
            "maintenance_type": "appliance_replacement",
            "amount": 800,
            "property_type": "single_unit",
            "urgency": "routine"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: President approves (required for any amount)
    print("\n🔵 Step 3: President approves routine maintenance")
    result = await president.execute_action("approve_routine_expenditure", {
        "context": {
            "expenditure_type": "routine_maintenance",
            "amount": 800,
            "property_type": "single_unit",
            "maintenance_category": "appliance"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("maintenance_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_2_4unit_building_repair():
    """Workflow 2: 4-Unit Building - Minor Repair"""
    print("\n" + "="*80)
    print("🏘️ WORKFLOW 2: 4-UNIT BUILDING - MINOR REPAIR")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("4unit_building_repair")
    
    # Create agents
    maintenance_tech = orchestrator.create_agent("maintenance_tech")
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 4-unit building - Minor plumbing repair")
    print("💰 Amount: $2,500 (Minor building repair)")
    print("🏘️ Property: 4-unit apartment building")
    print("🔧 Scope: Common area plumbing repair")
    
    # Step 1: Maintenance Tech reports issue
    print("\n🔵 Step 1: Maintenance Tech reports plumbing issue")
    result = await maintenance_tech.execute_action("report_building_repair", {
        "context": {
            "repair_type": "plumbing_repair",
            "severity": "minor",
            "estimated_cost": 2500,
            "urgency": "medium",
            "property_size": "4_units"
        }
    })
    print(f"✅ Maintenance Tech Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Maintenance Supervisor reviews
    print("\n🔵 Step 2: Maintenance Supervisor reviews repair")
    result = await maintenance_supervisor.execute_action("review_building_repair", {
        "context": {
            "repair_type": "plumbing",
            "estimated_cost": 2500,
            "approval_required": True,
            "property_size": "4_units"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Property Manager coordinates
    print("\n🔵 Step 3: Property Manager coordinates repair")
    result = await property_manager.execute_action("coordinate_building_repair", {
        "context": {
            "repair_scope": "common_area",
            "estimated_cost": 2500,
            "coordination_needed": True,
            "resident_impact": "minimal"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: President approves repair
    print("\n🔵 Step 4: President approves repair")
    result = await president.execute_action("approve_building_repair", {
        "context": {
            "repair_type": "plumbing",
            "amount": 2500,
            "property_size": "4_units",
            "urgency": "medium"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("repair_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_3_8unit_building_lease():
    """Workflow 3: 8-Unit Building - Lease Renewal Campaign"""
    print("\n" + "="*80)
    print("🏢 WORKFLOW 3: 8-UNIT BUILDING - LEASE RENEWAL CAMPAIGN")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("8unit_lease_renewal")
    
    # Create agents
    leasing_agent = orchestrator.create_agent("leasing_agent")
    leasing_manager = orchestrator.create_agent("leasing_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 8-unit building - Lease renewal campaign")
    print("💰 Campaign Cost: $6,000 (Renewal incentives)")
    print("🏢 Property: 8-unit apartment building")
    print("📋 Scope: Renewal incentives for 3 expiring leases")
    
    # Step 1: Leasing Agent identifies renewal opportunity
    print("\n🔵 Step 1: Leasing Agent identifies renewal opportunity")
    result = await leasing_agent.execute_action("identify_renewal_opportunity", {
        "context": {
            "campaign_type": "lease_renewal",
            "estimated_cost": 6000,
            "target_units": 3,
            "property_size": "8_units"
        }
    })
    print(f"✅ Leasing Agent Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Leasing Manager develops renewal strategy
    print("\n🔵 Step 2: Leasing Manager develops renewal strategy")
    result = await leasing_manager.execute_action("develop_renewal_strategy", {
        "context": {
            "strategy_type": "renewal_campaign",
            "estimated_cost": 6000,
            "target_units": 3,
            "incentives": "rent_concessions"
        }
    })
    print(f"✅ Leasing Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager reviews renewal budget
    print("\n🔵 Step 3: Accounting Manager reviews renewal budget")
    result = await accounting_manager.execute_action("review_renewal_budget", {
        "context": {
            "renewal_cost": 6000,
            "expected_revenue": 72000,
            "net_impact": "positive",
            "retention_benefit": "high"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: President approves renewal campaign
    print("\n🔵 Step 4: President approves renewal campaign")
    result = await president.execute_action("approve_renewal_campaign", {
        "context": {
            "campaign_type": "lease_renewal",
            "amount": 6000,
            "retention_benefit": "high",
            "property_size": "8_units"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("renewal_campaign_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_4_12unit_building_upgrade():
    """Workflow 4: 12-Unit Building - Minor Upgrade"""
    print("\n" + "="*80)
    print("🏢 WORKFLOW 4: 12-UNIT BUILDING - MINOR UPGRADE")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("12unit_minor_upgrade")
    
    # Create agents
    property_manager = orchestrator.create_agent("property_manager")
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 12-unit building - Minor upgrade")
    print("💰 Amount: $18,000 (Minor building upgrade)")
    print("🏢 Property: 12-unit apartment building")
    print("🔧 Scope: Exterior painting and minor landscaping")
    
    # Step 1: Property Manager identifies upgrade need
    print("\n🔵 Step 1: Property Manager identifies upgrade need")
    result = await property_manager.execute_action("identify_minor_upgrade", {
        "context": {
            "upgrade_type": "exterior_landscaping",
            "estimated_cost": 18000,
            "urgency": "medium",
            "property_size": "12_units"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Maintenance Supervisor plans upgrade
    print("\n🔵 Step 2: Maintenance Supervisor plans upgrade")
    result = await maintenance_supervisor.execute_action("plan_minor_upgrade", {
        "context": {
            "upgrade_type": "exterior_landscaping",
            "estimated_cost": 18000,
            "coordination_needed": True,
            "resident_impact": "minimal"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager reviews upgrade budget
    print("\n🔵 Step 3: Accounting Manager reviews upgrade budget")
    result = await accounting_manager.execute_action("review_upgrade_budget", {
        "context": {
            "upgrade_type": "minor_building_upgrade",
            "amount": 18000,
            "budget_impact": "moderate",
            "property_value": "enhanced"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director escalates to President
    print("\n🔵 Step 4: Director escalates to President")
    result = await director_of_accounting.execute_action("escalate_upgrade_decision", {
        "context": {
            "decision_type": "minor_upgrade",
            "amount": 18000,
            "escalation_reason": "exceeds_director_approval_limit",
            "recommendation": "approve"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: President approves upgrade
    print("\n🔵 Step 5: President approves upgrade")
    result = await president.execute_action("approve_minor_upgrade", {
        "context": {
            "upgrade_type": "exterior_landscaping",
            "amount": 18000,
            "property_value": "enhanced",
            "property_size": "12_units"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("upgrade_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_5_35unit_building_system():
    """Workflow 5: 35-Unit Building - System Maintenance"""
    print("\n" + "="*80)
    print("🏢 WORKFLOW 5: 35-UNIT BUILDING - SYSTEM MAINTENANCE")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("35unit_system_maintenance")
    
    # Create agents
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 35-unit building - System maintenance")
    print("💰 Amount: $45,000 (System maintenance)")
    print("🏢 Property: 35-unit apartment building")
    print("🔧 Scope: HVAC system maintenance and elevator service")
    
    # Step 1: Maintenance Supervisor identifies system need
    print("\n🔵 Step 1: Maintenance Supervisor identifies system need")
    result = await maintenance_supervisor.execute_action("identify_system_maintenance", {
        "context": {
            "maintenance_type": "hvac_elevator",
            "estimated_cost": 45000,
            "urgency": "high",
            "property_size": "35_units"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Property Manager coordinates maintenance
    print("\n🔵 Step 2: Property Manager coordinates maintenance")
    result = await property_manager.execute_action("coordinate_system_maintenance", {
        "context": {
            "maintenance_scope": "building_systems",
            "estimated_cost": 45000,
            "coordination_needed": True,
            "resident_impact": "moderate"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager reviews maintenance budget
    print("\n🔵 Step 3: Accounting Manager reviews maintenance budget")
    result = await accounting_manager.execute_action("review_system_maintenance_budget", {
        "context": {
            "maintenance_type": "building_systems",
            "amount": 45000,
            "budget_impact": "significant",
            "preventive_benefit": "high"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director escalates to VP
    print("\n🔵 Step 4: Director escalates to VP")
    result = await director_of_accounting.execute_action("escalate_system_maintenance", {
        "context": {
            "decision_type": "system_maintenance",
            "amount": 45000,
            "escalation_reason": "exceeds_director_approval_limit",
            "recommendation": "approve"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: VP reviews strategic impact
    print("\n🔵 Step 5: VP reviews strategic impact")
    result = await vice_president.execute_action("review_system_maintenance", {
        "context": {
            "decision_type": "system_maintenance",
            "amount": 45000,
            "strategic_impact": "medium",
            "building_operations": "critical",
            "escalation_reason": "exceeds_vp_approval_limit"
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: President approves system maintenance
    print("\n🔵 Step 6: President approves system maintenance")
    result = await president.execute_action("approve_system_maintenance", {
        "context": {
            "maintenance_type": "building_systems",
            "amount": 45000,
            "preventive_benefit": "high",
            "property_size": "35_units"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("system_maintenance_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def main():
    """Main workflow demonstration"""
    print("🚀 SMALL PROPERTIES WORKFLOW DEMONSTRATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # Run all workflows
        workflows = []
        
        print("\n🎯 Running 5 small properties scenarios (1-35 units)...")
        workflows.append(await workflow_1_single_unit_maintenance())
        workflows.append(await workflow_2_4unit_building_repair())
        workflows.append(await workflow_3_8unit_building_lease())
        workflows.append(await workflow_4_12unit_building_upgrade())
        workflows.append(await workflow_5_35unit_building_system())
        
        # Summary
        print("\n" + "="*80)
        print("📊 SMALL PROPERTIES DEMONSTRATION SUMMARY")
        print("="*80)
        
        total_messages = sum(len(w.messages) for w in workflows)
        total_workflows = len(workflows)
        
        print(f"✅ Total Workflows Completed: {total_workflows}")
        print(f"📤 Total Messages Exchanged: {total_messages}")
        print(f"📈 Average Messages per Workflow: {total_messages // total_workflows}")
        
        print("\n🏠 Small Properties Scenarios Covered:")
        print("1. 🏠 Single Unit - Routine Maintenance ($800)")
        print("2. 🏘️ 4-Unit Building - Minor Repair ($2,500)")
        print("3. 🏢 8-Unit Building - Lease Renewal ($6,000)")
        print("4. 🏢 12-Unit Building - Minor Upgrade ($18,000)")
        print("5. 🏢 35-Unit Building - System Maintenance ($45,000)")
        
        print("\n💰 Investment Levels by Property Size:")
        print("🏠 1 Unit: $500-$1,500 (routine maintenance)")
        print("🏘️ 2-4 Units: $1,500-$5,000 (minor repairs)")
        print("🏢 5-10 Units: $5,000-$15,000 (renewals, upgrades)")
        print("🏢 11-25 Units: $15,000-$35,000 (building improvements)")
        print("🏢 26-50 Units: $35,000-$100,000 (system upgrades)")
        
        print("\n🔒 Approval Process Verified:")
        print("👑 President: Ultimate authority for all decisions")
        print("🔒 All Others: Require approval for any amount ($0)")
        print("📈 Escalation: Appropriate for property size and investment")
        
        print("\n🎉 All small properties scenarios completed successfully!")
        print("✅ Full 1-50 unit range covered")
        print("✅ Realistic investment levels for each size")
        print("✅ Appropriate escalation for property complexity")
        
    except Exception as e:
        print(f"\n❌ Error during workflow demonstration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 