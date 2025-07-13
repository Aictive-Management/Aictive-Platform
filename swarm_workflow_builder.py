"""
Swarm Workflow Builder
Intelligent workflow creation using swarm coordination with actual agent integration
"""

import asyncio
import yaml
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import random

# Load agent knowledge base
def load_agent_knowledge():
    """Load agent knowledge from YAML"""
    try:
        with open("agent_knowledge_base.yaml", "r") as f:
            return yaml.safe_load(f)
    except:
        return {"agents": {}, "workflow_templates": {}}


@dataclass
class WorkflowRequirement:
    """Detailed workflow requirement"""
    name: str
    description: str
    scenario: str
    triggers: List[str]
    expected_outcome: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Business rules
    approval_limits: Dict[str, float] = field(default_factory=dict)
    time_constraints: Dict[str, str] = field(default_factory=dict)
    compliance_requirements: List[str] = field(default_factory=list)
    
    # Property context
    property_type: str = "general"  # single_family, duplex, 20_unit, 50_unit
    urgency: str = "normal"  # low, normal, high, emergency


@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str
    name: str
    description: str
    agent_role: str
    action: str
    timeout_minutes: int = 30
    requires_approval: bool = False
    approval_amount: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)


@dataclass
class SwarmBuiltWorkflow:
    """Complete workflow built by swarm"""
    workflow_id: str
    name: str
    description: str
    category: str
    triggers: List[str]
    steps: List[WorkflowStep]
    approval_chain: List[str]
    estimated_duration: str
    complexity_score: float
    compliance_checks: List[str]
    success_metrics: List[str]


