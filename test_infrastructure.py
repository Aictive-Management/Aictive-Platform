"""
Comprehensive Testing Infrastructure for Aictive Platform
Production-ready testing framework with fixtures, mocks, and utilities
"""

import asyncio
import json
import random
import uuid
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from faker import Faker
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from contextlib import asynccontextmanager

# Initialize Faker for test data generation
fake = Faker()

T = TypeVar('T')


@dataclass
class TestConfig:
    """Test configuration"""
    use_real_api: bool = False
    api_base_url: str = "http://localhost:8000"
    rentvine_base_url: str = "https://api.rentvine.com/v2"
    test_tenant_id: str = "test_tenant_123"
    seed: int = 42
    enable_logging: bool = True


class TestDataGenerator:
    """Generate realistic test data for all entities"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            Faker.seed(seed)
            random.seed(seed)
    
    def generate_property(self, property_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate test property data"""
        return {
            "id": property_id or str(uuid.uuid4()),
            "name": f"{fake.company()} {random.choice(['Apartments', 'Residences', 'Commons'])}",
            "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "zip": fake.zipcode()
            },
            "units": random.randint(1, 50),
            "type": random.choice(["single_family", "multi_family", "apartment_complex"]),
            "manager_id": str(uuid.uuid4()),
            "owner_id": str(uuid.uuid4()),
            "created_at": fake.date_time_between(start_date="-2y", end_date="now").isoformat(),
            "monthly_rent": random.randint(800, 3000),
            "occupied_units": random.randint(0, 50),
            "status": "active"
        }
    
    def generate_tenant(self, property_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate test tenant data"""
        return {
            "id": str(uuid.uuid4()),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "property_id": property_id or str(uuid.uuid4()),
            "unit_number": fake.building_number(),
            "lease_start": fake.date_between(start_date="-1y", end_date="today").isoformat(),
            "lease_end": fake.date_between(start_date="today", end_date="+1y").isoformat(),
            "monthly_rent": random.randint(800, 3000),
            "security_deposit": random.randint(800, 3000),
            "status": random.choice(["active", "pending", "past"]),
            "balance": random.uniform(-500, 500),
            "created_at": fake.date_time_between(start_date="-1y", end_date="now").isoformat()
        }
    
    def generate_work_order(self, property_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate test work order data"""
        categories = ["plumbing", "electrical", "hvac", "appliance", "general"]
        priorities = ["low", "medium", "high", "emergency"]
        statuses = ["open", "in_progress", "completed", "cancelled"]
        
        return {
            "id": str(uuid.uuid4()),
            "property_id": property_id or str(uuid.uuid4()),
            "unit_number": fake.building_number(),
            "tenant_id": str(uuid.uuid4()),
            "category": random.choice(categories),
            "priority": random.choice(priorities),
            "status": random.choice(statuses),
            "description": fake.text(max_nb_chars=200),
            "created_at": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
            "scheduled_date": fake.date_between(start_date="today", end_date="+7d").isoformat(),
            "assigned_to": fake.name() if random.random() > 0.3 else None,
            "estimated_cost": random.randint(50, 1000),
            "actual_cost": random.randint(50, 1000) if random.random() > 0.5 else None,
            "notes": fake.text(max_nb_chars=100) if random.random() > 0.5 else None
        }
    
    def generate_transaction(self, property_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate test transaction data"""
        types = ["rent", "deposit", "fee", "refund", "maintenance"]
        methods = ["check", "ach", "credit_card", "cash"]
        
        return {
            "id": str(uuid.uuid4()),
            "property_id": property_id or str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "type": random.choice(types),
            "amount": random.uniform(50, 3000),
            "date": fake.date_between(start_date="-90d", end_date="today").isoformat(),
            "method": random.choice(methods),
            "reference": fake.bothify(text="REF-####-????"),
            "description": fake.text(max_nb_chars=100),
            "status": random.choice(["pending", "completed", "failed"]),
            "created_at": fake.date_time_between(start_date="-90d", end_date="now").isoformat()
        }
    
    def generate_lease(self, property_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate test lease data"""
        start_date = fake.date_between(start_date="-1y", end_date="today")
        end_date = fake.date_between(start_date=start_date, end_date="+2y")
        
        return {
            "id": str(uuid.uuid4()),
            "property_id": property_id or str(uuid.uuid4()),
            "unit_number": fake.building_number(),
            "tenant_id": str(uuid.uuid4()),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "monthly_rent": random.randint(800, 3000),
            "security_deposit": random.randint(800, 3000),
            "pet_deposit": random.randint(0, 500),
            "status": random.choice(["active", "expired", "terminated"]),
            "auto_renew": random.choice([True, False]),
            "created_at": fake.date_time_between(start_date="-1y", end_date="now").isoformat()
        }
    
    def generate_workflow_execution(self) -> Dict[str, Any]:
        """Generate test workflow execution data"""
        workflow_types = [
            "emergency_maintenance",
            "lease_renewal",
            "move_in",
            "move_out",
            "rent_collection",
            "inspection"
        ]
        
        return {
            "id": str(uuid.uuid4()),
            "workflow_type": random.choice(workflow_types),
            "status": random.choice(["pending", "in_progress", "completed", "failed"]),
            "started_at": fake.date_time_between(start_date="-7d", end_date="now").isoformat(),
            "completed_at": fake.date_time_between(start_date="-1d", end_date="now").isoformat() if random.random() > 0.3 else None,
            "property_id": str(uuid.uuid4()),
            "initiated_by": fake.name(),
            "steps_completed": random.randint(0, 10),
            "total_steps": random.randint(5, 15),
            "error": fake.text(max_nb_chars=100) if random.random() < 0.1 else None
        }


class MockRentVineAPI:
    """Mock RentVine API for testing"""
    
    def __init__(self, generator: TestDataGenerator):
        self.generator = generator
        self.properties: Dict[str, Dict] = {}
        self.tenants: Dict[str, Dict] = {}
        self.work_orders: Dict[str, Dict] = {}
        self.transactions: List[Dict] = []
        self._generate_initial_data()
    
    def _generate_initial_data(self):
        """Generate initial test data"""
        # Generate 10 properties
        for _ in range(10):
            prop = self.generator.generate_property()
            self.properties[prop["id"]] = prop
            
            # Generate 5-10 tenants per property
            for _ in range(random.randint(5, 10)):
                tenant = self.generator.generate_tenant(prop["id"])
                self.tenants[tenant["id"]] = tenant
            
            # Generate 2-5 work orders per property
            for _ in range(random.randint(2, 5)):
                order = self.generator.generate_work_order(prop["id"])
                self.work_orders[order["id"]] = order
            
            # Generate 10-20 transactions per property
            for _ in range(random.randint(10, 20)):
                transaction = self.generator.generate_transaction(prop["id"])
                self.transactions.append(transaction)
    
    async def get_properties(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Mock get properties endpoint"""
        properties = list(self.properties.values())
        return {
            "data": properties[offset:offset + limit],
            "total": len(properties),
            "limit": limit,
            "offset": offset
        }
    
    async def get_property(self, property_id: str) -> Dict[str, Any]:
        """Mock get single property"""
        if property_id in self.properties:
            return {"data": self.properties[property_id]}
        raise httpx.HTTPStatusError("Property not found", request=Mock(), response=Mock(status_code=404))
    
    async def create_property(self, property_data: Dict) -> Dict[str, Any]:
        """Mock create property"""
        prop_id = str(uuid.uuid4())
        property_data["id"] = prop_id
        property_data["created_at"] = datetime.utcnow().isoformat()
        self.properties[prop_id] = property_data
        return {"data": property_data}
    
    async def get_work_orders(self, property_id: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Mock get work orders"""
        orders = list(self.work_orders.values())
        
        if property_id:
            orders = [o for o in orders if o["property_id"] == property_id]
        if status:
            orders = [o for o in orders if o["status"] == status]
        
        return {"data": orders}


class TestFixtures:
    """Reusable test fixtures"""
    
    @staticmethod
    @pytest.fixture
    async def mock_rentvine_client():
        """Mock RentVine API client"""
        generator = TestDataGenerator()
        mock_api = MockRentVineAPI(generator)
        
        client = AsyncMock()
        client.get_properties = mock_api.get_properties
        client.get_property = mock_api.get_property
        client.create_property = mock_api.create_property
        client.get_work_orders = mock_api.get_work_orders
        
        return client
    
    @staticmethod
    @pytest.fixture
    def test_property():
        """Generate test property"""
        generator = TestDataGenerator()
        return generator.generate_property()
    
    @staticmethod
    @pytest.fixture
    def test_tenant():
        """Generate test tenant"""
        generator = TestDataGenerator()
        return generator.generate_tenant()
    
    @staticmethod
    @pytest.fixture
    def test_work_order():
        """Generate test work order"""
        generator = TestDataGenerator()
        return generator.generate_work_order()
    
    @staticmethod
    @pytest.fixture
    async def mock_orchestration_engine():
        """Mock orchestration engine"""
        engine = AsyncMock()
        engine.execute_workflow = AsyncMock(return_value={
            "workflow_id": str(uuid.uuid4()),
            "status": "completed",
            "result": {"success": True}
        })
        return engine


class IntegrationTestBase:
    """Base class for integration tests"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.generator = TestDataGenerator(config.seed)
        self.created_resources: List[Tuple[str, str]] = []  # (resource_type, resource_id)
    
    async def setup(self):
        """Setup test environment"""
        pass
    
    async def teardown(self):
        """Cleanup test resources"""
        # Clean up any created resources
        for resource_type, resource_id in reversed(self.created_resources):
            try:
                await self._delete_resource(resource_type, resource_id)
            except Exception as e:
                print(f"Failed to cleanup {resource_type} {resource_id}: {e}")
    
    async def _delete_resource(self, resource_type: str, resource_id: str):
        """Delete a test resource"""
        # Implementation depends on actual API
        pass
    
    def track_resource(self, resource_type: str, resource_id: str):
        """Track resource for cleanup"""
        self.created_resources.append((resource_type, resource_id))


class LoadTestRunner:
    """Load testing framework"""
    
    def __init__(self, target_url: str, concurrent_users: int = 10):
        self.target_url = target_url
        self.concurrent_users = concurrent_users
        self.results: List[Dict[str, Any]] = []
    
    async def run_load_test(
        self,
        test_func: Callable,
        duration_seconds: int = 60,
        ramp_up_seconds: int = 10
    ):
        """Run load test with given parameters"""
        print(f"Starting load test: {self.concurrent_users} users, {duration_seconds}s duration")
        
        start_time = datetime.utcnow()
        tasks = []
        
        # Ramp up users gradually
        for i in range(self.concurrent_users):
            delay = (i / self.concurrent_users) * ramp_up_seconds
            task = asyncio.create_task(self._run_user_session(test_func, start_time, duration_seconds, delay))
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        # Analyze results
        self._analyze_results()
    
    async def _run_user_session(
        self,
        test_func: Callable,
        start_time: datetime,
        duration_seconds: int,
        initial_delay: float
    ):
        """Run a single user session"""
        await asyncio.sleep(initial_delay)
        
        session_results = []
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        while datetime.utcnow() < end_time:
            request_start = datetime.utcnow()
            
            try:
                await test_func()
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
            
            request_end = datetime.utcnow()
            duration = (request_end - request_start).total_seconds()
            
            session_results.append({
                "timestamp": request_start,
                "duration": duration,
                "success": success,
                "error": error
            })
            
            # Small delay between requests
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        self.results.extend(session_results)
    
    def _analyze_results(self):
        """Analyze load test results"""
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r["success"])
        failed_requests = total_requests - successful_requests
        
        durations = [r["duration"] for r in self.results if r["success"]]
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            p95_duration = sorted(durations)[int(len(durations) * 0.95)]
        else:
            avg_duration = min_duration = max_duration = p95_duration = 0
        
        print("\n=== Load Test Results ===")
        print(f"Total Requests: {total_requests}")
        print(f"Successful: {successful_requests} ({successful_requests/total_requests*100:.1f}%)")
        print(f"Failed: {failed_requests} ({failed_requests/total_requests*100:.1f}%)")
        print(f"Average Duration: {avg_duration:.3f}s")
        print(f"Min Duration: {min_duration:.3f}s")
        print(f"Max Duration: {max_duration:.3f}s")
        print(f"95th Percentile: {p95_duration:.3f}s")
        
        # Show errors if any
        errors = [r["error"] for r in self.results if r["error"]]
        if errors:
            print("\nTop Errors:")
            from collections import Counter
            error_counts = Counter(errors)
            for error, count in error_counts.most_common(5):
                print(f"  {error}: {count} times")


class ContractTest:
    """Contract testing utilities"""
    
    @staticmethod
    def validate_property_schema(data: Dict) -> bool:
        """Validate property data schema"""
        required_fields = ["id", "name", "address", "units", "type", "status"]
        address_fields = ["street", "city", "state", "zip"]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check address structure
        if not isinstance(data["address"], dict):
            raise ValueError("Address must be a dictionary")
        
        for field in address_fields:
            if field not in data["address"]:
                raise ValueError(f"Missing address field: {field}")
        
        # Validate data types
        if not isinstance(data["units"], int) or data["units"] < 1:
            raise ValueError("Units must be a positive integer")
        
        return True
    
    @staticmethod
    def validate_work_order_schema(data: Dict) -> bool:
        """Validate work order data schema"""
        required_fields = ["id", "property_id", "category", "priority", "status", "description"]
        valid_priorities = ["low", "medium", "high", "emergency"]
        valid_statuses = ["open", "in_progress", "completed", "cancelled"]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate enums
        if data["priority"] not in valid_priorities:
            raise ValueError(f"Invalid priority: {data['priority']}")
        
        if data["status"] not in valid_statuses:
            raise ValueError(f"Invalid status: {data['status']}")
        
        return True


# Example test scenarios
async def test_emergency_workflow():
    """Test emergency maintenance workflow"""
    generator = TestDataGenerator()
    
    # Generate test data
    property_data = generator.generate_property()
    emergency_order = generator.generate_work_order(property_data["id"])
    emergency_order["priority"] = "emergency"
    emergency_order["category"] = "plumbing"
    emergency_order["description"] = "Major water leak in unit 205"
    
    # Simulate workflow execution
    print(f"Testing emergency workflow for property: {property_data['name']}")
    print(f"Emergency: {emergency_order['description']}")
    
    # This would integrate with actual workflow engine
    workflow_result = {
        "workflow_id": str(uuid.uuid4()),
        "type": "emergency_maintenance",
        "status": "completed",
        "steps": [
            {"name": "Initial Assessment", "duration": "15 minutes", "completed": True},
            {"name": "Dispatch Technician", "duration": "30 minutes", "completed": True},
            {"name": "Repair Completion", "duration": "2 hours", "completed": True},
            {"name": "Documentation", "duration": "15 minutes", "completed": True}
        ],
        "total_duration": "3 hours",
        "cost": 850.00
    }
    
    print(f"Workflow completed in {workflow_result['total_duration']}")
    print(f"Total cost: ${workflow_result['cost']}")
    
    return workflow_result


if __name__ == "__main__":
    # Example usage
    config = TestConfig()
    generator = TestDataGenerator(config.seed)
    
    # Generate sample data
    print("Sample Property:")
    print(json.dumps(generator.generate_property(), indent=2))
    
    print("\nSample Work Order:")
    print(json.dumps(generator.generate_work_order(), indent=2))
    
    # Run emergency workflow test
    print("\n" + "="*50)
    print("Running Emergency Workflow Test")
    print("="*50)
    asyncio.run(test_emergency_workflow())