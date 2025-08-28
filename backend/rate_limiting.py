"""
Phase 4: API rate limiting and quota management system
Implements token bucket, sliding window, and user quota systems
"""
import os
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """Rate limit types"""
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    CONCURRENT = "concurrent"

@dataclass
class RateLimit:
    """Rate limit configuration"""
    limit: int
    window_seconds: int
    limit_type: RateLimitType
    burst_multiplier: float = 1.5

@dataclass
class UserQuota:
    """User quota configuration"""
    daily_transcription_minutes: int
    monthly_transcription_minutes: int
    max_file_size_mb: int
    concurrent_jobs: int
    api_calls_per_hour: int
    storage_quota_gb: float
    tier: str = "free"

@dataclass
class QuotaUsage:
    """Current quota usage"""
    daily_transcription_minutes_used: float
    monthly_transcription_minutes_used: float
    storage_used_gb: float
    api_calls_this_hour: int
    active_jobs: int
    last_reset: datetime

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens, return True if successful"""
        now = time.time()
        
        # Refill tokens based on time passed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bucket status"""
        now = time.time()
        time_passed = now - self.last_refill
        current_tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        
        return {
            "current_tokens": current_tokens,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "fill_percentage": (current_tokens / self.capacity) * 100
        }

class SlidingWindowCounter:
    """Sliding window counter for rate limiting"""
    
    def __init__(self, window_seconds: int, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.requests = deque()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        now = time.time()
        
        # Remove old requests outside the window
        while self.requests and self.requests[0] <= now - self.window_seconds:
            self.requests.popleft()
        
        # Check if under the limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current window status"""
        now = time.time()
        
        # Count requests in current window
        current_requests = sum(1 for req_time in self.requests if req_time > now - self.window_seconds)
        
        return {
            "current_requests": current_requests,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "usage_percentage": (current_requests / self.max_requests) * 100
        }

class RateLimiter:
    """Main rate limiting system"""
    
    def __init__(self):
        self.buckets = {}
        self.windows = {}
        self.enabled = os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
        
        # Default rate limits
        self.default_limits = {
            "api_general": RateLimit(100, 60, RateLimitType.PER_MINUTE),
            "api_upload": RateLimit(10, 60, RateLimitType.PER_MINUTE),
            "api_transcription": RateLimit(20, 3600, RateLimitType.PER_HOUR),
            "concurrent_jobs": RateLimit(5, 0, RateLimitType.CONCURRENT)
        }
    
    def _get_bucket_key(self, identifier: str, limit_name: str) -> str:
        """Generate bucket key"""
        return f"{identifier}:{limit_name}"
    
    def _get_or_create_bucket(self, identifier: str, limit_name: str) -> TokenBucket:
        """Get or create token bucket for identifier and limit"""
        key = self._get_bucket_key(identifier, limit_name)
        
        if key not in self.buckets:
            rate_limit = self.default_limits.get(limit_name)
            if not rate_limit:
                # Default fallback
                rate_limit = RateLimit(60, 60, RateLimitType.PER_MINUTE)
            
            # Convert to tokens per second
            refill_rate = rate_limit.limit / rate_limit.window_seconds if rate_limit.window_seconds > 0 else 0
            capacity = int(rate_limit.limit * rate_limit.burst_multiplier)
            
            self.buckets[key] = TokenBucket(capacity, refill_rate)
        
        return self.buckets[key]
    
    def _get_or_create_window(self, identifier: str, limit_name: str) -> SlidingWindowCounter:
        """Get or create sliding window counter"""
        key = self._get_bucket_key(identifier, limit_name)
        
        if key not in self.windows:
            rate_limit = self.default_limits.get(limit_name)
            if not rate_limit:
                rate_limit = RateLimit(60, 60, RateLimitType.PER_MINUTE)
            
            self.windows[key] = SlidingWindowCounter(rate_limit.window_seconds, rate_limit.limit)
        
        return self.windows[key]
    
    async def is_allowed(self, identifier: str, limit_name: str, tokens: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed"""
        if not self.enabled:
            return True, {"status": "rate_limiting_disabled"}
        
        rate_limit = self.default_limits.get(limit_name)
        if not rate_limit:
            return True, {"status": "no_limit_configured"}
        
        if rate_limit.limit_type == RateLimitType.CONCURRENT:
            # Handle concurrent limits separately
            return await self._check_concurrent_limit(identifier, limit_name, tokens)
        else:
            # Use sliding window for time-based limits
            window = self._get_or_create_window(identifier, limit_name)
            
            allowed = window.is_allowed()
            status = window.get_status()
            
            return allowed, {
                **status,
                "limit_name": limit_name,
                "identifier": identifier,
                "allowed": allowed
            }
    
    async def _check_concurrent_limit(self, identifier: str, limit_name: str, delta: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """Check concurrent resource limits"""
        # This would typically be stored in Redis or database
        # For now, use in-memory tracking
        key = self._get_bucket_key(identifier, "concurrent_count")
        
        if key not in self.buckets:
            self.buckets[key] = {"count": 0}
        
        current_count = self.buckets[key]["count"]
        rate_limit = self.default_limits.get(limit_name)
        max_concurrent = rate_limit.limit if rate_limit else 5
        
        if delta > 0:  # Acquiring resource
            if current_count + delta <= max_concurrent:
                self.buckets[key]["count"] = current_count + delta
                return True, {
                    "allowed": True,
                    "current_count": current_count + delta,
                    "max_concurrent": max_concurrent
                }
            else:
                return False, {
                    "allowed": False,
                    "current_count": current_count,
                    "max_concurrent": max_concurrent,
                    "error": "concurrent_limit_exceeded"
                }
        else:  # Releasing resource
            self.buckets[key]["count"] = max(0, current_count + delta)
            return True, {
                "allowed": True,
                "current_count": self.buckets[key]["count"],
                "max_concurrent": max_concurrent
            }
    
    async def acquire_resource(self, identifier: str, limit_name: str) -> bool:
        """Acquire a concurrent resource"""
        allowed, _ = await self._check_concurrent_limit(identifier, limit_name, 1)
        return allowed
    
    async def release_resource(self, identifier: str, limit_name: str):
        """Release a concurrent resource"""
        await self._check_concurrent_limit(identifier, limit_name, -1)
    
    def get_limits_status(self, identifier: str) -> Dict[str, Any]:
        """Get status of all limits for an identifier"""
        status = {}
        
        for limit_name in self.default_limits.keys():
            if limit_name.endswith("concurrent"):
                key = self._get_bucket_key(identifier, "concurrent_count")
                if key in self.buckets:
                    status[limit_name] = {
                        "current_count": self.buckets[key]["count"],
                        "limit": self.default_limits[limit_name].limit
                    }
            else:
                window = self._get_or_create_window(identifier, limit_name)
                status[limit_name] = window.get_status()
        
        return status

class QuotaManager:
    """User quota management system"""
    
    def __init__(self):
        self.enabled = os.getenv("QUOTA_ENABLED", "true").lower() == "true"
        
        # Default quotas by tier
        self.default_quotas = {
            "free": UserQuota(
                daily_transcription_minutes=60,
                monthly_transcription_minutes=600,
                max_file_size_mb=50,
                concurrent_jobs=2,
                api_calls_per_hour=100,
                storage_quota_gb=1.0,
                tier="free"
            ),
            "premium": UserQuota(
                daily_transcription_minutes=480,  # 8 hours
                monthly_transcription_minutes=4800,  # 80 hours
                max_file_size_mb=500,
                concurrent_jobs=10,
                api_calls_per_hour=1000,
                storage_quota_gb=50.0,
                tier="premium"
            ),
            "enterprise": UserQuota(
                daily_transcription_minutes=1440,  # 24 hours
                monthly_transcription_minutes=14400,  # 240 hours
                max_file_size_mb=2000,  # 2GB
                concurrent_jobs=50,
                api_calls_per_hour=5000,
                storage_quota_gb=500.0,
                tier="enterprise"
            )
        }
        
        # In-memory usage tracking (would use database in production)
        self.usage_data = {}
    
    async def get_user_quota(self, user_id: str, user_tier: str = "free") -> UserQuota:
        """Get user quota configuration"""
        if not self.enabled:
            return self.default_quotas["enterprise"]  # No limits when disabled
        
        # Check for custom quota (would query database)
        # For now, return default based on tier
        return self.default_quotas.get(user_tier, self.default_quotas["free"])
    
    async def get_user_usage(self, user_id: str) -> QuotaUsage:
        """Get current user usage"""
        if user_id not in self.usage_data:
            self.usage_data[user_id] = QuotaUsage(
                daily_transcription_minutes_used=0.0,
                monthly_transcription_minutes_used=0.0,
                storage_used_gb=0.0,
                api_calls_this_hour=0,
                active_jobs=0,
                last_reset=datetime.now(timezone.utc)
            )
        
        usage = self.usage_data[user_id]
        
        # Reset daily/hourly counters if needed
        now = datetime.now(timezone.utc)
        if now.date() > usage.last_reset.date():
            usage.daily_transcription_minutes_used = 0.0
            usage.last_reset = now
        
        if now.hour != usage.last_reset.hour:
            usage.api_calls_this_hour = 0
        
        return usage
    
    async def check_quota(self, user_id: str, user_tier: str, 
                         transcription_minutes: float = 0,
                         file_size_mb: float = 0,
                         storage_gb: float = 0,
                         concurrent_jobs: int = 0) -> Tuple[bool, Dict[str, Any]]:
        """Check if user can perform operation within quota"""
        if not self.enabled:
            return True, {"status": "quotas_disabled"}
        
        quota = await self.get_user_quota(user_id, user_tier)
        usage = await self.get_user_usage(user_id)
        
        violations = []
        
        # Check transcription minutes
        if usage.daily_transcription_minutes_used + transcription_minutes > quota.daily_transcription_minutes:
            violations.append("daily_transcription_minutes_exceeded")
        
        if usage.monthly_transcription_minutes_used + transcription_minutes > quota.monthly_transcription_minutes:
            violations.append("monthly_transcription_minutes_exceeded")
        
        # Check file size
        if file_size_mb > quota.max_file_size_mb:
            violations.append("file_size_exceeded")
        
        # Check storage
        if usage.storage_used_gb + storage_gb > quota.storage_quota_gb:
            violations.append("storage_quota_exceeded")
        
        # Check concurrent jobs
        if usage.active_jobs + concurrent_jobs > quota.concurrent_jobs:
            violations.append("concurrent_jobs_exceeded")
        
        allowed = len(violations) == 0
        
        return allowed, {
            "allowed": allowed,
            "violations": violations,
            "quota": quota.__dict__,
            "usage": usage.__dict__,
            "remaining": {
                "daily_transcription_minutes": quota.daily_transcription_minutes - usage.daily_transcription_minutes_used,
                "monthly_transcription_minutes": quota.monthly_transcription_minutes - usage.monthly_transcription_minutes_used,
                "storage_gb": quota.storage_quota_gb - usage.storage_used_gb,
                "concurrent_jobs": quota.concurrent_jobs - usage.active_jobs
            }
        }
    
    async def consume_quota(self, user_id: str, 
                           transcription_minutes: float = 0,
                           storage_gb: float = 0,
                           api_calls: int = 1,
                           concurrent_jobs: int = 0):
        """Consume user quota"""
        if not self.enabled:
            return
        
        usage = await self.get_user_usage(user_id)
        
        usage.daily_transcription_minutes_used += transcription_minutes
        usage.monthly_transcription_minutes_used += transcription_minutes
        usage.storage_used_gb += storage_gb
        usage.api_calls_this_hour += api_calls
        usage.active_jobs += concurrent_jobs
        
        self.usage_data[user_id] = usage
    
    async def get_quota_summary(self, user_id: str, user_tier: str) -> Dict[str, Any]:
        """Get comprehensive quota summary"""
        quota = await self.get_user_quota(user_id, user_tier)
        usage = await self.get_user_usage(user_id)
        
        return {
            "user_id": user_id,
            "tier": user_tier,
            "quota": quota.__dict__,
            "usage": usage.__dict__,
            "usage_percentages": {
                "daily_transcription": (usage.daily_transcription_minutes_used / quota.daily_transcription_minutes) * 100,
                "monthly_transcription": (usage.monthly_transcription_minutes_used / quota.monthly_transcription_minutes) * 100,
                "storage": (usage.storage_used_gb / quota.storage_quota_gb) * 100,
                "concurrent_jobs": (usage.active_jobs / quota.concurrent_jobs) * 100
            },
            "limits_approaching": {
                "daily_transcription": usage.daily_transcription_minutes_used > quota.daily_transcription_minutes * 0.8,
                "monthly_transcription": usage.monthly_transcription_minutes_used > quota.monthly_transcription_minutes * 0.8,
                "storage": usage.storage_used_gb > quota.storage_quota_gb * 0.8
            }
        }

# Global instances
rate_limiter = RateLimiter()
quota_manager = QuotaManager()

# Middleware functions
async def check_rate_limit(user_id: str, endpoint: str) -> Tuple[bool, Dict[str, Any]]:
    """Check rate limits for user and endpoint"""
    # Map endpoints to limit names
    endpoint_limits = {
        "upload": "api_upload",
        "transcription": "api_transcription",
        "general": "api_general"
    }
    
    limit_name = endpoint_limits.get(endpoint, "api_general")
    return await rate_limiter.is_allowed(user_id, limit_name)

async def check_user_quota(user_id: str, user_tier: str = "free", **kwargs) -> Tuple[bool, Dict[str, Any]]:
    """Check user quotas"""
    return await quota_manager.check_quota(user_id, user_tier, **kwargs)

async def acquire_job_slot(user_id: str) -> bool:
    """Acquire a concurrent job slot"""
    return await rate_limiter.acquire_resource(user_id, "concurrent_jobs")

async def release_job_slot(user_id: str):
    """Release a concurrent job slot"""
    await rate_limiter.release_resource(user_id, "concurrent_jobs")

# FastAPI dependencies for rate limiting
from fastapi import HTTPException, Request

def create_rate_limit_dependency(limit_name: str):
    """Create a FastAPI dependency for rate limiting"""
    async def rate_limit_dependency(request: Request):
        # Extract user ID from request (simplified)
        user_id = getattr(request.state, 'user_id', 'anonymous')
        
        allowed, status = await rate_limiter.is_allowed(user_id, limit_name)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "limit_info": status,
                    "retry_after": status.get("retry_after", 60)
                }
            )
        
        return status
    
    return rate_limit_dependency