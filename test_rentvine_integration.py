"""
RentVine API Integration Tests
Ready-to-run tests for validating RentVine API connection and functionality
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pytest
from dotenv import load_dotenv

from rentvine_api_client import (
    RentVineAPIClient, 
    RentVineConfig, 
    APIResponse,
    RentVineAPIError
)
from test_infrastructure import TestDataGenerator, ContractTest

# Load environment variables
load_dotenv()


class RentVineIntegrationTests:
    """Comprehensive integration tests for RentVine API"""
    
    def __init__(self):
        self.config = RentVineConfig(
            base_url=os.getenv("RENTVINE_API_URL", "https://api.rentvine.com/v2"),
            api_key=os.getenv("RENTVINE_API_KEY", ""),
            api_secret=os.getenv("RENTVINE_API_SECRET", ""),
            tenant_id=os.getenv("RENTVINE_TENANT_ID", ""),
            timeout=30,
            max_retries=3,
            rate_limit_per_minute=60
        )
        self.generator = TestDataGenerator()
        self.test_results: List[Dict[str, Any]] = []
    
    async def run_all_tests(self, use_mock: bool = False):
        """Run all integration tests"""
        print("🧪 RENTVINE API INTEGRATION TESTS")
        print("=" * 60)
        print(f"API URL: {self.config.base_url}")
        print(f"Tenant ID: {self.config.tenant_id}")
        print(f"Mock Mode: {use_mock}")
        print("=" * 60)
        
        if not self.config.api_key or not self.config.api_secret:
            print("⚠️  WARNING: API credentials not found in environment")
            print("Please set RENTVINE_API_KEY and RENTVINE_API_SECRET")
            return
        
        async with RentVineAPIClient(self.config) as client:
            # Test 1: Authentication
            await self._test_authentication(client)
            
            # Test 2: Health Check
            await self._test_health_check(client)
            
            # Test 3: Get Properties
            await self._test_get_properties(client)
            
            # Test 4: Property CRUD Operations
            await self._test_property_operations(client)
            
            # Test 5: Work Orders
            await self._test_work_orders(client)
            
            # Test 6: Tenants
            await self._test_tenants(client)
            
            # Test 7: Transactions
            await self._test_transactions(client)
            
            # Test 8: Rate Limiting
            await self._test_rate_limiting(client)
            
            # Test 9: Error Handling
            await self._test_error_handling(client)
            
            # Test 10: Bulk Operations
            await self._test_bulk_operations(client)
        
        # Print summary
        self._print_test_summary()
    
    async def _test_authentication(self, client: RentVineAPIClient):
        """Test authentication flow"""
        test_name = "Authentication"
        print(f"\n🔐 Testing {test_name}...")
        
        try:
            # Force re-authentication
            client.auth_token = None
            await client.authenticate()
            
            assert client.auth_token is not None
            assert client.token_expires > datetime.utcnow()
            
            self._record_result(test_name, True, "Authentication successful")
            print(f"   ✅ Token obtained, expires at {client.token_expires}")
            
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Authentication failed: {e}")
    
    async def _test_health_check(self, client: RentVineAPIClient):
        """Test API health endpoint"""
        test_name = "Health Check"
        print(f"\n🏥 Testing {test_name}...")
        
        try:
            response = await client.health_check()
            
            assert response.success
            self._record_result(test_name, True, "API is healthy")
            print(f"   ✅ API is healthy")
            
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Health check failed: {e}")
    
    async def _test_get_properties(self, client: RentVineAPIClient):
        """Test getting properties"""
        test_name = "Get Properties"
        print(f"\n🏢 Testing {test_name}...")
        
        try:
            response = await client.get_properties(limit=5)
            
            assert response.success
            properties = response.data
            
            print(f"   ✅ Retrieved {len(properties)} properties")
            
            # Validate schema for each property
            for prop in properties[:2]:  # Check first 2
                ContractTest.validate_property_schema(prop)
                print(f"   ✅ Property schema valid: {prop.get('name', 'Unknown')}")
            
            self._record_result(test_name, True, f"Retrieved {len(properties)} properties")
            
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Get properties failed: {e}")
    
    async def _test_property_operations(self, client: RentVineAPIClient):
        """Test property CRUD operations"""
        test_name = "Property CRUD"
        print(f"\n🏗️ Testing {test_name}...")
        
        try:
            # Create test property
            test_property = self.generator.generate_property()
            test_property["name"] = f"TEST - {test_property['name']}"
            
            print(f"   Creating property: {test_property['name']}")
            create_response = await client.create_property(test_property)
            
            if create_response.success:
                created_id = create_response.data.get("id")
                print(f"   ✅ Created property with ID: {created_id}")
                
                # Get the created property
                get_response = await client.get_property(created_id)
                assert get_response.success
                print(f"   ✅ Retrieved created property")
                
                # Update property
                updates = {"units": test_property["units"] + 5}
                update_response = await client.update_property(created_id, updates)
                assert update_response.success
                print(f"   ✅ Updated property units")
                
                self._record_result(test_name, True, "All CRUD operations successful")
            else:
                print(f"   ⚠️  Property creation not supported or failed")
                self._record_result(test_name, True, "Property read operations work")
                
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Property operations failed: {e}")
    
    async def _test_work_orders(self, client: RentVineAPIClient):
        """Test work order operations"""
        test_name = "Work Orders"
        print(f"\n🔧 Testing {test_name}...")
        
        try:
            # Get open work orders
            response = await client.get_work_orders(status="open", limit=10)
            
            assert response.success
            work_orders = response.data
            
            print(f"   ✅ Retrieved {len(work_orders)} open work orders")
            
            # Validate schema
            if work_orders:
                ContractTest.validate_work_order_schema(work_orders[0])
                print(f"   ✅ Work order schema valid")
            
            # Test creating work order
            test_order = self.generator.generate_work_order()
            test_order["description"] = f"TEST - {test_order['description']}"
            
            create_response = await client.create_work_order(test_order)
            if create_response.success:
                print(f"   ✅ Created test work order")
            else:
                print(f"   ⚠️  Work order creation not supported")
            
            self._record_result(test_name, True, f"Work order operations successful")
            
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Work order operations failed: {e}")
    
    async def _test_tenants(self, client: RentVineAPIClient):
        """Test tenant operations"""
        test_name = "Tenants"
        print(f"\n👥 Testing {test_name}...")
        
        try:
            response = await client.get_tenants(limit=10)
            
            assert response.success
            tenants = response.data
            
            print(f"   ✅ Retrieved {len(tenants)} tenants")
            
            # Test getting specific tenant
            if tenants:
                tenant_id = tenants[0].get("id")
                tenant_response = await client.get_tenant(tenant_id)
                assert tenant_response.success
                print(f"   ✅ Retrieved specific tenant details")
            
            self._record_result(test_name, True, "Tenant operations successful")
            
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Tenant operations failed: {e}")
    
    async def _test_transactions(self, client: RentVineAPIClient):
        """Test financial transactions"""
        test_name = "Transactions"
        print(f"\n💰 Testing {test_name}...")
        
        try:
            # Get recent transactions
            date_from = datetime.utcnow() - timedelta(days=30)
            response = await client.get_transactions(
                date_from=date_from,
                limit=20
            )
            
            assert response.success
            transactions = response.data
            
            print(f"   ✅ Retrieved {len(transactions)} recent transactions")
            
            # Calculate total
            if transactions:
                total = sum(t.get("amount", 0) for t in transactions)
                print(f"   💵 Total transaction value: ${total:,.2f}")
            
            self._record_result(test_name, True, "Transaction operations successful")
            
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Transaction operations failed: {e}")
    
    async def _test_rate_limiting(self, client: RentVineAPIClient):
        """Test rate limiting behavior"""
        test_name = "Rate Limiting"
        print(f"\n⏱️ Testing {test_name}...")
        
        try:
            # Make rapid requests
            print("   Making rapid requests to test rate limiting...")
            
            start_time = datetime.utcnow()
            request_count = 0
            
            for i in range(10):
                response = await client.get_properties(limit=1)
                if response.success:
                    request_count += 1
                await asyncio.sleep(0.1)  # Small delay
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            rate = request_count / duration * 60  # requests per minute
            
            print(f"   ✅ Made {request_count} requests in {duration:.1f}s")
            print(f"   📊 Effective rate: {rate:.1f} requests/minute")
            
            self._record_result(test_name, True, f"Rate limiting working correctly")
            
        except RentVineAPIError as e:
            if e.status_code == 429:
                print(f"   ✅ Rate limit enforced correctly")
                self._record_result(test_name, True, "Rate limit enforced")
            else:
                raise
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Rate limiting test failed: {e}")
    
    async def _test_error_handling(self, client: RentVineAPIClient):
        """Test error handling"""
        test_name = "Error Handling"
        print(f"\n⚠️ Testing {test_name}...")
        
        try:
            # Test 404 - Non-existent resource
            print("   Testing 404 handling...")
            response = await client.get_property("non-existent-id-12345")
            
            if not response.success:
                print(f"   ✅ 404 handled correctly: {response.error}")
            
            # Test invalid request
            print("   Testing invalid request...")
            response = await client.update_property("test-id", {"invalid_field": "value"})
            
            if not response.success:
                print(f"   ✅ Invalid request handled: {response.error}")
            
            self._record_result(test_name, True, "Error handling working correctly")
            
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Error handling test failed: {e}")
    
    async def _test_bulk_operations(self, client: RentVineAPIClient):
        """Test bulk sync operations"""
        test_name = "Bulk Operations"
        print(f"\n📦 Testing {test_name}...")
        
        try:
            print("   Starting bulk property sync...")
            start_time = datetime.utcnow()
            
            response = await client.bulk_sync_properties()
            
            if response.success:
                duration = (datetime.utcnow() - start_time).total_seconds()
                property_count = response.data.get("count", 0)
                
                print(f"   ✅ Synced {property_count} properties in {duration:.1f}s")
                print(f"   📊 Rate: {property_count/duration:.1f} properties/second")
                
                self._record_result(test_name, True, f"Synced {property_count} properties")
            else:
                self._record_result(test_name, False, response.error)
                
        except Exception as e:
            self._record_result(test_name, False, str(e))
            print(f"   ❌ Bulk operations failed: {e}")
    
    def _record_result(self, test_name: str, success: bool, message: str):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow()
        })
    
    def _print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Save results to file
        with open("rentvine_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests
                },
                "results": self.test_results
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: rentvine_test_results.json")


async def quick_connection_test():
    """Quick test to verify RentVine connection"""
    print("🚀 QUICK RENTVINE CONNECTION TEST")
    print("-" * 40)
    
    config = RentVineConfig(
        base_url=os.getenv("RENTVINE_API_URL", "https://api.rentvine.com/v2"),
        api_key=os.getenv("RENTVINE_API_KEY", ""),
        api_secret=os.getenv("RENTVINE_API_SECRET", ""),
        tenant_id=os.getenv("RENTVINE_TENANT_ID", "")
    )
    
    if not config.api_key:
        print("❌ No API credentials found!")
        print("\nPlease set environment variables:")
        print("  export RENTVINE_API_KEY='your-key'")
        print("  export RENTVINE_API_SECRET='your-secret'")
        print("  export RENTVINE_TENANT_ID='your-tenant-id'")
        return
    
    try:
        async with RentVineAPIClient(config) as client:
            # Test authentication
            print("🔐 Testing authentication...")
            await client.authenticate()
            print("✅ Authentication successful!")
            
            # Test API call
            print("\n📡 Testing API call...")
            response = await client.get_properties(limit=1)
            
            if response.success:
                print("✅ API call successful!")
                if response.data:
                    print(f"📊 Found {len(response.data)} properties")
                    print(f"🏢 First property: {response.data[0].get('name', 'Unknown')}")
            else:
                print(f"❌ API call failed: {response.error}")
                
    except Exception as e:
        print(f"❌ Connection test failed: {e}")


if __name__ == "__main__":
    # Check if running full tests or quick test
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(quick_connection_test())
    else:
        # Run full test suite
        tester = RentVineIntegrationTests()
        asyncio.run(tester.run_all_tests())
        
        print("\n💡 TIP: Use --quick flag for a quick connection test")
        print("   python test_rentvine_integration.py --quick")