#!/usr/bin/env python3
"""
Test script for Admin Assistant Agent
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Optional

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from role_agents import AdminAssistantAgent
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

async def test_admin_assistant():
    """Test the Admin Assistant Agent"""
    
    print("📋 Testing Admin Assistant Agent")
    print("=" * 50)
    
    # Create mock orchestrator
    orchestrator = MockOrchestrator()
    
    # Create the agent (ignore type checking for mock)
    agent = AdminAssistantAgent(orchestrator)  # type: ignore
    
    print(f"✅ Agent created: {agent.role}")
    print(f"💰 Approval limit: ${agent.can_approve_up_to}")
    print(f"🔑 Permissions: {', '.join(agent.permissions)}")
    print()
    
    # Test 1: Manage documents
    print("📄 Test 1: Manage Documents")
    print("-" * 30)
    
    doc_result = await agent.execute_action("manage_documents", {
        "context": {
            "document_type": "lease",
            "action_type": "file",
            "document_id": "DOC-001",
            "resident_id": "RES-001"
        }
    })
    
    print(f"✅ Document managed: {doc_result['completed']}")
    if doc_result['completed']:
        output = doc_result['output']
        print(f"   Document type: {output['document_record']['document_type']}")
        print(f"   Filing location: {output['filing_location']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 2: Schedule appointment
    print("📅 Test 2: Schedule Appointment")
    print("-" * 30)
    
    appointment_result = await agent.execute_action("schedule_appointment", {
        "context": {
            "appointment_type": "maintenance",
            "participant": "John Smith",
            "date_time": "2024-12-15 10:00",
            "duration": 60
        }
    })
    
    print(f"✅ Appointment scheduled: {appointment_result['completed']}")
    if appointment_result['completed']:
        output = appointment_result['output']
        print(f"   Appointment type: {output['appointment']['appointment_type']}")
        print(f"   Participant: {output['appointment']['participant']}")
        print(f"   Manager notified: {output['manager_notified']}")
    print()
    
    # Test 3: Perform data entry
    print("📝 Test 3: Perform Data Entry")
    print("-" * 30)
    
    data_entry_result = await agent.execute_action("perform_data_entry", {
        "context": {
            "data_type": "resident",
            "records": [
                {"resident_id": "RES-002", "name": "Jane Doe", "unit": "101"},
                {"resident_id": "RES-003", "name": "Bob Wilson", "unit": "102"}
            ],
            "update_type": "add"
        }
    })
    
    print(f"✅ Data entry completed: {data_entry_result['completed']}")
    if data_entry_result['completed']:
        output = data_entry_result['output']
        print(f"   Data type: {output['entry_summary']['data_type']}")
        print(f"   Records processed: {output['entry_summary']['records_processed']}")
        print(f"   Validation passed: {output['validation_passed']}")
    print()
    
    # Test 4: Generate report
    print("📊 Test 4: Generate Report")
    print("-" * 30)
    
    report_result = await agent.execute_action("generate_report", {
        "context": {
            "report_type": "occupancy",
            "date_range": "monthly",
            "format_type": "summary"
        }
    })
    
    print(f"✅ Report generated: {report_result['completed']}")
    if report_result['completed']:
        output = report_result['output']
        print(f"   Report type: {output['report']['report_type']}")
        print(f"   Date range: {output['report']['date_range']}")
        print(f"   Manager notified: {output['manager_notified']}")
        print(f"   Occupancy rate: {output['report']['content']['occupancy_rate']}%")
    print()
    
    # Test 5: Coordinate office
    print("🏢 Test 5: Coordinate Office")
    print("-" * 30)
    
    office_result = await agent.execute_action("coordinate_office", {
        "context": {
            "coordination_type": "supply_order",
            "details": "printer paper, pens, folders"
        }
    })
    
    print(f"✅ Office coordinated: {office_result['completed']}")
    if office_result['completed']:
        output = office_result['output']
        print(f"   Coordination type: {output['coordination_record']['coordination_type']}")
        print(f"   Action: {output['coordination_record']['action']}")
        print(f"   Items: {len(output['coordination_record']['items'])} items")
    print()
    
    # Test 6: Handle communications
    print("💬 Test 6: Handle Communications")
    print("-" * 30)
    
    comm_result = await agent.execute_action("handle_communications", {
        "context": {
            "communication_type": "maintenance",
            "message": "Need repair for broken window",
            "sender": "Resident",
            "priority": "normal"
        }
    })
    
    print(f"✅ Communication handled: {comm_result['completed']}")
    if comm_result['completed']:
        output = comm_result['output']
        print(f"   Communication type: {output['communication_record']['communication_type']}")
        print(f"   Priority: {output['communication_record']['priority']}")
        print(f"   Routed: {output['routed']}")
    print()
    
    # Test 7: Manage sensitive document
    print("🔒 Test 7: Manage Sensitive Document")
    print("-" * 30)
    
    sensitive_doc_result = await agent.execute_action("manage_documents", {
        "context": {
            "document_type": "legal",
            "action_type": "file",
            "document_id": "DOC-002",
            "resident_id": "RES-004"
        }
    })
    
    print(f"✅ Sensitive document managed: {sensitive_doc_result['completed']}")
    if sensitive_doc_result['completed']:
        output = sensitive_doc_result['output']
        print(f"   Document type: {output['document_record']['document_type']}")
        print(f"   Filing location: {output['filing_location']}")
        print(f"   Escalated: {output['escalated']}")
    print()
    
    # Test 8: Generate financial report
    print("💰 Test 8: Generate Financial Report")
    print("-" * 30)
    
    financial_report_result = await agent.execute_action("generate_report", {
        "context": {
            "report_type": "financial",
            "date_range": "quarterly",
            "format_type": "detailed"
        }
    })
    
    print(f"✅ Financial report generated: {financial_report_result['completed']}")
    if financial_report_result['completed']:
        output = financial_report_result['output']
        print(f"   Report type: {output['report']['report_type']}")
        print(f"   Date range: {output['report']['date_range']}")
        print(f"   Manager notified: {output['manager_notified']}")
        print(f"   Net income: ${output['report']['content']['net_income']}")
    print()
    
    # Test 9: Office maintenance request
    print("🔧 Test 9: Office Maintenance Request")
    print("-" * 30)
    
    office_maint_result = await agent.execute_action("coordinate_office", {
        "context": {
            "coordination_type": "maintenance_request",
            "details": "Office HVAC system not working properly"
        }
    })
    
    print(f"✅ Office maintenance coordinated: {office_maint_result['completed']}")
    if office_maint_result['completed']:
        output = office_maint_result['output']
        print(f"   Coordination type: {output['coordination_record']['coordination_type']}")
        print(f"   Action: {output['coordination_record']['action']}")
    print()
    
    # Test 10: Handle urgent communication
    print("🚨 Test 10: Handle Urgent Communication")
    print("-" * 30)
    
    urgent_comm_result = await agent.execute_action("handle_communications", {
        "context": {
            "communication_type": "general",
            "message": "Fire alarm going off in building",
            "sender": "Security",
            "priority": "urgent"
        }
    })
    
    print(f"✅ Urgent communication handled: {urgent_comm_result['completed']}")
    if urgent_comm_result['completed']:
        output = urgent_comm_result['output']
        print(f"   Communication type: {output['communication_record']['communication_type']}")
        print(f"   Priority: {output['communication_record']['priority']}")
        print(f"   Routed: {output['routed']}")
    print()
    
    # Show all messages sent
    print("📨 Messages Sent:")
    print("-" * 30)
    for i, msg in enumerate(orchestrator.messages, 1):
        print(f"{i}. To {msg['to_role']}: {msg['subject']}")
    
    print()
    print("🎉 Admin Assistant Agent testing completed!")
    print(f"📊 Total messages sent: {len(orchestrator.messages)}")

if __name__ == "__main__":
    asyncio.run(test_admin_assistant()) 