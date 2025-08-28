"""
Phase 4: Production-grade caching system
Supports Redis, in-memory, and hybrid caching strategies
"""
import os
import json
import time
import hashlib
import asyncio
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")

class CacheBackend(ABC):
    """Abstract cache backend interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass

class InMemoryCacheBackend(CacheBackend):
    """In-memory cache backend with TTL support"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.expiry = {}
        self.max_size = max_size
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        await self._cleanup_expired()
        
        if key in self.cache:
            if key not in self.expiry or self.expiry[key] > time.time():
                self.stats["hits"] += 1
                return self.cache[key]
            else:
                # Expired
                await self.delete(key)
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        try:
            # Check size limits
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict_oldest()
            
            self.cache[key] = value
            
            if ttl:
                self.expiry[key] = time.time() + ttl
            elif key in self.expiry:
                del self.expiry[key]
            
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache"""
        deleted = False
        if key in self.cache:
            del self.cache[key]
            deleted = True
        
        if key in self.expiry:
            del self.expiry[key]
        
        if deleted:
            self.stats["deletes"] += 1
        
        return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        value = await self.get(key)
        return value is not None
    
    async def clear(self) -> bool:
        """Clear all entries"""
        self.cache.clear()
        self.expiry.clear()
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            **self.stats,
            "size": len(self.cache),
            "max_size": self.max_size,
            "expired_keys": len([k for k, exp in self.expiry.items() if exp <= time.time()])
        }
    
    async def _cleanup_expired(self):
        """Remove expired keys"""
        current_time = time.time()
        expired_keys = [k for k, exp in self.expiry.items() if exp <= current_time]
        
        for key in expired_keys:
            await self.delete(key)
    
    async def _evict_oldest(self):
        """Evict oldest entry to make space"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            await self.delete(oldest_key)
            self.stats["evictions"] += 1

