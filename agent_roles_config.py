"""
Agent Roles Configuration for Aictive Platform v2
Defines the 13 property management roles and their AI capabilities
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from claude_service import ClaudeService
from ai_services import MultimodalAIService


@dataclass
class AgentRoleConfig:
    """Configuration for property management agent roles"""
    
    # Define agent specializations based on their actual job functions
    role_specializations = {
        "property_manager": {
            "focus": "Overall property operations and tenant relations",
            "capabilities": ["damage_assessment", "tenant_communication", "owner_reporting"],
            "decision_style": "balanced",  # Considers all stakeholders
            "priority": "property_value_preservation"
        },
        "director_leasing": {
            "focus": "Maximizing occupancy and rental income",
            "capabilities": ["lead_scoring", "application_processing", "market_analysis"],
            "decision_style": "sales_oriented",
            "priority": "occupancy_rate"
        },
        "leasing_agent": {
            "focus": "Direct tenant interaction and property showings",
            "capabilities": ["showing_scheduling", "prospect_communication", "tour_management"],
            "decision_style": "customer_service",
            "priority": "tenant_satisfaction"
        },
        "assistant_manager": {
            "focus": "Supporting daily operations",
            "capabilities": ["task_coordination", "vendor_management", "emergency_response"],
            "decision_style": "operational",
            "priority": "efficiency"
        },
        "regional_manager": {
            "focus": "Multi-property oversight and strategy",
            "capabilities": ["portfolio_analysis", "team_management", "strategic_planning"],
            "decision_style": "strategic",
            "priority": "portfolio_performance"
        },
        "bookkeeper": {
            "focus": "Accurate financial record keeping",
            "capabilities": ["transaction_recording", "account_reconciliation", "report_generation"],
            "decision_style": "detail_oriented",
            "priority": "accuracy"
        },
        "admin_assistant": {
            "focus": "Administrative support and documentation",
            "capabilities": ["document_management", "scheduling", "communication_coordination"],
            "decision_style": "process_focused",
            "priority": "organization"
        },
        "property_accountant": {
            "focus": "Financial analysis and reporting",
            "capabilities": ["financial_analysis", "budget_planning", "variance_analysis"],
            "decision_style": "analytical",
            "priority": "financial_health"
        },
        "marketing_manager": {
            "focus": "Property marketing and branding",
            "capabilities": ["campaign_creation", "market_research", "content_generation"],
            "decision_style": "creative",
            "priority": "brand_visibility"
        },
        "client_experience": {
            "focus": "Resident satisfaction and retention",
            "capabilities": ["satisfaction_analysis", "retention_strategies", "community_building"],
            "decision_style": "empathetic",
            "priority": "resident_retention"
        },
        "resident_services": {
            "focus": "Handling resident needs and concerns",
            "capabilities": ["issue_resolution", "service_coordination", "feedback_management"],
            "decision_style": "service_oriented",
            "priority": "resident_happiness"
        },
        "staff_manager": {
            "focus": "General management and oversight",
            "capabilities": ["team_coordination", "policy_implementation", "performance_management"],
            "decision_style": "leadership",
            "priority": "team_effectiveness"
        },
        "maintenance_coordinator": {
            "focus": "Maintenance scheduling and vendor management",
            "capabilities": ["work_order_management", "vendor_coordination", "preventive_maintenance"],
            "decision_style": "practical",
            "priority": "property_condition"
        }
    }


class PropertyManagementAIOrchestrator:
    """
    Orchestrates AI capabilities for 13 property management roles
    Each agent has specific prompting strategies based on their role
    """
    
    def __init__(self):
        self.config = AgentRoleConfig()
        self.ai_service = MultimodalAIService()
        self.claude = ClaudeService()
        
    async def process_as_role(
        self,
        role: str,
        task_type: str,
        data: Dict,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Process task with role-specific AI configuration
        
        Args:
            role: One of the 13 property management roles
            task_type: Type of task to perform
            data: Input data for processing
            context: Additional context (previous interactions, property info, etc.)
        """
        
        if role not in self.config.role_specializations:
            raise ValueError(f"Unknown role: {role}")
            
        role_config = self.config.role_specializations[role]
        
        # Build role-specific prompt
        prompt = self._build_role_prompt(
            role=role,
            role_config=role_config,
            task_type=task_type,
            data=data,
            context=context
        )
        
        # Process with appropriate AI approach
        result = await self._process_with_ai(
            prompt=prompt,
            role=role,
            capabilities=role_config["capabilities"]
        )
        
        return {
            "role": role,
            "task_type": task_type,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "decision_style": role_config["decision_style"]
        }
    
    def _build_role_prompt(
        self,
        role: str,
        role_config: Dict,
        task_type: str,
        data: Dict,
        context: Optional[Dict]
    ) -> str:
        """Build prompt tailored to the specific role"""
        
        role_title = role.replace('_', ' ').title()
        
        prompt = f"""
        You are acting as a {role_title} for a property management company.
        
        Your Focus: {role_config['focus']}
        Your Priority: {role_config['priority']}
        Decision Style: {role_config['decision_style']}
        
        Task: {task_type}
        
        Input Data:
        {json.dumps(data, indent=2)}
        """
        
        if context:
            prompt += f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        # Add role-specific instructions
        prompt += self._get_role_instructions(role, task_type)
        
        return prompt
    
    def _get_role_instructions(self, role: str, task_type: str) -> str:
        """Get specific instructions based on role and task"""
        
        instructions = "\n\nSpecific Instructions:\n"
        
        # Role-specific guidelines
        if role == "property_manager":
            instructions += """
            - Balance tenant needs with property owner interests
            - Ensure compliance with all regulations
            - Document all decisions clearly
            - Consider long-term property value
            """
        elif role == "director_leasing":
            instructions += """
            - Focus on qualifying leads effectively
            - Maximize rental income while maintaining standards
            - Track market trends and adjust strategies
            - Ensure fair housing compliance
            """
        elif role == "maintenance_coordinator":
            instructions += """
            - Prioritize based on urgency and safety
            - Track vendor performance and costs
            - Ensure quality work completion
            - Maintain detailed work order records
            """
        # Add more role-specific instructions...
        
        return instructions
    
    async def _process_with_ai(
        self,
        prompt: str,
        role: str,
        capabilities: List[str]
    ) -> Dict:
        """Process with AI based on role capabilities"""
        
        # For roles that need image analysis
        if "damage_assessment" in capabilities:
            # Use multimodal AI for image analysis
            return await self.ai_service.analyze_with_vision(prompt)
        
        # For financial roles
        elif any(cap in capabilities for cap in ["financial_analysis", "budget_planning"]):
            # Use structured data analysis
            return await self.ai_service.analyze_financial_data(prompt)
        
        # For communication roles
        elif any(cap in capabilities for cap in ["tenant_communication", "prospect_communication"]):
            # Optimize for clear, friendly communication
            return await self.claude.generate_response(
                prompt + "\n\nOptimize for clear, professional, and friendly communication."
            )
        
        # Default processing
        else:
            return await self.claude.generate(prompt)


