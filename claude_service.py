import os
import json
from typing import Dict, List, Optional, Any
from anthropic import Anthropic, AnthropicError
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ClaudeResponse:
    content: str
    usage: Dict[str, int]
    model: str
    stop_reason: Optional[str] = None

class ClaudeService:
    """Service for interacting with Claude API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = Anthropic(api_key=self.api_key)
        
        # Model configurations
        self.models = {
            "fast": "claude-3-5-haiku-20241022",
            "balanced": "claude-3-5-sonnet-20241022", 
            "powerful": "claude-3-5-opus-20241022",
            "latest": "claude-3-5-sonnet-20241022"
        }
        
    async def classify_email(self, email_data: Dict[str, str]) -> Dict[str, Any]:
        """Classify email into categories with confidence scores"""
        
        system_prompt = """You are an email classifier for a property management system.
        
        Categories:
        - maintenance: Repair requests, property issues, broken items
        - payment: Rent, balances, payment methods, financial questions  
        - lease: Lease renewals, terms, move-in/out
        - general: All other inquiries
        
        Analyze the email and return a JSON response with:
        {
            "primary_category": "category_name",
            "confidence": 0.0-1.0,
            "secondary_category": "category_name or null",
            "keywords": ["relevant", "keywords"],
            "urgency": "low|medium|high|emergency",
            "sentiment": "positive|neutral|negative"
        }
        """
        
        user_prompt = f"""
        From: {email_data.get('sender_email', 'Unknown')}
        Subject: {email_data.get('subject', 'No Subject')}
        Body: {email_data.get('body_text', 'No Content')[:1000]}
        """
        
        try:
            response = self.client.messages.create(
                model=self.models["latest"],
                max_tokens=300,
                temperature=0.1,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse JSON response
            content = response.content[0].text
            result = json.loads(content)
            
            # Add metadata
            result['model_used'] = response.model
            result['processing_time'] = datetime.utcnow().isoformat()
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            # Fallback classification
            return {
                "primary_category": "general",
                "confidence": 0.5,
                "secondary_category": None,
                "keywords": [],
                "urgency": "medium",
                "sentiment": "neutral",
                "error": "Failed to parse AI response"
            }
        except AnthropicError as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def analyze_maintenance_request(self, email_content: str) -> Dict[str, Any]:
        """Extract detailed maintenance information"""
        
        system_prompt = """You are a maintenance request analyzer. Extract structured data from maintenance emails.
        
        Return a JSON object with:
        {
            "issue_type": "plumbing|electrical|hvac|appliance|structural|pest|other",
            "specific_issue": "brief description",
            "location": {
                "unit_area": "kitchen|bathroom|bedroom|living_room|exterior|other",
                "details": "specific location details"
            },
            "urgency_indicators": {
                "has_water_damage": boolean,
                "no_utilities": boolean,  
                "safety_hazard": boolean,
                "multiple_units_affected": boolean
            },
            "urgency_level": "emergency|high|medium|low",
            "tenant_impact": "cannot_use_area|inconvenient|cosmetic",
            "estimated_repair_complexity": "simple|moderate|complex",
            "tenant_availability": "extracted availability or null",
            "special_instructions": "any special notes",
            "detected_appliances": ["list of mentioned appliances"],
            "requires_parts": boolean,
            "confidence_score": 0.0-1.0
        }
        """
        
        try:
            response = self.client.messages.create(
                model=self.models["latest"],
                max_tokens=500,
                temperature=0.2,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Analyze this maintenance request:\n\n{email_content}"}
                ]
            )
            
            return json.loads(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error analyzing maintenance request: {e}")
            raise

    async def generate_response(
        self, 
        template_type: str,
        context: Dict[str, Any],
        tone: str = "professional"
    ) -> str:
        """Generate email responses using templates and context"""
        
        templates = {
            "maintenance_acknowledgment": """Generate a professional email acknowledging a maintenance request.
                Context: {context}
                Include: ticket number, estimated timeline, next steps.
                Tone: {tone}, empathetic, clear.""",
            
            "payment_balance": """Generate an email providing balance information.
                Context: {context}
                Include: current balance, due date, payment options.
                Tone: {tone}, helpful, non-threatening.""",
            
            "general_response": """Generate a helpful response to a general inquiry.
                Context: {context}
                Tone: {tone}, friendly, informative."""
        }
        
        template = templates.get(template_type, templates["general_response"])
        prompt = template.format(context=json.dumps(context, indent=2), tone=tone)
        
        try:
            response = self.client.messages.create(
                model=self.models["balanced"],
                max_tokens=500,
                temperature=0.7,
                system="You are a helpful property management assistant. Write clear, concise emails.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        
        prompt = """Extract the following entities from the text:
        - names (people)
        - addresses (unit numbers, street addresses)
        - phone numbers
        - dates and times
        - dollar amounts
        
        Return as JSON: {
            "names": [],
            "addresses": [],
            "phone_numbers": [],
            "dates_times": [],
            "amounts": []
        }"""
        
        try:
            response = self.client.messages.create(
                model=self.models["fast"],
                max_tokens=300,
                temperature=0.1,
                system=prompt,
                messages=[
                    {"role": "user", "content": text}
                ]
            )
            
            return json.loads(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {
                "names": [],
                "addresses": [],
                "phone_numbers": [],
                "dates_times": [],
                "amounts": []
            }

    async def check_compliance(self, message: str, state: str = "CA") -> Dict[str, Any]:
        """Check if message complies with rental law requirements"""
        
        prompt = f"""Review this property management message for legal compliance in {state}.
        
        Check for:
        1. Fair Housing Act compliance
        2. State-specific rental law compliance
        3. Discriminatory language
        4. Required disclosures
        5. Privacy concerns
        
        Message: {message}
        
        Return JSON: {{
            "is_compliant": boolean,
            "issues": ["list of issues"],
            "suggestions": ["list of fixes"],
            "risk_level": "low|medium|high"
        }}"""
        
        try:
            response = self.client.messages.create(
                model=self.models["balanced"],
                max_tokens=400,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            raise

# Example usage function
async def process_email_with_claude(email_data: Dict[str, str]):
    """Complete email processing pipeline with Claude"""
    
    claude = ClaudeService()
    
    # Step 1: Classify email
    classification = await claude.classify_email(email_data)
    print(f"Classification: {classification}")
    
    # Step 2: If maintenance, analyze details
    if classification['primary_category'] == 'maintenance':
        maintenance_details = await claude.analyze_maintenance_request(
            email_data['body_text']
        )
        print(f"Maintenance Analysis: {maintenance_details}")
        
        # Step 3: Generate response
        response_context = {
            "ticket_id": f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "issue": maintenance_details['specific_issue'],
            "urgency": maintenance_details['urgency_level'],
            "timeline": "24 hours" if maintenance_details['urgency_level'] != 'emergency' else "4 hours"
        }
        
        response_email = await claude.generate_response(
            "maintenance_acknowledgment",
            response_context
        )
        print(f"Generated Response:\n{response_email}")
        
        # Step 4: Check compliance
        compliance = await claude.check_compliance(response_email)
        print(f"Compliance Check: {compliance}")
    
    return classification