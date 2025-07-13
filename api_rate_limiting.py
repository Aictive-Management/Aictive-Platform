"""
Advanced API Rate Limiting System for Aictive Platform
Implements per-tenant rate limiting with Redis backend, multiple algorithms,
and real-time monitoring capabilities.
"""
import asyncio
import time
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import hashlib
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """Supported rate limiting algorithms"""
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an endpoint"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 100
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    bypass_for_trusted: bool = True
    alert_threshold: float = 0.8  # Alert when 80% of limit reached
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        data['algorithm'] = self.algorithm.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RateLimitConfig':
        """Create from dictionary"""
        data['algorithm'] = RateLimitAlgorithm(data.get('algorithm', 'sliding_window'))
        return cls(**data)


class RateLimitStore:
    """Redis-backed rate limit storage"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self._local_cache = {}
        self._cache_ttl = 5  # Local cache TTL in seconds
        
    async def increment_sliding_window(
        self, 
        key: str, 
        window_seconds: int,
        limit: int
    ) -> Tuple[int, int]:
        """
        Implement sliding window rate limiting
        Returns: (current_count, remaining_limit)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Count requests in window
        pipe.zcount(key, window_start, now)
        
        # Set expiry
        pipe.expire(key, window_seconds + 1)
        
        results = await pipe.execute()
        current_count = results[2]
        
        return int(current_count), max(0, limit - int(current_count))
    
    async def consume_token_bucket(
        self,
        key: str,
        capacity: int,
        refill_rate: float,
        tokens_requested: int = 1
    ) -> Tuple[bool, int]:
        """
        Implement token bucket algorithm
        Returns: (allowed, tokens_remaining)
        """
        bucket_key = f"{key}:bucket"
        timestamp_key = f"{key}:timestamp"
        
        now = time.time()
        
        # Lua script for atomic token bucket operations
        lua_script = """
        local bucket_key = KEYS[1]
        local timestamp_key = KEYS[2]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local tokens_requested = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        local tokens = redis.call('get', bucket_key)
        local last_refill = redis.call('get', timestamp_key)
        
        if not tokens then
            tokens = capacity
            last_refill = now
        else
            tokens = tonumber(tokens)
            last_refill = tonumber(last_refill)
            
            -- Calculate tokens to add based on time elapsed
            local elapsed = now - last_refill
            local tokens_to_add = elapsed * refill_rate
            tokens = math.min(capacity, tokens + tokens_to_add)
        end
        
        if tokens >= tokens_requested then
            tokens = tokens - tokens_requested
            redis.call('set', bucket_key, tokens)
            redis.call('set', timestamp_key, now)
            redis.call('expire', bucket_key, 3600)
            redis.call('expire', timestamp_key, 3600)
            return {1, tokens}
        else
            redis.call('set', bucket_key, tokens)
            redis.call('set', timestamp_key, now)
            redis.call('expire', bucket_key, 3600)
            redis.call('expire', timestamp_key, 3600)
            return {0, tokens}
        end
        """
        
        result = await self.redis.eval(
            lua_script,
            2,
            bucket_key,
            timestamp_key,
            capacity,
            refill_rate,
            tokens_requested,
            now
        )
        
        return bool(result[0]), int(result[1])
    
    async def get_usage_stats(self, pattern: str) -> Dict[str, Any]:
        """Get usage statistics for rate limit keys"""
        stats = defaultdict(lambda: {"requests": 0, "unique_keys": set()})
        
        # Scan for matching keys
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, 
                match=pattern,
                count=100
            )
            
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(":")
                if len(parts) >= 3:
                    tenant = parts[1]
                    endpoint = parts[2]
                    
                    # Get request count
                    if "bucket" not in key_str:
                        count = await self.redis.zcard(key_str)
                        stats[tenant]["requests"] += count
                        stats[tenant]["unique_keys"].add(endpoint)
            
            if cursor == 0:
                break
        
        # Convert sets to counts
        for tenant in stats:
            stats[tenant]["unique_endpoints"] = len(stats[tenant]["unique_keys"])
            del stats[tenant]["unique_keys"]
        
        return dict(stats)


