#!/usr/bin/env python3
"""
Basic tracking scanner implementation

Uses modular services for a straightforward tracking pixel detection.
"""

import asyncio
import time
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from ..interfaces import Fetcher, Parser, Storage, Analyzer, Reporter
from ..services import NetworkService, HTMLParserService, StorageService, AnalyzerService, ReporterService
from ..models import (
    ScanResult, TrackerInfo, PerformanceMetrics, PrivacyAnalysis, 
    RiskLevel, TrackerCategory, ScanConfiguration
)
from ..config import ConfigManager
import logging

logger = logging.getLogger(__name__)


class BasicTrackingScanner:
    """Basic tracking scanner using modular services"""
    
    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        fetcher: Optional[Fetcher] = None,
        parser: Optional[Parser] = None,
        storage: Optional[Storage] = None,
        analyzer: Optional[Analyzer] = None,
        reporter: Optional[Reporter] = None
    ):
        """
        Initialize the basic scanner with dependency injection
        
        Args:
            config_manager: Configuration manager instance
            fetcher: Custom fetcher implementation
            parser: Custom parser implementation  
            storage: Custom storage implementation
            analyzer: Custom analyzer implementation
            reporter: Custom reporter implementation
        """
        self.config_manager = config_manager or ConfigManager()
        
        # Create scan configuration
        scan_config = self.config_manager.get_scan_configuration()
        
        # Initialize services with dependency injection
        self.fetcher = fetcher or NetworkService(scan_config)
        self.parser = parser or HTMLParserService()
        self.storage = storage or StorageService(self.config_manager.database.path)
        self.analyzer = analyzer or AnalyzerService()
        self.reporter = reporter or ReporterService()
        
        logger.info("BasicTrackingScanner initialized")
    
    async def scan_url(self, url: str) -> ScanResult:
        """
        Scan a single URL for tracking pixels
        
        Args:
            url: URL to scan
            
        Returns:
            ScanResult containing analysis results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting scan of {url}")
            
            # Fetch content
            fetch_result = await self.fetcher.fetch(url)
            content = fetch_result['content']
            fetch_metrics = fetch_result['metrics']
            
            if not content:
                return self._create_error_result(url, "Failed to fetch content", start_time)
            
            # Parse content for tracking elements
            parsed_data = self.parser.parse(content, url)
            
            # Convert parsed data to TrackerInfo objects
            trackers = self._convert_to_tracker_info(parsed_data, url)
            
            # Create performance metrics
            performance_metrics = PerformanceMetrics(
                response_time=fetch_metrics.get('response_time', 0),
                content_length=fetch_metrics.get('content_length', 0),
                status_code=fetch_metrics.get('status_code', 200),
                redirects=fetch_metrics.get('redirects', 0)
            )
            
            # Analyze privacy impact
            privacy_impact = self.analyzer.analyze_privacy_impact(trackers, url=url)
            privacy_analysis = PrivacyAnalysis(
                privacy_score=privacy_impact['privacy_score'],
                risk_level=privacy_impact['risk_level'],
                detected_categories=privacy_impact['detected_categories'],
                high_risk_domains=privacy_impact['high_risk_domains'],
                recommendations=privacy_impact['recommendations']
            )
            
            # Create scan result
            scan_duration = time.time() - start_time
            result = ScanResult(
                url=url,
                timestamp=datetime.now().isoformat(),
                trackers=trackers,
                performance_metrics=performance_metrics,
                privacy_analysis=privacy_analysis,
                scan_duration=scan_duration,
                scan_type="basic",
                javascript_enabled=False
            )
            
            # Store result if storage is enabled
            if self.config_manager.database.enabled:
                await self.storage.store_result(result)
            
            logger.info(f"Completed scan of {url} in {scan_duration:.2f}s - found {len(trackers)} trackers")
            return result
            
        except Exception as e:
            logger.error(f"Error scanning {url}: {e}")
            return self._create_error_result(url, str(e), start_time)
    
    async def scan_multiple_urls(self, urls: List[str]) -> List[ScanResult]:
        """
        Scan multiple URLs concurrently
        
        Args:
            urls: List of URLs to scan
            
        Returns:
            List of ScanResult objects
        """
        concurrent_limit = self.config_manager.scanning.concurrent_requests
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def scan_with_semaphore(url: str) -> ScanResult:
            async with semaphore:
                return await self.scan_url(url)
        
        logger.info(f"Starting concurrent scan of {len(urls)} URLs (limit: {concurrent_limit})")
        
        tasks = [scan_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scan {urls[i]}: {result}")
                error_result = self._create_error_result(urls[i], str(result), time.time())
                valid_results.append(error_result)
            else:
                valid_results.append(result)
        
        logger.info(f"Completed scan of {len(urls)} URLs")
        return valid_results
    
    def _convert_to_tracker_info(self, parsed_data: dict, url: str) -> List[TrackerInfo]:
        """Convert parsed data to TrackerInfo objects"""
        trackers = []
        
        # Process tracking pixels
        for pixel in parsed_data.get('pixels', []):
            domain = self._extract_domain(pixel.get('src', ''))
            tracker = TrackerInfo(
                tracker_type='tracking_pixel',
                domain=domain,
                source=pixel.get('src', ''),
                category=TrackerCategory.ANALYTICS,  # Default category
                risk_level=RiskLevel.MEDIUM,
                purpose='tracking',
                first_seen=datetime.now().isoformat(),
                details=pixel
            )
            trackers.append(tracker)
        
        # Process JavaScript trackers
        for js_tracker in parsed_data.get('js_trackers', []):
            domain = js_tracker.get('domain', self._extract_domain(js_tracker.get('src', '')))
            tracker = TrackerInfo(
                tracker_type='javascript_tracker',
                domain=domain,
                source=js_tracker.get('src', 'inline'),
                category=TrackerCategory.ANALYTICS,
                risk_level=RiskLevel.HIGH if js_tracker.get('type') == 'external_script' else RiskLevel.MEDIUM,
                purpose='tracking',
                first_seen=datetime.now().isoformat(),
                details=js_tracker
            )
            trackers.append(tracker)
        
        # Process meta trackers
        for meta_tracker in parsed_data.get('meta_trackers', []):
            domain = urlparse(url).netloc  # Use current domain for meta tags
            tracker = TrackerInfo(
                tracker_type='meta_tracker',
                domain=domain,
                source='meta_tag',
                category=TrackerCategory.ANALYTICS,
                risk_level=RiskLevel.LOW,
                purpose='verification',
                first_seen=datetime.now().isoformat(),
                details=meta_tracker
            )
            trackers.append(tracker)
        
        return trackers
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc or 'unknown'
        except Exception:
            return 'unknown'
    
    def _create_error_result(self, url: str, error_message: str, start_time: float) -> ScanResult:
        """Create a ScanResult for errors"""
        scan_duration = time.time() - start_time
        
        return ScanResult(
            url=url,
            timestamp=datetime.now().isoformat(),
            trackers=[],
            performance_metrics=PerformanceMetrics(
                response_time=0,
                content_length=0,
                status_code=0,
                redirects=0
            ),
            privacy_analysis=PrivacyAnalysis(
                privacy_score=0,
                risk_level=RiskLevel.LOW,
                detected_categories=[],
                high_risk_domains=[],
                recommendations=[]
            ),
            scan_duration=scan_duration,
            scan_type="basic",
            javascript_enabled=False,
            error=error_message
        )
    
    async def generate_report(self, results: List[ScanResult], format: str = "json") -> str:
        """Generate a report from scan results"""
        return self.reporter.generate_report(results, format)
    
    async def export_results(self, results: List[ScanResult], output_path: str, format: str = "json") -> bool:
        """Export scan results to file"""
        return self.reporter.export_data(results, format, output_path)
    
    def get_configuration(self) -> ConfigManager:
        """Get the current configuration manager"""
        return self.config_manager
    
    async def get_stored_results(self, url: Optional[str] = None, limit: Optional[int] = None) -> List[ScanResult]:
        """Retrieve stored scan results"""
        if not self.config_manager.database.enabled:
            logger.warning("Database storage is disabled")
            return []
        
        return await self.storage.retrieve_results(url, limit)
