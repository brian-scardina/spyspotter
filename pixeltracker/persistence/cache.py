#!/usr/bin/env python3
"""
Cache service for PixelTracker

Provides a caching mechanism for URL scan results using Redis with support for TTL and ETag.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import redis

logger = logging.getLogger(__name__)

class CacheService:
    """
    Caching service leveraging Redis for storing scanned URLs with TTL and ETag.
    """
    
    def __init__(self, redis_url: str = None, ttl_seconds: int = 3600):
        """
        Initialize the cache service
        
        Args:
            redis_url: URL for connecting to the Redis server
            ttl_seconds: Default time-to-live for cached items
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.ttl_seconds = ttl_seconds
        
        self.redis_client = redis.Redis.from_url(self.redis_url)
        logger.info(f"Initialized Redis caching with TTL={self.ttl_seconds} seconds")
    
    def get_cache_key(self, url: str) -> str:
        """Generate a cache key for a given URL"""
        return f"url_cache:{hash(url)}"
    
    def cache_scan_result(self, url: str, etag: str, scan_result: Dict[str, Any]) -> None:
        """Cache scan result with ETag support"""
        key = self.get_cache_key(url)
        value = json.dumps({'etag': etag, 'result': scan_result, 'cached_at': datetime.utcnow().isoformat()})
        self.redis_client.setex(key, self.ttl_seconds, value)
        logger.debug(f"Cached result for URL: {url} with ETag: {etag}")
    
    def get_cached_result(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached scan result if available and not expired"""
        key = self.get_cache_key(url)
        cached_value = self.redis_client.get(key)
        if cached_value:
            try:
                deserialized = json.loads(cached_value)
                if 'result' in deserialized:
                    logger.debug(f"Cache hit for URL: {url}")
                    return deserialized
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode cache entry for URL: {url}")
        else:
            logger.debug(f"Cache miss for URL: {url}")
        return None
    
    def invalidate_cache(self, url: str) -> None:
        """Invalidate cache entry for a URL"""
        key = self.get_cache_key(url)
        self.redis_client.delete(key)
        logger.info(f"Invalidated cache for URL: {url}")
