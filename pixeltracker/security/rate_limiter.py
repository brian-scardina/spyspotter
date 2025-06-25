#!/usr/bin/env python3
"""
Distributed rate limiting using Redis token bucket algorithm

Provides rate limiting capabilities for both CLI and API usage with
global and per-domain limits.
"""

import time
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests: int = 100  # Max requests per window
    window_seconds: int = 60  # Time window in seconds
    refill_rate: float = 1.0  # Tokens added per second
    burst_size: int = 10  # Max burst tokens
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.max_requests
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens, return True if successful"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now
        
        # Add tokens based on refill rate
        tokens_to_add = elapsed * self.config.refill_rate
        self.tokens = min(
            self.config.max_requests,
            self.tokens + tokens_to_add
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return {
            'tokens': self.tokens,
            'last_refill': self.last_refill,
            'config': self.config.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenBucket':
        """Create from dictionary"""
        config = RateLimitConfig(**data['config'])
        bucket = cls(config)
        bucket.tokens = data['tokens']
        bucket.last_refill = data['last_refill']
        return bucket


class DistributedRateLimiter:
    """Distributed rate limiter using Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is required for distributed rate limiting")
        
        self.redis_url = redis_url
        self.redis_client = None
        self.default_config = RateLimitConfig()
        self.global_config = RateLimitConfig(
            max_requests=1000,
            window_seconds=3600,  # 1 hour
            refill_rate=0.28,     # ~1000 per hour
            burst_size=50
        )
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    @asynccontextmanager
    async def rate_limit_context(self):
        """Context manager for rate limiting"""
        await self.initialize()
        try:
            yield self
        finally:
            await self.close()
    
    async def check_rate_limit(
        self,
        key: str,
        config: Optional[RateLimitConfig] = None,
        tokens: int = 1
    ) -> Dict[str, Any]:
        """
        Check rate limit for a given key
        
        Returns:
            Dict with 'allowed', 'remaining', 'reset_time', and 'retry_after'
        """
        if not self.redis_client:
            await self.initialize()
        
        config = config or self.default_config
        redis_key = f"rate_limit:{key}"
        
        try:
            # Get current bucket state
            bucket_data = await self.redis_client.get(redis_key)
            
            if bucket_data:
                bucket = TokenBucket.from_dict(json.loads(bucket_data))
            else:
                bucket = TokenBucket(config)
            
            # Try to consume tokens
            allowed = bucket.consume(tokens)
            
            # Save updated bucket state
            await self.redis_client.setex(
                redis_key,
                config.window_seconds * 2,  # TTL with buffer
                json.dumps(bucket.to_dict())
            )
            
            # Calculate reset time and retry after
            reset_time = bucket.last_refill + config.window_seconds
            retry_after = max(0, tokens - bucket.tokens) / config.refill_rate if not allowed else 0
            
            return {
                'allowed': allowed,
                'remaining': int(bucket.tokens),
                'reset_time': reset_time,
                'retry_after': retry_after,
                'key': key
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed for {key}: {e}")
            # Fail open - allow request if Redis is down
            return {
                'allowed': True,
                'remaining': config.max_requests,
                'reset_time': time.time() + config.window_seconds,
                'retry_after': 0,
                'key': key,
                'error': str(e)
            }
    
    async def check_global_limit(self, client_id: str) -> Dict[str, Any]:
        """Check global rate limit"""
        return await self.check_rate_limit(
            f"global:{client_id}",
            self.global_config
        )
    
    async def check_domain_limit(self, domain: str, client_id: str) -> Dict[str, Any]:
        """Check per-domain rate limit"""
        domain_config = RateLimitConfig(
            max_requests=50,
            window_seconds=300,  # 5 minutes
            refill_rate=0.17,    # ~50 per 5 minutes
            burst_size=10
        )
        
        return await self.check_rate_limit(
            f"domain:{domain}:{client_id}",
            domain_config
        )
    
    async def get_rate_limit_status(self, client_id: str) -> Dict[str, Any]:
        """Get comprehensive rate limit status"""
        global_status = await self.check_global_limit(client_id)
        
        return {
            'client_id': client_id,
            'global': global_status,
            'timestamp': time.time()
        }


class LocalRateLimiter:
    """Local rate limiter fallback when Redis is not available"""
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.default_config = RateLimitConfig()
    
    def _get_or_create_bucket(self, key: str, config: RateLimitConfig) -> TokenBucket:
        """Get or create token bucket for key"""
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(config)
        return self.buckets[key]
    
    def check_rate_limit(
        self,
        key: str,
        config: Optional[RateLimitConfig] = None,
        tokens: int = 1
    ) -> Dict[str, Any]:
        """Check rate limit locally"""
        config = config or self.default_config
        bucket = self._get_or_create_bucket(key, config)
        
        allowed = bucket.consume(tokens)
        retry_after = max(0, tokens - bucket.tokens) / config.refill_rate if not allowed else 0
        
        return {
            'allowed': allowed,
            'remaining': int(bucket.tokens),
            'reset_time': bucket.last_refill + config.window_seconds,
            'retry_after': retry_after,
            'key': key,
            'local': True
        }


def create_rate_limiter(redis_url: Optional[str] = None) -> DistributedRateLimiter:
    """Create rate limiter instance"""
    if redis_url and REDIS_AVAILABLE:
        return DistributedRateLimiter(redis_url)
    else:
        logger.warning("Redis not available, using local rate limiter")
        return LocalRateLimiter()


# CLI integration functions
def add_rate_limit_args(parser):
    """Add rate limiting arguments to CLI parser"""
    rate_group = parser.add_argument_group('rate limiting')
    rate_group.add_argument(
        '--global-rate-limit',
        type=int,
        default=1000,
        help='Global rate limit (requests per hour)'
    )
    rate_group.add_argument(
        '--domain-rate-limit',
        type=int, 
        default=50,
        help='Per-domain rate limit (requests per 5 minutes)'
    )
    rate_group.add_argument(
        '--redis-url',
        default='redis://localhost:6379/0',
        help='Redis URL for distributed rate limiting'
    )
    rate_group.add_argument(
        '--disable-rate-limiting',
        action='store_true',
        help='Disable rate limiting'
    )


async def check_rate_limits(
    url: str,
    client_id: str,
    rate_limiter: DistributedRateLimiter
) -> bool:
    """
    Check both global and domain rate limits
    
    Returns True if request is allowed, False if rate limited
    """
    from urllib.parse import urlparse
    
    try:
        domain = urlparse(url).netloc
        
        # Check global limit
        global_check = await rate_limiter.check_global_limit(client_id)
        if not global_check['allowed']:
            logger.warning(f"Global rate limit exceeded for {client_id}")
            return False
        
        # Check domain limit
        domain_check = await rate_limiter.check_domain_limit(domain, client_id)
        if not domain_check['allowed']:
            logger.warning(f"Domain rate limit exceeded for {domain}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Fail open
        return True
