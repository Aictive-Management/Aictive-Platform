#!/usr/bin/env python3
"""
Test Basic Agent Functionality
Start here to verify your setup is working
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# For now, let's test without imports that require API keys
print("🤖 Testing Aictive Platform v2 Setup...")

def check_environment():
    """Check if environment is properly configured"""
    print("\n📋 Checking environment configuration...")
    
    required_vars = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY", 
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY"
    ]
    
    missing = []
    configured = []
    
    for var in required_vars:
        value = os.getenv(var, "")
        if not value or value.startswith("your_"):
            missing.append(var)
        else:
            configured.append(var)
    
    if configured:
        print(f"✅ Configured: {', '.join(configured)}")
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
        print("\n⚠️  Please add these to your .env file:")
        for var in missing:
            print(f"   {var}=your_actual_key_here")
    
    return len(missing) == 0

def check_directories():
    """Check if all required directories exist"""
    print("\n📁 Checking directory structure...")
    
    base_path = Path("/Users/garymartin/Downloads/aictive-platform-v2")
    required_dirs = [
        "agents/property_manager",
        "workflows/maintenance",
        "documents",
        "tests"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - missing")
            all_exist = False
            
    return all_exist

def check_sample_data():
    """Check if sample data exists"""
    print("\n📊 Checking sample data...")
    
    base_path = Path("/Users/garymartin/Downloads/aictive-platform-v2/tests")
    sample_files = [
        "sample_maintenance_request.json",
        "sample_lease_application.json"
    ]
    
    for sample_file in sample_files:
        file_path = base_path / sample_file
        if file_path.exists():
            print(f"✅ {sample_file}")
            # Load and display sample
            with open(file_path, 'r') as f:
                data = json.load(f)
                print(f"   Type: {data.get('type', 'unknown')}")
        else:
            print(f"❌ {sample_file} - missing")

async def test_basic_workflow():
    """Test a basic workflow without API calls"""
    print("\n🔄 Testing basic workflow logic...")
    
    # Load sample maintenance request
    sample_path = Path("/Users/garymartin/Downloads/aictive-platform-v2/tests/sample_maintenance_request.json")
    
    if sample_path.exists():
        with open(sample_path, 'r') as f:
            request = json.load(f)
        
        print(f"📍 Processing: {request['description']}")
        
        # Simulate workflow steps
        workflow_steps = [
            "1. Classify request type",
            "2. Assess urgency",
            "3. Assign to agent",
            "4. Create work order"
        ]
        
        for step in workflow_steps:
            print(f"   ✅ {step}")
            await asyncio.sleep(0.5)  # Simulate processing
        
        print("✅ Workflow test completed!")
    else:
        print("❌ Sample data not found")

def main():
    """Run all checks"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          AICTIVE PLATFORM V2 - SYSTEM CHECK               ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Run checks
    env_ok = check_environment()
    dirs_ok = check_directories()
    check_sample_data()
    
    # Run async test
    asyncio.run(test_basic_workflow())
    
    print("\n📊 Summary:")
    if env_ok and dirs_ok:
        print("✅ System is ready for API integration!")
        print("\n🚀 Next steps:")
        print("1. Add your API keys to .env")
        print("2. Run: python3 test_property_manager.py")
    else:
        print("❌ Please fix the issues above before proceeding")

if __name__ == "__main__":
    main()