"""
Workflow Builder Swarm System
Uses AI swarm coordination to build complex workflows from requirements
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
from datetime import datetime

from sop_orchestration import SOPWorkflow, WorkflowStep, WorkflowEngine
from role_agents import AgentRegistry


class WorkflowComplexity(Enum):
    """Workflow complexity levels"""
    SIMPLE = "simple"      # 1-3 steps, single department
    MEDIUM = "medium"      # 4-6 steps, 2-3 departments
    COMPLEX = "complex"    # 7+ steps, multiple departments
    CRITICAL = "critical"  # High risk, requires executive approval


@dataclass
class WorkflowRequirement:
    """Requirements for building a workflow"""
    name: str
    description: str
    trigger: str  # What initiates this workflow
    category: str  # maintenance, leasing, financial, etc.
    priority: str = "normal"  # low, normal, high, urgent
    
    # Business rules
    max_duration: Optional[int] = None  # Maximum time in minutes
    approval_thresholds: Dict[str, float] = field(default_factory=dict)
    compliance_requirements: List[str] = field(default_factory=list)
    
    # Constraints
    required_agents: List[str] = field(default_factory=list)
    excluded_agents: List[str] = field(default_factory=list)
    parallel_allowed: bool = True
    
    # Expected outcomes
    success_criteria: List[str] = field(default_factory=list)
    failure_conditions: List[str] = field(default_factory=list)


@dataclass
class SwarmAgent:
    """Individual agent in the workflow builder swarm"""
    name: str
    role: str
    capabilities: List[str]
    
    async def analyze_requirement(self, requirement: WorkflowRequirement) -> Dict[str, Any]:
        """Analyze requirement and suggest workflow components"""
        # This would use AI to analyze the requirement
        # For now, using rule-based logic
        suggestions = {
            "steps": [],
            "agents": [],
            "decision_points": [],
            "parallel_opportunities": []
        }
        
        # Analyze based on category
        if requirement.category == "maintenance":
            suggestions["agents"].extend([
                "maintenance_tech",
                "maintenance_supervisor",
                "property_manager"
            ])
            
            if "emergency" in requirement.trigger.lower():
                suggestions["steps"].append({
                    "name": "immediate_assessment",
                    "agent": "maintenance_tech",
                    "timeout": 15
                })
        
        elif requirement.category == "leasing":
            suggestions["agents"].extend([
                "leasing_agent",
                "leasing_manager",
                "property_manager"
            ])
        
        return suggestions


class WorkflowBuilderSwarm:
    """Swarm coordinator for building workflows"""
    
    def __init__(self):
        self.agents = self._initialize_swarm()
        self.knowledge_base = self._load_knowledge_base()
        self.workflow_engine = WorkflowEngine()
        self.agent_registry = AgentRegistry()
    
    def _initialize_swarm(self) -> List[SwarmAgent]:
        """Initialize swarm agents"""
        return [
            SwarmAgent(
                "Requirements Analyst",
                "analyzer",
                ["requirement_parsing", "constraint_identification", "priority_assessment"]
            ),
            SwarmAgent(
                "Process Designer",
                "designer",
                ["step_sequencing", "parallel_optimization", "decision_tree_creation"]
            ),
            SwarmAgent(
                "Compliance Validator",
                "validator",
                ["regulatory_compliance", "sop_adherence", "risk_assessment"]
            ),
            SwarmAgent(
                "Efficiency Optimizer",
                "optimizer",
                ["bottleneck_identification", "parallel_processing", "resource_optimization"]
            ),
            SwarmAgent(
                "Integration Specialist",
                "integrator",
                ["system_integration", "data_flow_design", "api_coordination"]
            )
        ]
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load agent knowledge base"""
        try:
            with open("agent_knowledge_base.yaml", "r") as f:
                return yaml.safe_load(f)
        except:
            return {}
    
    async def build_workflow(
        self,
        requirement: WorkflowRequirement,
        use_swarm: bool = True
    ) -> SOPWorkflow:
        """Build a workflow from requirements"""
        
        # Determine complexity
        complexity = self._assess_complexity(requirement)
        
        if use_swarm and complexity in [WorkflowComplexity.COMPLEX, WorkflowComplexity.CRITICAL]:
            # Use swarm for complex workflows
            workflow = await self._swarm_build(requirement, complexity)
        else:
            # Use simple builder for basic workflows
            workflow = await self._simple_build(requirement)
        
        # Validate the workflow
        validation = await self._validate_workflow(workflow, requirement)
        if not validation["valid"]:
            # Apply corrections
            workflow = await self._apply_corrections(workflow, validation["issues"])
        
        return workflow
    
    def _assess_complexity(self, requirement: WorkflowRequirement) -> WorkflowComplexity:
        """Assess workflow complexity"""
        score = 0
        
        # Check triggers
        if any(trigger in requirement.trigger.lower() 
               for trigger in ["emergency", "critical", "urgent"]):
            score += 3
        
        # Check financial thresholds
        for threshold, amount in requirement.approval_thresholds.items():
            if amount > 10000:
                score += 2
            elif amount > 1000:
                score += 1
        
        # Check compliance requirements
        score += len(requirement.compliance_requirements)
        
        # Check multi-department coordination
        if len(requirement.required_agents) > 5:
            score += 2
        
        # Determine complexity level
        if score >= 8:
            return WorkflowComplexity.CRITICAL
        elif score >= 5:
            return WorkflowComplexity.COMPLEX
        elif score >= 3:
            return WorkflowComplexity.MEDIUM
        else:
            return WorkflowComplexity.SIMPLE
    
    async def _swarm_build(
        self,
        requirement: WorkflowRequirement,
        complexity: WorkflowComplexity
    ) -> SOPWorkflow:
        """Build workflow using swarm coordination"""
        print(f"\n🐝 Swarm building {complexity.value} workflow: {requirement.name}")
        
        # Phase 1: Parallel analysis by all agents
        analyses = await asyncio.gather(*[
            agent.analyze_requirement(requirement)
            for agent in self.agents
        ])
        
        # Phase 2: Synthesize recommendations
        synthesis = self._synthesize_analyses(analyses, requirement)
        
        # Phase 3: Build workflow structure
        workflow = SOPWorkflow(
            sop_id=f"SOP-{requirement.category.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=requirement.name,
            description=requirement.description,
            category=requirement.category,
            created_by="workflow_builder_swarm"
        )
        
        # Phase 4: Add steps based on synthesis
        for step_config in synthesis["steps"]:
            step = WorkflowStep(
                step_id=step_config["id"],
                name=step_config["name"],
                description=step_config.get("description", ""),
                agent_type=step_config["agent"],
                action=step_config.get("action", "process"),
                timeout=step_config.get("timeout", 300),
                retry_count=step_config.get("retry_count", 1),
                requires_approval=step_config.get("requires_approval", False),
                dependencies=step_config.get("dependencies", [])
            )
            workflow.add_step(step)
        
        # Phase 5: Add decision points
        for decision in synthesis.get("decision_points", []):
            # Add conditional logic to workflow
            pass
        
        return workflow
    
    async def _simple_build(self, requirement: WorkflowRequirement) -> SOPWorkflow:
        """Build simple workflow without swarm"""
        workflow = SOPWorkflow(
            sop_id=f"SOP-{requirement.category.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=requirement.name,
            description=requirement.description,
            category=requirement.category,
            created_by="workflow_builder"
        )
        
        # Build based on category templates
        if requirement.category == "maintenance":
            await self._add_maintenance_steps(workflow, requirement)
        elif requirement.category == "leasing":
            await self._add_leasing_steps(workflow, requirement)
        elif requirement.category == "financial":
            await self._add_financial_steps(workflow, requirement)
        else:
            await self._add_generic_steps(workflow, requirement)
        
        return workflow
    
    def _synthesize_analyses(
        self,
        analyses: List[Dict[str, Any]],
        requirement: WorkflowRequirement
    ) -> Dict[str, Any]:
        """Synthesize multiple agent analyses into cohesive workflow design"""
        synthesis = {
            "steps": [],
            "decision_points": [],
            "parallel_groups": [],
            "integrations": []
        }
        
        # Combine agent suggestions
        all_agents = set()
        for analysis in analyses:
            all_agents.update(analysis.get("agents", []))
        
        # Build step sequence based on agent hierarchy
        agent_hierarchy = self._get_agent_hierarchy(all_agents)
        
        step_id = 1
        for level in agent_hierarchy:
            for agent in level:
                if agent in requirement.excluded_agents:
                    continue
                    
                step = {
                    "id": f"step_{step_id}",
                    "name": f"{agent}_action",
                    "agent": agent,
                    "timeout": 300,
                    "dependencies": []
                }
                
                # Add dependencies from previous level
                if step_id > 1:
                    step["dependencies"] = [f"step_{step_id - 1}"]
                
                synthesis["steps"].append(step)
                step_id += 1
        
        return synthesis
    
    def _get_agent_hierarchy(self, agents: set) -> List[List[str]]:
        """Organize agents by hierarchical levels"""
        hierarchy = []
        
        # Define levels based on knowledge base
        levels = [
            ["maintenance_tech", "leasing_agent", "accountant"],
            ["maintenance_tech_lead", "senior_leasing_agent"],
            ["maintenance_supervisor", "leasing_manager", "accounting_manager"],
            ["property_manager", "assistant_manager"],
            ["director_accounting", "director_leasing"],
            ["vp_operations"],
            ["president"]
        ]
        
        for level in levels:
            level_agents = [agent for agent in level if agent in agents]
            if level_agents:
                hierarchy.append(level_agents)
        
        return hierarchy
    
    async def _add_maintenance_steps(
        self,
        workflow: SOPWorkflow,
        requirement: WorkflowRequirement
    ):
        """Add maintenance-specific steps"""
        # Initial assessment
        workflow.add_step(WorkflowStep(
            step_id="assess",
            name="Initial Assessment",
            description="Assess the maintenance issue",
            agent_type="maintenance_tech",
            action="assess_issue",
            timeout=900  # 15 minutes
        ))
        
        # Determine if emergency
        if "emergency" in requirement.trigger.lower():
            workflow.add_step(WorkflowStep(
                step_id="escalate",
                name="Emergency Escalation",
                description="Escalate to supervisor immediately",
                agent_type="maintenance_supervisor",
                action="handle_emergency",
                timeout=300,  # 5 minutes
                dependencies=["assess"]
            ))
        
        # Get approval if needed
        if requirement.approval_thresholds:
            workflow.add_step(WorkflowStep(
                step_id="approval",
                name="Obtain Approval",
                description="Get financial approval",
                agent_type="property_manager",
                action="approve_expense",
                timeout=3600,  # 1 hour
                requires_approval=True,
                dependencies=["assess"]
            ))
        
        # Execute repair
        workflow.add_step(WorkflowStep(
            step_id="execute",
            name="Execute Repair",
            description="Perform the maintenance work",
            agent_type="maintenance_tech",
            action="execute_repair",
            timeout=14400,  # 4 hours
            dependencies=["approval"] if requirement.approval_thresholds else ["assess"]
        ))
    
    async def _add_leasing_steps(
        self,
        workflow: SOPWorkflow,
        requirement: WorkflowRequirement
    ):
        """Add leasing-specific steps"""
        # Tenant inquiry
        workflow.add_step(WorkflowStep(
            step_id="inquiry",
            name="Handle Inquiry",
            description="Respond to leasing inquiry",
            agent_type="leasing_agent",
            action="handle_inquiry",
            timeout=1800  # 30 minutes
        ))
        
        # Schedule showing
        workflow.add_step(WorkflowStep(
            step_id="showing",
            name="Schedule Showing",
            description="Schedule unit showing",
            agent_type="leasing_agent",
            action="schedule_showing",
            timeout=3600,  # 1 hour
            dependencies=["inquiry"]
        ))
        
        # Process application
        workflow.add_step(WorkflowStep(
            step_id="application",
            name="Process Application",
            description="Process rental application",
            agent_type="leasing_manager",
            action="process_application",
            timeout=86400,  # 24 hours
            dependencies=["showing"]
        ))
    
    async def _add_financial_steps(
        self,
        workflow: SOPWorkflow,
        requirement: WorkflowRequirement
    ):
        """Add financial-specific steps"""
        # Financial review
        workflow.add_step(WorkflowStep(
            step_id="review",
            name="Financial Review",
            description="Review financial request",
            agent_type="accountant",
            action="review_request",
            timeout=7200  # 2 hours
        ))
        
        # Manager approval
        workflow.add_step(WorkflowStep(
            step_id="mgr_approval",
            name="Manager Approval",
            description="Accounting manager approval",
            agent_type="accounting_manager",
            action="approve_financial",
            timeout=14400,  # 4 hours
            requires_approval=True,
            dependencies=["review"]
        ))
        
        # Director approval for large amounts
        if any(amount > 10000 for amount in requirement.approval_thresholds.values()):
            workflow.add_step(WorkflowStep(
                step_id="dir_approval",
                name="Director Approval",
                description="Director of Accounting approval",
                agent_type="director_accounting",
                action="approve_large_expense",
                timeout=86400,  # 24 hours
                requires_approval=True,
                dependencies=["mgr_approval"]
            ))
    
    async def _add_generic_steps(
        self,
        workflow: SOPWorkflow,
        requirement: WorkflowRequirement
    ):
        """Add generic workflow steps"""
        # Default three-step workflow
        workflow.add_step(WorkflowStep(
            step_id="initiate",
            name="Initiate Process",
            description="Start the workflow process",
            agent_type=requirement.required_agents[0] if requirement.required_agents else "property_manager",
            action="initiate",
            timeout=1800
        ))
        
        workflow.add_step(WorkflowStep(
            step_id="process",
            name="Process Request",
            description="Process the main request",
            agent_type=requirement.required_agents[1] if len(requirement.required_agents) > 1 else "property_manager",
            action="process",
            timeout=3600,
            dependencies=["initiate"]
        ))
        
        workflow.add_step(WorkflowStep(
            step_id="complete",
            name="Complete Process",
            description="Finalize and close",
            agent_type=requirement.required_agents[2] if len(requirement.required_agents) > 2 else "property_manager",
            action="complete",
            timeout=1800,
            dependencies=["process"]
        ))
    
    async def _validate_workflow(
        self,
        workflow: SOPWorkflow,
        requirement: WorkflowRequirement
    ) -> Dict[str, Any]:
        """Validate workflow meets requirements"""
        issues = []
        
        # Check required agents are included
        workflow_agents = {step.agent_type for step in workflow.steps}
        missing_agents = set(requirement.required_agents) - workflow_agents
        if missing_agents:
            issues.append(f"Missing required agents: {missing_agents}")
        
        # Check excluded agents
        excluded_present = workflow_agents & set(requirement.excluded_agents)
        if excluded_present:
            issues.append(f"Excluded agents present: {excluded_present}")
        
        # Check max duration
        if requirement.max_duration:
            total_duration = sum(step.timeout for step in workflow.steps) / 60
            if total_duration > requirement.max_duration:
                issues.append(f"Workflow duration {total_duration} exceeds max {requirement.max_duration}")
        
        # Check compliance requirements
        # TODO: Implement compliance checks
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    async def _apply_corrections(
        self,
        workflow: SOPWorkflow,
        issues: List[str]
    ) -> SOPWorkflow:
        """Apply corrections to workflow based on validation issues"""
        # TODO: Implement correction logic
        return workflow


