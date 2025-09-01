"""
Test suite for rate limiting and quota management system
Tests rate-limit exhaustion and quota check scenarios
"""
import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from rate_limiting import (
    RateLimiter, QuotaManager, TokenBucket, SlidingWindowCounter,
    rate_limiter, quota_manager, check_rate_limit, check_user_quota,
    RateLimit, RateLimitType, UserQuota
)

class TestTokenBucket:
    """Test token bucket algorithm"""
    
    def test_token_consumption(self):
        """Test basic token consumption"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)  # 1 token per second
        
        # Should be able to consume initial tokens
        assert bucket.consume(5) == True
        assert bucket.consume(5) == True
        
        # Should fail to consume more tokens
        assert bucket.consume(1) == False
    
    def test_token_refill(self):
        """Test token refill over time"""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)  # 2 tokens per second
        
        # Consume all tokens
        assert bucket.consume(10) == True
        assert bucket.consume(1) == False
        
        # Wait and verify refill (simulate 1 second)
        bucket.last_refill -= 1.0  # Simulate 1 second ago
        assert bucket.consume(2) == True  # Should have 2 new tokens
        assert bucket.consume(1) == False  # No more tokens
    
    def test_bucket_status(self):
        """Test bucket status reporting"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        status = bucket.get_status()
        
        assert status['capacity'] == 10
        assert status['refill_rate'] == 1.0
        assert status['current_tokens'] <= 10
        assert 0 <= status['fill_percentage'] <= 100

class TestSlidingWindowCounter:
    """Test sliding window rate limiting"""
    
    def test_window_allows_requests(self):
        """Test window allows requests within limit"""
        window = SlidingWindowCounter(window_seconds=60, max_requests=5)
        
        # Should allow requests up to the limit
        for i in range(5):
            assert window.is_allowed() == True
        
        # Should block the 6th request
        assert window.is_allowed() == False
    
    def test_window_resets_over_time(self):
        """Test window resets old requests"""
        window = SlidingWindowCounter(window_seconds=1, max_requests=2)
        
        # Fill the window
        assert window.is_allowed() == True
        assert window.is_allowed() == True
        assert window.is_allowed() == False
        
        # Simulate time passing by manipulating the requests deque
        old_time = time.time() - 2  # 2 seconds ago
        window.requests.clear()
        window.requests.append(old_time)
        
        # Should allow new requests after window reset
        assert window.is_allowed() == True
        assert window.is_allowed() == True
    
    def test_window_status(self):
        """Test window status reporting"""
        window = SlidingWindowCounter(window_seconds=60, max_requests=10)
        window.is_allowed()  # Make one request
        
        status = window.get_status()
        assert status['max_requests'] == 10
        assert status['window_seconds'] == 60
        assert status['current_requests'] >= 0
        assert 0 <= status['usage_percentage'] <= 100

class TestRateLimiter:
    """Test main rate limiter system"""
    
    @pytest.fixture
    def limiter(self):
        """Create a fresh rate limiter for each test"""
        return RateLimiter()
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_normal_requests(self, limiter):
        """Test that normal requests are allowed"""
        allowed, status = await limiter.is_allowed("test_user", "api_general")
        assert allowed == True
        assert status['allowed'] == True
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excessive_requests(self, limiter):
        """Test rate limit blocks excessive requests"""
        user_id = "test_heavy_user"
        limit_name = "api_general"
        
        # Make requests up to the limit
        allowed_count = 0
        for i in range(120):  # Try more than the limit
            allowed, status = await limiter.is_allowed(user_id, limit_name)
            if allowed:
                allowed_count += 1
            else:
                break
        
        # Should have blocked before 120 requests
        assert allowed_count < 120
        
        # The blocking request should have proper status
        blocked_allowed, blocked_status = await limiter.is_allowed(user_id, limit_name)
        assert blocked_allowed == False
        assert blocked_status['allowed'] == False
        assert blocked_status['usage_percentage'] >= 100
    
    @pytest.mark.asyncio
    async def test_concurrent_resource_limits(self, limiter):
        """Test concurrent resource limiting"""
        user_id = "test_concurrent_user"
        
        # Acquire resources up to the limit
        acquired = []
        for i in range(10):  # Try to acquire more than default limit (5)
            success = await limiter.acquire_resource(user_id, "concurrent_jobs")
            acquired.append(success)
        
        # Should have blocked some acquisitions
        successful_acquisitions = sum(acquired)
        assert successful_acquisitions <= 5  # Default concurrent limit
        
        # Release a resource and try again
        await limiter.release_resource(user_id, "concurrent_jobs")
        success = await limiter.acquire_resource(user_id, "concurrent_jobs")
        assert success == True
    
    @pytest.mark.asyncio
    async def test_different_users_separate_limits(self, limiter):
        """Test that different users have separate rate limits"""
        # User 1 hits their limit
        for i in range(100):
            await limiter.is_allowed("user1", "api_general")
        
        user1_blocked, _ = await limiter.is_allowed("user1", "api_general")
        user2_allowed, _ = await limiter.is_allowed("user2", "api_general")
        
        # User 1 should be blocked, User 2 should be allowed
        assert user1_blocked == False
        assert user2_allowed == True
    
    def test_limits_status_reporting(self, limiter):
        """Test comprehensive limits status reporting"""
        user_id = "test_status_user"
        status = limiter.get_limits_status(user_id)
        
        # Should return status for all configured limits
        expected_limits = ["api_general", "api_upload", "api_transcription", "concurrent_jobs"]
        for limit_name in expected_limits:
            assert limit_name in status

