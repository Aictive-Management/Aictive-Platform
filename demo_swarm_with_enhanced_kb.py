#!/usr/bin/env python3
"""
Demonstration: Swarm System Using Enhanced Knowledge Base
Shows how the converted System Manuals enhance swarm intelligence
"""

import asyncio
import yaml
from typing import Dict, List, Any
from super_claude_swarm_orchestrator import SuperClaudeSwarmOrchestrator
from swarm_workflow_builder import WorkflowBuilderSwarm, WorkflowRequirement


class EnhancedSwarmSystem:
    """Swarm system enhanced with converted knowledge base"""
    
    def __init__(self):
        # Load the enhanced knowledge base
        self.knowledge_base = self._load_knowledge_base()
        self.orchestrator = SuperClaudeSwarmOrchestrator()
        self.workflow_builder = WorkflowBuilderSwarm()
        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load the enhanced knowledge base"""
        try:
            with open("enhanced_agent_knowledge_base.yaml", "r") as f:
                return yaml.safe_load(f)
        except:
            print("⚠️  Enhanced knowledge base not found, using default")
            return {"agents": {}, "procedures": {}, "workflows": {}}
    
    async def demonstrate_enhanced_capabilities(self):
        """Show how enhanced KB improves swarm decisions"""
        print("🚀 ENHANCED SWARM SYSTEM DEMONSTRATION")
        print("=" * 80)
        print("Using converted System Manuals for intelligent decision making")
        print("=" * 80)
        
        # Test 1: Complex Owner Termination
        print("\n📋 Test 1: Owner Management Termination")
        print("-" * 60)
        
        termination_request = {
            "objective": "workflow_design",
            "description": "Owner wants to terminate property management agreement",
            "complexity": 0.7,
            "priority": "high",
            "constraints": {
                "notice_period": "30 days",
                "properties": 3,
                "security_deposits": 8500,
                "active_leases": 3
            },
            "context": {
                "owner": "Smith Properties LLC",
                "reason": "Selling portfolio",
                "requires": ["deposit_transfer", "final_accounting", "tenant_notification"]
            }
        }
        
        # Use enhanced KB to inform decision
        relevant_procedure = self._find_relevant_procedure("owner_termination")
        if relevant_procedure:
            print(f"📚 Found procedure: {relevant_procedure['name']}")
            print(f"   Steps: {len(relevant_procedure['steps'])}")
            print(f"   Timeline: {relevant_procedure['timeline']}")
        
        result = await self.orchestrator.process_request(termination_request)
        
        print(f"\n✅ Swarm Decision: {result['decision']['primary_approach']}")
        print(f"👥 Assigned Agents:")
        for agent in result['decision']['recommended_agents']:
            agent_info = self.knowledge_base['agents'].get(agent, {})
            if agent_info:
                print(f"   • {agent}: {agent_info.get('title', 'Unknown')} "
                      f"(Authority: ${agent_info.get('authority', {}).get('approval_limit', 0)})")
        
        # Test 2: Multi-Property Lease Renewal Campaign
        print("\n\n📋 Test 2: Multi-Property Lease Renewal Campaign")
        print("-" * 60)
        
        renewal_req = WorkflowRequirement(
            name="Q1 Lease Renewal Campaign",
            description="Process lease renewals for 50 units across 5 properties",
            scenario="Bulk lease renewals with market-rate adjustments and resident retention focus",
            triggers=["90_days_before_expiration", "bulk_renewal_date"],
            expected_outcome="85% renewal rate with 3-5% rent increases",
            constraints={
                "properties": 5,
                "total_units": 50,
                "target_increase": "3-5%",
                "concessions_budget": 25000
            },
            approval_limits={"concessions": 500, "total_concessions": 25000},
            time_constraints={"notice_period": "90 days", "decision_deadline": "60 days"},
            compliance_requirements=["fair_housing", "lease_law_compliance"],
            property_type="multi_property",
            urgency="normal"
        )
        
        # Build workflow using enhanced KB
        workflow = await self.workflow_builder.build_workflow(renewal_req)
        
        print(f"\n✅ Workflow Built: {workflow.name}")
        print(f"📊 Complexity: {workflow.complexity_score:.2f}")
        
        # Show how KB enhanced the workflow
        enhanced_steps = self._identify_kb_enhanced_steps(workflow.steps)
        print(f"\n📚 Knowledge Base Enhancements:")
        for step in enhanced_steps[:3]:
            print(f"   • {step['enhancement']}")
        
        # Test 3: Compliance Audit with System Manual Procedures
        print("\n\n📋 Test 3: Fair Housing Compliance Audit")
        print("-" * 60)
        
        compliance_request = {
            "objective": "compliance_audit",
            "description": "Comprehensive fair housing compliance review across portfolio",
            "complexity": 0.85,
            "priority": "high",
            "constraints": {
                "audit_areas": ["advertising", "application_processing", "reasonable_accommodations"],
                "properties": 10,
                "deadline": "2 weeks"
            },
            "context": {
                "trigger": "HUD_complaint",
                "risk_level": "high",
                "documentation_required": "extensive"
            }
        }
        
        # Find relevant compliance procedures
        compliance_procedures = self._find_compliance_procedures()
        print(f"📚 Found {len(compliance_procedures)} compliance procedures in knowledge base")
        
        audit_result = await self.orchestrator.process_request(compliance_request)
        
        print(f"\n✅ Audit Strategy: {audit_result['decision']['primary_approach']}")
        print(f"⚖️  Risk Level: {audit_result['decision']['risk_level']}")
        
        # Show implementation phases
        print(f"\n📊 Implementation Phases:")
        for phase in audit_result['implementation']['phases']:
            print(f"   {phase['phase']}. {phase['name']} ({phase['duration']})")
            
            # Match with KB procedures
            kb_procedures = self._match_phase_to_procedures(phase['name'])
            if kb_procedures:
                print(f"      → Using procedures: {', '.join(kb_procedures)}")
        
        # Summary of KB Impact
        print("\n\n📊 KNOWLEDGE BASE IMPACT SUMMARY")
        print("=" * 60)
        
        stats = {
            "Total Agents in KB": len(self.knowledge_base.get('agents', {})),
            "Total Procedures": len(self.knowledge_base.get('procedures', {})),
            "Total Workflows": len(self.knowledge_base.get('workflows', {})),
            "Approval Hierarchies": len(self.knowledge_base.get('approval_hierarchies', {})),
            "Form Templates": len(self.knowledge_base.get('forms', {}))
        }
        
        for stat, value in stats.items():
            print(f"   {stat}: {value}")
        
        print("\n🎯 Key Benefits of System Manual Conversion:")
        print("   ✅ Accurate role assignments based on actual responsibilities")
        print("   ✅ Proper approval limits from organizational structure")
        print("   ✅ Real procedures with correct timelines and forms")
        print("   ✅ Compliance requirements properly documented")
        print("   ✅ Communication templates ready for use")
        
    def _find_relevant_procedure(self, procedure_type: str) -> Dict[str, Any]:
        """Find relevant procedure from knowledge base"""
        for proc_id, procedure in self.knowledge_base.get('procedures', {}).items():
            if procedure_type in proc_id:
                return procedure
        return {}
    
    def _identify_kb_enhanced_steps(self, steps: List[Any]) -> List[Dict[str, str]]:
        """Identify steps enhanced by knowledge base"""
        enhancements = []
        
        for step in steps:
            agent = step.agent_role
            agent_info = self.knowledge_base.get('agents', {}).get(agent, {})
            
            if agent_info:
                enhancement = {
                    "step": step.name,
                    "enhancement": f"{agent_info['title']} assigned based on {agent_info['level']} authority"
                }
                enhancements.append(enhancement)
        
        return enhancements
    
    def _find_compliance_procedures(self) -> List[str]:
        """Find compliance-related procedures"""
        compliance_procs = []
        
        for proc_id, procedure in self.knowledge_base.get('procedures', {}).items():
            if procedure.get('category') == 'compliance' or 'compliance' in procedure.get('name', '').lower():
                compliance_procs.append(proc_id)
        
        return compliance_procs
    
    def _match_phase_to_procedures(self, phase_name: str) -> List[str]:
        """Match implementation phase to KB procedures"""
        matched = []
        phase_lower = phase_name.lower()
        
        for proc_id, procedure in self.knowledge_base.get('procedures', {}).items():
            proc_name_lower = procedure.get('name', '').lower()
            if any(word in proc_name_lower for word in phase_lower.split()):
                matched.append(proc_id)
        
        return matched[:2]  # Return top 2 matches


async def main():
    """Run the enhanced demonstration"""
    system = EnhancedSwarmSystem()
    await system.demonstrate_enhanced_capabilities()
    
    print("\n\n🚀 NEXT STEPS WITH ENHANCED KNOWLEDGE BASE:")
    print("-" * 60)
    print("1. Continue converting remaining System Manual documents")
    print("2. Add more detailed procedures from each role folder")
    print("3. Import actual forms and templates")
    print("4. Build role-specific training modules")
    print("5. Create automated workflow generation from procedures")
    print("\n💡 The system is now significantly smarter with real operational knowledge!")


if __name__ == "__main__":
    asyncio.run(main())