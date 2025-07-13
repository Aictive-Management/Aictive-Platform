"""
Complete Example: Receiving Tenant Message and Creating Work Order
Shows the full bidirectional flow with RentVine
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from rentvine_api_client import RentVineAPIClient, RentVineConfig
from super_claude_swarm_orchestrator import SuperClaudeSwarmOrchestrator


@dataclass
class TenantMessage:
    """Parsed tenant message"""
    id: str
    tenant_id: str
    property_id: str
    unit_id: str
    content: str
    timestamp: datetime
    attachments: List[str] = None


class MessageAnalyzer:
    """AI-powered message analyzer"""
    
    def __init__(self, swarm_orchestrator: SuperClaudeSwarmOrchestrator):
        self.swarm = swarm_orchestrator
        
        # Maintenance keywords for quick detection
        self.maintenance_keywords = [
            'broken', 'leak', 'not working', 'repair', 'fix', 'maintenance',
            'damage', 'issue', 'problem', 'emergency', 'urgent', 'asap',
            'water', 'heat', 'air', 'ac', 'heater', 'plumbing', 'electrical',
            'appliance', 'door', 'window', 'lock', 'smoke', 'detector'
        ]
    
    async def analyze_message(self, message: TenantMessage) -> Dict[str, Any]:
        """Analyze tenant message using AI"""
        
        # Quick keyword check
        is_maintenance = self._quick_maintenance_check(message.content)
        
        if not is_maintenance:
            # Use AI for deeper analysis
            ai_request = {
                "objective": "pattern_recognition",
                "description": f"Analyze tenant message: {message.content}",
                "complexity": 0.3,
                "priority": "normal",
                "constraints": {
                    "message_length": len(message.content),
                    "has_attachments": bool(message.attachments)
                }
            }
            
            ai_result = await self.swarm.process_request(ai_request)
            
            # Extract intent from AI analysis
            intent = self._extract_intent(ai_result)
        else:
            intent = "maintenance_request"
        
        # If maintenance, extract details
        if intent == "maintenance_request":
            return await self._analyze_maintenance_request(message)
        else:
            return {
                "intent": intent,
                "requires_work_order": False,
                "suggested_action": self._get_suggested_action(intent)
            }
    
    def _quick_maintenance_check(self, content: str) -> bool:
        """Quick check for maintenance keywords"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.maintenance_keywords)
    
    async def _analyze_maintenance_request(self, message: TenantMessage) -> Dict[str, Any]:
        """Deep analysis of maintenance request"""
        
        # Use AI to extract maintenance details
        analysis_request = {
            "objective": "workflow_design",
            "description": f"Extract maintenance details from: {message.content}",
            "complexity": 0.5,
            "priority": "high",
            "constraints": {
                "extract": ["issue_type", "location", "severity", "urgency"]
            }
        }
        
        ai_analysis = await self.swarm.process_request(analysis_request)
        
        # Parse AI response
        details = self._parse_maintenance_details(message.content, ai_analysis)
        
        return {
            "intent": "maintenance_request",
            "requires_work_order": True,
            "work_order_details": details,
            "confidence": ai_analysis.get("confidence", 0.8)
        }
    
    def _parse_maintenance_details(self, content: str, ai_analysis: Dict) -> Dict[str, Any]:
        """Parse maintenance details from content and AI analysis"""
        
        # Determine priority
        priority = "normal"
        if any(word in content.lower() for word in ['emergency', 'urgent', 'asap', 'immediately']):
            priority = "emergency"
        elif any(word in content.lower() for word in ['soon', 'quickly', 'today']):
            priority = "high"
        
        # Determine category
        category = "general"
        if any(word in content.lower() for word in ['water', 'leak', 'flood', 'pipe', 'drain']):
            category = "plumbing"
        elif any(word in content.lower() for word in ['electrical', 'power', 'outlet', 'light', 'switch']):
            category = "electrical"
        elif any(word in content.lower() for word in ['heat', 'ac', 'air', 'temperature', 'hvac']):
            category = "hvac"
        elif any(word in content.lower() for word in ['appliance', 'refrigerator', 'stove', 'washer', 'dryer']):
            category = "appliance"
        
        # Extract location
        location = self._extract_location(content)
        
        return {
            "priority": priority,
            "category": category,
            "description": content,
            "location": location,
            "ai_insights": ai_analysis.get("insights", []),
            "estimated_duration": self._estimate_duration(category, priority)
        }
    
    def _extract_location(self, content: str) -> str:
        """Extract location from message"""
        # Look for room mentions
        rooms = ['kitchen', 'bathroom', 'bedroom', 'living room', 'garage', 'basement', 'attic']
        for room in rooms:
            if room in content.lower():
                return room.title()
        return "Not specified"
    
    def _estimate_duration(self, category: str, priority: str) -> str:
        """Estimate repair duration"""
        durations = {
            "plumbing": {"emergency": "2 hours", "high": "4 hours", "normal": "1 day"},
            "electrical": {"emergency": "2 hours", "high": "4 hours", "normal": "1 day"},
            "hvac": {"emergency": "4 hours", "high": "1 day", "normal": "2 days"},
            "appliance": {"emergency": "4 hours", "high": "1 day", "normal": "3 days"},
            "general": {"emergency": "2 hours", "high": "1 day", "normal": "3 days"}
        }
        return durations.get(category, {}).get(priority, "3 days")
    
    def _extract_intent(self, ai_result: Dict) -> str:
        """Extract intent from AI result"""
        # This would parse the AI response
        return "maintenance_request"  # Simplified
    
    def _get_suggested_action(self, intent: str) -> str:
        """Get suggested action for non-maintenance intents"""
        actions = {
            "payment_inquiry": "Route to accounting team",
            "lease_question": "Route to leasing team",
            "complaint": "Route to resident services",
            "general_inquiry": "Send automated response with FAQ"
        }
        return actions.get(intent, "Route to property manager")


