#!/usr/bin/env python3
"""
Test script for the new AssistantManagerAgent
"""

import asyncio
import json
from role_agents import AssistantManagerAgent
from sop_orchestration import SOPOrchestrationEngine

async def test_assistant_manager():
    """Test the AssistantManagerAgent functionality"""
    
    print("🚀 Testing AssistantManagerAgent...")
    
    # Create orchestrator and agent
    orchestrator = SOPOrchestrationEngine()
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