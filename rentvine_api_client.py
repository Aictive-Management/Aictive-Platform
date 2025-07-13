"""
Production-Ready RentVine API Client
Handles all interactions with RentVine property management system
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import jwt
from functools import wraps
import time

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')


class RentVineAPIError(Exception):
    """Base exception for RentVine API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RentVineAuthError(RentVineAPIError):
    """Authentication-related errors"""
    pass


class RentVineRateLimitError(RentVineAPIError):
    """Rate limit exceeded"""
    pass


class EntityType(Enum):
    """RentVine entity types"""
    PROPERTY = "properties"
    TENANT = "tenants"
    LEASE = "leases"
    WORK_ORDER = "workorders"
    TRANSACTION = "transactions"
    OWNER = "owners"
    VENDOR = "vendors"
    UNIT = "units"


@dataclass
class RentVineConfig:
    """Configuration for RentVine API client"""
    base_url: str
    api_key: str
    api_secret: str
    tenant_id: str
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 60
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes


@dataclass
class APIResponse(Generic[T]):
    """Standardized API response wrapper"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func):
        """Decorator for circuit breaker"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if (datetime.utcnow() - self.last_failure_time).seconds > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise RentVineAPIError("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit breaker closed after successful call")
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = datetime.utcnow()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(f"Circuit breaker opened after {self.failure_count} failures")
                
                raise e
        
        return wrapper


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int, per: int = 60):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
    
    async def acquire(self):
        """Acquire permission to make a request"""
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        self.allowance += time_passed * (self.rate / self.per)
        
        if self.allowance > self.rate:
            self.allowance = self.rate
        
        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
            logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
            self.allowance = 0.0
        else:
            self.allowance -= 1.0


