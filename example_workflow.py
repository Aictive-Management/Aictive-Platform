"""
Example workflow showing the complete email response process
"""
import asyncio
from datetime import datetime
from response_system import EmailResponseSystem, EmailResponseRequest

async def example_maintenance_workflow():
    """Example: Assistant Manager handling emergency maintenance request"""
    
    print("=" * 60)
    print("🏢 AICTIVE PLATFORM - EMERGENCY MAINTENANCE WORKFLOW")
    print("=" * 60)
    
    # Step 1: Email received and classified
    print("\n1️⃣ EMAIL RECEIVED:")
    print("From: john.smith@apartment.com")
    print("Subject: URGENT - Water leak in bathroom!")
    print("Body: Water is flooding from under the sink! Please help!")
    
    classification = {
        "primary_category": "maintenance",
        "urgency": "emergency",
        "specific_issue": "Water leak under bathroom sink",
        "sentiment": "distressed",
        "keywords": ["water", "leak", "flooding", "urgent"]
    }
    print(f"\n🤖 AI Classification: {classification}")
    
    # Step 2: Assistant Manager reviews and prepares response
    print("\n2️⃣ ASSISTANT MANAGER RESPONSE:")
    
    request = EmailResponseRequest(
        email_id="email_12345",
        tenant_email="john.smith@apartment.com",
        tenant_id="tenant_rv_98765",  # RentVine ID
        subject="URGENT - Water leak in bathroom!",
        original_message="Water is flooding from under the sink! Please help!",
        classification=classification,
        
        # Response details
        selected_action="approve_emergency_repair",
        response_template="maintenance_acknowledgment",
        attachments=["emergency_work_order.pdf"],
        
        # Staff details
        staff_id="staff_am_001",
        staff_role="assistant_manager",
        staff_name="Sarah Johnson",
        
        # Options
        send_via_rentvine=True,
        require_approval=True,  # Emergency requires Property Manager approval
        create_work_order=True,
        work_order_details={
            "unit_id": "unit_405",
            "priority": "emergency",
            "issue_description": "Water leak under bathroom sink - flooding reported",
            "assigned_technician": "tech_001"
        }
    )
    
    # Initialize system
    system = EmailResponseSystem()
    
    # Generate response
    response_data = await system.generate_role_based_response(request)
    
    print("\n📝 GENERATED RESPONSE:")
    print("-" * 40)
    print(response_data["response_text"])
    print("-" * 40)
    print(f"\n⚠️  Requires Approval: {response_data['needs_approval']}")
    print(f"📎 Attachments: {', '.join(response_data['attachments'])}")
    
    # Step 3: Send to Slack for approval
    print("\n3️⃣ SLACK APPROVAL PROCESS:")
    print("📱 Sending to #approvals channel...")
    print("""
    ┌─────────────────────────────────────┐
    │ 📧 Email Response Approval Required │
    │                                     │
    │ From: Sarah Johnson (Asst Manager)  │
    │ To: john.smith@apartment.com       │
    │ Category: Emergency Maintenance     │
    │                                     │
    │ [✅ Approve] [✏️ Edit] [❌ Reject]  │
    └─────────────────────────────────────┘
    """)
    
    # Simulate approval after 3 seconds
    await asyncio.sleep(3)
    print("✅ Property Manager approved the response!")
    
    # Step 4: Send response
    print("\n4️⃣ SENDING RESPONSE:")
    status = await system.send_response(request, response_data)
    
    print(f"📤 Response Status: {status.status}")
    print(f"📍 Method: {status.method}")
    print(f"🆔 Response ID: {status.response_id}")
    
    # Step 5: Create work order in RentVine
    print("\n5️⃣ WORK ORDER CREATED:")
    print(f"🔧 Work Order #: WO-{datetime.now().strftime('%Y%m%d')}-001")
    print("👷 Assigned to: Mike Thompson (Maintenance Tech)")
    print("⏰ ETA: 30 minutes")
    
    print("\n✅ WORKFLOW COMPLETE!")
    print("Tenant has been notified and emergency maintenance dispatched.")

async def example_payment_workflow():
    """Example: Accountant handling payment plan request"""
    
    print("\n" + "=" * 60)
    print("💰 PAYMENT PLAN REQUEST WORKFLOW")
    print("=" * 60)
    
    # Similar workflow for payment requests...
    print("\n1️⃣ EMAIL RECEIVED:")
    print("From: jane.doe@apartment.com")
    print("Subject: Request for payment arrangement")
    print("Body: Due to reduced hours, can I pay rent in installments?")
    
    # ... (abbreviated for space)

async def main():
    """Run example workflows"""
    print("🚀 AICTIVE PLATFORM - WORKFLOW EXAMPLES")
    print("=====================================")
    
    # Run maintenance workflow
    await example_maintenance_workflow()
    
    # Optionally run other workflows
    # await example_payment_workflow()

if __name__ == "__main__":
    asyncio.run(main())