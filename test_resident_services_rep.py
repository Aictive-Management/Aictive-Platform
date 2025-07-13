#!/usr/bin/env python3
"""
Test script for Resident Services Rep Agent
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Optional

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from role_agents import ResidentServicesRepAgent
from sop_orchestration import SOPOrchestrationEngine

class MockOrchestrator:
    """Mock orchestrator for testing"""
    
    def __init__(self):
        self.agents = {}
        self.messages = []
    
    def register_agent(self, role: str, agent):
        self.agents[role] = agent
    
    async def send_message(self, to_role: str, subject: str, message: str, data: Optional[dict] = None, message_type: str = "notification"):
        self.messages.append({
            "to_role": to_role,
            "subject": subject,
            "message": message,
            "data": data or {},
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        print(f"📨 Message sent to {to_role}: {subject}")
    
    async def send_agent_message(self, from_role: str, to_role: str, subject: str, message: str, data: Optional[dict] = None, message_type: str = "notification"):
        """Mock send_agent_message method"""
        return await self.send_message(to_role, subject, message, data, message_type)

async def test_resident_services_rep():
    """Test the Resident Services Rep Agent"""
    
    print("👥 Testing Resident Services Rep Agent")
    print("=" * 50)
    
    # Create mock orchestrator
    orchestrator = MockOrchestrator()
    
    # Create the agent (ignore type checking for mock)
    agent = ResidentServicesRepAgent(orchestrator)  # type: ignore
    
    print(f"✅ Agent created: {agent.role}")
    print(f"💰 Approval limit: ${agent.can_approve_up_to}")
    print(f"🔑 Permissions: {', '.join(agent.permissions)}")
    print()
    
    # Test 1: Respond to inquiry
    print("💬 Test 1: Respond to Inquiry")
    print("-" * 30)
    
    inquiry_result = await agent.execute_action("respond_inquiry", {
        "context": {
            "inquiry": "What are the pool hours?",
            "resident_id": "RES-001"
        }
    })
    
    print(f"✅ Inquiry responded: {inquiry_result['completed']}")
    if inquiry_result['completed']:
        output = inquiry_result['output']
        print(f"   Resident ID: {output['resident_id']}")
        print(f"   Response: {output['response'][:100]}...")
    print()
    
    # Test 2: Log service request
    print("📝 Test 2: Log Service Request")
    print("-" * 30)
    
    service_result = await agent.execute_action("log_service_request", {
        "context": {
            "request_type": "maintenance",
            "details": "Kitchen sink is clogged",
            "resident_id": "RES-002",
            "urgency": "normal"
        }
    })
    
    print(f"✅ Service request logged: {service_result['completed']}")
    if service_result['completed']:
        output = service_result['output']
        print(f"   Request type: {output['log_entry']['request_type']}")
        print(f"   Urgency: {output['log_entry']['urgency']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 3: Provide information
    print("ℹ️ Test 3: Provide Information")
    print("-" * 30)
    
    info_result = await agent.execute_action("provide_info", {
        "context": {
            "topic": "amenity policies",
            "resident_id": "RES-003"
        }
    })
    
    print(f"✅ Information provided: {info_result['completed']}")
    if info_result['completed']:
        output = info_result['output']
        print(f"   Topic: {output['topic']}")
        print(f"   Info: {output['info'][:100]}...")
    print()
    
    # Test 4: Escalate issue
    print("🚨 Test 4: Escalate Issue")
    print("-" * 30)
    
    escalation_result = await agent.execute_action("escalate_issue", {
        "context": {
            "issue_type": "complaint",
            "resident_id": "RES-004",
            "details": "Noise complaint about neighbor",
            "severity": "high"
        }
    })
    
    print(f"✅ Issue escalated: {escalation_result['completed']}")
    if escalation_result['completed']:
        output = escalation_result['output']
        print(f"   Issue type: {output['issue_type']}")
        print(f"   Escalation role: {output['escalation_role']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 5: Assist move-in
    print("🏠 Test 5: Assist Move-In")
    print("-" * 30)
    
    move_in_result = await agent.execute_action("assist_move_in_out", {
        "context": {
            "move_type": "in",
            "resident_id": "RES-005",
            "unit_id": "UNIT-101"
        }
    })
    
    print(f"✅ Move-in assistance: {move_in_result['completed']}")
    if move_in_result['completed']:
        output = move_in_result['output']
        print(f"   Move type: {output['move_type']}")
        print(f"   Unit ID: {output['unit_id']}")
        print(f"   Checklist items: {len(output['checklist'])}")
        print(f"   Next steps: {len(output['next_steps'])}")
    print()
    
    # Test 6: Assist move-out
    print("🚪 Test 6: Assist Move-Out")
    print("-" * 30)
    
    move_out_result = await agent.execute_action("assist_move_in_out", {
        "context": {
            "move_type": "out",
            "resident_id": "RES-006",
            "unit_id": "UNIT-202"
        }
    })
    
    print(f"✅ Move-out assistance: {move_out_result['completed']}")
    if move_out_result['completed']:
        output = move_out_result['output']
        print(f"   Move type: {output['move_type']}")
        print(f"   Unit ID: {output['unit_id']}")
        print(f"   Checklist items: {len(output['checklist'])}")
        print(f"   Next steps: {len(output['next_steps'])}")
    print()
    
    # Test 7: Collect feedback (positive)
    print("👍 Test 7: Collect Positive Feedback")
    print("-" * 30)
    
    positive_feedback_result = await agent.execute_action("collect_feedback", {
        "context": {
            "resident_id": "RES-007",
            "feedback": "The maintenance team was very helpful and fixed my issue quickly",
            "feedback_type": "maintenance",
            "sentiment": "positive"
        }
    })
    
    print(f"✅ Positive feedback collected: {positive_feedback_result['completed']}")
    if positive_feedback_result['completed']:
        output = positive_feedback_result['output']
        print(f"   Feedback type: {output['feedback_type']}")
        print(f"   Sentiment: {output['sentiment']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 8: Collect feedback (negative)
    print("👎 Test 8: Collect Negative Feedback")
    print("-" * 30)
    
    negative_feedback_result = await agent.execute_action("collect_feedback", {
        "context": {
            "resident_id": "RES-008",
            "feedback": "The pool was closed for maintenance without notice",
            "feedback_type": "amenity",
            "sentiment": "negative"
        }
    })
    
    print(f"✅ Negative feedback collected: {negative_feedback_result['completed']}")
    if negative_feedback_result['completed']:
        output = negative_feedback_result['output']
        print(f"   Feedback type: {output['feedback_type']}")
        print(f"   Sentiment: {output['sentiment']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 9: Log urgent service request
    print("⚡ Test 9: Log Urgent Service Request")
    print("-" * 30)
    
    urgent_result = await agent.execute_action("log_service_request", {
        "context": {
            "request_type": "repair",
            "details": "No hot water in apartment",
            "resident_id": "RES-009",
            "urgency": "urgent"
        }
    })
    
    print(f"✅ Urgent request logged: {urgent_result['completed']}")
    if urgent_result['completed']:
        output = urgent_result['output']
        print(f"   Request type: {output['log_entry']['request_type']}")
        print(f"   Urgency: {output['log_entry']['urgency']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 10: Escalate billing issue
    print("💰 Test 10: Escalate Billing Issue")
    print("-" * 30)
    
    billing_result = await agent.execute_action("escalate_issue", {
        "context": {
            "issue_type": "billing",
            "resident_id": "RES-010",
            "details": "Dispute over late fee charges",
            "severity": "medium"
        }
    })
    
    print(f"✅ Billing issue escalated: {billing_result['completed']}")
    if billing_result['completed']:
        output = billing_result['output']
        print(f"   Issue type: {output['issue_type']}")
        print(f"   Escalation role: {output['escalation_role']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Show all messages sent
    print("📨 Messages Sent:")
    print("-" * 30)
    for i, msg in enumerate(orchestrator.messages, 1):
        print(f"{i}. To {msg['to_role']}: {msg['subject']}")
    
    print()
    print("🎉 Resident Services Rep Agent testing completed!")
    print(f"📊 Total messages sent: {len(orchestrator.messages)}")

if __name__ == "__main__":
    asyncio.run(test_resident_services_rep()) 