class RedisCacheBackend(CacheBackend):
    """Redis cache backend"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = None
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def _get_redis(self):
        """Get or create Redis connection"""
        if self.redis is None:
            try:
                self.redis = await aioredis.from_url(self.redis_url)
                # Test connection
                await self.redis.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise e
        return self.redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            redis = await self._get_redis()
            value = await redis.get(key)
            
            if value is not None:
                self.stats["hits"] += 1
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        try:
            redis = await self._get_redis()
            serialized_value = json.dumps(value, default=str)
            
            if ttl:
                result = await redis.setex(key, ttl, serialized_value)
            else:
                result = await redis.set(key, serialized_value)
            
            if result:
                self.stats["sets"] += 1
            
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            redis = await self._get_redis()
            result = await redis.delete(key)
            
            if result:
                self.stats["deletes"] += 1
            
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            redis = await self._get_redis()
            result = await redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def clear(self) -> bool:
        """Clear Redis database"""
        try:
            redis = await self._get_redis()
            await redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            self.stats["errors"] += 1
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        try:
            redis = await self._get_redis()
            info = await redis.info()
            
            return {
                **self.stats,
                "redis_memory_used": info.get("used_memory", 0),
                "redis_connected_clients": info.get("connected_clients", 0),
                "redis_keyspace_hits": info.get("keyspace_hits", 0),
                "redis_keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return self.stats

class CacheManager:
    """Production cache manager with multiple strategies"""
    
    def __init__(self):
        self.backend = self._initialize_backend()
        self.default_ttl = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))  # 1 hour
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    
    def _initialize_backend(self) -> CacheBackend:
        """Initialize cache backend"""
        cache_type = os.getenv("CACHE_TYPE", "redis" if REDIS_AVAILABLE else "memory").lower()
        
        if cache_type == "redis" and REDIS_AVAILABLE:
            try:
                return RedisCacheBackend()
            except Exception as e:
                logger.warning(f"Redis not available, falling back to memory cache: {e}")
                return InMemoryCacheBackend()
        else:
            max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))
            return InMemoryCacheBackend(max_size=max_size)
    
    def _generate_key(self, namespace: str, identifier: str, **kwargs) -> str:
        """Generate cache key with consistent format"""
        key_parts = [namespace, identifier]
        
        # Add additional parameters to key
        if kwargs:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        
        return ":".join(key_parts)
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get cached job status"""
        if not self.enabled:
            return None
        
        key = self._generate_key("job_status", job_id)
        return await self.backend.get(key)
    
    async def set_job_status(self, job_id: str, status_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache job status"""
        if not self.enabled:
            return True
        
        key = self._generate_key("job_status", job_id)
        ttl = ttl or self.default_ttl
        return await self.backend.set(key, status_data, ttl)
    
    async def get_transcription_result(self, job_id: str, format_type: str) -> Optional[bytes]:
        """Get cached transcription result"""
        if not self.enabled:
            return None
        
        key = self._generate_key("transcription", job_id, format=format_type)
        result = await self.backend.get(key)
        
        # Convert back to bytes if cached
        if result and isinstance(result, str):
            import base64
            return base64.b64decode(result)
        
        return result
    
    async def set_transcription_result(self, job_id: str, format_type: str, content: bytes, ttl: Optional[int] = None) -> bool:
        """Cache transcription result"""
        if not self.enabled:
            return True
        
        key = self._generate_key("transcription", job_id, format=format_type)
        
        # Convert bytes to base64 for JSON serialization
        import base64
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        ttl = ttl or (self.default_ttl * 24)  # Cache transcriptions longer
        return await self.backend.set(key, encoded_content, ttl)
    
    async def get_user_jobs(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached user job list"""
        if not self.enabled:
            return None
        
        key = self._generate_key("user_jobs", user_id)
        return await self.backend.get(key)
    
    async def set_user_jobs(self, user_id: str, jobs: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Cache user job list"""
        if not self.enabled:
            return True
        
        key = self._generate_key("user_jobs", user_id)
        ttl = ttl or 300  # Cache job lists for 5 minutes
        return await self.backend.set(key, jobs, ttl)
    
    async def invalidate_user_jobs(self, user_id: str) -> bool:
        """Invalidate cached user job list"""
        key = self._generate_key("user_jobs", user_id)
        return await self.backend.delete(key)
    
    async def get_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Get cached system metrics"""
        if not self.enabled:
            return None
        
        key = self._generate_key("system", "metrics")
        return await self.backend.get(key)
    
    async def set_system_metrics(self, metrics: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache system metrics"""
        if not self.enabled:
            return True
        
        key = self._generate_key("system", "metrics")
        ttl = ttl or 60  # Cache metrics for 1 minute
        return await self.backend.set(key, metrics, ttl)
    
    async def get_file_metadata(self, storage_key: str) -> Optional[Dict[str, Any]]:
        """Get cached file metadata"""
        if not self.enabled:
            return None
        
        key = self._generate_key("file_meta", storage_key.replace("/", "_"))
        return await self.backend.get(key)
    
    async def set_file_metadata(self, storage_key: str, metadata: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache file metadata"""
        if not self.enabled:
            return True
        
        key = self._generate_key("file_meta", storage_key.replace("/", "_"))
        ttl = ttl or (self.default_ttl * 6)  # Cache file metadata for 6 hours
        return await self.backend.set(key, metadata, ttl)
    
    async def clear_all(self) -> bool:
        """Clear all cached data"""
        return await self.backend.clear()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        backend_stats = await self.backend.get_stats()
        
        return {
            "enabled": self.enabled,
            "backend_type": type(self.backend).__name__,
            "default_ttl": self.default_ttl,
            **backend_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global cache manager instance
cache_manager = CacheManager()

# Decorator for caching function results
def cached(ttl: Optional[int] = None, key_prefix: str = "func"):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not cache_manager.enabled:
                return await func(*args, **kwargs)
            
            # Generate cache key from function name and arguments
            func_name = func.__name__
            args_str = "_".join(str(arg) for arg in args)
            kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = cache_manager._generate_key(
                key_prefix, 
                func_name, 
                args=hashlib.md5(args_str.encode()).hexdigest()[:8],
                kwargs=hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
            )
            
            # Try to get from cache
            cached_result = await cache_manager.backend.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.backend.set(cache_key, result, ttl or cache_manager.default_ttl)
            
            return result
        
        return wrapper
    return decorator