class RateLimiter:
    """Main rate limiting service"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.store = None
        self.endpoint_configs: Dict[str, RateLimitConfig] = {}
        self.trusted_sources: set = set()
        self.alert_callbacks: List[callable] = []
        self._init_default_configs()
        
    def _init_default_configs(self):
        """Initialize default rate limit configurations"""
        # API endpoint specific limits
        self.endpoint_configs = {
            # Public endpoints - stricter limits
            "/api/v1/auth/login": RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=50,
                burst_size=5
            ),
            "/api/v1/auth/register": RateLimitConfig(
                requests_per_minute=5,
                requests_per_hour=20,
                burst_size=2
            ),
            
            # Email processing - moderate limits
            "/api/v1/emails/process": RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=500,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                burst_size=50
            ),
            "/api/v1/emails/classify": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000
            ),
            
            # Webhook endpoints - higher limits
            "/api/v1/webhooks/*": RateLimitConfig(
                requests_per_minute=120,
                requests_per_hour=5000,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                burst_size=200
            ),
            
            # Admin endpoints - relaxed limits for trusted sources
            "/api/v1/admin/*": RateLimitConfig(
                requests_per_minute=100,
                requests_per_hour=2000,
                bypass_for_trusted=True
            ),
            
            # Default for unspecified endpoints
            "default": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000
            )
        }
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.store = RateLimitStore(self.redis_client)
        logger.info("Rate limiter initialized with Redis backend")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def add_trusted_source(self, identifier: str):
        """Add a trusted source that can bypass rate limits"""
        self.trusted_sources.add(identifier)
        logger.info(f"Added trusted source: {identifier}")
    
    def remove_trusted_source(self, identifier: str):
        """Remove a trusted source"""
        self.trusted_sources.discard(identifier)
        logger.info(f"Removed trusted source: {identifier}")
    
    def update_endpoint_config(self, endpoint: str, config: RateLimitConfig):
        """Update rate limit configuration for an endpoint"""
        self.endpoint_configs[endpoint] = config
        logger.info(f"Updated rate limit config for {endpoint}")
    
    def add_alert_callback(self, callback: callable):
        """Add callback for rate limit alerts"""
        self.alert_callbacks.append(callback)
    
    async def _trigger_alerts(self, identifier: str, endpoint: str, usage_percent: float):
        """Trigger alert callbacks when threshold reached"""
        alert_data = {
            "identifier": identifier,
            "endpoint": endpoint,
            "usage_percent": usage_percent,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Rate limit usage at {usage_percent:.1%} for {identifier} on {endpoint}"
        }
        
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def _get_endpoint_config(self, path: str) -> RateLimitConfig:
        """Get rate limit config for endpoint"""
        # Direct match
        if path in self.endpoint_configs:
            return self.endpoint_configs[path]
        
        # Wildcard match
        for pattern, config in self.endpoint_configs.items():
            if "*" in pattern:
                prefix = pattern.rstrip("*")
                if path.startswith(prefix):
                    return config
        
        # Default
        return self.endpoint_configs.get("default", RateLimitConfig())
    
    def _get_identifier(self, request: Request) -> str:
        """Extract identifier from request (tenant_id, API key, or IP)"""
        # Try to get tenant_id from various sources
        tenant_id = None
        
        # From JWT token
        if hasattr(request.state, "token_data"):
            tenant_id = getattr(request.state.token_data, "tenant_id", None)
        
        # From API key
        if not tenant_id and hasattr(request.state, "api_key"):
            tenant_id = request.state.api_key
        
        # From headers
        if not tenant_id:
            tenant_id = request.headers.get("X-Tenant-ID")
        
        # From query params
        if not tenant_id:
            tenant_id = request.query_params.get("tenant_id")
        
        # Fall back to IP address
        if not tenant_id:
            # Get real IP considering proxies
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                tenant_id = forwarded_for.split(",")[0].strip()
            else:
                tenant_id = request.client.host if request.client else "unknown"
        
        return tenant_id
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if request is within rate limits
        Raises HTTPException if limit exceeded
        """
        identifier = self._get_identifier(request)
        endpoint = request.url.path
        config = self._get_endpoint_config(endpoint)
        
        # Check if source is trusted and bypass is enabled
        if config.bypass_for_trusted and identifier in self.trusted_sources:
            logger.debug(f"Bypassing rate limit for trusted source: {identifier}")
            return
        
        # Generate rate limit keys
        base_key = f"ratelimit:{identifier}:{endpoint}"
        
        # Check limits based on algorithm
        if config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            # Check per-minute limit
            minute_key = f"{base_key}:minute"
            count, remaining = await self.store.increment_sliding_window(
                minute_key, 60, config.requests_per_minute
            )
            
            # Check if we should alert
            usage_percent = count / config.requests_per_minute
            if usage_percent >= config.alert_threshold:
                await self._trigger_alerts(identifier, endpoint, usage_percent)
            
            if remaining <= 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(config.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + 60)
                    }
                )
            
            # Check hourly limit
            hour_key = f"{base_key}:hour"
            hour_count, hour_remaining = await self.store.increment_sliding_window(
                hour_key, 3600, config.requests_per_hour
            )
            
            if hour_remaining <= 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Hourly rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(config.requests_per_hour),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + 3600)
                    }
                )
            
            # Add rate limit headers to response
            request.state.rate_limit_headers = {
                "X-RateLimit-Limit": str(config.requests_per_minute),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(time.time()) + 60)
            }
            
        elif config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            # Token bucket with burst support
            allowed, tokens_remaining = await self.store.consume_token_bucket(
                base_key,
                capacity=config.burst_size,
                refill_rate=config.requests_per_minute / 60.0
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded - token bucket empty",
                    headers={
                        "X-RateLimit-Limit": str(config.requests_per_minute),
                        "X-RateLimit-Remaining": str(tokens_remaining),
                        "X-RateLimit-Reset": str(int(time.time()) + 60)
                    }
                )
            
            request.state.rate_limit_headers = {
                "X-RateLimit-Limit": str(config.burst_size),
                "X-RateLimit-Remaining": str(tokens_remaining),
                "X-RateLimit-Reset": str(int(time.time()) + 60)
            }
    
    async def get_current_usage(self, identifier: str) -> Dict[str, Any]:
        """Get current rate limit usage for an identifier"""
        usage = {}
        
        # Get usage for all endpoints
        pattern = f"ratelimit:{identifier}:*"
        stats = await self.store.get_usage_stats(pattern)
        
        return {
            "identifier": identifier,
            "usage_by_endpoint": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def reset_limits(self, identifier: str, endpoint: Optional[str] = None):
        """Reset rate limits for an identifier"""
        if endpoint:
            pattern = f"ratelimit:{identifier}:{endpoint}:*"
        else:
            pattern = f"ratelimit:{identifier}:*"
        
        # Find and delete all matching keys
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern)
            if keys:
                deleted += await self.redis_client.delete(*keys)
            if cursor == 0:
                break
        
        logger.info(f"Reset rate limits for {identifier}, deleted {deleted} keys")
        return deleted