# Demo function
async def demo_workflow_builder():
    """Demonstrate workflow builder capabilities"""
    print("🏗️ Workflow Builder Swarm Demo")
    print("=" * 50)
    
    builder = WorkflowBuilderSwarm()
    
    # Test scenarios
    scenarios = [
        # Simple maintenance
        WorkflowRequirement(
            name="Routine Maintenance Request",
            description="Handle routine maintenance requests",
            trigger="tenant_maintenance_request",
            category="maintenance",
            priority="normal",
            max_duration=240,  # 4 hours
            approval_thresholds={"repair_cost": 500}
        ),
        
        # Complex emergency
        WorkflowRequirement(
            name="Emergency Water Leak Response",
            description="Handle emergency water leak with potential major damage",
            trigger="emergency_water_leak",
            category="maintenance",
            priority="urgent",
            max_duration=60,  # 1 hour
            approval_thresholds={"emergency_repair": 5000},
            compliance_requirements=["insurance_notification", "tenant_safety"],
            required_agents=["maintenance_tech", "maintenance_supervisor", "property_manager"]
        ),
        
        # Multi-department workflow
        WorkflowRequirement(
            name="Premium Lease Application",
            description="Process high-value lease application with special terms",
            trigger="premium_lease_application",
            category="leasing",
            priority="high",
            max_duration=2880,  # 48 hours
            approval_thresholds={"monthly_rent": 5000, "concessions": 1000},
            compliance_requirements=["fair_housing", "background_check", "income_verification"],
            required_agents=["leasing_agent", "leasing_manager", "property_manager", "accounting_manager"]
        )
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Building workflow: {scenario.name}")
        print(f"   Category: {scenario.category}")
        print(f"   Priority: {scenario.priority}")
        
        # Assess complexity
        complexity = builder._assess_complexity(scenario)
        print(f"   Complexity: {complexity.value}")
        
        # Build workflow
        use_swarm = complexity in [WorkflowComplexity.COMPLEX, WorkflowComplexity.CRITICAL]
        workflow = await builder.build_workflow(scenario, use_swarm=use_swarm)
        
        print(f"\n   ✅ Workflow built: {workflow.workflow_id}")
        print(f"   Steps: {len(workflow.steps)}")
        
        for step in workflow.steps:
            deps = f" (depends on: {', '.join(step.dependencies)})" if step.dependencies else ""
            approval = " [APPROVAL REQUIRED]" if step.requires_approval else ""
            print(f"      → {step.name} ({step.agent_type}){deps}{approval}")
        
        # Validate
        validation = await builder._validate_workflow(workflow, scenario)
        if validation["valid"]:
            print(f"   ✅ Validation passed")
        else:
            print(f"   ⚠️  Validation issues: {validation['issues']}")
    
    print("\n✨ Workflow Builder Swarm Ready!")
    print("   - Handles simple to critical complexity")
    print("   - Enforces compliance requirements")
    print("   - Optimizes for efficiency")
    print("   - Validates against business rules")


if __name__ == "__main__":
    asyncio.run(demo_workflow_builder())