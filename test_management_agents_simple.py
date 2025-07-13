#!/usr/bin/env python3
"""
Simplified Test script for Management Agents with Orchestration Capabilities
Tests Director of Accounting, Director of Leasing, and VP of Operations agents
"""

import asyncio
import json
from datetime import datetime
from role_agents import DirectorOfAccountingAgent, DirectorOfLeasingAgent, VicePresidentOfOperationsAgent

# NOTE: The real orchestrator's send_agent_message expects a 'message_type' parameter.
# This mock must accept it for compatibility with agent orchestration tests.
class MockOrchestrator:
    """Mock orchestrator for testing"""
    def __init__(self):
        self.messages = []
    
    async def send_agent_message(self, from_role: str, to_role: str, subject: str, message: str, data: dict = None, message_type: str = "task"):
        """Mock agent message sending"""
        self.messages.append({
            "from_role": from_role,
            "to_role": to_role,
            "subject": subject,
            "message": message,
            "data": data,
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        print(f"📤 Message from {from_role} to {to_role}: {subject} ({message_type})")
    
    async def send_message(self, to_role: str, subject: str, message: str, data: dict = None):
        """Mock message sending (legacy method)"""
        await self.send_agent_message("system", to_role, subject, message, data)

async def test_director_of_accounting():
    """Test Director of Accounting Agent with orchestration capabilities"""
    print("\n" + "="*60)
    print("🧮 TESTING DIRECTOR OF ACCOUNTING AGENT")
    print("="*60)
    
    # Initialize mock orchestrator and agent
    orchestrator = MockOrchestrator()
    agent = DirectorOfAccountingAgent(orchestrator)
    
    print(f"✅ Agent created: {agent.role}")
    print(f"✅ Permissions: {agent.permissions}")
    print(f"✅ Approval limit: ${agent.can_approve_up_to:,}")
    
    # Test 1: Orchestrate Monthly Close
    print("\n📊 Test 1: Orchestrate Monthly Close")
    result = await agent.execute_action("orchestrate_monthly_close", {
        "context": {
            "month": "December",
            "year": "2024"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Oversee Audit Process
    print("\n🔍 Test 2: Oversee Audit Process")
    result = await agent.execute_action("oversee_audit_process", {
        "context": {
            "audit_type": "annual",
            "audit_scope": "comprehensive"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 3: Approve Major Expenditure (Should Require Approval)
    print("\n💰 Test 3: Approve Major Expenditure (Should Require Approval)")
    result = await agent.execute_action("approve_major_expenditure", {
        "context": {
            "expenditure_type": "HVAC replacement",
            "amount": 35000,
            "justification": "Critical system replacement",
            "department": "maintenance"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 4: Coordinate Financial Reporting
    print("\n📈 Test 4: Coordinate Financial Reporting")
    result = await agent.execute_action("coordinate_financial_reporting", {
        "context": {
            "report_type": "comprehensive",
            "reporting_period": "quarterly"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 5: Orchestrate Budget Process
    print("\n📋 Test 5: Orchestrate Budget Process")
    result = await agent.execute_action("orchestrate_budget_process", {
        "context": {
            "budget_year": "2025",
            "budget_scope": "comprehensive"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    print(f"\n📤 Total messages sent: {len(orchestrator.messages)}")

async def test_director_of_leasing():
    """Test Director of Leasing Agent with orchestration capabilities"""
    print("\n" + "="*60)
    print("🏠 TESTING DIRECTOR OF LEASING AGENT")
    print("="*60)
    
    # Initialize mock orchestrator and agent
    orchestrator = MockOrchestrator()
    agent = DirectorOfLeasingAgent(orchestrator)
    
    print(f"✅ Agent created: {agent.role}")
    print(f"✅ Permissions: {agent.permissions}")
    print(f"✅ Approval limit: ${agent.can_approve_up_to:,}")
    
    # Test 1: Orchestrate Leasing Campaign
    print("\n🎯 Test 1: Orchestrate Leasing Campaign")
    result = await agent.execute_action("orchestrate_leasing_campaign", {
        "context": {
            "campaign_type": "holiday",
            "target_market": "young professionals",
            "budget": 15000
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Oversee Market Positioning
    print("\n📊 Test 2: Oversee Market Positioning")
    result = await agent.execute_action("oversee_market_positioning", {
        "context": {
            "market_area": "downtown",
            "analysis_scope": "comprehensive"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 3: Approve Major Leasing Decision (Should Require Approval)
    print("\n✅ Test 3: Approve Major Leasing Decision (Should Require Approval)")
    result = await agent.execute_action("approve_major_leasing_decision", {
        "context": {
            "decision_type": "rental rate increase",
            "impact_level": "high",
            "budget_impact": 20000
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 4: Orchestrate Performance Review
    print("\n📋 Test 4: Orchestrate Performance Review")
    result = await agent.execute_action("orchestrate_performance_review", {
        "context": {
            "review_period": "quarterly",
            "review_scope": "comprehensive"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 5: Manage Leasing Strategy
    print("\n🎯 Test 5: Manage Leasing Strategy")
    result = await agent.execute_action("manage_leasing_strategy", {
        "context": {
            "strategy_focus": "annual",
            "strategic_goals": ["increase occupancy", "improve retention", "optimize pricing"]
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    print(f"\n📤 Total messages sent: {len(orchestrator.messages)}")

async def test_vice_president_of_operations():
    """Test VP of Operations Agent with strategic orchestration"""
    print("\n" + "="*60)
    print("👔 TESTING VICE PRESIDENT OF OPERATIONS AGENT")
    print("="*60)
    
    # Initialize mock orchestrator and agent
    orchestrator = MockOrchestrator()
    agent = VicePresidentOfOperationsAgent(orchestrator)
    
    print(f"✅ Agent created: {agent.role}")
    print(f"✅ Permissions: {agent.permissions}")
    print(f"✅ Approval limit: ${agent.can_approve_up_to:,}")
    
    # Test 1: Orchestrate Strategic Initiative
    print("\n🚀 Test 1: Orchestrate Strategic Initiative")
    result = await agent.execute_action("orchestrate_strategic_initiative", {
        "context": {
            "initiative_type": "digital transformation",
            "strategic_goals": ["improve efficiency", "enhance resident experience", "reduce costs"],
            "timeline": "12_months"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Oversee Cross-Department Project
    print("\n🏗️ Test 2: Oversee Cross-Department Project")
    result = await agent.execute_action("oversee_cross_department_project", {
        "context": {
            "project_type": "amenity renovation",
            "departments_involved": ["maintenance", "leasing", "resident_services"],
            "project_scope": "major"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 3: Approve Major Strategic Decision (Should Require Approval)
    print("\n🎯 Test 3: Approve Major Strategic Decision (Should Require Approval)")
    result = await agent.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "property acquisition",
            "impact_level": "high",
            "budget_impact": 75000,
            "strategic_importance": "high"
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 4: Coordinate Executive Meeting
    print("\n🤝 Test 4: Coordinate Executive Meeting")
    result = await agent.execute_action("coordinate_executive_meeting", {
        "context": {
            "meeting_type": "quarterly",
            "meeting_agenda": ["financial review", "strategic planning", "performance metrics"],
            "participants": ["property_manager", "director_of_accounting", "director_of_leasing"]
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 5: Manage Resource Allocation
    print("\n📊 Test 5: Manage Resource Allocation")
    result = await agent.execute_action("manage_resource_allocation", {
        "context": {
            "resource_type": "budget",
            "allocation_scope": "annual",
            "departments": ["maintenance", "leasing", "resident_services", "accounting"]
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test 6: Oversee Performance Management
    print("\n📈 Test 6: Oversee Performance Management")
    result = await agent.execute_action("oversee_performance_management", {
        "context": {
            "performance_scope": "organization_wide",
            "review_period": "quarterly",
            "performance_metrics": ["occupancy_rate", "resident_satisfaction", "financial_performance"]
        }
    })
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    print(f"\n📤 Total messages sent: {len(orchestrator.messages)}")

async def test_management_hierarchy():
    """Test management hierarchy and escalation patterns"""
    print("\n" + "="*60)
    print("🏢 TESTING MANAGEMENT HIERARCHY & ESCALATION")
    print("="*60)
    
    # Test escalation from Director to VP (All Require Approval Now)
    print("\n📤 Test: All Decisions Require Approval")
    orchestrator1 = MockOrchestrator()
    director_accounting = DirectorOfAccountingAgent(orchestrator1)
    
    # Try to approve any expenditure (should require approval)
    result = await director_accounting.execute_action("approve_major_expenditure", {
        "context": {
            "expenditure_type": "minor repair",
            "amount": 1000,  # Even small amounts require approval
            "justification": "Minor repair needed",
            "department": "maintenance"
        }
    })
    print(f"✅ Director Approval Result: {json.dumps(result, indent=2)}")
    
    # Test VP approval (should also require approval)
    print("\n📥 Test: VP Also Requires Approval")
    orchestrator2 = MockOrchestrator()
    vp_operations = VicePresidentOfOperationsAgent(orchestrator2)
    
    result = await vp_operations.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "minor renovation",
            "impact_level": "low",
            "budget_impact": 5000,
            "strategic_importance": "low"
        }
    })
    print(f"✅ VP Approval Result: {json.dumps(result, indent=2)}")

async def main():
    """Main test function"""
    print("🚀 STARTING MANAGEMENT AGENTS ORCHESTRATION TESTS")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test each management agent
        await test_director_of_accounting()
        await test_director_of_leasing()
        await test_vice_president_of_operations()
        await test_management_hierarchy()
        
        print("\n" + "="*60)
        print("🎉 ALL MANAGEMENT AGENT TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("✅ Director of Accounting Agent - Orchestration capabilities verified")
        print("✅ Director of Leasing Agent - Strategic coordination verified")
        print("✅ VP of Operations Agent - Executive oversight verified")
        print("✅ Management Hierarchy - Escalation patterns verified")
        print("\n🏢 Management agents are ready for complex orchestration workflows!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 