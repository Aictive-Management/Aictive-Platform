#!/usr/bin/env python3
"""
Seasonal Operations Workflows
Recurring property management scenarios throughout the year
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

async def workflow_1_spring_maintenance():
    """Workflow 1: Spring Maintenance - Mixed Portfolio"""
    print("\n" + "="*80)
    print("🌸 WORKFLOW 1: SPRING MAINTENANCE - MIXED PORTFOLIO")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("spring_maintenance_mixed_portfolio")
    
    # Create agents
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Spring maintenance across mixed portfolio")
    print("💰 Amount: $18,000 (Seasonal maintenance)")
    print("📊 Portfolio: Mix of single families, duplexes, 20-unit, and 50-unit buildings")
    print("🌸 Scope: HVAC servicing, landscaping, exterior repairs")
    
    # Step 1: Maintenance Supervisor plans spring maintenance
    print("\n🔵 Step 1: Maintenance Supervisor plans spring maintenance")
    result = await maintenance_supervisor.execute_action("plan_seasonal_maintenance", {
        "context": {
            "season": "spring",
            "estimated_cost": 18000,
            "portfolio_scope": "mixed_sizes",
            "maintenance_type": "preventive"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Property Manager coordinates across properties
    print("\n🔵 Step 2: Property Manager coordinates across properties")
    result = await property_manager.execute_action("coordinate_seasonal_maintenance", {
        "context": {
            "maintenance_scope": "portfolio_wide",
            "coordination_needed": True,
            "property_mix": "all_sizes",
            "timeline": "seasonal"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager reviews seasonal budget
    print("\n🔵 Step 3: Accounting Manager reviews seasonal budget")
    result = await accounting_manager.execute_action("review_seasonal_budget", {
        "context": {
            "seasonal_expenditure": "spring_maintenance",
            "amount": 18000,
            "budget_category": "preventive_maintenance",
            "approval_required": True
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: President approves seasonal maintenance
    print("\n🔵 Step 4: President approves seasonal maintenance")
    result = await president.execute_action("approve_seasonal_expenditure", {
        "context": {
            "expenditure_type": "seasonal_maintenance",
            "amount": 18000,
            "season": "spring",
            "portfolio_benefit": "preventive_care"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("spring_maintenance_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_2_summer_leasing_campaign():
    """Workflow 2: Summer Leasing Campaign - 50-Unit Building"""
    print("\n" + "="*80)
    print("☀️ WORKFLOW 2: SUMMER LEASING CAMPAIGN - 50-UNIT BUILDING")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("summer_leasing_campaign_50unit")
    
    # Create agents
    leasing_agent = orchestrator.create_agent("leasing_agent")
    leasing_manager = orchestrator.create_agent("leasing_manager")
    leasing_coordinator = orchestrator.create_agent("leasing_coordinator")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 50-unit building - Summer leasing campaign")
    print("💰 Campaign Cost: $28,000 (Summer marketing and concessions)")
    print("🏢 Property: 50-unit apartment building")
    print("☀️ Scope: Marketing campaign, move-in specials, pool season promotion")
    
    # Step 1: Leasing Agent identifies summer opportunity
    print("\n🔵 Step 1: Leasing Agent identifies summer opportunity")
    result = await leasing_agent.execute_action("identify_seasonal_opportunity", {
        "context": {
            "season": "summer",
            "campaign_type": "seasonal_leasing",
            "estimated_cost": 28000,
            "market_timing": "optimal"
        }
    })
    print(f"✅ Leasing Agent Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Leasing Manager develops summer strategy
    print("\n🔵 Step 2: Leasing Manager develops summer strategy")
    result = await leasing_manager.execute_action("develop_seasonal_strategy", {
        "context": {
            "season": "summer",
            "strategy_type": "leasing_campaign",
            "estimated_cost": 28000,
            "target_units": 12,
            "concessions": "summer_specials"
        }
    })
    print(f"✅ Leasing Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Leasing Coordinator coordinates campaign
    print("\n🔵 Step 3: Leasing Coordinator coordinates campaign")
    result = await leasing_coordinator.execute_action("coordinate_seasonal_campaign", {
        "context": {
            "campaign_scope": "summer_leasing",
            "coordination_needed": True,
            "marketing_budget": 15000,
            "concessions_budget": 13000
        }
    })
    print(f"✅ Leasing Coordinator Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Leasing approves strategy
    print("\n🔵 Step 4: Director of Leasing approves strategy")
    result = await director_of_leasing.execute_action("approve_seasonal_strategy", {
        "context": {
            "strategy_type": "summer_leasing",
            "total_cost": 28000,
            "expected_roi": "high",
            "seasonal_timing": "optimal"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: Accounting Manager reviews campaign budget
    print("\n🔵 Step 5: Accounting Manager reviews campaign budget")
    result = await accounting_manager.execute_action("review_campaign_budget", {
        "context": {
            "campaign_cost": 28000,
            "expected_revenue": 360000,
            "net_impact": "positive",
            "seasonal_factor": "summer_peak"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: President approves summer campaign
    print("\n🔵 Step 6: President approves summer campaign")
    result = await president.execute_action("approve_seasonal_campaign", {
        "context": {
            "campaign_type": "summer_leasing",
            "amount": 28000,
            "seasonal_timing": "optimal",
            "market_advantage": "significant"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("summer_campaign_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_3_fall_preparation():
    """Workflow 3: Fall Preparation - 20-Unit Building"""
    print("\n" + "="*80)
    print("🍂 WORKFLOW 3: FALL PREPARATION - 20-UNIT BUILDING")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("fall_preparation_20unit")
    
    # Create agents
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    accounting_manager = orchestrator.create_agent("accounting_manager")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: 20-unit building - Fall preparation and winterization")
    print("💰 Amount: $22,000 (Fall preparation)")
    print("🏢 Property: 20-unit apartment building")
    print("🍂 Scope: HVAC winterization, insulation, weatherproofing")
    
    # Step 1: Maintenance Supervisor plans fall preparation
    print("\n🔵 Step 1: Maintenance Supervisor plans fall preparation")
    result = await maintenance_supervisor.execute_action("plan_fall_preparation", {
        "context": {
            "season": "fall",
            "preparation_type": "winterization",
            "estimated_cost": 22000,
            "property_size": "20_units",
            "urgency": "high"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Property Manager coordinates preparation
    print("\n🔵 Step 2: Property Manager coordinates preparation")
    result = await property_manager.execute_action("coordinate_fall_preparation", {
        "context": {
            "preparation_scope": "full_building",
            "coordination_needed": True,
            "resident_impact": "minimal",
            "timeline": "before_winter"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Accounting Manager reviews preparation budget
    print("\n🔵 Step 3: Accounting Manager reviews preparation budget")
    result = await accounting_manager.execute_action("review_preparation_budget", {
        "context": {
            "preparation_type": "fall_winterization",
            "amount": 22000,
            "budget_impact": "moderate",
            "preventive_benefit": "high"
        }
    })
    print(f"✅ Accounting Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director escalates to President
    print("\n🔵 Step 4: Director escalates to President")
    result = await director_of_accounting.execute_action("escalate_preparation_decision", {
        "context": {
            "decision_type": "fall_preparation",
            "amount": 22000,
            "escalation_reason": "exceeds_director_approval_limit",
            "recommendation": "approve"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: President approves fall preparation
    print("\n🔵 Step 5: President approves fall preparation")
    result = await president.execute_action("approve_fall_preparation", {
        "context": {
            "preparation_type": "winterization",
            "amount": 22000,
            "preventive_benefit": "high",
            "winter_readiness": "critical"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("fall_preparation_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_4_winter_emergency_response():
    """Workflow 4: Winter Emergency Response - Single Family"""
    print("\n" + "="*80)
    print("❄️ WORKFLOW 4: WINTER EMERGENCY RESPONSE - SINGLE FAMILY")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("winter_emergency_single_family")
    
    # Create agents
    maintenance_tech = orchestrator.create_agent("maintenance_tech")
    maintenance_supervisor = orchestrator.create_agent("maintenance_supervisor")
    property_manager = orchestrator.create_agent("property_manager")
    president = orchestrator.create_agent("president")
    
    print("\n📋 Scenario: Single family home - Winter pipe burst emergency")
    print("💰 Amount: $4,200 (Emergency winter repair)")
    print("🏠 Property: 3-bedroom single family home")
    print("❄️ Urgency: Emergency - Frozen pipe burst, water damage")
    
    # Step 1: Maintenance Tech responds to winter emergency
    print("\n🔵 Step 1: Maintenance Tech responds to winter emergency")
    result = await maintenance_tech.execute_action("respond_to_winter_emergency", {
        "context": {
            "emergency_type": "pipe_burst",
            "severity": "critical",
            "estimated_cost": 4200,
            "urgency": "emergency",
            "weather_condition": "freezing"
        }
    })
    print(f"✅ Maintenance Tech Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: Maintenance Supervisor assesses winter damage
    print("\n🔵 Step 2: Maintenance Supervisor assesses winter damage")
    result = await maintenance_supervisor.execute_action("assess_winter_damage", {
        "context": {
            "damage_type": "pipe_burst",
            "estimated_cost": 4200,
            "approval_required": True,
            "immediate_action": "required"
        }
    })
    print(f"✅ Maintenance Supervisor Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Property Manager escalates winter emergency
    print("\n🔵 Step 3: Property Manager escalates winter emergency")
    result = await property_manager.execute_action("escalate_winter_emergency", {
        "context": {
            "emergency_type": "pipe_burst",
            "amount": 4200,
            "escalation_reason": "winter_emergency_approval_required",
            "immediate_action": "required"
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: President approves winter emergency repair
    print("\n🔵 Step 4: President approves winter emergency repair")
    result = await president.execute_action("approve_winter_emergency", {
        "context": {
            "emergency_type": "pipe_burst",
            "amount": 4200,
            "urgency": "emergency",
            "weather_condition": "freezing"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("winter_emergency_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def workflow_5_annual_budget_planning():
    """Workflow 5: Annual Budget Planning - Mixed Portfolio"""
    print("\n" + "="*80)
    print("📊 WORKFLOW 5: ANNUAL BUDGET PLANNING - MIXED PORTFOLIO")
    print("="*80)
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.start_workflow("annual_budget_planning_mixed_portfolio")
    
    # Create agents
    president = orchestrator.create_agent("president")
    vice_president = orchestrator.create_agent("vice_president_of_operations")
    director_of_accounting = orchestrator.create_agent("director_of_accounting")
    director_of_leasing = orchestrator.create_agent("director_of_leasing")
    internal_controller = orchestrator.create_agent("internal_controller")
    property_manager = orchestrator.create_agent("property_manager")
    
    print("\n📋 Scenario: Mixed portfolio - Annual budget planning")
    print("📊 Portfolio: Mix of single families, duplexes, 20-unit, and 50-unit buildings")
    print("💰 Budget Period: Annual planning cycle")
    print("📋 Scope: Comprehensive budget planning across all properties")
    
    # Step 1: President sets annual budget strategy
    print("\n🔵 Step 1: President sets annual budget strategy")
    result = await president.execute_action("set_annual_budget_strategy", {
        "context": {
            "budget_period": "annual",
            "portfolio_scope": "mixed_sizes",
            "strategic_focus": "growth_and_maintenance",
            "financial_targets": "realistic"
        }
    })
    print(f"✅ President Result: {result['output'].get('status', 'completed')}")
    
    # Step 2: VP Operations aligns operational budgets
    print("\n🔵 Step 2: VP Operations aligns operational budgets")
    result = await vice_president.execute_action("align_operational_budgets", {
        "context": {
            "budget_scope": "operational",
            "portfolio_mix": "mixed_sizes",
            "operational_focus": "efficiency",
            "coordination_needed": True
        }
    })
    print(f"✅ VP Operations Result: {result['output'].get('status', 'completed')}")
    
    # Step 3: Director of Accounting develops financial plan
    print("\n🔵 Step 3: Director of Accounting develops financial plan")
    result = await director_of_accounting.execute_action("develop_annual_financial_plan", {
        "context": {
            "financial_planning": "annual",
            "portfolio_type": "mixed",
            "financial_focus": "comprehensive",
            "budget_allocation": "balanced"
        }
    })
    print(f"✅ Director of Accounting Result: {result['output'].get('status', 'completed')}")
    
    # Step 4: Director of Leasing develops revenue strategy
    print("\n🔵 Step 4: Director of Leasing develops revenue strategy")
    result = await director_of_leasing.execute_action("develop_revenue_strategy", {
        "context": {
            "revenue_planning": "annual",
            "market_focus": "diversified",
            "property_mix": "single_family_to_50unit",
            "growth_targets": "realistic"
        }
    })
    print(f"✅ Director of Leasing Result: {result['output'].get('status', 'completed')}")
    
    # Step 5: Internal Controller ensures budget compliance
    print("\n🔵 Step 5: Internal Controller ensures budget compliance")
    result = await internal_controller.execute_action("ensure_budget_compliance", {
        "context": {
            "compliance_scope": "budget_planning",
            "regulatory_focus": "financial_standards",
            "risk_assessment": "comprehensive",
            "approval_required": True
        }
    })
    print(f"✅ Internal Controller Result: {result['output'].get('status', 'completed')}")
    
    # Step 6: Property Manager implements budget strategy
    print("\n🔵 Step 6: Property Manager implements budget strategy")
    result = await property_manager.execute_action("implement_budget_strategy", {
        "context": {
            "implementation_scope": "operational",
            "property_mix": "all_sizes",
            "budget_execution": "coordinated",
            "coordination_needed": True
        }
    })
    print(f"✅ Property Manager Result: {result['output'].get('status', 'completed')}")
    
    orchestrator.end_workflow("annual_budget_approved")
    print(f"\n📊 Workflow Summary: {len(orchestrator.messages)} messages exchanged")
    return orchestrator

async def main():
    """Main workflow demonstration"""
    print("🚀 SEASONAL OPERATIONS WORKFLOW DEMONSTRATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # Run all workflows
        workflows = []
        
        print("\n🎯 Running 5 seasonal operations scenarios...")
        workflows.append(await workflow_1_spring_maintenance())
        workflows.append(await workflow_2_summer_leasing_campaign())
        workflows.append(await workflow_3_fall_preparation())
        workflows.append(await workflow_4_winter_emergency_response())
        workflows.append(await workflow_5_annual_budget_planning())
        
        # Summary
        print("\n" + "="*80)
        print("📊 SEASONAL OPERATIONS DEMONSTRATION SUMMARY")
        print("="*80)
        
        total_messages = sum(len(w.messages) for w in workflows)
        total_workflows = len(workflows)
        
        print(f"✅ Total Workflows Completed: {total_workflows}")
        print(f"📤 Total Messages Exchanged: {total_messages}")
        print(f"📈 Average Messages per Workflow: {total_messages // total_workflows}")
        
        print("\n🌸 Seasonal Scenarios Covered:")
        print("1. 🌸 Spring Maintenance - Mixed Portfolio ($18,000)")
        print("2. ☀️ Summer Leasing Campaign - 50-Unit ($28,000)")
        print("3. 🍂 Fall Preparation - 20-Unit ($22,000)")
        print("4. ❄️ Winter Emergency Response - Single Family ($4,200)")
        print("5. 📊 Annual Budget Planning - Mixed Portfolio")
        
        print("\n💰 Seasonal Investment Types:")
        print("🌸 Spring: Preventive maintenance across portfolio")
        print("☀️ Summer: Peak leasing season campaigns")
        print("🍂 Fall: Winter preparation and weatherization")
        print("❄️ Winter: Emergency response to weather events")
        print("📊 Annual: Strategic budget planning and allocation")
        
        print("\n🔒 Seasonal Approval Process:")
        print("👑 President: Ultimate authority for all seasonal decisions")
        print("🔒 All Others: Require approval for any seasonal expenditure ($0)")
        print("📈 Escalation: Appropriate for seasonal timing and urgency")
        
        print("\n🎉 All seasonal scenarios completed successfully!")
        print("✅ Year-round property management operations covered")
        print("✅ Seasonal timing and urgency considerations")
        print("✅ Multi-agent orchestration functioning across seasons")
        
    except Exception as e:
        print(f"\n❌ Error during workflow demonstration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 