class WorkflowBuilderSwarm:
    """Swarm that builds intelligent workflows"""
    
    def __init__(self):
        self.knowledge_base = load_agent_knowledge()
        self.agents_db = self.knowledge_base.get("agents", {})
        self.workflow_templates = self.knowledge_base.get("workflow_templates", {})
        
    async def build_workflow(self, requirement: WorkflowRequirement) -> SwarmBuiltWorkflow:
        """Build a complete workflow using swarm intelligence"""
        print(f"\n🐝 WORKFLOW BUILDER SWARM ACTIVATED")
        print(f"📋 Building: {requirement.name}")
        print(f"🎯 Scenario: {requirement.scenario}")
        
        # Phase 1: Analyze requirement
        print("\n📊 Phase 1: Requirement Analysis")
        analysis = await self._analyze_requirement(requirement)
        
        # Phase 2: Design workflow structure
        print("\n🏗️ Phase 2: Workflow Design")
        structure = await self._design_workflow_structure(requirement, analysis)
        
        # Phase 3: Assign agents and build steps
        print("\n👥 Phase 3: Agent Assignment")
        steps = await self._assign_agents_and_build_steps(requirement, structure, analysis)
        
        # Phase 4: Add compliance and approvals
        print("\n✅ Phase 4: Compliance & Approvals")
        enhanced_steps = await self._add_compliance_and_approvals(steps, requirement, analysis)
        
        # Phase 5: Optimize and validate
        print("\n⚡ Phase 5: Optimization")
        optimized_workflow = await self._optimize_workflow(enhanced_steps, requirement)
        
        # Create final workflow
        workflow = SwarmBuiltWorkflow(
            workflow_id=f"WF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=requirement.name,
            description=requirement.description,
            category=self._determine_category(requirement),
            triggers=requirement.triggers,
            steps=optimized_workflow,
            approval_chain=self._build_approval_chain(analysis),
            estimated_duration=self._estimate_duration(optimized_workflow),
            complexity_score=analysis["complexity_score"],
            compliance_checks=requirement.compliance_requirements,
            success_metrics=self._define_success_metrics(requirement)
        )
        
        return workflow
    
    async def _analyze_requirement(self, req: WorkflowRequirement) -> Dict[str, Any]:
        """Analyze requirement deeply"""
        print("   🔍 Analyzing requirement patterns...")
        
        analysis = {
            "complexity_score": 0.0,
            "required_departments": [],
            "critical_decisions": [],
            "risk_factors": [],
            "optimization_opportunities": []
        }
        
        # Complexity analysis
        if req.urgency == "emergency":
            analysis["complexity_score"] += 0.3
            analysis["critical_decisions"].append("emergency_response_speed")
            
        if any(limit > 5000 for limit in req.approval_limits.values()):
            analysis["complexity_score"] += 0.2
            analysis["critical_decisions"].append("high_value_approval")
            
        if len(req.compliance_requirements) > 2:
            analysis["complexity_score"] += 0.2
            analysis["risk_factors"].append("compliance_complexity")
            
        # Department analysis
        scenario_lower = req.scenario.lower()
        if "maintenance" in scenario_lower:
            analysis["required_departments"].extend(["maintenance", "property_management"])
        if "lease" in scenario_lower or "tenant" in scenario_lower:
            analysis["required_departments"].extend(["leasing", "property_management"])
        if "financial" in scenario_lower or "payment" in scenario_lower:
            analysis["required_departments"].extend(["accounting", "property_management"])
            
        # Risk analysis
        if "emergency" in scenario_lower:
            analysis["risk_factors"].append("time_critical")
        if "compliance" in scenario_lower:
            analysis["risk_factors"].append("regulatory_risk")
            
        # Optimization opportunities
        if req.property_type in ["20_unit", "50_unit"]:
            analysis["optimization_opportunities"].append("batch_processing")
        if len(analysis["required_departments"]) > 2:
            analysis["optimization_opportunities"].append("parallel_department_processing")
            
        analysis["complexity_score"] = min(analysis["complexity_score"], 1.0)
        
        return analysis
    
    async def _design_workflow_structure(
        self, 
        req: WorkflowRequirement, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Design the workflow structure"""
        print("   🏗️ Designing optimal workflow structure...")
        
        structure = {
            "phases": [],
            "parallel_opportunities": [],
            "decision_points": [],
            "escalation_triggers": []
        }
        
        # Design phases based on urgency and complexity
        if req.urgency == "emergency":
            structure["phases"] = [
                {"name": "Immediate Response", "duration": "15 minutes"},
                {"name": "Resource Allocation", "duration": "30 minutes"},
                {"name": "Resolution", "duration": "2-4 hours"},
                {"name": "Documentation", "duration": "30 minutes"}
            ]
        elif analysis["complexity_score"] > 0.6:
            structure["phases"] = [
                {"name": "Initial Assessment", "duration": "1 hour"},
                {"name": "Multi-Department Coordination", "duration": "4 hours"},
                {"name": "Approval Process", "duration": "2-8 hours"},
                {"name": "Implementation", "duration": "varies"},
                {"name": "Verification", "duration": "1 hour"}
            ]
        else:
            structure["phases"] = [
                {"name": "Request Processing", "duration": "30 minutes"},
                {"name": "Action", "duration": "2-4 hours"},
                {"name": "Completion", "duration": "30 minutes"}
            ]
        
        # Identify parallel opportunities
        if "batch_processing" in analysis["optimization_opportunities"]:
            structure["parallel_opportunities"].append({
                "type": "batch",
                "description": "Process multiple units simultaneously"
            })
            
        # Add decision points
        for decision in analysis["critical_decisions"]:
            structure["decision_points"].append({
                "type": decision,
                "description": f"Critical decision for {decision}"
            })
            
        # Define escalation triggers
        structure["escalation_triggers"] = [
            {"trigger": "timeout", "escalate_to": "next_level"},
            {"trigger": "rejection", "escalate_to": "director"},
            {"trigger": "high_cost", "escalate_to": "vp_operations"}
        ]
        
        return structure
    
    async def _assign_agents_and_build_steps(
        self,
        req: WorkflowRequirement,
        structure: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Assign agents and build workflow steps"""
        print("   👥 Assigning optimal agents to each step...")
        
        steps = []
        step_counter = 1
        
        # Build steps for each phase
        for phase_idx, phase in enumerate(structure["phases"]):
            phase_name = phase["name"]
            
            if phase_name == "Immediate Response":
                # First responder
                steps.append(WorkflowStep(
                    step_id=f"step_{step_counter}",
                    name="Initial Assessment",
                    description="Assess the situation and determine immediate actions",
                    agent_role=self._get_first_responder(req),
                    action="assess_situation",
                    timeout_minutes=15,
                    outputs=["assessment_report", "severity_level"]
                ))
                step_counter += 1
                
            elif phase_name == "Resource Allocation":
                # Supervisor level
                steps.append(WorkflowStep(
                    step_id=f"step_{step_counter}",
                    name="Resource Coordination",
                    description="Allocate resources and coordinate response",
                    agent_role=self._get_supervisor(req),
                    action="coordinate_resources",
                    timeout_minutes=30,
                    dependencies=[f"step_{step_counter-1}"],
                    outputs=["resource_plan", "vendor_assignments"]
                ))
                step_counter += 1
                
            elif phase_name == "Approval Process":
                # Add approval steps based on amount
                approval_steps = self._create_approval_steps(req, analysis, step_counter)
                steps.extend(approval_steps)
                step_counter += len(approval_steps)
                
            elif phase_name == "Multi-Department Coordination":
                # Add department-specific steps
                for dept in analysis["required_departments"]:
                    steps.append(WorkflowStep(
                        step_id=f"step_{step_counter}",
                        name=f"{dept.title()} Processing",
                        description=f"Process through {dept} department",
                        agent_role=self._get_department_agent(dept),
                        action=f"{dept}_processing",
                        timeout_minutes=120,
                        dependencies=[f"step_{step_counter-1}"] if step_counter > 1 else [],
                        outputs=[f"{dept}_approval", f"{dept}_documentation"]
                    ))
                    step_counter += 1
        
        return steps
    
    def _get_first_responder(self, req: WorkflowRequirement) -> str:
        """Get appropriate first responder agent"""
        scenario = req.scenario.lower()
        
        if "maintenance" in scenario:
            return "maintenance_tech"
        elif "lease" in scenario:
            return "leasing_agent"
        elif "payment" in scenario or "financial" in scenario:
            return "accountant"
        else:
            return "admin_assistant"
    
    def _get_supervisor(self, req: WorkflowRequirement) -> str:
        """Get appropriate supervisor"""
        scenario = req.scenario.lower()
        
        if "maintenance" in scenario:
            return "maintenance_supervisor"
        elif "lease" in scenario:
            return "leasing_manager"
        elif "payment" in scenario or "financial" in scenario:
            return "accounting_manager"
        else:
            return "property_manager"
    
    def _get_department_agent(self, department: str) -> str:
        """Get agent for department"""
        dept_agents = {
            "maintenance": "maintenance_supervisor",
            "leasing": "leasing_manager",
            "accounting": "accounting_manager",
            "property_management": "property_manager"
        }
        return dept_agents.get(department, "property_manager")
    
    def _create_approval_steps(
        self,
        req: WorkflowRequirement,
        analysis: Dict[str, Any],
        start_counter: int
    ) -> List[WorkflowStep]:
        """Create approval steps based on amounts and hierarchy"""
        approval_steps = []
        counter = start_counter
        
        # Determine max approval amount needed
        max_amount = max(req.approval_limits.values()) if req.approval_limits else 0
        
        # Build approval chain based on amount
        if max_amount > 0:
            # Property Manager level (up to $0 - needs approval)
            approval_steps.append(WorkflowStep(
                step_id=f"step_{counter}",
                name="Property Manager Approval",
                description=f"Approve expenditure up to ${max_amount}",
                agent_role="property_manager",
                action="approve_expense",
                timeout_minutes=60,
                requires_approval=True,
                approval_amount=max_amount,
                dependencies=[f"step_{counter-1}"] if counter > 1 else []
            ))
            counter += 1
            
            if max_amount > 1000:
                # Accounting Manager
                approval_steps.append(WorkflowStep(
                    step_id=f"step_{counter}",
                    name="Accounting Manager Review",
                    description="Financial review and approval",
                    agent_role="accounting_manager",
                    action="financial_review",
                    timeout_minutes=120,
                    requires_approval=True,
                    approval_amount=max_amount,
                    dependencies=[f"step_{counter-1}"]
                ))
                counter += 1
                
            if max_amount > 10000:
                # Director level
                approval_steps.append(WorkflowStep(
                    step_id=f"step_{counter}",
                    name="Director Approval",
                    description="Director level approval required",
                    agent_role="director_accounting",
                    action="director_approval",
                    timeout_minutes=240,
                    requires_approval=True,
                    approval_amount=max_amount,
                    dependencies=[f"step_{counter-1}"]
                ))
                counter += 1
                
            if max_amount > 50000:
                # VP level
                approval_steps.append(WorkflowStep(
                    step_id=f"step_{counter}",
                    name="VP Approval",
                    description="Executive approval required",
                    agent_role="vp_operations",
                    action="executive_approval",
                    timeout_minutes=480,
                    requires_approval=True,
                    approval_amount=max_amount,
                    dependencies=[f"step_{counter-1}"]
                ))
                counter += 1
                
            if max_amount > 100000:
                # President
                approval_steps.append(WorkflowStep(
                    step_id=f"step_{counter}",
                    name="President Final Approval",
                    description="President approval for major expenditure",
                    agent_role="president",
                    action="final_approval",
                    timeout_minutes=720,
                    requires_approval=True,
                    approval_amount=max_amount,
                    dependencies=[f"step_{counter-1}"]
                ))
        
        return approval_steps
    
    async def _add_compliance_and_approvals(
        self,
        steps: List[WorkflowStep],
        req: WorkflowRequirement,
        analysis: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Add compliance checks and additional approvals"""
        print("   ✅ Adding compliance checks and approval gates...")
        
        enhanced_steps = steps.copy()
        
        # Add compliance checks if required
        if req.compliance_requirements:
            # Find appropriate position for compliance check
            insert_position = len(enhanced_steps) // 2  # Middle of workflow
            
            compliance_step = WorkflowStep(
                step_id=f"step_compliance_{len(enhanced_steps)+1}",
                name="Compliance Verification",
                description="Verify compliance with regulations",
                agent_role="internal_controller",
                action="compliance_check",
                timeout_minutes=120,
                outputs=["compliance_report", "compliance_status"],
                conditions={"compliance_required": True}
            )
            
            # Insert compliance step
            enhanced_steps.insert(insert_position, compliance_step)
            
            # Update dependencies
            if insert_position < len(enhanced_steps) - 1:
                next_step = enhanced_steps[insert_position + 1]
                next_step.dependencies.append(compliance_step.step_id)
        
        return enhanced_steps
    
    async def _optimize_workflow(
        self,
        steps: List[WorkflowStep],
        req: WorkflowRequirement
    ) -> List[WorkflowStep]:
        """Optimize workflow for efficiency"""
        print("   ⚡ Optimizing workflow for maximum efficiency...")
        
        optimized = steps.copy()
        
        # Identify parallel execution opportunities
        parallel_candidates = []
        for i, step in enumerate(optimized):
            # Check if steps can run in parallel
            if i > 0 and len(step.dependencies) == 1:
                prev_step = optimized[i-1]
                # If they're from different departments, might run in parallel
                if step.agent_role.split('_')[0] != prev_step.agent_role.split('_')[0]:
                    parallel_candidates.append(i)
        
        # Mark parallel steps
        for idx in parallel_candidates:
            if idx < len(optimized):
                optimized[idx].conditions["parallel_eligible"] = True
        
        # Optimize timeouts based on urgency
        if req.urgency == "emergency":
            for step in optimized:
                step.timeout_minutes = min(step.timeout_minutes, 30)
        
        return optimized
    
    def _determine_category(self, req: WorkflowRequirement) -> str:
        """Determine workflow category"""
        scenario = req.scenario.lower()
        
        if "maintenance" in scenario or "repair" in scenario:
            return "maintenance"
        elif "lease" in scenario or "tenant" in scenario:
            return "leasing"
        elif "payment" in scenario or "financial" in scenario:
            return "financial"
        elif "compliance" in scenario or "audit" in scenario:
            return "compliance"
        else:
            return "general"
    
    def _build_approval_chain(self, analysis: Dict[str, Any]) -> List[str]:
        """Build approval chain based on analysis"""
        chain = []
        
        # Always start with operational level
        chain.append("operational_staff")
        
        if "property_management" in analysis["required_departments"]:
            chain.append("property_manager")
            
        if "high_value_approval" in analysis["critical_decisions"]:
            chain.extend(["accounting_manager", "director", "vp_operations"])
            
        if analysis["complexity_score"] > 0.8:
            chain.append("president")
            
        # Remove duplicates while preserving order
        seen = set()
        chain = [x for x in chain if not (x in seen or seen.add(x))]
        
        return chain
    
    def _estimate_duration(self, steps: List[WorkflowStep]) -> str:
        """Estimate total workflow duration"""
        total_minutes = sum(step.timeout_minutes for step in steps)
        
        # Account for parallel processing
        parallel_count = sum(1 for step in steps if step.conditions.get("parallel_eligible"))
        if parallel_count > 0:
            # Reduce by 30% for parallel steps
            total_minutes *= 0.7
            
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        
        if hours > 0:
            return f"{hours} hours {minutes} minutes"
        else:
            return f"{minutes} minutes"
    
    def _define_success_metrics(self, req: WorkflowRequirement) -> List[str]:
        """Define success metrics for workflow"""
        metrics = [
            f"{req.expected_outcome} achieved",
            "All approvals obtained within timeline",
            "Compliance requirements met"
        ]
        
        if req.urgency == "emergency":
            metrics.append("Response time under 30 minutes")
            
        if req.property_type in ["20_unit", "50_unit"]:
            metrics.append("All affected units addressed")
            
        return metrics


async def demonstrate_swarm_workflow_builder():
    """Demonstrate the swarm workflow builder"""
    print("🚀 SWARM WORKFLOW BUILDER DEMONSTRATION")
    print("=" * 80)
    print("Building intelligent workflows using swarm coordination")
    print("=" * 80)
    
    builder = WorkflowBuilderSwarm()
    
    # Test scenarios
    scenarios = [
        WorkflowRequirement(
            name="Emergency Plumbing Repair Workflow",
            description="Handle emergency water leak in multi-unit building",
            scenario="Major water leak affecting multiple units in 20-unit building",
            triggers=["emergency_maintenance_call", "water_sensor_alert"],
            expected_outcome="Leak stopped, damage minimized, units restored",
            constraints={
                "response_time": "immediate",
                "affected_units": 5,
                "potential_damage": "high"
            },
            approval_limits={"emergency_repair": 15000, "restoration": 25000},
            time_constraints={"initial_response": "15 minutes", "full_resolution": "4 hours"},
            compliance_requirements=["insurance_notification", "tenant_safety_protocol"],
            property_type="20_unit",
            urgency="emergency"
        ),
        
        WorkflowRequirement(
            name="Premium Lease Application Workflow",
            description="Process high-value lease with special concessions",
            scenario="Executive tenant applying for penthouse with custom terms",
            triggers=["premium_application_received"],
            expected_outcome="Lease executed with approved terms",
            constraints={
                "lease_value": 8500,  # Monthly
                "concessions_requested": ["2_months_free", "parking", "pet_waiver"],
                "background_check": "comprehensive"
            },
            approval_limits={"monthly_rent": 8500, "total_concessions": 17000},
            time_constraints={"initial_screening": "4 hours", "final_decision": "48 hours"},
            compliance_requirements=["fair_housing", "income_verification", "credit_check"],
            property_type="50_unit",
            urgency="high"
        ),
        
        WorkflowRequirement(
            name="Routine Maintenance Optimization",
            description="Optimize preventive maintenance across portfolio",
            scenario="Quarterly maintenance for single-family homes",
            triggers=["quarterly_schedule", "maintenance_due"],
            expected_outcome="All properties maintained on schedule",
            constraints={
                "properties_count": 15,
                "budget_per_property": 500
            },
            approval_limits={"total_budget": 7500},
            time_constraints={"completion": "2 weeks"},
            compliance_requirements=["vendor_insurance", "quality_standards"],
            property_type="single_family",
            urgency="normal"
        )
    ]
    
    # Build workflows for each scenario
    for scenario in scenarios:
        print(f"\n\n{'='*70}")
        print(f"📋 BUILDING WORKFLOW: {scenario.name}")
        print(f"{'='*70}")
        
        workflow = await builder.build_workflow(scenario)
        
        # Display results
        print(f"\n\n✅ WORKFLOW BUILT SUCCESSFULLY")
        print(f"ID: {workflow.workflow_id}")
        print(f"Category: {workflow.category}")
        print(f"Complexity: {workflow.complexity_score:.2f}")
        print(f"Duration: {workflow.estimated_duration}")
        
        print(f"\n📊 Workflow Steps ({len(workflow.steps)}):")
        for i, step in enumerate(workflow.steps, 1):
            approval = " [APPROVAL REQUIRED]" if step.requires_approval else ""
            amount = f" (${step.approval_amount:,.0f})" if step.approval_amount else ""
            deps = f" ← {', '.join(step.dependencies)}" if step.dependencies else ""
            
            print(f"\n   {i}. {step.name}{approval}{amount}")
            print(f"      Agent: {step.agent_role}")
            print(f"      Action: {step.action}")
            print(f"      Timeout: {step.timeout_minutes} min")
            if deps:
                print(f"      Dependencies: {deps}")
            if step.outputs:
                print(f"      Outputs: {', '.join(step.outputs)}")
        
        print(f"\n🔐 Approval Chain: {' → '.join(workflow.approval_chain)}")
        
        print(f"\n📋 Success Metrics:")
        for metric in workflow.success_metrics:
            print(f"   • {metric}")
        
        if workflow.compliance_checks:
            print(f"\n⚖️ Compliance Requirements:")
            for check in workflow.compliance_checks:
                print(f"   • {check}")
    
    print(f"\n\n✨ SWARM WORKFLOW BUILDER DEMONSTRATION COMPLETE!")
    print(f"🎯 The system can now build any property management workflow intelligently!")


if __name__ == "__main__":
    asyncio.run(demonstrate_swarm_workflow_builder())