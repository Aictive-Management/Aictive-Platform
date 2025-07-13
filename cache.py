"""
Caching layer for Aictive Platform
Following SuperClaude performance optimization standards
"""
import json
import hashlib
from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import logging

from config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """In-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired())
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if datetime.utcnow() < entry["expires_at"]:
                    logger.debug(f"Cache hit for key: {key[:20]}...")
                    return entry["value"]
                else:
                    # Expired, remove it
                    del self._cache[key]
                    logger.debug(f"Cache expired for key: {key[:20]}...")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> None:
        """Set value in cache with TTL"""
        if ttl_seconds is None:
            ttl_seconds = settings.cache_ttl_seconds
            
        async with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds),
                "created_at": datetime.utcnow()
            }
            logger.debug(f"Cache set for key: {key[:20]}... (TTL: {ttl_seconds}s)")
    
    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted for key: {key[:20]}...")
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    async def _cleanup_expired(self) -> None:
        """Background task to cleanup expired entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                async with self._lock:
                    now = datetime.utcnow()
                    expired_keys = [
                        key for key, entry in self._cache.items()
                        if now >= entry["expires_at"]
                    ]
                    for key in expired_keys:
                        del self._cache[key]
                    
                    if expired_keys:
                        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")

# Global cache instance
cache_manager = CacheManager()

def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key from prefix and parameters"""
    # Sort kwargs for consistent key generation
    sorted_params = sorted(kwargs.items())
    param_str = json.dumps(sorted_params, sort_keys=True)
    
    # Create hash for long keys
    if len(param_str) > 100:
        param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]
        return f"{prefix}:{param_hash}"
    else:
        return f"{prefix}:{param_str}"

def cached(prefix: str, ttl_seconds: Optional[int] = None):
    """Decorator for caching async function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(prefix, args=str(args), kwargs=str(kwargs))
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator

class ClaudeResponseCache:
    """Specialized cache for Claude API responses"""
    
    @staticmethod
    def should_cache_classification(category: str, confidence: float) -> bool:
        """Determine if classification should be cached"""
        # Cache high-confidence classifications
        if confidence >= 0.9:
            return True
        
        # Always cache certain categories
        cacheable_categories = ["payment", "lease", "general"]
        if category in cacheable_categories and confidence >= 0.8:
            return True
            
        return False
    
    @staticmethod
    async def cache_classification(
        email_hash: str,
        classification: Dict[str, Any],
        ttl_override: Optional[int] = None
    ) -> None:
        """Cache email classification with smart TTL"""
        # Determine TTL based on classification
        if not ttl_override:
            category = classification.get("primary_category")
            confidence = classification.get("confidence", 0)
            
            if ClaudeResponseCache.should_cache_classification(category, confidence):
                # High confidence = longer cache
                if confidence >= 0.95:
                    ttl_override = 7200  # 2 hours
                elif confidence >= 0.9:
                    ttl_override = 3600  # 1 hour
                else:
                    ttl_override = 1800  # 30 minutes
            else:
                # Don't cache low confidence results
                return
        
        cache_key = f"classification:{email_hash}"
        await cache_manager.set(cache_key, classification, ttl_override)
    
    @staticmethod
    async def get_cached_classification(email_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached classification"""
        cache_key = f"classification:{email_hash}"
        return await cache_manager.get(cache_key)
    
    @staticmethod
    def generate_email_hash(sender: str, subject: str, body: str) -> str:
        """Generate hash for email content"""
        content = f"{sender}:{subject}:{body[:500]}"  # First 500 chars of body
        return hashlib.sha256(content.encode()).hexdigest()[:32]

class TemplateCache:
    """Cache for generated response templates"""
    
    @staticmethod
    async def cache_template(
        template_type: str,
        context_hash: str,
        response: str,
        ttl_seconds: int = 3600
    ) -> None:
        """Cache generated template response"""
        cache_key = f"template:{template_type}:{context_hash}"
        await cache_manager.set(cache_key, response, ttl_seconds)
    
    @staticmethod
    async def get_cached_template(
        template_type: str,
        context_hash: str
    ) -> Optional[str]:
        """Get cached template response"""
        cache_key = f"template:{template_type}:{context_hash}"
        return await cache_manager.get(cache_key)
    
    @staticmethod
    def generate_context_hash(context: Dict[str, Any]) -> str:
        """Generate hash for template context"""
        # Remove volatile fields
        stable_context = {
            k: v for k, v in context.items()
            if k not in ["timestamp", "id", "created_at"]
        }
        context_str = json.dumps(stable_context, sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()[:16]

# Rate limiting cache
class RateLimitCache:
    """Cache for rate limiting data"""
    
    @staticmethod
    async def increment_request_count(user_id: str) -> int:
        """Increment and return request count for user"""
        cache_key = f"rate_limit:{user_id}"
        current = await cache_manager.get(cache_key) or []
        
        now = datetime.utcnow()
        # Filter requests within window
        window_start = now - timedelta(minutes=1)
        current = [ts for ts in current if ts > window_start]
        
        # Add current request
        current.append(now)
        
        # Cache for 1 minute
        await cache_manager.set(cache_key, current, 60)
        
        return len(current)
    
    @staticmethod
    async def get_request_count(user_id: str) -> int:
        """Get current request count for user"""
        cache_key = f"rate_limit:{user_id}"
        current = await cache_manager.get(cache_key) or []
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        current = [ts for ts in current if ts > window_start]
        
        return len(current)

# Performance monitoring
class CacheMetrics:
    """Track cache performance metrics"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_rate": f"{self.hit_rate:.2%}",
            "total_requests": self.hits + self.misses
        }

# Global metrics instance
cache_metrics = CacheMetrics()

# Example usage in Claude service
async def get_classification_with_cache(
    email_data: Dict[str, Any],
    claude_service: Any
) -> Dict[str, Any]:
    """Get email classification with caching"""
    # Generate hash for email
    email_hash = ClaudeResponseCache.generate_email_hash(
        email_data["sender_email"],
        email_data["subject"],
        email_data["body_text"]
    )
    
    # Check cache
    cached = await ClaudeResponseCache.get_cached_classification(email_hash)
    if cached:
        cache_metrics.hits += 1
        logger.info(f"Classification cache hit (hash: {email_hash[:8]}...)")
        return cached
    
    cache_metrics.misses += 1
    
    # Call Claude API
    classification = await claude_service.classify_email(email_data)
    
    # Cache result if appropriate
    await ClaudeResponseCache.cache_classification(email_hash, classification)
    cache_metrics.sets += 1
    
    return classification