class TestQuotaManager:
    """Test user quota management system"""
    
    @pytest.fixture
    def quota_mgr(self):
        """Create a fresh quota manager for each test"""
        return QuotaManager()
    
    @pytest.mark.asyncio
    async def test_get_user_quota_by_tier(self, quota_mgr):
        """Test getting user quotas by tier"""
        free_quota = await quota_mgr.get_user_quota("user1", "free")
        premium_quota = await quota_mgr.get_user_quota("user2", "premium")
        enterprise_quota = await quota_mgr.get_user_quota("user3", "enterprise")
        
        # Premium should have higher limits than free
        assert premium_quota.daily_transcription_minutes > free_quota.daily_transcription_minutes
        assert enterprise_quota.daily_transcription_minutes > premium_quota.daily_transcription_minutes
        
        # Verify tier assignment
        assert free_quota.tier == "free"
        assert premium_quota.tier == "premium"
        assert enterprise_quota.tier == "enterprise"
    
    @pytest.mark.asyncio
    async def test_quota_consumption_tracking(self, quota_mgr):
        """Test quota consumption is properly tracked"""
        user_id = "test_consumption_user"
        
        # Initial usage should be zero
        usage = await quota_mgr.get_user_usage(user_id)
        assert usage.daily_transcription_minutes_used == 0.0
        assert usage.api_calls_this_hour == 0
        
        # Consume some quota
        await quota_mgr.consume_quota(user_id, transcription_minutes=10.0, api_calls=5)
        
        # Verify consumption is tracked
        updated_usage = await quota_mgr.get_user_usage(user_id)
        assert updated_usage.daily_transcription_minutes_used == 10.0
        assert updated_usage.api_calls_this_hour == 5
    
    @pytest.mark.asyncio
    async def test_quota_violation_detection(self, quota_mgr):
        """Test quota violation detection"""
        user_id = "test_violation_user"
        user_tier = "free"
        
        # Try to exceed daily transcription limit
        quota_ok, status = await quota_mgr.check_quota(
            user_id, user_tier, transcription_minutes=100.0  # More than free tier daily limit
        )
        
        assert quota_ok == False
        assert "daily_transcription_minutes_exceeded" in status['violations']
        assert len(status['violations']) > 0
    
    @pytest.mark.asyncio
    async def test_file_size_quota_check(self, quota_mgr):
        """Test file size quota checking"""
        user_id = "test_filesize_user"
        
        # Free tier has 50MB limit
        small_file_ok, _ = await quota_mgr.check_quota(user_id, "free", file_size_mb=25.0)
        large_file_ok, status = await quota_mgr.check_quota(user_id, "free", file_size_mb=100.0)
        
        assert small_file_ok == True
        assert large_file_ok == False
        assert "file_size_exceeded" in status['violations']
    
    @pytest.mark.asyncio
    async def test_storage_quota_accumulation(self, quota_mgr):
        """Test storage quota accumulation"""
        user_id = "test_storage_user"
        
        # Consume storage gradually
        await quota_mgr.consume_quota(user_id, storage_gb=0.3)
        await quota_mgr.consume_quota(user_id, storage_gb=0.4)
        await quota_mgr.consume_quota(user_id, storage_gb=0.5)  # Total: 1.2GB
        
        # Free tier has 1.0GB limit, should be exceeded
        quota_ok, status = await quota_mgr.check_quota(user_id, "free", storage_gb=0.1)
        
        assert quota_ok == False
        assert "storage_quota_exceeded" in status['violations']
    
    @pytest.mark.asyncio
    async def test_quota_summary_generation(self, quota_mgr):
        """Test comprehensive quota summary"""
        user_id = "test_summary_user"
        user_tier = "premium"
        
        # Use some quota
        await quota_mgr.consume_quota(user_id, transcription_minutes=50.0, storage_gb=5.0)
        
        summary = await quota_mgr.get_quota_summary(user_id, user_tier)
        
        # Verify summary structure
        assert 'quota' in summary
        assert 'usage' in summary
        assert 'usage_percentages' in summary
        assert 'limits_approaching' in summary
        
        # Verify percentages are calculated
        assert 0 <= summary['usage_percentages']['daily_transcription'] <= 100
        assert 0 <= summary['usage_percentages']['storage'] <= 100

