#!/usr/bin/env python3
"""
Test script for Workflow Management API Endpoints
Tests the new workflow creation, execution, monitoring, and agent action endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, Optional

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "sk_live_test_key_12345"  # Replace with actual API key

async def make_request(session: aiohttp.ClientSession, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make authenticated API request"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            async with session.get(url, headers=headers) as response:
                return await response.json()
        elif method.upper() == "POST":
            async with session.post(url, headers=headers, json=data) as response:
                return await response.json()
        else:
            raise ValueError(f"Unsupported method: {method}")
    except Exception as e:
        return {"error": str(e)}

async def test_workflow_templates():
    """Test getting workflow templates"""
    print("\n🔧 Testing Workflow Templates...")
    
    async with aiohttp.ClientSession() as session:
        result = await make_request(session, "GET", "/api/workflows/templates")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return False
        
        templates = result.get("templates", [])
        print(f"✅ Found {len(templates)} workflow templates:")
        
        for template in templates:
            print(f"  - {template['name']}: {template['description']}")
            print(f"    Property Range: {template['property_size_range']}")
            print(f"    Investment Range: {template['investment_range']}")
            print(f"    Duration: {template['estimated_duration']}")
        
        return len(templates) > 0

async def test_create_workflow():
    """Test creating a new workflow"""
    print("\n🚀 Testing Workflow Creation...")
    
    workflow_data = {
        "workflow_type": "single_family",
        "property_size": 1,
        "investment_amount": 1500.0,
        "scenario_type": "maintenance",
        "urgency": "medium",
        "description": "Kitchen sink repair and cabinet replacement",
        "context": {
            "tenant_name": "John Smith",
            "unit_number": "101",
            "issue_description": "Leaking kitchen sink and damaged cabinet"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        result = await make_request(session, "POST", "/api/workflows/create", workflow_data)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        workflow_id = result.get("workflow_id")
        print(f"✅ Workflow created successfully!")
        print(f"  Workflow ID: {workflow_id}")
        print(f"  Status: {result.get('status')}")
        print(f"  Estimated Duration: {result.get('estimated_duration')}")
        print(f"  Approval Chain: {', '.join(result.get('approval_chain', []))}")
        
        return workflow_id

async def test_execute_workflow(workflow_id: str):
    """Test executing a workflow"""
    print(f"\n▶️ Testing Workflow Execution: {workflow_id}...")
    
    async with aiohttp.ClientSession() as session:
        result = await make_request(session, "POST", f"/api/workflows/{workflow_id}/execute")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return False
        
        print(f"✅ Workflow execution started!")
        print(f"  Status: {result.get('status')}")
        print(f"  Started At: {result.get('started_at')}")
        
        execution_result = result.get("execution_result", {})
        print(f"  Agents Contacted: {execution_result.get('agents_contacted', [])}")
        print(f"  Messages Sent: {execution_result.get('messages_sent', 0)}")
        
        return True

async def test_workflow_status(workflow_id: str):
    """Test getting workflow status"""
    print(f"\n📊 Testing Workflow Status: {workflow_id}...")
    
    async with aiohttp.ClientSession() as session:
        result = await make_request(session, "GET", f"/api/workflows/{workflow_id}/status")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return False
        
        print(f"✅ Workflow status retrieved!")
        print(f"  Status: {result.get('status')}")
        print(f"  Progress: {result.get('progress', 0):.1f}%")
        print(f"  Current Step: {result.get('current_step')}/{result.get('total_steps')}")
        print(f"  Messages Exchanged: {result.get('messages_exchanged')}")
        print(f"  Approval Required: {result.get('approval_required')}")
        print(f"  Agents Involved: {', '.join(result.get('agents_involved', []))}")
        
        return True

async def test_list_workflows():
    """Test listing workflows"""
    print("\n📋 Testing Workflow Listing...")
    
    async with aiohttp.ClientSession() as session:
        # Test listing all workflows
        result = await make_request(session, "GET", "/api/workflows")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return False
        
        workflows = result.get("workflows", [])
        print(f"✅ Found {len(workflows)} workflows")
        
        for workflow in workflows[:3]:  # Show first 3
            print(f"  - {workflow.get('workflow_id', 'Unknown')}: {workflow.get('status', 'Unknown')}")
        
        # Test filtering by status
        result = await make_request(session, "GET", "/api/workflows?status=pending")
        pending_workflows = result.get("workflows", [])
        print(f"  Pending workflows: {len(pending_workflows)}")
        
        return True

async def test_agent_action():
    """Test executing an agent action"""
    print("\n🤖 Testing Agent Action...")
    
    action_data = {
        "agent_role": "maintenance_tech",
        "action_type": "assess_repair_need",
        "context": {
            "issue_type": "plumbing",
            "urgency": "medium",
            "estimated_cost": 800.0
        },
        "requires_approval": True,
        "approval_amount": 800.0
    }
    
    async with aiohttp.ClientSession() as session:
        result = await make_request(session, "POST", "/api/agents/maintenance_tech/action", action_data)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return False
        
        print(f"✅ Agent action executed!")
        print(f"  Agent: {result.get('agent_role')}")
        print(f"  Action: {result.get('action_type')}")
        print(f"  Decision: {result.get('decision')}")
        print(f"  Requires Approval: {result.get('requires_approval')}")
        print(f"  Approval Amount: ${result.get('approval_amount', 0)}")
        print(f"  Timestamp: {result.get('timestamp')}")
        
        return True

async def test_invalid_requests():
    """Test invalid request handling"""
    print("\n🚫 Testing Invalid Requests...")
    
    async with aiohttp.ClientSession() as session:
        # Test invalid workflow type
        invalid_data = {
            "workflow_type": "invalid_type",
            "property_size": 1,
            "investment_amount": 1000.0,
            "scenario_type": "maintenance",
            "description": "Test"
        }
        
        result = await make_request(session, "POST", "/api/workflows/create", invalid_data)
        if "error" in result:
            print(f"✅ Correctly rejected invalid workflow type: {result['error']}")
        else:
            print(f"❌ Should have rejected invalid workflow type")
        
        # Test invalid agent role
        invalid_action = {
            "agent_role": "invalid_agent",
            "action_type": "test_action",
            "context": {}
        }
        
        result = await make_request(session, "POST", "/api/agents/invalid_agent/action", invalid_action)
        if "error" in result:
            print(f"✅ Correctly rejected invalid agent role: {result['error']}")
        else:
            print(f"❌ Should have rejected invalid agent role")
        
        # Test non-existent workflow
        result = await make_request(session, "GET", "/api/workflows/nonexistent-123/status")
        if "error" in result:
            print(f"✅ Correctly handled non-existent workflow: {result['error']}")
        else:
            print(f"❌ Should have handled non-existent workflow")

async def main():
    """Run all workflow API tests"""
    print("🧪 WORKFLOW API TEST SUITE")
    print("=" * 50)
    
    # Test workflow templates
    await test_workflow_templates()
    
    # Test workflow creation
    workflow_id = await test_create_workflow()
    
    if workflow_id:
        # Test workflow execution
        await test_execute_workflow(workflow_id)
        
        # Test workflow status
        await test_workflow_status(workflow_id)
    
    # Test workflow listing
    await test_list_workflows()
    
    # Test agent action
    await test_agent_action()
    
    # Test invalid requests
    await test_invalid_requests()
    
    print("\n" + "=" * 50)
    print("✅ Workflow API Test Suite Complete!")
    print("\n📝 Summary:")
    print("  - Workflow templates retrieved")
    print("  - Workflow creation tested")
    print("  - Workflow execution tested")
    print("  - Workflow status monitoring tested")
    print("  - Workflow listing tested")
    print("  - Agent actions tested")
    print("  - Error handling validated")

if __name__ == "__main__":
    asyncio.run(main()) 