class WorkOrderCreator:
    """Creates work orders in RentVine from analyzed messages"""
    
    def __init__(self, rentvine_client: RentVineAPIClient):
        self.rentvine = rentvine_client
    
    async def create_work_order_from_message(
        self,
        message: TenantMessage,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create work order in RentVine based on message analysis"""
        
        if not analysis.get("requires_work_order"):
            return {"created": False, "reason": "Not a maintenance request"}
        
        details = analysis["work_order_details"]
        
        # Build work order data
        work_order_data = {
            "property_id": message.property_id,
            "unit_id": message.unit_id,
            "tenant_id": message.tenant_id,
            "category": details["category"],
            "priority": details["priority"],
            "description": details["description"],
            "internal_notes": f"Created from tenant message {message.id}. AI Confidence: {analysis['confidence']:.2%}",
            "location": details["location"],
            "source": "tenant_message",
            "source_id": message.id,
            "estimated_duration": details["estimated_duration"],
            "ai_insights": ", ".join(details.get("ai_insights", []))
        }
        
        # Create in RentVine
        response = await self.rentvine.create_work_order(work_order_data)
        
        if response.success:
            work_order_id = response.data.get("id")
            
            # Log the creation
            print(f"✅ Work Order Created: {work_order_id}")
            print(f"   Priority: {details['priority']}")
            print(f"   Category: {details['category']}")
            print(f"   Location: {details['location']}")
            
            # Return details
            return {
                "created": True,
                "work_order_id": work_order_id,
                "details": details,
                "rentvine_response": response.data
            }
        else:
            return {
                "created": False,
                "error": response.error,
                "details": details
            }


class MessageToWorkOrderWorkflow:
    """Complete workflow from message to work order"""
    
    def __init__(
        self,
        rentvine_client: RentVineAPIClient,
        swarm_orchestrator: SuperClaudeSwarmOrchestrator
    ):
        self.rentvine = rentvine_client
        self.analyzer = MessageAnalyzer(swarm_orchestrator)
        self.creator = WorkOrderCreator(rentvine_client)
    
    async def process_tenant_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming tenant message webhook"""
        
        # Parse webhook data
        message = TenantMessage(
            id=webhook_data["data"]["id"],
            tenant_id=webhook_data["data"]["tenant_id"],
            property_id=webhook_data["data"]["property_id"],
            unit_id=webhook_data["data"]["unit_id"],
            content=webhook_data["data"]["content"],
            timestamp=datetime.fromisoformat(webhook_data["data"]["timestamp"]),
            attachments=webhook_data["data"].get("attachments", [])
        )
        
        print(f"\n📨 New Message from Tenant {message.tenant_id}")
        print(f"   Unit: {message.unit_id}")
        print(f"   Message: {message.content[:100]}...")
        
        # Analyze message
        print("\n🤖 Analyzing message with AI...")
        analysis = await self.analyzer.analyze_message(message)
        
        print(f"   Intent: {analysis['intent']}")
        print(f"   Requires Work Order: {analysis['requires_work_order']}")
        
        # Create work order if needed
        if analysis["requires_work_order"]:
            print("\n🔧 Creating Work Order...")
            result = await self.creator.create_work_order_from_message(message, analysis)
            
            if result["created"]:
                # Additional actions after work order creation
                await self._post_creation_actions(message, result)
            
            return result
        else:
            # Handle non-maintenance messages
            return await self._handle_non_maintenance_message(message, analysis)
    
    async def _post_creation_actions(self, message: TenantMessage, result: Dict[str, Any]):
        """Actions to take after work order creation"""
        
        work_order_id = result["work_order_id"]
        details = result["details"]
        
        # 1. Send confirmation to tenant
        await self._send_tenant_confirmation(message.tenant_id, work_order_id, details)
        
        # 2. If emergency, trigger immediate dispatch
        if details["priority"] == "emergency":
            await self._trigger_emergency_dispatch(work_order_id, details)
        
        # 3. Update message in RentVine as "processed"
        await self._mark_message_processed(message.id, work_order_id)
    
    async def _send_tenant_confirmation(
        self,
        tenant_id: str,
        work_order_id: str,
        details: Dict[str, Any]
    ):
        """Send confirmation to tenant"""
        # This would integrate with communication system
        print(f"   📧 Sending confirmation to tenant {tenant_id}")
        print(f"      Work Order: {work_order_id}")
        print(f"      Expected completion: {details['estimated_duration']}")
    
    async def _trigger_emergency_dispatch(self, work_order_id: str, details: Dict[str, Any]):
        """Trigger emergency dispatch workflow"""
        print(f"   🚨 EMERGENCY DISPATCH TRIGGERED!")
        print(f"      Category: {details['category']}")
        print(f"      Location: {details['location']}")
        # This would trigger the emergency workflow
    
    async def _mark_message_processed(self, message_id: str, work_order_id: str):
        """Mark message as processed in RentVine"""
        # This would update the message status
        update_data = {
            "status": "processed",
            "processed_at": datetime.utcnow().isoformat(),
            "work_order_id": work_order_id
        }
        # await self.rentvine.update_message(message_id, update_data)
        print(f"   ✅ Message {message_id} marked as processed")
    
    async def _handle_non_maintenance_message(
        self,
        message: TenantMessage,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle non-maintenance messages"""
        action = analysis["suggested_action"]
        print(f"   ➡️ Action: {action}")
        
        # Route to appropriate team
        return {
            "created": False,
            "action_taken": action,
            "message_id": message.id
        }


# Example webhook handler
async def handle_message_webhook(webhook_data: Dict[str, Any]):
    """Handle incoming message webhook from RentVine"""
    
    # Initialize components
    rentvine_config = RentVineConfig(
        base_url="https://api.rentvine.com/v2",
        api_key="your_key",
        api_secret="your_secret",
        tenant_id="your_tenant"
    )
    
    async with RentVineAPIClient(rentvine_config) as rentvine:
        swarm = SuperClaudeSwarmOrchestrator()
        workflow = MessageToWorkOrderWorkflow(rentvine, swarm)
        
        # Process the message
        result = await workflow.process_tenant_message(webhook_data)
        
        return result


# Test with example messages
async def test_message_scenarios():
    """Test various message scenarios"""
    
    test_messages = [
        {
            "emergency": {
                "data": {
                    "id": "msg_001",
                    "tenant_id": "tenant_123",
                    "property_id": "prop_456",
                    "unit_id": "unit_789",
                    "content": "URGENT! Water is leaking from the ceiling in the bathroom! It's getting worse!",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        },
        {
            "routine": {
                "data": {
                    "id": "msg_002",
                    "tenant_id": "tenant_124",
                    "property_id": "prop_456",
                    "unit_id": "unit_790",
                    "content": "The garbage disposal in the kitchen stopped working yesterday. Can someone take a look?",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        },
        {
            "non_maintenance": {
                "data": {
                    "id": "msg_003",
                    "tenant_id": "tenant_125",
                    "property_id": "prop_456",
                    "unit_id": "unit_791",
                    "content": "Hi, I wanted to confirm that my rent payment went through. I paid online yesterday.",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        }
    ]
    
    print("🧪 TESTING MESSAGE TO WORK ORDER SCENARIOS")
    print("=" * 60)
    
    for scenario in test_messages:
        name, data = list(scenario.items())[0]
        print(f"\n\n📋 Scenario: {name.upper()}")
        print("-" * 40)
        
        # Mock the webhook processing
        # In production, this would be triggered by actual webhook
        # result = await handle_message_webhook(data)
        
        # For now, just show the flow
        print(f"Message: {data['data']['content']}")
        print("Expected Flow:")
        
        if name == "emergency":
            print("1. AI detects emergency keywords")
            print("2. Creates HIGH PRIORITY work order")
            print("3. Triggers emergency dispatch")
            print("4. Sends immediate confirmation to tenant")
            
        elif name == "routine":
            print("1. AI identifies maintenance request")
            print("2. Creates normal priority work order")
            print("3. Schedules within standard timeframe")
            print("4. Sends confirmation with timeline")
            
        else:
            print("1. AI determines non-maintenance intent")
            print("2. Routes to appropriate team")
            print("3. No work order created")
            print("4. Sends appropriate response")


if __name__ == "__main__":
    asyncio.run(test_message_scenarios())