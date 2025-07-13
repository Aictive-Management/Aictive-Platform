#!/bin/bash
# Easy setup script for Aictive Platform

echo "🚀 Welcome to Aictive Platform Setup!"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "main_secure.py" ]; then
    echo "❌ Error: Please run this script from the aictive-platform directory"
    exit 1
fi

# Step 1: Activate virtual environment
echo "📦 Step 1: Setting up Python environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Step 2: Install dependencies
echo ""
echo "📦 Step 2: Installing required packages..."
echo "This may take a few minutes..."
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ All packages installed successfully"
else
    echo "❌ Error installing packages. Trying again..."
    pip install -r requirements.txt
fi

# Step 3: Check for .env file
echo ""
echo "🔐 Step 3: Checking configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating one for you..."
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: You need to add your API keys to the .env file"
    echo "   Open .env in a text editor and replace the placeholder values"
    echo ""
    echo "Press Enter when you've added your API keys..."
    read
fi

# Step 4: Run tests (optional)
echo ""
echo "🧪 Step 4: Would you like to run tests? (y/n)"
read -n 1 run_tests
echo ""
if [[ $run_tests =~ ^[Yy]$ ]]; then
    echo "Running security tests..."
    pytest test_security.py -v --tb=short
    echo ""
    echo "Press Enter to continue..."
    read
fi

# Step 5: Start the server
echo ""
echo "🌟 Step 5: Starting Aictive Platform..."
echo ""
echo "The server will start at: http://localhost:8000"
echo "API Documentation will be at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "===================================="
echo ""

# Run the server
uvicorn main_secure:app --reload --host 0.0.0.0 --port 8000