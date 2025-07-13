"""
Demo version of Aictive Platform without authentication
For testing and demonstration purposes only
"""
from fastapi import FastAPI, HTTPException
from datetime import datetime
import logging
from claude_service import ClaudeService
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Aictive Platform API (Demo Mode)",
    description="AI-powered property management email processing - Demo without authentication",
    version="1.0.0-demo"
)

# Initialize Claude service
claude_service = ClaudeService()

# Simple request model
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class EmailRequest(BaseModel):
    sender_email: str
    subject: str
    body_text: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "active",
        "service": "Aictive Platform API (Demo Mode)",
        "message": "⚠️ Running in demo mode without authentication",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/classify-email")
async def classify_email(email: EmailRequest):
    """Classify incoming email - DEMO VERSION"""
    try:
        logger.info(f"Demo: Classifying email from {email.sender_email}")
        
        # Classify email using Claude
        classification = await claude_service.classify_email({
            "sender_email": email.sender_email,
            "subject": email.subject,
            "body_text": email.body_text
        })
        
        # Generate response
        email_id = f"demo_email_{int(datetime.utcnow().timestamp())}"
        
        return {
            "email_id": email_id,
            "primary_category": classification["primary_category"],
            "confidence": classification["confidence"],
            "secondary_category": classification.get("secondary_category"),
            "keywords": classification["keywords"],
            "urgency": classification["urgency"],
            "sentiment": classification["sentiment"],
            "processing_time": datetime.utcnow().isoformat(),
            "demo_mode": True
        }
        
    except Exception as e:
        logger.error(f"Error in demo classification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-maintenance")
async def analyze_maintenance(request: Dict[str, str]):
    """Analyze maintenance request - DEMO VERSION"""
    try:
        email_content = request.get("email_content", "")
        
        # Analyze maintenance request
        details = await claude_service.analyze_maintenance_request(email_content)
        
        return {
            **details,
            "demo_mode": True
        }
        
    except Exception as e:
        logger.error(f"Error in demo maintenance analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-response")
async def generate_response(request: Dict[str, Any]):
    """Generate email response - DEMO VERSION"""
    try:
        template_type = request.get("template_type", "general_response")
        context = request.get("context", {})
        tone = request.get("tone", "professional")
        
        response_text = await claude_service.generate_response(
            template_type=template_type,
            context=context,
            tone=tone
        )
        
        return {
            "response": response_text,
            "template_used": template_type,
            "generated_at": datetime.utcnow().isoformat(),
            "demo_mode": True
        }
        
    except Exception as e:
        logger.error(f"Error in demo response generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/demo-examples")
async def get_demo_examples():
    """Get example requests for testing"""
    return {
        "email_classification_example": {
            "endpoint": "POST /api/classify-email",
            "request": {
                "sender_email": "tenant@example.com",
                "subject": "Water leak in bathroom",
                "body_text": "There's water dripping from the ceiling in my bathroom. It started yesterday and is getting worse. Please send someone to fix it as soon as possible!"
            }
        },
        "maintenance_analysis_example": {
            "endpoint": "POST /api/analyze-maintenance",
            "request": {
                "email_content": "The kitchen sink is clogged and water won't drain. I tried using a plunger but it didn't help. The garbage disposal also makes a strange noise when turned on."
            }
        },
        "response_generation_example": {
            "endpoint": "POST /api/generate-response",
            "request": {
                "template_type": "maintenance_acknowledgment",
                "context": {
                    "ticket_id": "TKT-12345",
                    "issue": "Kitchen sink clog",
                    "timeline": "24 hours"
                },
                "tone": "professional"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*50)
    print("🚀 AICTIVE PLATFORM - DEMO MODE")
    print("="*50)
    print("\n⚠️  Running without authentication for demo purposes")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("🎯 Example requests: http://localhost:8000/api/demo-examples")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)