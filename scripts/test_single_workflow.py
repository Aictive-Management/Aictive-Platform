#!/usr/bin/env python3
"""
Interactive Workflow Testing Script for Aictive Platform
Test individual workflows and see how AI agents work together
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class WorkflowTester:
    def __init__(self):
        self.workflows = {
            "1": {
                "name": "Email Classification",
                "description": "Classify an email into categories (maintenance, payment, lease, general)",
                "function": self.test_email_classification
            },
            "2": {
                "name": "Maintenance Analysis", 
                "description": "Analyze a maintenance request and extract detailed information",
                "function": self.test_maintenance_analysis
            },
            "3": {
                "name": "Response Generation",
                "description": "Generate a professional email response",
                "function": self.test_response_generation
            },
            "4": {
                "name": "Entity Extraction",
                "description": "Extract entities (names, addresses, phone numbers) from text",
                "function": self.test_entity_extraction
            },
            "5": {
                "name": "Compliance Check",
                "description": "Check if a message complies with rental laws",
                "function": self.test_compliance_check
            },
            "6": {
                "name": "Full Email Processing",
                "description": "Complete workflow: classify, analyze, and generate response",
                "function": self.test_full_email_processing
            }
        }
    
    def print_header(self):
        """Print the script header"""
        print("🤖 Aictive Platform - Interactive Workflow Tester")
        print("=" * 60)
        print("Test individual workflows and see AI agents in action!")
        print()
    
    def print_menu(self):
        """Print the available workflows menu"""
        print("📋 Available Workflows:")
        print()
        for key, workflow in self.workflows.items():
            print(f"  {key}. {workflow['name']}")
            print(f"     {workflow['description']}")
            print()
        print("  0. Exit")
        print()
    
    def get_user_input(self, prompt: str, default: str = "") -> str:
        """Get user input with optional default value"""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        else:
            return input(f"{prompt}: ").strip()
    
    def print_result(self, title: str, data: Any):
        """Print a formatted result"""
        print(f"\n📊 {title}")
        print("-" * 40)
        if isinstance(data, dict):
            print(json.dumps(data, indent=2, default=str))
        else:
            print(data)
        print()
    
    async def test_email_classification(self):
        """Test email classification workflow"""
        print("\n📧 Email Classification Test")
        print("-" * 30)
        
        # Get test email data
        sender_email = self.get_user_input("Sender email", "tenant@example.com")
        subject = self.get_user_input("Email subject", "Water leak in bathroom")
        body = self.get_user_input("Email body", "There is water leaking from under the sink in the bathroom. It's been dripping for a few days now.")
        
        try:
            from claude_service import ClaudeService
            service = ClaudeService()
            
            email_data = {
                "sender_email": sender_email,
                "subject": subject,
                "body_text": body
            }
            
            print("\n🔄 Processing...")
            result = await service.classify_email(email_data)
            
            self.print_result("Classification Result", result)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    async def test_maintenance_analysis(self):
        """Test maintenance analysis workflow"""
        print("\n🔧 Maintenance Analysis Test")
        print("-" * 30)
        
        # Get maintenance request
        request = self.get_user_input(
            "Maintenance request description",
            "The kitchen sink is clogged and water is backing up. There's also a strange noise coming from the garbage disposal. I can't use the kitchen sink at all."
        )
        
        try:
            from claude_service import ClaudeService
            service = ClaudeService()
            
            print("\n🔄 Analyzing...")
            result = await service.analyze_maintenance_request(request)
            
            self.print_result("Maintenance Analysis", result)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    async def test_response_generation(self):
        """Test response generation workflow"""
        print("\n✉️ Response Generation Test")
        print("-" * 30)
        
        # Get context for response
        template_type = self.get_user_input(
            "Response type (maintenance_acknowledgment/payment_balance/general_response)",
            "maintenance_acknowledgment"
        )
        
        context = {
            "tenant_name": self.get_user_input("Tenant name", "John Doe"),
            "issue": self.get_user_input("Issue description", "Kitchen sink clogged"),
            "ticket_number": self.get_user_input("Ticket number", "MT-2024-001"),
            "estimated_timeline": self.get_user_input("Estimated timeline", "2-3 business days")
        }
        
        tone = self.get_user_input("Tone (professional/friendly/formal)", "professional")
        
        try:
            from claude_service import ClaudeService
            service = ClaudeService()
            
            print("\n🔄 Generating response...")
            result = await service.generate_response(template_type, context, tone)
            
            self.print_result("Generated Response", result)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    async def test_entity_extraction(self):
        """Test entity extraction workflow"""
        print("\n🔍 Entity Extraction Test")
        print("-" * 30)
        
        text = self.get_user_input(
            "Text to analyze",
            "Hi, this is Sarah Johnson calling about unit 2B. My phone number is 555-123-4567 and I need to schedule a maintenance visit for next Tuesday at 2 PM. The address is 123 Main Street, Apt 2B."
        )
        
        try:
            from claude_service import ClaudeService
            service = ClaudeService()
            
            print("\n🔄 Extracting entities...")
            result = await service.extract_entities(text)
            
            self.print_result("Extracted Entities", result)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    async def test_compliance_check(self):
        """Test compliance checking workflow"""
        print("\n⚖️ Compliance Check Test")
        print("-" * 30)
        
        message = self.get_user_input(
            "Message to check",
            "Your rent is overdue. If you don't pay within 3 days, we will begin eviction proceedings immediately."
        )
        
        state = self.get_user_input("State (for compliance laws)", "CA")
        
        try:
            from claude_service import ClaudeService
            service = ClaudeService()
            
            print("\n🔄 Checking compliance...")
            result = await service.check_compliance(message, state)
            
            self.print_result("Compliance Check Result", result)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    async def test_full_email_processing(self):
        """Test complete email processing workflow"""
        print("\n📨 Full Email Processing Test")
        print("-" * 30)
        
        # Get email data
        sender_email = self.get_user_input("Sender email", "tenant@example.com")
        subject = self.get_user_input("Email subject", "Kitchen sink clogged")
        body = self.get_user_input(
            "Email body", 
            "Hi, the kitchen sink is clogged and water is backing up. There's also a strange noise coming from the garbage disposal. I can't use the kitchen sink at all. My name is Sarah Johnson and I'm in unit 2B. My phone is 555-123-4567. Can someone come fix this soon?"
        )
        
        try:
            from claude_service import ClaudeService
            service = ClaudeService()
            
            email_data = {
                "sender_email": sender_email,
                "subject": subject,
                "body_text": body
            }
            
            print("\n🔄 Processing email...")
            
            # Step 1: Classify email
            print("  1. Classifying email...")
            classification = await service.classify_email(email_data)
            
            # Step 2: Analyze maintenance (if applicable)
            maintenance_analysis = None
            if classification.get("primary_category") == "maintenance":
                print("  2. Analyzing maintenance request...")
                maintenance_analysis = await service.analyze_maintenance_request(body)
            
            # Step 3: Extract entities
            print("  3. Extracting entities...")
            entities = await service.extract_entities(body)
            
            # Step 4: Generate response
            print("  4. Generating response...")
            context = {
                "tenant_name": entities.get("names", ["Tenant"])[0] if entities.get("names") else "Tenant",
                "issue": subject,
                "ticket_number": f"MT-2024-{hash(sender_email) % 1000:03d}",
                "estimated_timeline": "2-3 business days"
            }
            response = await service.generate_response("maintenance_acknowledgment", context)
            
            # Compile results
            result = {
                "classification": classification,
                "maintenance_analysis": maintenance_analysis,
                "entities": entities,
                "generated_response": response
            }
            
            self.print_result("Complete Email Processing", result)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    async def run(self):
        """Main interactive loop"""
        self.print_header()
        
        while True:
            self.print_menu()
            choice = input("Select a workflow to test (0-6): ").strip()
            
            if choice == "0":
                print("\n👋 Thanks for testing! Goodbye!")
                break
            
            if choice in self.workflows:
                workflow = self.workflows[choice]
                print(f"\n🚀 Testing: {workflow['name']}")
                await workflow['function']()
                
                # Ask if user wants to continue
                continue_test = input("\nTest another workflow? (y/n): ").strip().lower()
                if continue_test not in ['y', 'yes']:
                    print("\n👋 Thanks for testing! Goodbye!")
                    break
            else:
                print("❌ Invalid choice. Please select 0-6.")
                input("Press Enter to continue...")

def main():
    """Main function"""
    tester = WorkflowTester()
    asyncio.run(tester.run())

if __name__ == "__main__":
    main() 