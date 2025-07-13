#!/usr/bin/env python3
"""
Health Check Script for Aictive Platform
Verifies environment, dependencies, and core functionality
"""

import sys
import os
import asyncio
import importlib
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class HealthChecker:
    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
    
    def log_result(self, check_name: str, status: str, message: str = ""):
        """Log a health check result"""
        result = {
            "check": check_name,
            "status": status,
            "message": message
        }
        self.results.append(result)
        
        if status == "ERROR":
            self.errors.append(result)
        elif status == "WARNING":
            self.warnings.append(result)
        
        # Print with color coding
        if status == "PASS":
            print(f"✅ {check_name}: {message}")
        elif status == "WARNING":
            print(f"⚠️  {check_name}: {message}")
        elif status == "ERROR":
            print(f"❌ {check_name}: {message}")
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 9:
            self.log_result("Python Version", "PASS", f"Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.log_result("Python Version", "ERROR", f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.9+")
            return False
    
    def check_virtual_environment(self) -> bool:
        """Check if virtual environment is activated"""
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.log_result("Virtual Environment", "PASS", "Virtual environment is activated")
            return True
        else:
            self.log_result("Virtual Environment", "WARNING", "Virtual environment not detected - recommended for development")
            return False
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        required_packages = [
            "fastapi",
            "uvicorn",
            "anthropic",
            "supabase",
            "pydantic",
            "dotenv",
            "jose",
            "bcrypt",
            "slowapi",
            "httpx"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                missing_packages.append(package)
        
        if not missing_packages:
            self.log_result("Dependencies", "PASS", f"All {len(required_packages)} required packages installed")
            return True
        else:
            self.log_result("Dependencies", "ERROR", f"Missing packages: {', '.join(missing_packages)}")
            return False
    
    def check_environment_variables(self) -> bool:
        """Check for required environment variables"""
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY", 
            "ANTHROPIC_API_KEY",
            "API_KEY",
            "SECRET_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if not missing_vars:
            self.log_result("Environment Variables", "PASS", "All required environment variables set")
            return True
        else:
            self.log_result("Environment Variables", "WARNING", f"Missing variables: {', '.join(missing_vars)} (using defaults/mocks)")
            return False
    
    def check_project_structure(self) -> bool:
        """Check if key project files exist"""
        required_files = [
            "main_secure.py",
            "role_agents.py", 
            "sop_orchestration.py",
            "integrations.py",
            "config.py",
            "requirements.txt"
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(project_root / file).exists():
                missing_files.append(file)
        
        if not missing_files:
            self.log_result("Project Structure", "PASS", "All key project files present")
            return True
        else:
            self.log_result("Project Structure", "ERROR", f"Missing files: {', '.join(missing_files)}")
            return False
    
    async def check_database_connection(self) -> bool:
        """Check database connectivity"""
        try:
            # Check if Supabase environment variables are set
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                self.log_result("Database Connection", "WARNING", "Supabase credentials not configured (using mocks)")
                return False
            
            # Try to import and test Supabase connection
            from supabase._sync.client import create_client
            client = create_client(supabase_url, supabase_key)
            
            # Try a simple query
            response = client.table("emails").select("id").limit(1).execute()
            self.log_result("Database Connection", "PASS", "Successfully connected to Supabase")
            return True
        except Exception as e:
            self.log_result("Database Connection", "WARNING", f"Database connection failed: {str(e)} (using mocks)")
            return False
    
    async def check_claude_service(self) -> bool:
        """Check Claude AI service connectivity"""
        try:
            from claude_service import ClaudeService
            service = ClaudeService()
            
            # Try a simple test using the classify_email method
            test_email = {
                "sender_email": "test@example.com",
                "subject": "Test email",
                "body_text": "This is a test email for health check."
            }
            response = await service.classify_email(test_email)
            
            if response and "primary_category" in response:
                self.log_result("Claude Service", "PASS", "Successfully connected to Claude AI")
                return True
            else:
                self.log_result("Claude Service", "WARNING", "Claude service returned empty response (using mocks)")
                return False
        except Exception as e:
            self.log_result("Claude Service", "WARNING", f"Claude service failed: {str(e)} (using mocks)")
            return False
    
    async def check_api_endpoints(self) -> bool:
        """Check if API endpoints are accessible"""
        try:
            import httpx
            
            # Start server in background
            import subprocess
            import time
            
            # Check if server is already running
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/health", timeout=5.0)
                    if response.status_code == 200:
                        self.log_result("API Endpoints", "PASS", "API server is running and accessible")
                        return True
            except:
                pass
            
            self.log_result("API Endpoints", "WARNING", "API server not running - start with: uvicorn main_secure:app --reload")
            return False
            
        except Exception as e:
            self.log_result("API Endpoints", "WARNING", f"API check failed: {str(e)}")
            return False
    
    def check_demo_files(self) -> bool:
        """Check if demo files are present and runnable"""
        demo_files = [
            "simple_demo.py",
            "workflow_demo.py",
            "demo.html",
            "demo_advanced.html"
        ]
        
        missing_demos = []
        for file in demo_files:
            if not Path(project_root / file).exists():
                missing_demos.append(file)
        
        if not missing_demos:
            self.log_result("Demo Files", "PASS", "All demo files present")
            return True
        else:
            self.log_result("Demo Files", "WARNING", f"Missing demo files: {', '.join(missing_demos)}")
            return False
    
    def run_all_checks(self) -> Dict:
        """Run all health checks"""
        print("🔍 Running Aictive Platform Health Check...\n")
        
        # Synchronous checks
        self.check_python_version()
        self.check_virtual_environment()
        self.check_dependencies()
        self.check_environment_variables()
        self.check_project_structure()
        self.check_demo_files()
        
        # Asynchronous checks
        async def run_async_checks():
            await self.check_database_connection()
            await self.check_claude_service()
            await self.check_api_endpoints()
        
        asyncio.run(run_async_checks())
        
        # Summary
        print(f"\n📊 Health Check Summary:")
        print(f"   ✅ Passed: {len([r for r in self.results if r['status'] == 'PASS'])}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        print(f"   ❌ Errors: {len(self.errors)}")
        
        if self.errors:
            print(f"\n❌ Critical Issues Found:")
            for error in self.errors:
                print(f"   - {error['check']}: {error['message']}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning['check']}: {warning['message']}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if not self.errors:
            print("   🎉 Your environment is ready! You can:")
            print("   - Run: python simple_demo.py")
            print("   - Start server: uvicorn main_secure:app --reload")
            print("   - Test workflows: python scripts/test_single_workflow.py")
        else:
            print("   🔧 Fix the critical issues above before proceeding")
        
        return {
            "passed": len([r for r in self.results if r['status'] == 'PASS']),
            "warnings": len(self.warnings),
            "errors": len(self.errors),
            "results": self.results
        }

def main():
    """Main function"""
    checker = HealthChecker()
    results = checker.run_all_checks()
    
    # Exit with error code if critical issues found
    if results["errors"] > 0:
        sys.exit(1)
    else:
        print("\n🚀 Ready to build amazing AI-powered workflows!")
        sys.exit(0)

if __name__ == "__main__":
    main() 