class RentVineAPIClient:
    """Production-ready RentVine API client"""
    
    def __init__(self, config: RentVineConfig):
        self.config = config
        self.session: Optional[httpx.AsyncClient] = None
        self.auth_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "User-Agent": "Aictive-Platform/2.0",
                "X-Tenant-ID": self.config.tenant_id
            }
        )
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    async def authenticate(self) -> str:
        """Authenticate with RentVine API"""
        try:
            payload = {
                "api_key": self.config.api_key,
                "api_secret": self.config.api_secret,
                "tenant_id": self.config.tenant_id
            }
            
            response = await self.session.post("/auth/token", json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.auth_token = data["access_token"]
            
            # Decode token to get expiration
            token_data = jwt.decode(self.auth_token, options={"verify_signature": False})
            self.token_expires = datetime.fromtimestamp(token_data["exp"])
            
            logger.info(f"Successfully authenticated with RentVine, token expires at {self.token_expires}")
            return self.auth_token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Authentication failed: {e.response.status_code} - {e.response.text}")
            raise RentVineAuthError(f"Authentication failed: {e.response.text}", e.response.status_code)
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}")
            raise RentVineAuthError(f"Authentication error: {str(e)}")
    
    async def ensure_authenticated(self):
        """Ensure we have a valid authentication token"""
        if not self.auth_token or not self.token_expires:
            await self.authenticate()
        elif datetime.utcnow() >= self.token_expires - timedelta(minutes=5):
            logger.info("Token expiring soon, refreshing...")
            await self.authenticate()
    
    def _get_cache_key(self, method: str, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key"""
        param_str = json.dumps(params, sort_keys=True) if params else ""
        return f"{method}:{url}:{param_str}"
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if not self.config.enable_caching:
            return None
        
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.utcnow() - timestamp).seconds < self.config.cache_ttl:
                logger.debug(f"Cache hit for {key}")
                return data
            else:
                del self._cache[key]
        
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Set data in cache"""
        if self.config.enable_caching:
            self._cache[key] = (data, datetime.utcnow())
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError))
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """Make HTTP request with retry logic"""
        await self.ensure_authenticated()
        await self.rate_limiter.acquire()
        
        # Check cache for GET requests
        cache_key = self._get_cache_key(method, endpoint, params)
        if method == "GET":
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return APIResponse(
                    success=True,
                    data=cached_data,
                    metadata={"cache": True},
                    correlation_id=correlation_id
                )
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "X-Correlation-ID": correlation_id or str(datetime.utcnow().timestamp())
        }
        
        try:
            response = await self.session.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
                headers=headers
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited, retry after {retry_after} seconds")
                raise RentVineRateLimitError(f"Rate limited, retry after {retry_after}s", 429)
            
            response.raise_for_status()
            
            data = response.json()
            
            # Cache successful GET requests
            if method == "GET":
                self._set_cache(cache_key, data)
            
            return APIResponse(
                success=True,
                data=data,
                metadata={
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                },
                correlation_id=headers["X-Correlation-ID"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return APIResponse(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
                metadata={"status_code": e.response.status_code},
                correlation_id=headers["X-Correlation-ID"]
            )
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return APIResponse(
                success=False,
                error=str(e),
                correlation_id=headers["X-Correlation-ID"]
            )
    
    # Entity-specific methods
    
    async def get_properties(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict] = None
    ) -> APIResponse[List[Dict]]:
        """Get properties with pagination"""
        params = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        
        return await self._make_request("GET", "/properties", params=params)
    
    async def get_property(self, property_id: str) -> APIResponse[Dict]:
        """Get single property by ID"""
        return await self._make_request("GET", f"/properties/{property_id}")
    
    async def create_property(self, property_data: Dict) -> APIResponse[Dict]:
        """Create new property"""
        return await self._make_request("POST", "/properties", json_data=property_data)
    
    async def update_property(self, property_id: str, updates: Dict) -> APIResponse[Dict]:
        """Update property"""
        return await self._make_request("PUT", f"/properties/{property_id}", json_data=updates)
    
    async def get_tenants(
        self,
        property_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse[List[Dict]]:
        """Get tenants with optional property filter"""
        params = {"limit": limit, "offset": offset}
        if property_id:
            params["property_id"] = property_id
        
        return await self._make_request("GET", "/tenants", params=params)
    
    async def get_tenant(self, tenant_id: str) -> APIResponse[Dict]:
        """Get single tenant by ID"""
        return await self._make_request("GET", f"/tenants/{tenant_id}")
    
    async def get_work_orders(
        self,
        property_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse[List[Dict]]:
        """Get work orders with filters"""
        params = {"limit": limit, "offset": offset}
        if property_id:
            params["property_id"] = property_id
        if status:
            params["status"] = status
        
        return await self._make_request("GET", "/workorders", params=params)
    
    async def create_work_order(self, work_order_data: Dict) -> APIResponse[Dict]:
        """Create new work order"""
        return await self._make_request("POST", "/workorders", json_data=work_order_data)
    
    async def update_work_order(self, work_order_id: str, updates: Dict) -> APIResponse[Dict]:
        """Update work order"""
        return await self._make_request("PUT", f"/workorders/{work_order_id}", json_data=updates)
    
    async def get_transactions(
        self,
        property_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse[List[Dict]]:
        """Get financial transactions"""
        params = {"limit": limit, "offset": offset}
        if property_id:
            params["property_id"] = property_id
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        
        return await self._make_request("GET", "/transactions", params=params)
    
    # Bulk operations
    
    async def bulk_sync_properties(self) -> APIResponse[Dict]:
        """Sync all properties in batches"""
        all_properties = []
        offset = 0
        limit = 100
        
        while True:
            response = await self.get_properties(limit=limit, offset=offset)
            if not response.success:
                return response
            
            properties = response.data
            if not properties:
                break
            
            all_properties.extend(properties)
            offset += limit
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return APIResponse(
            success=True,
            data={"properties": all_properties, "count": len(all_properties)},
            metadata={"sync_time": datetime.utcnow().isoformat()}
        )
    
    # Health check
    
    async def health_check(self) -> APIResponse[Dict]:
        """Check API health status"""
        try:
            response = await self._make_request("GET", "/health")
            return response
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Health check failed: {str(e)}"
            )


# Example usage and testing
async def demo_rentvine_client():
    """Demonstrate RentVine API client usage"""
    config = RentVineConfig(
        base_url="https://api.rentvine.com/v2",
        api_key="your_api_key",
        api_secret="your_api_secret",
        tenant_id="your_tenant_id"
    )
    
    async with RentVineAPIClient(config) as client:
        # Health check
        health = await client.health_check()
        print(f"API Health: {health.success}")
        
        # Get properties
        properties = await client.get_properties(limit=10)
        if properties.success:
            print(f"Found {len(properties.data)} properties")
        
        # Get work orders
        work_orders = await client.get_work_orders(status="open")
        if work_orders.success:
            print(f"Found {len(work_orders.data)} open work orders")


if __name__ == "__main__":
    # This would be used for testing
    # asyncio.run(demo_rentvine_client())
    pass