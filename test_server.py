import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test environment variables
print("Environment Variables Check:")
print(f"SUPABASE_URL: {'✅' if os.getenv('SUPABASE_URL') else '❌'}")
print(f"SUPABASE_ANON_KEY: {'✅' if os.getenv('SUPABASE_ANON_KEY') else '❌'}")
print(f"ANTHROPIC_API_KEY: {'✅' if os.getenv('ANTHROPIC_API_KEY') else '❌'}")
print(f"RENTVINE_SUBDOMAIN: {'✅' if os.getenv('RENTVINE_SUBDOMAIN') else '❌'}")
print(f"SLACK_WEBHOOK_URL: {'✅' if os.getenv('SLACK_WEBHOOK_URL') else '❌'}")

print("\nTesting basic FastAPI server...")

from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Test Server")

@app.get("/")
async def root():
    return {
        "status": "active",
        "message": "Test server is running!",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("\nStarting test server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)