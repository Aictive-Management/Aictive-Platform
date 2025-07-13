#!/usr/bin/env python3
"""
Simplified test script for the new AssistantManagerAgent
"""

import asyncio
import json
from datetime import datetime
from claude_service import ClaudeService

class MockOrchestrator:
    """Mock orchestrator for testing"""
    def __init__(self):
        self.agents = {}
    
    def register_agent(self, role, agent):
        self.agents[role] = agent
    
    async def send_message(self, to_role, subject, message, data=None, message_type="normal"):
        print(f"📨 Message sent to {to_role}: {subject}")
        print(f"   Content: {message}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")

class AssistantManagerAgent:
    """Assistant Property Manager agent with delegated authority"""
    
    def __init__(self, orchestrator):
        self.role = "assistant_manager"
        self.orchestrator = orchestrator
        self.claude = ClaudeService()
        self.can_approve_up_to = 5000
        self.permissions = [
            "approve_maintenance_up_to_5000",
            "approve_payment_plans", 
            "tenant_communications",
            "staff_scheduling",
            "emergency_decisions"
        ]
    
    async def execute_action(self, action: str, input_data: dict) -> dict:
        """Execute assistant manager actions"""
        context = input_data.get('context', {})
        
        if action == "approve_maintenance_request":
            return await self._approve_maintenance_request(context)
        elif action == "approve_payment_plan":
            return await self._approve_payment_plan(context)
        elif action == "handle_tenant_communication":
            return await self._handle_tenant_communication(context)
        elif action == "handle_emergency":
            return await self._handle_emergency(context)
        else:
            return await self._generic_action(action, context)
    
    async def make_decision(self, decision_input: dict) -> dict:
        """Make assistant manager decisions"""
        context = decision_input.get('context', {})
        decision_type = context.get('decision_type', 'general')
        
        # Use Claude for decision making
        decision_prompt = f"""
        As an Assistant Property Manager, make a decision based on:
        Decision Type: {decision_type}
        Context: {context}
        Approval Limit: ${self.can_approve_up_to}
        
        Consider operational efficiency, tenant satisfaction, and cost management.
        Provide clear reasoning and next steps.
        """
        
        try:
            response = await self.claude.generate_response(
                "general_response",
                {"prompt": decision_prompt, "context": context}
            )
            
            return {
                "decision": "approve",  # Default decision
                "reasoning": response,
                "confidence": 0.7,
                "requires_escalation": False
            }
        except Exception as e:
            return {
                "decision": "approve",
                "reasoning": f"Decision made based on operational needs. Error: {str(e)}",
                "confidence": 0.7,
                "requires_escalation": False
            }
    
    async def _approve_maintenance_request(self, context: dict) -> dict:
        """Approve maintenance requests up to $5000"""
        request_details = context.get('request_details', {})
        estimated_cost = request_details.get('estimated_cost', 0)
        urgency = request_details.get('urgency', 'normal')
        
        if estimated_cost <= self.can_approve_up_to:
            approval = {
                "approved": True,
                "approved_amount": estimated_cost,
                "approved_by": self.role,
                "notes": f"Approved by Assistant Manager - {urgency} priority",
                "authorization_code": f"AM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Notify maintenance team
            await self.orchestrator.send_message(
                "maintenance_supervisor",
                "Maintenance Request Approved",
                f"Maintenance request approved for ${estimated_cost}. Priority: {urgency}",
                {"approval": approval, "request_details": request_details}
            )
            
            return {"completed": True, "output": approval}
        else:
            # Escalate to property manager
            await self.orchestrator.send_message(
                "property_manager",
                "Maintenance Request Escalation",
                f"Maintenance request for ${estimated_cost} exceeds my limit. Requires your approval.",
                context
            )
            
            return {
                "completed": True,
                "output": {
                    "approved": False,
                    "reason": "exceeds_approval_limit",
                    "escalated_to": "property_manager"
                }
            }
    
    async def _approve_payment_plan(self, context: dict) -> dict:
        """Approve payment plans for tenants"""
        tenant_id = context.get('tenant_id')
        total_amount = context.get('total_amount', 0)
        installments = context.get('installments', 2)
        reason = context.get('reason', 'financial_hardship')
        
        # Assistant manager can approve payment plans
        plan = {
            "plan_id": f"PLAN-AM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "tenant_id": tenant_id,
            "total_amount": total_amount,
            "installments": installments,
            "monthly_payment": total_amount / installments,
            "approved_by": self.role,
            "reason": reason,
            "status": "approved"
        }
        
        # Notify accounting team
        await self.orchestrator.send_message(
            "accountant",
            "Payment Plan Approved",
            f"Payment plan approved for tenant {tenant_id}. ${total_amount} over {installments} months.",
            {"plan": plan}
        )
        
        return {"completed": True, "output": plan}
    
    async def _handle_tenant_communication(self, context: dict) -> dict:
        """Handle tenant communications and issues"""
        tenant_id = context.get('tenant_id')
        issue_type = context.get('issue_type', 'general')
        priority = context.get('priority', 'normal')
        
        # Use Claude to generate appropriate response
        response_prompt = f"""
        As an Assistant Property Manager, respond to a tenant issue:
        Issue Type: {issue_type}
        Priority: {priority}
        Context: {context}
        
        Provide a professional, helpful response that addresses the tenant's concerns.
        """
        
        try:
            response = await self.claude.generate_response(
                "general_response",
                {"prompt": response_prompt, "context": context}
            )
            
            communication = {
                "tenant_id": tenant_id,
                "issue_type": issue_type,
                "priority": priority,
                "response": response,
                "action_items": [],
                "follow_up_required": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # If high priority, notify relevant department
            if priority in ['high', 'urgent']:
                if issue_type == 'maintenance':
                    await self.orchestrator.send_message(
                        "maintenance_supervisor",
                        "High Priority Tenant Issue",
                        f"High priority maintenance issue from tenant {tenant_id}",
                        communication
                    )
                elif issue_type == 'payment':
                    await self.orchestrator.send_message(
                        "accountant",
                        "High Priority Payment Issue",
                        f"High priority payment issue from tenant {tenant_id}",
                        communication
                    )
            
            return {"completed": True, "output": communication}
        except Exception as e:
            return {
                "completed": True,
                "output": {
                    "tenant_id": tenant_id,
                    "issue_type": issue_type,
                    "priority": priority,
                    "response": f"Thank you for contacting us. We're looking into this matter. Error: {str(e)}",
                    "action_items": [],
                    "follow_up_required": False,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _handle_emergency(self, context: dict) -> dict:
        """Handle emergency situations"""
        emergency_type = context.get('emergency_type', 'unknown')
        severity = context.get('severity', 'medium')
        location = context.get('location', 'unknown')
        
        # Take immediate action based on emergency type
        if emergency_type == 'fire':
            action = "evacuate_and_call_fire_department"
        elif emergency_type == 'flood':
            action = "shut_off_water_and_assess_damage"
        elif emergency_type == 'power_outage':
            action = "check_electrical_systems_and_generators"
        elif emergency_type == 'security_breach':
            action = "secure_area_and_notify_authorities"
        else:
            action = "assess_situation_and_respond_appropriately"
        
        emergency_response = {
            "emergency_id": f"EMG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "type": emergency_type,
            "severity": severity,
            "location": location,
            "action_taken": action,
            "responded_by": self.role,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Notify property manager immediately
        await self.orchestrator.send_message(
            "property_manager",
            f"EMERGENCY: {emergency_type.upper()}",
            f"{severity} emergency at {location}. Action taken: {action}",
            {"emergency": emergency_response}
        )
        
        return {"completed": True, "output": emergency_response}
    
    async def _generic_action(self, action: str, context: dict) -> dict:
        """Handle any other action within assistant manager scope"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "assistant_manager",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

async def test_assistant_manager():
    """Test the AssistantManagerAgent functionality"""
    
    print("🚀 Testing AssistantManagerAgent...")
    
    # Create mock orchestrator and agent
    orchestrator = MockOrchestrator()
    agent = AssistantManagerAgent(orchestrator)
    
    print(f"✅ Created AssistantManagerAgent with approval limit: ${agent.can_approve_up_to}")
    print(f"📋 Permissions: {agent.permissions}")
    
    # Test 1: Approve maintenance request within limit
    print("\n🔧 Test 1: Approve maintenance request ($3000)")
    result = await agent.execute_action("approve_maintenance_request", {
        "context": {
            "request_details": {
                "estimated_cost": 3000,
                "urgency": "high",
                "description": "HVAC system replacement"
            }
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Try to approve maintenance request over limit
    print("\n🔧 Test 2: Try to approve maintenance request ($8000) - should escalate")
    result = await agent.execute_action("approve_maintenance_request", {
        "context": {
            "request_details": {
                "estimated_cost": 8000,
                "urgency": "normal",
                "description": "Major plumbing repair"
            }
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 3: Approve payment plan
    print("\n💰 Test 3: Approve payment plan")
    result = await agent.execute_action("approve_payment_plan", {
        "context": {
            "tenant_id": "TEN-001",
            "total_amount": 2400,
            "installments": 3,
            "reason": "financial_hardship"
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 4: Handle tenant communication
    print("\n📞 Test 4: Handle tenant communication")
    result = await agent.execute_action("handle_tenant_communication", {
        "context": {
            "tenant_id": "TEN-002",
            "issue_type": "maintenance",
            "priority": "high",
            "description": "No hot water in unit"
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 5: Handle emergency
    print("\n🚨 Test 5: Handle emergency")
    result = await agent.execute_action("handle_emergency", {
        "context": {
            "emergency_type": "power_outage",
            "severity": "high",
            "location": "Building A"
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 6: Make decision
    print("\n🤔 Test 6: Make decision")
    result = await agent.make_decision({
        "context": {
            "decision_type": "maintenance_approval",
            "cost": 2500,
            "urgency": "medium"
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    print("\n✅ AssistantManagerAgent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_assistant_manager()) 