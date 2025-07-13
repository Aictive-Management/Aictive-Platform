"""
Multi-tier Redis Caching Strategy for Aictive Platform
Implements L1 (memory) and L2 (Redis) caching with intelligent invalidation,
cache warming, and distributed coordination for RentVine data
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Set, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import pickle
from functools import wraps
import weakref

import aioredis
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache level identifiers"""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    BOTH = "both"


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL_BASED = "ttl_based"
    TAG_BASED = "tag_based"
    DEPENDENCY_BASED = "dependency_based"
    EVENT_DRIVEN = "event_driven"


class CachePattern(Enum):
    """Common caching patterns"""
    CACHE_ASIDE = "cache_aside"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    tags: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    size_bytes: int = 0
    serialized: bool = False


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage: int = 0
    network_calls: int = 0
    serialization_time: float = 0.0
    deserialization_time: float = 0.0
    cache_warming_time: float = 0.0
    
    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_ratio(self) -> float:
        return 1.0 - self.hit_ratio


class L1MemoryCache:
    """High-performance in-memory cache (L1)"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU eviction
        self.metrics = CacheMetrics()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check expiration
                if entry.expires_at and datetime.utcnow() > entry.expires_at:
                    await self._remove(key)
                    self.metrics.misses += 1
                    return None
                
                # Update access info
                entry.access_count += 1
                entry.last_accessed = datetime.utcnow()
                
                # Move to end for LRU
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                
                self.metrics.hits += 1
                return entry.value
            
            self.metrics.misses += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None
    ) -> None:
        """Set value in L1 cache"""
        async with self._lock:
            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = len(str(value).encode('utf-8'))
            
            # Check if we need to evict
            await self._ensure_capacity(size_bytes)
            
            # Create cache entry
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                tags=tags or set(),
                dependencies=dependencies or set(),
                size_bytes=size_bytes
            )
            
            # Store entry
            self.cache[key] = entry
            if key not in self.access_order:
                self.access_order.append(key)
            
            self.metrics.sets += 1
            self.metrics.memory_usage += size_bytes
    
    async def delete(self, key: str) -> bool:
        """Delete key from L1 cache"""
        async with self._lock:
            if key in self.cache:
                await self._remove(key)
                self.metrics.deletes += 1
                return True
            return False
    
    async def delete_by_tags(self, tags: Set[str]) -> int:
        """Delete all entries with matching tags"""
        async with self._lock:
            keys_to_delete = []
            for key, entry in self.cache.items():
                if tags.intersection(entry.tags):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                await self._remove(key)
            
            self.metrics.deletes += len(keys_to_delete)
            return len(keys_to_delete)
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self.cache.clear()
            self.access_order.clear()
            self.metrics.memory_usage = 0
    
    async def _ensure_capacity(self, new_size: int) -> None:
        """Ensure cache has capacity for new entry"""
        # Check memory limit
        while (self.metrics.memory_usage + new_size > self.max_memory_bytes and 
               self.access_order):
            oldest_key = self.access_order[0]
            await self._remove(oldest_key)
            self.metrics.evictions += 1
        
        # Check size limit
        while len(self.cache) >= self.max_size and self.access_order:
            oldest_key = self.access_order[0]
            await self._remove(oldest_key)
            self.metrics.evictions += 1
    
    async def _remove(self, key: str) -> None:
        """Remove entry from cache"""
        if key in self.cache:
            entry = self.cache[key]
            self.metrics.memory_usage -= entry.size_bytes
            del self.cache[key]
        
        if key in self.access_order:
            self.access_order.remove(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "memory_usage_mb": self.metrics.memory_usage / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
            "hit_ratio": self.metrics.hit_ratio,
            "metrics": self.metrics.__dict__
        }


class L2RedisCache:
    """Redis-based distributed cache (L2)"""
    
    def __init__(self, redis_url: str, key_prefix: str = "aictive"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis: Optional[aioredis.Redis] = None
        self.metrics = CacheMetrics()
        self.serialization_format = "pickle"  # or "json"
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle serialization manually
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test connection
            await self.redis.ping()
            logger.info("Connected to Redis for L2 caching")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
    
    def _make_key(self, key: str) -> str:
        """Create Redis key with prefix"""
        return f"{self.key_prefix}:{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage"""
        start_time = time.time()
        try:
            if self.serialization_format == "pickle":
                serialized = pickle.dumps(value)
            else:  # json
                serialized = json.dumps(value, default=str).encode('utf-8')
            
            self.metrics.serialization_time += time.time() - start_time
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            raise
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from Redis"""
        start_time = time.time()
        try:
            if self.serialization_format == "pickle":
                value = pickle.loads(data)
            else:  # json
                value = json.loads(data.decode('utf-8'))
            
            self.metrics.deserialization_time += time.time() - start_time
            return value
            
        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.redis:
            return None
        
        try:
            redis_key = self._make_key(key)
            data = await self.redis.get(redis_key)
            
            if data:
                self.metrics.hits += 1
                self.metrics.network_calls += 1
                return self._deserialize(data)
            else:
                self.metrics.misses += 1
                self.metrics.network_calls += 1
                return None
                
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {str(e)}")
            self.metrics.misses += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None
    ) -> bool:
        """Set value in Redis"""
        if not self.redis:
            return False
        
        try:
            redis_key = self._make_key(key)
            serialized_value = self._serialize(value)
            
            # Set with TTL
            if ttl_seconds:
                result = await self.redis.setex(redis_key, ttl_seconds, serialized_value)
            else:
                result = await self.redis.set(redis_key, serialized_value)
            
            # Handle tags
            if tags:
                await self._set_tags(key, tags, ttl_seconds)
            
            self.metrics.sets += 1
            self.metrics.network_calls += 1
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.redis:
            return False
        
        try:
            redis_key = self._make_key(key)
            result = await self.redis.delete(redis_key)
            
            # Also delete tag associations
            await self._delete_tag_associations(key)
            
            self.metrics.deletes += 1
            self.metrics.network_calls += 1
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {str(e)}")
            return False
    
    async def delete_by_tags(self, tags: Set[str]) -> int:
        """Delete all keys with matching tags"""
        if not self.redis:
            return 0
        
        try:
            keys_to_delete = set()
            
            for tag in tags:
                tag_key = self._make_key(f"tag:{tag}")
                tagged_keys = await self.redis.smembers(tag_key)
                keys_to_delete.update(tagged_keys)
            
            # Delete all tagged keys
            deleted_count = 0
            for key in keys_to_delete:
                if await self.delete(key.decode('utf-8') if isinstance(key, bytes) else key):
                    deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Redis delete by tags error: {str(e)}")
            return 0
    
    async def _set_tags(self, key: str, tags: Set[str], ttl_seconds: Optional[int] = None) -> None:
        """Associate tags with key"""
        for tag in tags:
            tag_key = self._make_key(f"tag:{tag}")
            await self.redis.sadd(tag_key, key)
            
            if ttl_seconds:
                await self.redis.expire(tag_key, ttl_seconds + 3600)  # Tag expires 1 hour after data
    
    async def _delete_tag_associations(self, key: str) -> None:
        """Remove key from all tag associations"""
        # This is expensive - consider implementing a reverse index
        pattern = self._make_key("tag:*")
        async for tag_key in self.redis.scan_iter(match=pattern):
            await self.redis.srem(tag_key, key)
    
    async def clear_namespace(self, namespace: str = None) -> int:
        """Clear all keys in namespace"""
        if not self.redis:
            return 0
        
        pattern = self._make_key(f"{namespace}:*" if namespace else "*")
        deleted = 0
        
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)
            deleted += 1
        
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        return {
            "connected": self.redis is not None,
            "hit_ratio": self.metrics.hit_ratio,
            "network_calls": self.metrics.network_calls,
            "avg_serialization_time": (
                self.metrics.serialization_time / max(1, self.metrics.sets)
            ),
            "avg_deserialization_time": (
                self.metrics.deserialization_time / max(1, self.metrics.hits)
            ),
            "metrics": self.metrics.__dict__
        }


class MultiTierCacheManager:
    """Manages L1 (memory) and L2 (Redis) caches with intelligent coordination"""
    
    def __init__(
        self,
        redis_url: str,
        l1_max_size: int = 1000,
        l1_max_memory_mb: int = 100,
        default_ttl: int = 3600
    ):
        self.l1_cache = L1MemoryCache(l1_max_size, l1_max_memory_mb)
        self.l2_cache = L2RedisCache(redis_url)
        self.default_ttl = default_ttl
        self.cache_warming_tasks: Set[str] = set()
        self.invalidation_patterns: Dict[str, List[str]] = {}
        
        # RentVine-specific configuration
        self.rentvine_cache_config = {
            "properties": {"ttl": 1800, "tags": {"properties", "rentvine"}},  # 30 min
            "tenants": {"ttl": 900, "tags": {"tenants", "rentvine"}},        # 15 min
            "leases": {"ttl": 3600, "tags": {"leases", "rentvine"}},         # 1 hour
            "work_orders": {"ttl": 300, "tags": {"work_orders", "rentvine"}}, # 5 min
            "transactions": {"ttl": 7200, "tags": {"transactions", "rentvine"}} # 2 hours
        }
    
    async def initialize(self) -> None:
        """Initialize cache connections"""
        await self.l2_cache.connect()
        logger.info("Multi-tier cache manager initialized")
    
    async def shutdown(self) -> None:
        """Shutdown cache connections"""
        await self.l1_cache.clear()
        await self.l2_cache.disconnect()
    
    async def get(
        self, 
        key: str, 
        strategy: CacheLevel = CacheLevel.BOTH
    ) -> Optional[Any]:
        """Get value from cache with specified strategy"""
        
        if strategy in (CacheLevel.L1_MEMORY, CacheLevel.BOTH):
            # Try L1 first
            value = await self.l1_cache.get(key)
            if value is not None:
                return value
        
        if strategy in (CacheLevel.L2_REDIS, CacheLevel.BOTH):
            # Try L2
            value = await self.l2_cache.get(key)
            if value is not None:
                # Promote to L1 if using both levels
                if strategy == CacheLevel.BOTH:
                    await self.l1_cache.set(key, value, self.default_ttl // 2)
                return value
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None,
        strategy: CacheLevel = CacheLevel.BOTH
    ) -> bool:
        """Set value in cache with specified strategy"""
        
        ttl = ttl_seconds or self.default_ttl
        success = True
        
        if strategy in (CacheLevel.L1_MEMORY, CacheLevel.BOTH):
            await self.l1_cache.set(key, value, ttl, tags, dependencies)
        
        if strategy in (CacheLevel.L2_REDIS, CacheLevel.BOTH):
            redis_success = await self.l2_cache.set(key, value, ttl, tags)
            success = success and redis_success
        
        return success
    
    async def delete(self, key: str, strategy: CacheLevel = CacheLevel.BOTH) -> bool:
        """Delete key from cache"""
        success = True
        
        if strategy in (CacheLevel.L1_MEMORY, CacheLevel.BOTH):
            await self.l1_cache.delete(key)
        
        if strategy in (CacheLevel.L2_REDIS, CacheLevel.BOTH):
            redis_success = await self.l2_cache.delete(key)
            success = success and redis_success
        
        return success
    
    async def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalidate all cache entries with matching tags"""
        l1_deleted = await self.l1_cache.delete_by_tags(tags)
        l2_deleted = await self.l2_cache.delete_by_tags(tags)
        
        total_deleted = l1_deleted + l2_deleted
        logger.info(f"Invalidated {total_deleted} entries with tags: {tags}")
        
        return total_deleted
    
    async def warm_cache(
        self, 
        warm_func: Callable,
        key_pattern: str,
        tags: Set[str],
        ttl: int = None
    ) -> int:
        """Warm cache with data from warm_func"""
        if key_pattern in self.cache_warming_tasks:
            logger.warning(f"Cache warming already in progress for {key_pattern}")
            return 0
        
        self.cache_warming_tasks.add(key_pattern)
        warmed_count = 0
        
        try:
            start_time = time.time()
            
            # Get data to warm
            warm_data = await warm_func()
            
            if isinstance(warm_data, dict):
                for key, value in warm_data.items():
                    cache_key = f"{key_pattern}:{key}"
                    await self.set(cache_key, value, ttl, tags)
                    warmed_count += 1
            
            elif isinstance(warm_data, list):
                for i, value in enumerate(warm_data):
                    cache_key = f"{key_pattern}:{i}"
                    await self.set(cache_key, value, ttl, tags)
                    warmed_count += 1
            
            warming_time = time.time() - start_time
            self.l1_cache.metrics.cache_warming_time += warming_time
            
            logger.info(
                f"Cache warming completed for {key_pattern}: "
                f"{warmed_count} entries in {warming_time:.3f}s"
            )
            
        except Exception as e:
            logger.error(f"Cache warming failed for {key_pattern}: {str(e)}")
        
        finally:
            self.cache_warming_tasks.discard(key_pattern)
        
        return warmed_count
    
    # RentVine-specific caching methods
    
    async def cache_rentvine_data(
        self, 
        data_type: str, 
        entity_id: str, 
        data: Any
    ) -> bool:
        """Cache RentVine data with appropriate configuration"""
        if data_type not in self.rentvine_cache_config:
            logger.warning(f"Unknown RentVine data type: {data_type}")
            return False
        
        config = self.rentvine_cache_config[data_type]
        key = f"rentvine:{data_type}:{entity_id}"
        
        return await self.set(
            key=key,
            value=data,
            ttl_seconds=config["ttl"],
            tags=config["tags"],
            dependencies={f"rentvine:{data_type}"}
        )
    
    async def get_rentvine_data(self, data_type: str, entity_id: str) -> Optional[Any]:
        """Get cached RentVine data"""
        key = f"rentvine:{data_type}:{entity_id}"
        return await self.get(key)
    
    async def invalidate_rentvine_data(self, data_type: str, entity_id: str = None) -> int:
        """Invalidate RentVine data by type or specific entity"""
        if entity_id:
            # Invalidate specific entity
            key = f"rentvine:{data_type}:{entity_id}"
            await self.delete(key)
            return 1
        else:
            # Invalidate all entities of this type
            tags = {data_type, "rentvine"}
            return await self.invalidate_by_tags(tags)
    
    async def warm_rentvine_cache(self, rentvine_client: Any) -> int:
        """Warm cache with frequently accessed RentVine data"""
        total_warmed = 0
        
        # Warm properties
        async def get_properties():
            response = await rentvine_client.get_properties(limit=100)
            return {prop["id"]: prop for prop in response.data} if response.success else {}
        
        properties_warmed = await self.warm_cache(
            warm_func=get_properties,
            key_pattern="rentvine:properties",
            tags={"properties", "rentvine"},
            ttl=self.rentvine_cache_config["properties"]["ttl"]
        )
        total_warmed += properties_warmed
        
        # Warm active work orders
        async def get_work_orders():
            response = await rentvine_client.get_work_orders(status="open", limit=50)
            return {wo["id"]: wo for wo in response.data} if response.success else {}
        
        work_orders_warmed = await self.warm_cache(
            warm_func=get_work_orders,
            key_pattern="rentvine:work_orders",
            tags={"work_orders", "rentvine"},
            ttl=self.rentvine_cache_config["work_orders"]["ttl"]
        )
        total_warmed += work_orders_warmed
        
        logger.info(f"RentVine cache warming completed: {total_warmed} entries")
        return total_warmed
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        l1_stats = self.l1_cache.get_stats()
        l2_stats = self.l2_cache.get_stats()
        
        # Combined metrics
        total_hits = l1_stats["metrics"]["hits"] + l2_stats["metrics"]["hits"]
        total_misses = l1_stats["metrics"]["misses"] + l2_stats["metrics"]["misses"]
        combined_hit_ratio = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "l1_cache": l1_stats,
            "l2_cache": l2_stats,
            "combined": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_ratio": combined_hit_ratio,
                "cache_warming_tasks": len(self.cache_warming_tasks)
            },
            "rentvine_config": self.rentvine_cache_config
        }


