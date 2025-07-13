#!/bin/bash
# Super simple demo runner

echo "🚀 Starting Aictive Platform in DEMO MODE..."
echo ""
echo "This will run a simplified version without authentication"
echo "Perfect for testing and seeing how it works!"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    echo "ANTHROPIC_API_KEY=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" > .env
    echo "✅ Using the API key you provided"
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || {
    echo "Setting up Python environment..."
    python3 -m venv venv
    source venv/bin/activate
}

# Install dependencies quietly
echo "Installing required packages (this may take a minute)..."
pip install fastapi uvicorn anthropic pydantic python-dotenv > /dev/null 2>&1

# Run the demo
echo ""
echo "✅ Everything is ready!"
echo ""
echo "The demo server is starting at:"
echo "👉 http://localhost:8000/docs"
echo ""
echo "Open this link in your web browser to try it out!"
echo "Press Ctrl+C to stop"
echo ""

python demo_no_auth.py