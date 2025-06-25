#!/usr/bin/env python3
"""
Network service implementation for PixelTracker

Handles HTTP requests, rate limiting, retries, and more.
"""

import asyncio
import aiohttp
import time
import random
from typing import Dict, Any
from urllib.parse import urlparse
from ..interfaces import Fetcher
from ..models import ScanConfiguration
import logging

logger = logging.getLogger(__name__)


class NetworkService(Fetcher):
    """Asynchronous network service for web requests"""
    
    def __init__(self, config: ScanConfiguration):
        self.config = config
        self.headers = config.custom_headers or {}
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.last_request_time = 0
        
    def _get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)

    async def fetch(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch content from a URL asynchronously.

        Args:
            url: URL to fetch
            **kwargs: Additional request parameters

        Returns:
            Dictionary containing fetch results and metadata
        """
        async with aiohttp.ClientSession(
            headers={**self.headers, 'User-Agent': self._get_random_user_agent()},
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
        ) as session:
            await self._enforce_rate_limit()
            response_content, metrics = await self._fetch_content(session, url, **kwargs)
            return {
                'content': response_content,
                'metrics': metrics
            }

    async def _fetch_content(self, session: aiohttp.ClientSession, url: str, **kwargs) -> tuple[str, Dict[str, Any]]:
        """Handle the fetching of the content from URL."""
        try:
            start_time = time.time()
            async with session.get(url, **kwargs) as response:
                response.raise_for_status()
                content = await response.text()
                elapsed_time = time.time() - start_time
                metrics = {
                    'response_time': elapsed_time,
                    'status_code': response.status,
                    'content_length': len(content)
                }
                logger.info(f"Fetched {url} in {elapsed_time:.2f}s (Status Code: {response.status})")
                return content, metrics
        except aiohttp.ClientResponseError as e:
            logger.error(f"Client error {e.status} while fetching {url}: {e.message}")
            raise e
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise e

    async def _enforce_rate_limit(self) -> None:
        """Enforce a delay between requests as per rate limit configuration"""
        elapsed_time = time.time() - self.last_request_time
        if elapsed_time < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - elapsed_time)
        self.last_request_time = time.time()

    def set_headers(self, headers: Dict[str, str]) -> None:
        self.headers.update(headers)

    def set_timeout(self, timeout: float) -> None:
        self.config.request_timeout = timeout
