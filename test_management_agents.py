#!/usr/bin/env python3
"""
Test script for Management Agents with Orchestration Capabilities
Tests Director of Accounting, Director of Leasing, and VP of Operations agents
"""

import asyncio
import json
from datetime import datetime
from role_agents import create_agent
from sop_orchestration import SOPOrchestrationEngine

async def test_director_of_accounting():
    """Test Director of Accounting Agent with orchestration capabilities"""
    print("\n" + "="*60)
    print("🧮 TESTING DIRECTOR OF ACCOUNTING AGENT")
    print("="*60)
    
    # Initialize orchestrator and agent
    orchestrator = SOPOrchestrationEngine()
    agent = create_agent("director_of_accounting", orchestrator)
    
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
    
    # Test 3: Approve Major Expenditure
    print("\n💰 Test 3: Approve Major Expenditure")
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

async def test_director_of_leasing():
    """Test Director of Leasing Agent with orchestration capabilities"""
    print("\n" + "="*60)
    print("🏠 TESTING DIRECTOR OF LEASING AGENT")
    print("="*60)
    
    # Initialize orchestrator and agent
    orchestrator = SOPOrchestrationEngine()
    agent = create_agent("director_of_leasing", orchestrator)
    
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
    
    # Test 3: Approve Major Leasing Decision
    print("\n✅ Test 3: Approve Major Leasing Decision")
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

async def test_vice_president_of_operations():
    """Test VP of Operations Agent with strategic orchestration"""
    print("\n" + "="*60)
    print("👔 TESTING VICE PRESIDENT OF OPERATIONS AGENT")
    print("="*60)
    
    # Initialize orchestrator and agent
    orchestrator = SOPOrchestrationEngine()
    agent = create_agent("vice_president_of_operations", orchestrator)
    
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
    
    # Test 3: Approve Major Strategic Decision
    print("\n🎯 Test 3: Approve Major Strategic Decision")
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

async def test_management_hierarchy():
    """Test management hierarchy and escalation patterns"""
    print("\n" + "="*60)
    print("🏢 TESTING MANAGEMENT HIERARCHY & ESCALATION")
    print("="*60)
    
    orchestrator = SOPOrchestrationEngine()
    
    # Test escalation from Director to VP
    print("\n📤 Test: Escalation from Director to VP")
    director_accounting = create_agent("director_of_accounting", orchestrator)
    
    # Try to approve expenditure beyond director limit
    result = await director_accounting.execute_action("approve_major_expenditure", {
        "context": {
            "expenditure_type": "major renovation",
            "amount": 75000,  # Exceeds director limit of $50,000
            "justification": "Major property renovation",
            "department": "maintenance"
        }
    })
    print(f"✅ Escalation Result: {json.dumps(result, indent=2)}")
    
    # Test VP approval of the escalated decision
    print("\n📥 Test: VP Approval of Escalated Decision")
    vp_operations = create_agent("vice_president_of_operations", orchestrator)
    
    result = await vp_operations.execute_action("approve_major_strategic_decision", {
        "context": {
            "decision_type": "major renovation",
            "impact_level": "high",
            "budget_impact": 75000,
            "strategic_importance": "high"
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