# Decorators for easy caching

def cached_rentvine(data_type: str, ttl: Optional[int] = None):
    """Decorator for caching RentVine API responses"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract entity ID from arguments
            entity_id = None
            if args and len(args) > 1:
                entity_id = str(args[1])  # Assuming second arg is entity ID
            elif 'entity_id' in kwargs:
                entity_id = str(kwargs['entity_id'])
            elif 'id' in kwargs:
                entity_id = str(kwargs['id'])
            
            if not entity_id:
                # Can't cache without entity ID
                return await func(*args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_manager.get_rentvine_data(data_type, entity_id)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            if result:
                await cache_manager.cache_rentvine_data(data_type, entity_id, result)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate_on_update(data_type: str):
    """Decorator to invalidate cache on data updates"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # If update was successful, invalidate cache
            if result and hasattr(result, 'success') and result.success:
                # Extract entity ID
                entity_id = None
                if args and len(args) > 1:
                    entity_id = str(args[1])
                elif 'entity_id' in kwargs:
                    entity_id = str(kwargs['entity_id'])
                
                if entity_id:
                    await cache_manager.invalidate_rentvine_data(data_type, entity_id)
                else:
                    # Invalidate all entries of this type
                    await cache_manager.invalidate_rentvine_data(data_type)
            
            return result
        
        return wrapper
    return decorator


# Global cache manager instance
cache_manager: Optional[MultiTierCacheManager] = None


async def initialize_cache_system(redis_url: str = None) -> MultiTierCacheManager:
    """Initialize the global cache system"""
    global cache_manager
    
    redis_url = redis_url or getattr(settings, 'redis_url', 'redis://localhost:6379/0')
    
    cache_manager = MultiTierCacheManager(
        redis_url=redis_url,
        l1_max_size=getattr(settings, 'cache_l1_max_size', 1000),
        l1_max_memory_mb=getattr(settings, 'cache_l1_max_memory_mb', 100),
        default_ttl=getattr(settings, 'cache_default_ttl', 3600)
    )
    
    await cache_manager.initialize()
    logger.info("Cache system initialized successfully")
    
    return cache_manager


async def shutdown_cache_system():
    """Shutdown the global cache system"""
    global cache_manager
    if cache_manager:
        await cache_manager.shutdown()
        cache_manager = None
        logger.info("Cache system shutdown complete")