class AgentCoordinator:
    """
    Coordinates multiple agents for complex workflows
    This is the actual swarm coordination, not SuperClaude
    """
    
    def __init__(self):
        self.orchestrator = PropertyManagementAIOrchestrator()
        self.active_workflows = {}
        
    async def coordinate_agents(
        self,
        workflow_type: str,
        initial_data: Dict
    ) -> Dict:
        """
        Coordinate multiple agents for a workflow
        
        Example workflows:
        - Maintenance request: Property Manager → Maintenance Coordinator → Bookkeeper
        - New application: Director of Leasing → Leasing Agent → Property Manager
        """
        
        workflows = {
            "maintenance_request": [
                ("property_manager", "intake_request"),
                ("maintenance_coordinator", "schedule_repair"),
                ("bookkeeper", "track_expense")
            ],
            "rental_application": [
                ("director_leasing", "screen_application"),
                ("leasing_agent", "schedule_showing"),
                ("property_manager", "final_approval")
            ],
            "monthly_reporting": [
                ("bookkeeper", "compile_transactions"),
                ("property_accountant", "analyze_financials"),
                ("property_manager", "review_report"),
                ("regional_manager", "strategic_review")
            ]
        }
        
        if workflow_type not in workflows:
            raise ValueError(f"Unknown workflow: {workflow_type}")
        
        workflow_id = f"WF-{datetime.utcnow().timestamp()}"
        results = []
        context = initial_data.copy()
        
        for role, task in workflows[workflow_type]:
            result = await self.orchestrator.process_as_role(
                role=role,
                task_type=task,
                data=context,
                context={"previous_steps": results}
            )
            
            results.append(result)
            # Update context with results from this step
            context.update(result.get("result", {}))
        
        return {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "steps_completed": len(results),
            "results": results,
            "final_outcome": context
        }


# Example usage
async def example_usage():
    """Example of using the property management AI system"""
    
    coordinator = AgentCoordinator()
    
    # Process a maintenance request through multiple agents
    maintenance_data = {
        "tenant_name": "John Smith",
        "unit": "101",
        "issue": "Water leak under kitchen sink",
        "urgency": "high",
        "images": ["leak1.jpg", "leak2.jpg"]
    }
    
    result = await coordinator.coordinate_agents(
        workflow_type="maintenance_request",
        initial_data=maintenance_data
    )
    
    print(f"Workflow completed: {result['workflow_id']}")
    print(f"Agents involved: {result['steps_completed']}")


if __name__ == "__main__":
    asyncio.run(example_usage())