class TestIntegratedRateLimitingSystem:
    """Test the integrated rate limiting system"""
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_function(self):
        """Test the check_rate_limit utility function"""
        # Test normal usage
        allowed, status = await check_rate_limit("test_user", "general")
        assert allowed == True
        
        # Test with different endpoint types
        upload_allowed, _ = await check_rate_limit("test_user", "upload")
        transcription_allowed, _ = await check_rate_limit("test_user", "transcription")
        
        assert upload_allowed == True
        assert transcription_allowed == True
    
    @pytest.mark.asyncio
    async def test_check_user_quota_function(self):
        """Test the check_user_quota utility function"""
        # Test normal quota check
        allowed, status = await check_user_quota("test_user", "free")
        assert allowed == True
        
        # Test quota violation
        violation_allowed, violation_status = await check_user_quota(
            "test_user", "free", transcription_minutes=1000.0  # Exceeds daily limit
        )
        assert violation_allowed == False
        assert len(violation_status['violations']) > 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_exhaustion_scenario(self):
        """Test complete rate limit exhaustion scenario"""
        user_id = "exhaustion_test_user"
        
        # Rapidly make requests until rate limited
        requests_made = 0
        max_requests = 200  # Safety limit
        
        for i in range(max_requests):
            allowed, status = await check_rate_limit(user_id, "general")
            requests_made += 1
            
            if not allowed:
                # Rate limit hit
                assert status['allowed'] == False
                assert 'current_requests' in status or 'usage_percentage' in status
                break
        
        # Should have hit rate limit before max_requests
        assert requests_made < max_requests
        
        # Subsequent request should still be blocked
        still_blocked, _ = await check_rate_limit(user_id, "general")
        assert still_blocked == False
    
    @pytest.mark.asyncio
    async def test_quota_exhaustion_scenario(self):
        """Test complete quota exhaustion scenario"""
        user_id = "quota_exhaustion_user"
        user_tier = "free"
        
        # Consume quota up to the limit
        await quota_manager.consume_quota(user_id, transcription_minutes=55.0)  # Near daily limit
        
        # Try to use more quota
        allowed, status = await check_user_quota(user_id, user_tier, transcription_minutes=10.0)
        
        assert allowed == False
        assert "daily_transcription_minutes_exceeded" in status['violations']
        assert status['remaining']['daily_transcription_minutes'] < 10.0
    
    @pytest.mark.asyncio
    async def test_multiple_quota_violations(self):
        """Test scenarios with multiple quota violations"""
        user_id = "multi_violation_user"
        
        # Set up user with high usage
        await quota_manager.consume_quota(
            user_id, 
            transcription_minutes=55.0,  # Near daily limit
            storage_gb=0.9  # Near storage limit
        )
        
        # Try operation that would violate multiple quotas
        allowed, status = await check_user_quota(
            user_id, 
            "free",
            transcription_minutes=10.0,  # Would exceed daily
            storage_gb=0.2  # Would exceed storage
        )
        
        assert allowed == False
        violations = status['violations']
        assert "daily_transcription_minutes_exceeded" in violations
        assert "storage_quota_exceeded" in violations
        assert len(violations) >= 2

# Integration tests with mocked FastAPI request
class TestServerIntegration:
    """Test integration with server middleware"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_disabled_mode(self):
        """Test system behavior when rate limiting is disabled"""
        with patch.dict(os.environ, {"RATE_LIMITING_ENABLED": "false"}):
            # Create new instances with disabled rate limiting
            disabled_limiter = RateLimiter()
            
            # Should always allow requests when disabled
            for i in range(1000):  # Far beyond normal limits
                allowed, status = await disabled_limiter.is_allowed("test_user", "api_general")
                assert allowed == True
                assert status["status"] == "rate_limiting_disabled"
    
    @pytest.mark.asyncio
    async def test_quota_disabled_mode(self):
        """Test system behavior when quotas are disabled"""
        with patch.dict(os.environ, {"QUOTA_ENABLED": "false"}):
            disabled_quota_mgr = QuotaManager()
            
            # Should always allow operations when disabled
            allowed, status = await disabled_quota_mgr.check_quota(
                "test_user", "free", transcription_minutes=10000.0  # Huge amount
            )
            assert allowed == True
            assert status["status"] == "quotas_disabled"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])