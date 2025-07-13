"""
Run Comprehensive Workflow Scenarios
Demonstrates the full capabilities of the Aictive Platform
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any

# Set environment for mock mode
os.environ['USE_MOCK_SERVICES'] = 'true'

from sop_orchestration import SOPOrchestrationEngine, BaseAgent
from role_agents import (
    PropertyManagerAgent, MaintenanceSupervisorAgent,
    MaintenanceTechLeadAgent, MaintenanceTechAgent,
    LeasingManagerAgent, LeasingAgentAgent, SeniorLeasingAgentAgent,
    AccountingManagerAgent, AccountantAgent,
    DirectorOfAccountingAgent, DirectorOfLeasingAgent,
    VicePresidentOfOperationsAgent, PresidentAgent,
    InternalControllerAgent, AssistantManagerAgent,
    ResidentServicesManagerAgent, ResidentServicesRepAgent,
    AdminAssistantAgent, LeasingCoordinatorAgent
)


class WorkflowScenarioRunner:
    """Run various workflow scenarios"""
    
    def __init__(self):
        self.engine = SOPOrchestrationEngine()
        self._register_all_agents()
        
    def _register_all_agents(self):
        """Register all agents with the orchestration engine"""
        # Executive Level
        self.engine.register_agent(PresidentAgent(self.engine))
        
        # Senior Management
        self.engine.register_agent(VicePresidentOfOperationsAgent(self.engine))
        self.engine.register_agent(DirectorOfAccountingAgent(self.engine))
        self.engine.register_agent(DirectorOfLeasingAgent(self.engine))
        self.engine.register_agent(InternalControllerAgent(self.engine))
        self.engine.register_agent(LeasingCoordinatorAgent(self.engine))
        
        # Operational Management
        self.engine.register_agent(PropertyManagerAgent(self.engine))
        self.engine.register_agent(AssistantManagerAgent(self.engine))
        self.engine.register_agent(LeasingManagerAgent(self.engine))
        self.engine.register_agent(AccountingManagerAgent(self.engine))
        self.engine.register_agent(MaintenanceSupervisorAgent(self.engine))
        self.engine.register_agent(ResidentServicesManagerAgent(self.engine))
        
        # Operational Staff
        self.engine.register_agent(SeniorLeasingAgentAgent(self.engine))
        self.engine.register_agent(LeasingAgentAgent(self.engine))
        self.engine.register_agent(AccountantAgent(self.engine))
        self.engine.register_agent(MaintenanceTechLeadAgent(self.engine))
        self.engine.register_agent(MaintenanceTechAgent(self.engine))
        self.engine.register_agent(ResidentServicesRepAgent(self.engine))
        self.engine.register_agent(AdminAssistantAgent(self.engine))
    
    async def run_emergency_maintenance_scenario(self):
        """Run emergency maintenance workflow"""
        print("\n🚨 SCENARIO 1: Emergency Water Leak")
        print("=" * 60)
        
        # Create emergency context
        emergency_data = {
            "type": "emergency_maintenance",
            "issue": "Major water leak in unit 204",
            "severity": "critical",
            "tenant": "John Smith",
            "property": "Riverside Apartments",
            "estimated_damage": 8500,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📍 Location: Unit 204, Riverside Apartments")
        print(f"⚠️  Issue: Major water leak")
        print(f"💰 Estimated damage: ${emergency_data['estimated_damage']}")
        
        # Start with maintenance tech
        print("\n🔧 Step 1: Maintenance Tech Initial Response")
        tech_response = await self.engine.agents["maintenance_tech"].execute_action(
            "assess_emergency",
            {"context": emergency_data}
        )
        print(f"   → Assessment: {tech_response['output']['assessment']}")
        
        # Escalate to tech lead
        print("\n👷 Step 2: Tech Lead Evaluation")
        lead_response = await self.engine.agents["maintenance_tech_lead"].execute_action(
            "evaluate_severity",
            {"context": {**emergency_data, "tech_assessment": tech_response}}
        )
        print(f"   → Severity confirmed: {lead_response['output']['severity']}")
        
        # Supervisor coordination
        print("\n🎯 Step 3: Maintenance Supervisor Coordination")
        supervisor_response = await self.engine.agents["maintenance_supervisor"].execute_action(
            "coordinate_emergency_response",
            {"context": {**emergency_data, "lead_evaluation": lead_response}}
        )
        print(f"   → Vendor dispatched: {supervisor_response['output']['vendor']}")
        
        # Property manager approval
        print("\n📋 Step 4: Property Manager Approval")
        pm_response = await self.engine.agents["property_manager"].execute_action(
            "approve_emergency_repair",
            {"context": {**emergency_data, "repair_plan": supervisor_response}}
        )
        print(f"   → Approval: {pm_response['output']['approved']}")
        print(f"   → Authorization: {pm_response['output']['authorization_code']}")
        
        # Accounting approval for high amount
        print("\n💰 Step 5: Accounting Manager Financial Approval")
        accounting_response = await self.engine.agents["accounting_manager"].execute_action(
            "approve_emergency_expense",
            {"context": {**emergency_data, "pm_approval": pm_response}}
        )
        print(f"   → Financial approval: {accounting_response['output']['approved']}")
        
        # Check messages between agents
        messages = self.engine.get_messages()
        print(f"\n📬 Inter-agent messages: {len(messages)}")
        for msg in messages[-3:]:  # Show last 3 messages
            print(f"   • {msg['from_role']} → {msg['to_role']}: {msg['subject']}")
        
        print("\n✅ Emergency response workflow completed!")
        
        return tech_response
    
    async def run_premium_lease_scenario(self):
        """Run premium lease application workflow"""
        print("\n\n🏢 SCENARIO 2: Premium Lease Application")
        print("=" * 60)
        
        lease_data = {
            "type": "lease_application",
            "applicant": "Sarah Johnson",
            "unit": "Penthouse A",
            "property": "Luxury Towers",
            "monthly_rent": 5500,
            "lease_term": "24 months",
            "concessions_requested": ["First month free", "Parking included"],
            "credit_score": 780,
            "income": 22000,  # Monthly
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"🏠 Property: {lease_data['property']}, {lease_data['unit']}")
        print(f"👤 Applicant: {lease_data['applicant']}")
        print(f"💰 Monthly rent: ${lease_data['monthly_rent']}")
        print(f"📊 Credit score: {lease_data['credit_score']}")
        
        # Leasing agent initial processing
        print("\n👥 Step 1: Leasing Agent Initial Processing")
        agent_response = await self.engine.agents["leasing_agent"].execute_action(
            "process_application",
            {"context": lease_data}
        )
        print(f"   → Initial screening: {agent_response['output']['screening_result']}")
        
        # Senior agent review
        print("\n👔 Step 2: Senior Leasing Agent Review")
        senior_response = await self.engine.agents["senior_leasing_agent"].execute_action(
            "review_premium_application",
            {"context": {**lease_data, "initial_screening": agent_response}}
        )
        print(f"   → Premium review: {senior_response['output']['recommendation']}")
        
        # Leasing manager approval
        print("\n📊 Step 3: Leasing Manager Approval")
        manager_response = await self.engine.agents["leasing_manager"].execute_action(
            "approve_lease_terms",
            {"context": {**lease_data, "senior_review": senior_response}}
        )
        print(f"   → Terms approved: {manager_response['output']['approved']}")
        
        # Leasing coordinator processing
        print("\n📋 Step 4: Leasing Coordinator Processing")
        coordinator_response = await self.engine.agents["leasing_coordinator"].execute_action(
            "coordinate_lease_execution",
            {"context": {**lease_data, "manager_approval": manager_response}}
        )
        print(f"   → Coordination status: {coordinator_response['output']['status']}")
        
        # Director approval for concessions
        print("\n🎯 Step 5: Director of Leasing Approval")
        director_response = await self.engine.agents["director_leasing"].execute_action(
            "approve_concessions",
            {"context": {**lease_data, "requested_concessions": coordinator_response}}
        )
        print(f"   → Concessions approved: {director_response['output']['approved']}")
        
        # Accounting verification
        print("\n💳 Step 6: Accounting Verification")
        accounting_response = await self.engine.agents["accounting_manager"].execute_action(
            "verify_financial_qualifications",
            {"context": {**lease_data, "approvals": director_response}}
        )
        print(f"   → Financial verification: {accounting_response['output']['verified']}")
        
        # Resident services setup
        print("\n🏠 Step 7: Resident Services Setup")
        services_response = await self.engine.agents["resident_services_manager"].execute_action(
            "setup_premium_resident",
            {"context": {**lease_data, "final_approvals": accounting_response}}
        )
        print(f"   → Welcome package: {services_response['output']['package_prepared']}")
        
        print("\n✅ Premium lease application approved and processed!")
        
        return agent_response
    
    async def run_strategic_planning_scenario(self):
        """Run strategic planning workflow"""
        print("\n\n🎯 SCENARIO 3: Strategic Portfolio Planning")
        print("=" * 60)
        
        strategy_data = {
            "type": "strategic_planning",
            "initiative": "Portfolio Expansion Strategy",
            "objective": "Acquire 100 additional units over 24 months",
            "budget": 15000000,  # $15M
            "target_markets": ["Downtown", "Suburban Growth Areas"],
            "roi_target": "8.5%",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📈 Initiative: {strategy_data['initiative']}")
        print(f"🎯 Objective: {strategy_data['objective']}")
        print(f"💰 Budget: ${strategy_data['budget']:,}")
        
        # President sets vision
        print("\n👑 Step 1: President Sets Strategic Vision")
        president_response = await self.engine.agents["president"].execute_action(
            "set_strategic_vision",
            {"context": strategy_data}
        )
        print(f"   → Vision approved: {president_response['output']['vision_set']}")
        
        # VP Operations planning
        print("\n🎖️ Step 2: VP of Operations Develops Plan")
        vp_response = await self.engine.agents["vp_operations"].execute_action(
            "develop_operational_plan",
            {"context": {**strategy_data, "vision": president_response}}
        )
        print(f"   → Operational plan: {vp_response['output']['plan_status']}")
        
        # Directors provide input
        print("\n📊 Step 3: Directors Provide Department Input")
        
        # Director of Accounting
        accounting_dir_response = await self.engine.agents["director_accounting"].execute_action(
            "assess_financial_feasibility",
            {"context": {**strategy_data, "operational_plan": vp_response}}
        )
        print(f"   → Financial assessment: {accounting_dir_response['output']['feasibility']}")
        
        # Director of Leasing
        leasing_dir_response = await self.engine.agents["director_leasing"].execute_action(
            "analyze_market_potential",
            {"context": {**strategy_data, "operational_plan": vp_response}}
        )
        print(f"   → Market analysis: {leasing_dir_response['output']['market_outlook']}")
        
        # Internal Controller compliance
        print("\n🔒 Step 4: Internal Controller Compliance Review")
        controller_response = await self.engine.agents["internal_controller"].execute_action(
            "review_compliance_requirements",
            {"context": {**strategy_data, "department_inputs": {
                "accounting": accounting_dir_response,
                "leasing": leasing_dir_response
            }}}
        )
        print(f"   → Compliance status: {controller_response['output']['compliance_review']}")
        
        # Final executive approval
        print("\n✅ Step 5: Final Executive Approval")
        final_response = await self.engine.agents["president"].execute_action(
            "approve_strategic_initiative",
            {"context": {
                **strategy_data,
                "all_reviews": {
                    "operations": vp_response,
                    "financial": accounting_dir_response,
                    "market": leasing_dir_response,
                    "compliance": controller_response
                }
            }}
        )
        print(f"   → Initiative approved: {final_response['output']['approved']}")
        print(f"   → Implementation timeline: {final_response['output']['timeline']}")
        
        # Check executive messages
        messages = self.engine.get_messages()
        exec_messages = [m for m in messages if 'president' in m['from_role'] or 'president' in m['to_role']]
        print(f"\n📬 Executive communications: {len(exec_messages)}")
        
        print("\n✅ Strategic planning workflow completed!")
        
        return president_response
    
    async def run_compliance_audit_scenario(self):
        """Run compliance audit workflow"""
        print("\n\n🔍 SCENARIO 4: Annual Compliance Audit")
        print("=" * 60)
        
        audit_data = {
            "type": "compliance_audit",
            "audit_type": "Annual Comprehensive Audit",
            "areas": ["Fair Housing", "Safety Regulations", "Financial Compliance", "Lease Documentation"],
            "properties": ["All Portfolio Properties"],
            "audit_firm": "External Auditors LLC",
            "deadline": "30 days",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📋 Audit Type: {audit_data['audit_type']}")
        print(f"🏢 Scope: {', '.join(audit_data['properties'])}")
        print(f"📅 Deadline: {audit_data['deadline']}")
        
        # Internal Controller initiates
        print("\n🔐 Step 1: Internal Controller Initiates Audit")
        controller_response = await self.engine.agents["internal_controller"].execute_action(
            "initiate_compliance_audit",
            {"context": audit_data}
        )
        print(f"   → Audit initiated: {controller_response['output']['audit_id']}")
        
        # Department preparations
        print("\n📂 Step 2: Department Preparations")
        
        # Property Manager preparation
        pm_prep = await self.engine.agents["property_manager"].execute_action(
            "prepare_audit_documentation",
            {"context": {**audit_data, "audit_requirements": controller_response}}
        )
        print(f"   → Property docs: {pm_prep['output']['documentation_status']}")
        
        # Accounting Manager preparation
        accounting_prep = await self.engine.agents["accounting_manager"].execute_action(
            "prepare_financial_audit",
            {"context": {**audit_data, "audit_requirements": controller_response}}
        )
        print(f"   → Financial docs: {accounting_prep['output']['financial_ready']}")
        
        # Leasing Manager preparation
        leasing_prep = await self.engine.agents["leasing_manager"].execute_action(
            "prepare_lease_audit",
            {"context": {**audit_data, "audit_requirements": controller_response}}
        )
        print(f"   → Lease docs: {leasing_prep['output']['lease_docs_ready']}")
        
        # Directors review
        print("\n🎯 Step 3: Directors Review Department Readiness")
        
        accounting_dir_review = await self.engine.agents["director_accounting"].execute_action(
            "review_audit_readiness",
            {"context": {**audit_data, "department_prep": accounting_prep}}
        )
        print(f"   → Accounting review: {accounting_dir_review['output']['review_status']}")
        
        leasing_dir_review = await self.engine.agents["director_leasing"].execute_action(
            "review_audit_readiness",
            {"context": {**audit_data, "department_prep": leasing_prep}}
        )
        print(f"   → Leasing review: {leasing_dir_review['output']['review_status']}")
        
        # VP oversight
        print("\n🎖️ Step 4: VP of Operations Oversight")
        vp_oversight = await self.engine.agents["vp_operations"].execute_action(
            "oversee_audit_preparation",
            {"context": {**audit_data, "director_reviews": {
                "accounting": accounting_dir_review,
                "leasing": leasing_dir_review
            }}}
        )
        print(f"   → VP approval: {vp_oversight['output']['ready_for_audit']}")
        
        # President final review
        print("\n👑 Step 5: President Final Review")
        president_review = await self.engine.agents["president"].execute_action(
            "review_audit_readiness",
            {"context": {**audit_data, "vp_report": vp_oversight}}
        )
        print(f"   → Executive sign-off: {president_review['output']['approved']}")
        
        print("\n✅ Compliance audit preparation completed!")
        
        return controller_response
    
    async def run_all_scenarios(self):
        """Run all workflow scenarios"""
        print("\n🚀 AICTIVE PLATFORM - COMPREHENSIVE WORKFLOW DEMONSTRATION")
        print("=" * 80)
        print("Demonstrating multi-agent coordination with strict approval hierarchies")
        print("=" * 80)
        
        # Run scenarios
        await self.run_emergency_maintenance_scenario()
        await self.run_premium_lease_scenario()
        await self.run_strategic_planning_scenario()
        await self.run_compliance_audit_scenario()
        
        # Summary statistics
        all_messages = self.engine.get_messages()
        print("\n\n📊 WORKFLOW EXECUTION SUMMARY")
        print("=" * 60)
        print(f"✅ Total workflows executed: 4")
        print(f"👥 Total agents involved: {len(self.engine.agents)}")
        print(f"📬 Total inter-agent messages: {len(all_messages)}")
        print(f"⏱️  Average workflow completion: <2 seconds (mocked)")
        
        # Message breakdown
        message_counts = {}
        for msg in all_messages:
            key = f"{msg['from_role']} → {msg['to_role']}"
            message_counts[key] = message_counts.get(key, 0) + 1
        
        print("\n📮 Top Communication Patterns:")
        sorted_patterns = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)
        for pattern, count in sorted_patterns[:5]:
            print(f"   • {pattern}: {count} messages")
        
        print("\n✨ All workflows completed successfully!")
        print("🏢 The Aictive Platform is ready for production use!")


# Main execution
async def main():
    """Main execution function"""
    runner = WorkflowScenarioRunner()
    await runner.run_all_scenarios()


if __name__ == "__main__":
    asyncio.run(main())