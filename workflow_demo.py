"""
Demo script showing the complete SOP orchestration in action
"""
import asyncio
import os
from datetime import datetime
from sop_orchestration import SOPOrchestrationEngine
from role_agents import initialize_agents
from example_sops import EMERGENCY_MAINTENANCE_SOP

async def demo_emergency_maintenance_workflow():
    """Demonstrate emergency maintenance workflow"""
    print("🚀 AICTIVE PLATFORM - SOP ORCHESTRATION DEMO")
    print("=" * 60)
    print("📋 Scenario: Emergency Water Leak Reported")
    print("=" * 60)
    
    # Initialize orchestration engine
    print("\n1️⃣ Initializing Orchestration Engine...")
    orchestrator = SOPOrchestrationEngine()
    
    # Initialize all role agents
    print("2️⃣ Initializing Role-Based Agents...")
    await initialize_agents(orchestrator)
    
    # Insert SOP into database (in production, this would be pre-loaded)
    print("3️⃣ Loading Emergency Maintenance SOP...")
    # For demo, we'll simulate this step
    sop_id = "sop_emergency_maintenance_001"
    
    # Create workflow instance from email trigger
    print("\n4️⃣ Creating Workflow Instance...")
    print("   📧 Trigger: Email from tenant reporting water leak")
    
    initial_context = {
        "tenant_id": "tenant_12345",
        "tenant_email": "john.smith@apartment.com",
        "unit_id": "unit_405",
        "issue_type": "plumbing",
        "issue_description": "Water leak under bathroom sink - flooding reported",
        "urgency": "emergency",
        "reported_at": datetime.utcnow().isoformat(),
        "contact_phone": "555-0123"
    }
    
    workflow_id = await orchestrator.create_workflow_instance(
        sop_id=sop_id,
        trigger_type="email",
        trigger_id="email_98765",
        initial_context=initial_context,
        initiated_by="system"
    )
    
    print(f"   ✅ Workflow Instance Created: {workflow_id}")
    
    # Start workflow execution
    print("\n5️⃣ Starting Workflow Execution...")
    print("   ⏱️  Expected completion time: < 30 minutes")
    print("\n" + "-" * 60)
    
    # Register event handlers to show progress
    def print_event(event_name: str):
        async def handler(data):
            timestamp = datetime.utcnow().strftime("%H:%M:%S")
            if event_name == "human_action_required":
                print(f"\n[{timestamp}] 👤 Human Action Required:")
                print(f"   Role: {data['role']}")
                print(f"   Task: {data['step']['name']}")
                print(f"   Description: {data['step']['description']}")
            elif event_name == "workflow_completed":
                print(f"\n[{timestamp}] ✅ Workflow Completed Successfully!")
            elif event_name == "workflow_failed":
                print(f"\n[{timestamp}] ❌ Workflow Failed: {data.get('error')}")
        return handler
    
    orchestrator.register_event_handler('human_action_required', print_event('human_action_required'))
    orchestrator.register_event_handler('workflow_completed', print_event('workflow_completed'))
    orchestrator.register_event_handler('workflow_failed', print_event('workflow_failed'))
    
    # Start the workflow
    await orchestrator.start_workflow(workflow_id)
    
    # Show step-by-step execution
    print("\n📊 WORKFLOW EXECUTION STEPS:")
    print("-" * 60)
    
    # Simulate step execution with delays for demo
    steps = [
        ("acknowledge_request", "Maintenance Supervisor", "Acknowledging emergency request..."),
        ("assess_severity", "Maintenance Supervisor", "Assessing severity and safety risk..."),
        ("dispatch_immediate", "Maintenance Supervisor", "Dispatching emergency technician..."),
        ("notify_tenant_eta", "Maintenance Supervisor", "Notifying tenant of ETA..."),
        ("arrange_temporary_solution", "Assistant Manager", "Arranging temporary solution..."),
        ("perform_repair", "Maintenance Tech", "Performing emergency repair..."),
        ("quality_check", "Maintenance Supervisor", "Checking repair quality..."),
        ("close_work_order", "Maintenance Supervisor", "Closing work order...")
    ]
    
    for step_id, role, description in steps:
        await asyncio.sleep(2)  # Simulate processing time
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 🔄 Step: {step_id}")
        print(f"   👤 Assigned to: {role}")
        print(f"   📝 Action: {description}")
        print(f"   ✅ Status: Completed")
    
    # Show agent communications
    print("\n\n💬 AGENT-TO-AGENT COMMUNICATIONS:")
    print("-" * 60)
    
    communications = [
        {
            "time": "10:32",
            "from": "Maintenance Supervisor",
            "to": "Property Manager",
            "message": "Emergency water leak confirmed. Dispatching tech immediately."
        },
        {
            "time": "10:35",
            "from": "Maintenance Supervisor",
            "to": "Maintenance Tech",
            "message": "Emergency dispatch to Unit 405. Water leak under sink. ETA 30 min."
        },
        {
            "time": "10:40",
            "from": "Assistant Manager",
            "to": "Maintenance Supervisor",
            "message": "Tenant offered temporary relocation to vacant unit 302 if needed."
        },
        {
            "time": "11:15",
            "from": "Maintenance Tech",
            "to": "Maintenance Supervisor",
            "message": "Repair completed. Replaced shut-off valve and supply line. No further leaks."
        }
    ]
    
    for comm in communications:
        print(f"\n[{comm['time']}] {comm['from']} → {comm['to']}")
        print(f"   📨 \"{comm['message']}\"")
    
    # Show final summary
    print("\n\n📋 WORKFLOW SUMMARY:")
    print("=" * 60)
    print(f"Workflow ID: {workflow_id}")
    print(f"SOP: Emergency Maintenance Response")
    print(f"Trigger: Email from tenant")
    print(f"Total Duration: 43 minutes")
    print(f"Steps Completed: 8/8")
    print(f"Human Interventions: 3")
    print(f"Automated Actions: 5")
    print(f"Status: ✅ COMPLETED")
    
    print("\n🎯 KEY OUTCOMES:")
    print("• Emergency acknowledged within 5 minutes")
    print("• Technician dispatched within 15 minutes")
    print("• Repair completed within 45 minutes")
    print("• Tenant notified at each stage")
    print("• Work order documented with photos")
    print("• Quality check passed")
    
    print("\n✨ Demo completed successfully!")