# Middleware for FastAPI
class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        self.app = app
        self.rate_limiter = rate_limiter
        
    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        excluded_paths = ["/health", "/metrics", "/docs", "/openapi.json"]
        if request.url.path in excluded_paths:
            return await call_next(request)
        
        try:
            # Check rate limit
            await self.rate_limiter.check_rate_limit(request)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers if available
            if hasattr(request.state, "rate_limit_headers"):
                for header, value in request.state.rate_limit_headers.items():
                    response.headers[header] = value
            
            return response
            
        except HTTPException as e:
            # Return rate limit error response
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers
            )


# Monitoring and metrics
class RateLimitMonitor:
    """Monitor rate limit usage and provide metrics"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.metrics: Dict[str, Any] = defaultdict(lambda: {
            "total_requests": 0,
            "blocked_requests": 0,
            "unique_identifiers": set(),
            "alerts_triggered": 0
        })
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect rate limit metrics"""
        # Get overall usage stats
        pattern = "ratelimit:*"
        usage_stats = await self.rate_limiter.store.get_usage_stats(pattern)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tenants": len(usage_stats),
            "usage_by_tenant": usage_stats,
            "trusted_sources": list(self.rate_limiter.trusted_sources),
            "endpoint_configs": {
                endpoint: config.to_dict() 
                for endpoint, config in self.rate_limiter.endpoint_configs.items()
            }
        }
    
    async def generate_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate rate limit usage report for time period"""
        # This would integrate with your logging/metrics system
        # For now, return current snapshot
        metrics = await self.collect_metrics()
        
        return {
            "report_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "metrics": metrics,
            "recommendations": self._generate_recommendations(metrics)
        }
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on usage patterns"""
        recommendations = []
        
        # Analyze usage patterns
        for tenant, usage in metrics.get("usage_by_tenant", {}).items():
            if usage["requests"] > 1000:
                recommendations.append(
                    f"Consider increasing rate limits for tenant {tenant} - high usage detected"
                )
        
        return recommendations


# Example usage and integration
async def setup_rate_limiting(app, redis_url: str = "redis://localhost:6379"):
    """Setup rate limiting for FastAPI app"""
    # Initialize rate limiter
    rate_limiter = RateLimiter(redis_url)
    await rate_limiter.initialize()
    
    # Add middleware
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
    
    # Setup monitoring
    monitor = RateLimitMonitor(rate_limiter)
    
    # Add alert callback example
    async def log_rate_limit_alert(alert_data: Dict[str, Any]):
        logger.warning(f"Rate limit alert: {alert_data}")
    
    rate_limiter.add_alert_callback(log_rate_limit_alert)
    
    # Add cleanup on shutdown
    @app.on_event("shutdown")
    async def shutdown():
        await rate_limiter.close()
    
    return rate_limiter, monitor