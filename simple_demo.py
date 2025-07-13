"""
Simple demo of Aictive Platform - No setup required!
"""
from fastapi import FastAPI
from datetime import datetime
import os

# Create the web app
app = FastAPI(
    title="🏠 Aictive Email AI Demo",
    description="See how AI categorizes property management emails!",
    version="1.0"
)

# Home page
@app.get("/")
async def home():
    return {
        "message": "🎉 Aictive Demo is running!",
        "instructions": "Go to http://localhost:8000/docs to try the AI",
        "time": datetime.now().strftime("%I:%M %p")
    }

# Email classifier (mock version for demo)
@app.post("/api/classify-email")
async def classify_email(email: dict):
    """
    Try this email classification!
    
    Example email to try:
    {
        "sender_email": "tenant@example.com",
        "subject": "Water leak in bathroom",
        "body_text": "Help! Water is dripping from my bathroom ceiling!"
    }
    """
    
    # Simple keyword-based classification for demo
    body = email.get("body_text", "").lower()
    subject = email.get("subject", "").lower()
    text = f"{subject} {body}"
    
    # Determine category
    if any(word in text for word in ["leak", "broken", "repair", "fix", "maintenance"]):
        category = "maintenance"
        urgency = "high" if "emergency" in text or "urgent" in text or "!" in text else "medium"
    elif any(word in text for word in ["pay", "rent", "bill", "invoice", "payment"]):
        category = "payment"
        urgency = "medium"
    elif any(word in text for word in ["lease", "renew", "contract", "agreement"]):
        category = "lease"
        urgency = "low"
    else:
        category = "general"
        urgency = "low"
    
    # Determine sentiment
    if any(word in text for word in ["help", "please", "urgent", "asap", "!"]):
        sentiment = "concerned"
    elif any(word in text for word in ["thank", "appreciate", "great"]):
        sentiment = "positive"
    else:
        sentiment = "neutral"
    
    return {
        "🏷️ category": category,
        "⚡ urgency": urgency,
        "😊 sentiment": sentiment,
        "📧 from": email.get("sender_email"),
        "📋 subject": email.get("subject"),
        "🤖 ai_confidence": "95%",
        "⏰ processed_at": datetime.now().strftime("%I:%M %p"),
        "💡 explanation": f"This looks like a {category} request with {urgency} urgency"
    }

# Test examples
@app.get("/api/examples")
async def get_examples():
    return {
        "🏠 Try these examples": [
            {
                "title": "🚰 Maintenance Emergency",
                "email": {
                    "sender_email": "john.doe@email.com",
                    "subject": "URGENT - Pipe burst in kitchen!",
                    "body_text": "Water is flooding my kitchen! Please send help immediately!"
                }
            },
            {
                "title": "💰 Payment Question",
                "email": {
                    "sender_email": "jane.smith@email.com",
                    "subject": "Question about rent payment",
                    "body_text": "Can I pay my rent in two installments this month?"
                }
            },
            {
                "title": "📄 Lease Renewal",
                "email": {
                    "sender_email": "tenant@apartment.com",
                    "subject": "Lease renewal",
                    "body_text": "I would like to renew my lease for another year."
                }
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "🌟"*25)
    print("🏠 AICTIVE EMAIL AI DEMO")
    print("🌟"*25)
    print("\n✅ Demo is starting...")
    print("\n📱 Open your web browser and go to:")
    print("👉 http://localhost:8000/docs")
    print("\n💡 Try classifying different emails!")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)