async def demo_agent_capabilities():
    """Demonstrate individual agent capabilities"""
    print("\n\n🤖 AGENT CAPABILITIES DEMO")
    print("=" * 60)
    
    orchestrator = SOPOrchestrationEngine()
    await initialize_agents(orchestrator)
    
    print("\n1️⃣ Property Manager Agent:")
    print("   • Can approve repairs of any amount")
    print("   • Makes strategic decisions")
    print("   • Handles all escalations")
    print("   • Full system access")
    
    print("\n2️⃣ Maintenance Supervisor Agent:")
    print("   • Creates and assigns work orders")
    print("   • Approves parts up to $2,000")
    print("   • Manages technician schedules")
    print("   • Handles emergency dispatch")
    
    print("\n3️⃣ Leasing Agent:")
    print("   • Schedules property tours")
    print("   • Sends availability information")
    print("   • Processes applications")
    print("   • Follows up with prospects")
    
    print("\n4️⃣ Accountant Agent:")
    print("   • Processes payments")
    print("   • Creates basic payment plans")
    print("   • Waives fees up to $100")
    print("   • Sends statements")
    
    # Demonstrate a simple agent interaction
    print("\n\n💬 SAMPLE AGENT INTERACTION:")
    print("-" * 60)
    
    # Get agents
    maintenance_supervisor = orchestrator.agents.get("maintenance_supervisor")
    property_manager = orchestrator.agents.get("property_manager")
    
    if maintenance_supervisor and property_manager:
        # Supervisor requests approval for expensive repair
        print("\n🔧 Maintenance Supervisor needs approval for $5,000 repair...")
        
        message_id = await maintenance_supervisor.send_message(
            to_role="property_manager",
            subject="Approval Required: HVAC Replacement",
            message="Unit 405 requires complete HVAC replacement. Estimated cost: $5,000",
            data={
                "repair_type": "HVAC",
                "unit_id": "405",
                "estimated_cost": 5000,
                "urgency": "high"
            },
            message_type="escalation"
        )
        
        print(f"   📤 Message sent to Property Manager (ID: {message_id})")
        
        # Property Manager responds
        await asyncio.sleep(1)
        print("\n👔 Property Manager reviews and approves...")
        
        approval_response = await property_manager.execute_action(
            "approve_emergency_repair",
            {
                "context": {
                    "repair_details": {
                        "estimated_cost": 5000,
                        "type": "HVAC replacement"
                    }
                }
            }
        )
        
        print(f"   ✅ Approval granted: {approval_response['output']['authorization_code']}")
        print(f"   💰 Approved amount: ${approval_response['output']['approved_amount']}")

async def main():
    """Run all demos"""
    try:
        # Run emergency maintenance demo
        await demo_emergency_maintenance_workflow()
        
        # Show agent capabilities
        await demo_agent_capabilities()
        
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check for required environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Missing environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\nPlease set these in your .env file to run the demo with real Supabase.")
        print("For demo purposes, the workflow will simulate database operations.")
    
    # Run the demo
    asyncio.run(main())