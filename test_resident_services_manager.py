#!/usr/bin/env python3
"""
Test script for Resident Services Manager Agent
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Optional

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from role_agents import ResidentServicesManagerAgent
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

async def test_resident_services_manager():
    """Test the Resident Services Manager Agent"""
    
    print("🏠 Testing Resident Services Manager Agent")
    print("=" * 50)
    
    # Create mock orchestrator
    orchestrator = MockOrchestrator()
    
    # Create the agent (ignore type checking for mock)
    agent = ResidentServicesManagerAgent(orchestrator)  # type: ignore
    
    print(f"✅ Agent created: {agent.role}")
    print(f"💰 Approval limit: ${agent.can_approve_up_to}")
    print(f"🔑 Permissions: {', '.join(agent.permissions)}")
    print()
    
    # Test 1: Handle resident complaint
    print("📝 Test 1: Handle Resident Complaint")
    print("-" * 30)
    
    complaint_result = await agent.execute_action("handle_resident_complaint", {
        "context": {
            "complaint_type": "noise",
            "severity": "high",
            "resident_id": "RES-001",
            "description": "Loud music from neighbor at 2 AM"
        }
    })
    
    print(f"✅ Complaint handled: {complaint_result['completed']}")
    if complaint_result['completed']:
        output = complaint_result['output']
        print(f"   Strategy: {output['response_strategy']}")
        print(f"   Response time: {output['response_time']}")
        print(f"   Escalation: {output['resolution_plan']['escalation_role']}")
    print()
    
    # Test 2: Organize community event
    print("🎉 Test 2: Organize Community Event")
    print("-" * 30)
    
    event_result = await agent.execute_action("organize_community_event", {
        "context": {
            "event_type": "holiday",
            "budget": 1500,
            "expected_attendance": 75,
            "date": "2024-12-15"
        }
    })
    
    print(f"✅ Event organized: {event_result['completed']}")
    if event_result['completed']:
        output = event_result['output']
        print(f"   Event type: {output['event_plan']['event_type']}")
        print(f"   Budget: ${output['event_plan']['budget']}")
        print(f"   Activities: {', '.join(output['event_plan']['activities'])}")
        print(f"   Venue: {output['event_plan']['logistics']['venue']}")
    print()
    
    # Test 3: Manage amenity request
    print("🏊 Test 3: Manage Amenity Request")
    print("-" * 30)
    
    amenity_result = await agent.execute_action("manage_amenity_request", {
        "context": {
            "amenity_type": "pool",
            "request_type": "maintenance",
            "resident_feedback": [
                {"sentiment": "negative", "comment": "Pool is too cold"},
                {"sentiment": "positive", "comment": "Pool area is clean"},
                {"sentiment": "negative", "comment": "Pool hours are too limited"}
            ]
        }
    })
    
    print(f"✅ Amenity managed: {amenity_result['completed']}")
    if amenity_result['completed']:
        output = amenity_result['output']
        print(f"   Amenity: {output['management_plan']['amenity_type']}")
        print(f"   Priority: {output['management_plan']['priority']}")
        print(f"   Recommendations: {', '.join(output['management_plan']['recommendations'])}")
    print()
    
    # Test 4: Conduct satisfaction survey
    print("📊 Test 4: Conduct Satisfaction Survey")
    print("-" * 30)
    
    survey_result = await agent.execute_action("conduct_satisfaction_survey", {
        "context": {
            "survey_type": "general",
            "target_residents": "all",
            "survey_period": "quarterly"
        }
    })
    
    print(f"✅ Survey created: {survey_result['completed']}")
    if survey_result['completed']:
        output = survey_result['output']
        print(f"   Survey type: {output['distribution_plan']['target_residents']}")
        print(f"   Method: {output['distribution_plan']['method']}")
        print(f"   Questions: {len(output['survey_questions'])} questions")
        print(f"   Expected completion: {output['expected_completion']}")
    print()
    
    # Test 5: Resolve resident issue
    print("🔧 Test 5: Resolve Resident Issue")
    print("-" * 30)
    
    issue_result = await agent.execute_action("resolve_resident_issue", {
        "context": {
            "issue_type": "maintenance",
            "resident_id": "RES-002",
            "urgency": "high"
        }
    })
    
    print(f"✅ Issue resolved: {issue_result['completed']}")
    if issue_result['completed']:
        output = issue_result['output']
        print(f"   Issue type: {output['resolution_plan']['issue_type']}")
        print(f"   Approach: {output['resolution_plan']['resolution_approach']}")
        print(f"   Timeline: {output['resolution_plan']['timeline']}")
        print(f"   Escalation sent: {output['escalation_sent']}")
    print()
    
    # Test 6: Manage feedback
    print("💬 Test 6: Manage Feedback")
    print("-" * 30)
    
    feedback_result = await agent.execute_action("manage_feedback", {
        "context": {
            "feedback_type": "general",
            "feedback_data": [
                {"category": "maintenance", "sentiment": "positive", "priority": "normal"},
                {"category": "amenity", "sentiment": "negative", "priority": "high"},
                {"category": "communication", "sentiment": "neutral", "priority": "normal"},
                {"category": "maintenance", "sentiment": "negative", "priority": "critical"}
            ]
        }
    })
    
    print(f"✅ Feedback managed: {feedback_result['completed']}")
    if feedback_result['completed']:
        output = feedback_result['output']
        print(f"   Action items: {len(output['response_plan']['action_items'])}")
        print(f"   Improvement areas: {len(output['response_plan']['improvement_areas'])}")
        print(f"   Critical feedback escalated: {output['critical_feedback_escalated']}")
    print()
    
    # Test 7: Make decision
    print("🤔 Test 7: Make Decision")
    print("-" * 30)
    
    decision_result = await agent.make_decision({
        "decision_criteria": {
            "resident_satisfaction": "high_priority",
            "budget_constraints": "within_limits",
            "community_impact": "positive"
        },
        "context": {
            "decision_type": "amenity_upgrade",
            "cost": 1500,
            "resident_demand": "high"
        }
    })
    
    print(f"✅ Decision made: {decision_result['decision']}")
    print(f"   Confidence: {decision_result['confidence']}")
    print(f"   Reasoning: {decision_result['reasoning'][:100]}...")
    print()
    
    # Show all messages sent
    print("📨 Messages Sent:")
    print("-" * 30)
    for i, msg in enumerate(orchestrator.messages, 1):
        print(f"{i}. To {msg['to_role']}: {msg['subject']}")
    
    print()
    print("🎉 Resident Services Manager Agent testing completed!")
    print(f"📊 Total messages sent: {len(orchestrator.messages)}")

if __name__ == "__main__":
    asyncio.run(test_resident_services_manager()) 