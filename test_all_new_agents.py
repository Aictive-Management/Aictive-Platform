#!/usr/bin/env python3
"""
Test script for all newly implemented agents:
- Maintenance Tech Lead Agent
- Maintenance Tech Agent  
- Senior Leasing Agent Agent
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Optional

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from role_agents import (
    MaintenanceTechLeadAgent, 
    MaintenanceTechAgent, 
    SeniorLeasingAgentAgent
)
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

async def test_maintenance_tech_lead():
    """Test the Maintenance Tech Lead Agent"""
    
    print("🔧 Testing Maintenance Tech Lead Agent")
    print("=" * 50)
    
    orchestrator = MockOrchestrator()
    agent = MaintenanceTechLeadAgent(orchestrator)  # type: ignore
    
    print(f"✅ Agent created: {agent.role}")
    print(f"💰 Approval limit: ${agent.can_approve_up_to}")
    print(f"🔑 Permissions: {', '.join(agent.permissions)}")
    print()
    
    # Test 1: Create work order
    print("📋 Test 1: Create Work Order")
    print("-" * 30)
    
    work_order_result = await agent.execute_action("create_work_order", {
        "context": {
            "unit_id": "UNIT-101",
            "issue_type": "plumbing",
            "description": "Leaking faucet in kitchen",
            "priority": "normal",
            "estimated_hours": 3
        }
    })
    
    print(f"✅ Work order created: {work_order_result['completed']}")
    if work_order_result['completed']:
        output = work_order_result['output']
        print(f"   Work order ID: {output['work_order']['work_order_id']}")
        print(f"   Required skills: {len(output['work_order']['required_skills'])} skills")
        print(f"   Safety requirements: {len(output['work_order']['safety_requirements'])} requirements")
    print()
    
    # Test 2: Update work status
    print("📊 Test 2: Update Work Status")
    print("-" * 30)
    
    status_result = await agent.execute_action("update_work_status", {
        "context": {
            "work_order_id": "WO-20241215120000",
            "status": "completed",
            "progress_notes": "Faucet replaced successfully",
            "hours_worked": 2.5,
            "technician_id": "TECH-001"
        }
    })
    
    print(f"✅ Status updated: {status_result['completed']}")
    if status_result['completed']:
        output = status_result['output']
        print(f"   Status: {output['status_update']['status']}")
        print(f"   Hours worked: {output['status_update']['hours_worked']}")
        print(f"   Supervisor notified: {output['supervisor_notified']}")
    print()
    
    # Test 3: Request parts
    print("🔧 Test 3: Request Parts")
    print("-" * 30)
    
    parts_result = await agent.execute_action("request_parts", {
        "context": {
            "part_name": "Kitchen faucet assembly",
            "quantity": 1,
            "urgency": "normal",
            "work_order_id": "WO-20241215120000",
            "estimated_cost": 150
        }
    })
    
    print(f"✅ Parts requested: {parts_result['completed']}")
    if parts_result['completed']:
        output = parts_result['output']
        print(f"   Part: {output['parts_request']['part_name']}")
        print(f"   Cost: ${output['parts_request']['estimated_cost']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 4: Train junior tech
    print("👨‍🏫 Test 4: Train Junior Tech")
    print("-" * 30)
    
    training_result = await agent.execute_action("train_junior_tech", {
        "context": {
            "technician_id": "TECH-002",
            "skill_topic": "electrical",
            "training_duration": 90,
            "training_type": "hands_on"
        }
    })
    
    print(f"✅ Training scheduled: {training_result['completed']}")
    if training_result['completed']:
        output = training_result['output']
        print(f"   Skill topic: {output['training_session']['skill_topic']}")
        print(f"   Duration: {output['training_session']['training_duration']} minutes")
        print(f"   Materials created: {output['materials_created']}")
    print()
    
    # Test 5: Quality check
    print("✅ Test 5: Quality Check")
    print("-" * 30)
    
    quality_result = await agent.execute_action("conduct_quality_check", {
        "context": {
            "work_order_id": "WO-20241215120000",
            "technician_id": "TECH-001",
            "quality_score": 9.2,
            "issues_found": []
        }
    })
    
    print(f"✅ Quality check completed: {quality_result['completed']}")
    if quality_result['completed']:
        output = quality_result['output']
        print(f"   Quality score: {output['quality_report']['quality_score']}")
        print(f"   Passed: {output['quality_report']['passed']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    return orchestrator.messages

async def test_maintenance_tech():
    """Test the Maintenance Tech Agent"""
    
    print("🔧 Testing Maintenance Tech Agent")
    print("=" * 50)
    
    orchestrator = MockOrchestrator()
    agent = MaintenanceTechAgent(orchestrator)  # type: ignore
    
    print(f"✅ Agent created: {agent.role}")
    print(f"💰 Approval limit: ${agent.can_approve_up_to}")
    print(f"🔑 Permissions: {', '.join(agent.permissions)}")
    print()
    
    # Test 1: Accept work order
    print("📋 Test 1: Accept Work Order")
    print("-" * 30)
    
    accept_result = await agent.execute_action("accept_work_order", {
        "context": {
            "work_order_id": "WO-20241215120000",
            "technician_id": "TECH-001",
            "estimated_duration": 2
        }
    })
    
    print(f"✅ Work order accepted: {accept_result['completed']}")
    if accept_result['completed']:
        output = accept_result['output']
        print(f"   Work order ID: {output['work_acceptance']['work_order_id']}")
        print(f"   Status: {output['work_acceptance']['status']}")
        print(f"   Lead notified: {output['lead_notified']}")
    print()
    
    # Test 2: Update progress
    print("📊 Test 2: Update Progress")
    print("-" * 30)
    
    progress_result = await agent.execute_action("update_progress", {
        "context": {
            "work_order_id": "WO-20241215120000",
            "progress_percentage": 75,
            "notes": "Faucet removed, installing new one",
            "hours_worked": 1.5
        }
    })
    
    print(f"✅ Progress updated: {progress_result['completed']}")
    if progress_result['completed']:
        output = progress_result['output']
        print(f"   Progress: {output['progress_update']['progress_percentage']}%")
        print(f"   Hours worked: {output['progress_update']['hours_worked']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 3: Request parts approval
    print("🔧 Test 3: Request Parts Approval")
    print("-" * 30)
    
    parts_result = await agent.execute_action("request_parts_approval", {
        "context": {
            "part_name": "Faucet cartridge",
            "quantity": 1,
            "estimated_cost": 25,
            "work_order_id": "WO-20241215120000",
            "urgency": "normal"
        }
    })
    
    print(f"✅ Parts request submitted: {parts_result['completed']}")
    if parts_result['completed']:
        output = parts_result['output']
        print(f"   Part: {output['parts_request']['part_name']}")
        print(f"   Cost: ${output['parts_request']['estimated_cost']}")
        print(f"   Approval requested: {output['approval_requested']}")
    print()
    
    # Test 4: Complete repair
    print("✅ Test 4: Complete Repair")
    print("-" * 30)
    
    complete_result = await agent.execute_action("complete_repair", {
        "context": {
            "work_order_id": "WO-20241215120000",
            "completion_notes": "New faucet installed and tested, no leaks",
            "hours_worked": 2.5,
            "parts_used": ["Kitchen faucet assembly", "Plumber's tape"]
        }
    })
    
    print(f"✅ Repair completed: {complete_result['completed']}")
    if complete_result['completed']:
        output = complete_result['output']
        print(f"   Hours worked: {output['completion_report']['hours_worked']}")
        print(f"   Parts used: {len(output['completion_report']['parts_used'])}")
        print(f"   Quality check requested: {output['quality_check_requested']}")
    print()
    
    # Test 5: Report safety issue
    print("⚠️ Test 5: Report Safety Issue")
    print("-" * 30)
    
    safety_result = await agent.execute_action("report_safety_issue", {
        "context": {
            "issue_type": "electrical",
            "description": "Exposed wiring in utility closet",
            "location": "Building A - Utility Closet",
            "severity": "medium"
        }
    })
    
    print(f"✅ Safety issue reported: {safety_result['completed']}")
    if safety_result['completed']:
        output = safety_result['output']
        print(f"   Issue type: {output['safety_report']['issue_type']}")
        print(f"   Severity: {output['safety_report']['severity']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    return orchestrator.messages

async def test_senior_leasing_agent():
    """Test the Senior Leasing Agent Agent"""
    
    print("🏠 Testing Senior Leasing Agent Agent")
    print("=" * 50)
    
    orchestrator = MockOrchestrator()
    agent = SeniorLeasingAgentAgent(orchestrator)  # type: ignore
    
    print(f"✅ Agent created: {agent.role}")
    print(f"💰 Approval limit: ${agent.can_approve_up_to}")
    print(f"🔑 Permissions: {', '.join(agent.permissions)}")
    print()
    
    # Test 1: Process application
    print("📝 Test 1: Process Application")
    print("-" * 30)
    
    app_result = await agent.execute_action("process_application", {
        "context": {
            "applicant_id": "APP-001",
            "application_data": {
                "credit_score": 720,
                "income_ratio": 3.2,
                "rental_history": "good"
            },
            "unit_preference": "2BR-2BA"
        }
    })
    
    print(f"✅ Application processed: {app_result['completed']}")
    if app_result['completed']:
        output = app_result['output']
        print(f"   Credit score: {output['application_analysis']['credit_score']}")
        print(f"   Income ratio: {output['application_analysis']['income_ratio']}")
        print(f"   Recommendation: {output['application_analysis']['recommendation']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 2: Conduct advanced tour
    print("🏠 Test 2: Conduct Advanced Tour")
    print("-" * 30)
    
    tour_result = await agent.execute_action("conduct_advanced_tour", {
        "context": {
            "prospect_name": "John Smith",
            "unit_id": "UNIT-201",
            "tour_type": "premium",
            "special_requirements": ["pet_friendly", "parking"]
        }
    })
    
    print(f"✅ Advanced tour conducted: {tour_result['completed']}")
    if tour_result['completed']:
        output = tour_result['output']
        print(f"   Tour type: {output['tour_details']['tour_type']}")
        print(f"   Duration: {output['tour_details']['duration']} minutes")
        print(f"   Materials provided: {len(output['tour_details']['materials_provided'])}")
        print(f"   Follow-up created: {output['follow_up_created']}")
    print()
    
    # Test 3: Preliminary approval
    print("✅ Test 3: Preliminary Approval")
    print("-" * 30)
    
    approval_result = await agent.execute_action("preliminary_approval", {
        "context": {
            "applicant_id": "APP-001",
            "application_id": "APP-20241215-001",
            "approval_conditions": ["Security deposit required", "Pet deposit required"]
        }
    })
    
    print(f"✅ Preliminary approval granted: {approval_result['completed']}")
    if approval_result['completed']:
        output = approval_result['output']
        print(f"   Approval type: {output['preliminary_approval']['approval_type']}")
        print(f"   Requires manager final: {output['preliminary_approval']['requires_manager_final']}")
        print(f"   Manager notified: {output['manager_notified']}")
    print()
    
    # Test 4: Approve small concession
    print("💰 Test 4: Approve Small Concession")
    print("-" * 30)
    
    concession_result = await agent.execute_action("approve_small_concession", {
        "context": {
            "concession_type": "application_fee_waiver",
            "amount": 150,
            "applicant_id": "APP-001",
            "justification": "Excellent credit score and rental history"
        }
    })
    
    print(f"✅ Concession approved: {concession_result['completed']}")
    if concession_result['completed']:
        output = concession_result['output']
        print(f"   Concession type: {output['concession_approval']['concession_type']}")
        print(f"   Amount: ${output['concession_approval']['amount']}")
        print(f"   Status: {output['concession_approval']['status']}")
    print()
    
    # Test 5: Mentor junior agent
    print("👨‍🏫 Test 5: Mentor Junior Agent")
    print("-" * 30)
    
    mentor_result = await agent.execute_action("mentor_junior_agent", {
        "context": {
            "junior_agent_id": "AGENT-002",
            "mentoring_topic": "application_processing",
            "session_duration": 90
        }
    })
    
    print(f"✅ Mentoring scheduled: {mentor_result['completed']}")
    if mentor_result['completed']:
        output = mentor_result['output']
        print(f"   Mentoring topic: {output['mentoring_session']['mentoring_topic']}")
        print(f"   Duration: {output['mentoring_session']['session_duration']} minutes")
        print(f"   Materials: {len(output['mentoring_session']['materials'])}")
    print()
    
    # Test 6: Conduct market analysis
    print("📊 Test 6: Conduct Market Analysis")
    print("-" * 30)
    
    market_result = await agent.execute_action("conduct_market_analysis", {
        "context": {
            "market_area": "downtown",
            "analysis_type": "pricing",
            "time_period": "monthly"
        }
    })
    
    print(f"✅ Market analysis completed: {market_result['completed']}")
    if market_result['completed']:
        output = market_result['output']
        print(f"   Market area: {output['market_analysis']['market_area']}")
        print(f"   Analysis type: {output['market_analysis']['analysis_type']}")
        print(f"   Average rent: ${output['market_analysis']['findings']['average_rent']}")
        print(f"   Manager notified: {output['manager_notified']}")
    print()
    
    return orchestrator.messages

async def main():
    """Run all tests"""
    
    print("🚀 Testing All New Agents")
    print("=" * 60)
    print()
    
    # Test Maintenance Tech Lead
    tech_lead_messages = await test_maintenance_tech_lead()
    print()
    
    # Test Maintenance Tech
    tech_messages = await test_maintenance_tech()
    print()
    
    # Test Senior Leasing Agent
    senior_leasing_messages = await test_senior_leasing_agent()
    print()
    
    # Summary
    total_messages = len(tech_lead_messages) + len(tech_messages) + len(senior_leasing_messages)
    
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Maintenance Tech Lead: {len(tech_lead_messages)} messages sent")
    print(f"✅ Maintenance Tech: {len(tech_messages)} messages sent")
    print(f"✅ Senior Leasing Agent: {len(senior_leasing_messages)} messages sent")
    print(f"📨 Total messages sent: {total_messages}")
    print()
    print("🎉 All new agents tested successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 