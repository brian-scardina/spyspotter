#!/usr/bin/env python3
"""
Enhanced Tracking Pixel Scanner
A comprehensive tool for detecting tracking technologies with advanced capabilities.
"""

import asyncio
import aiohttp
import re
import json
import time
import hashlib
import sqlite3
import warnings

import whois
import dns.resolver

try:
    from elasticsearch import Elasticsearch
    OPTIONAL_DEPS['elasticsearch'] = True
except ImportError:
    Elasticsearch = None

# Import our comprehensive tracker database
try:
    from .tracker_database import tracker_db
except ImportError:
    print("Warning: Could not import tracker database. Using fallback patterns.")
    tracker_db = None
from urllib.parse import urlparse, parse_qs, urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import tempfile
import yaml

from .ml import MLModels
from .browser import scan_with_javascript
from .config import Config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TrackerInfo:
    """Data class for tracking information"""
    tracker_type: str
    domain: str
    source: str
    category: str
    risk_level: str
    purpose: str
    first_seen: str
    details: Dict[str, Any]

@dataclass
class ScanResult:
    """Data class for scan results"""
    url: str
    timestamp: str
    trackers: List[TrackerInfo]
    performance_metrics: Dict[str, Any]
    privacy_score: int
    risk_assessment: Dict[str, Any]


class EnhancedTrackingScanner:
    """Enhanced tracking scanner with advanced capabilities"""

    def __init__(self, config: Config):
        self.config = config
        self.tracker_db = tracker_db
        self.ml_models = MLModels()
        self.session_cache = {}
        self.performance_metrics = {}

        # Advanced detection patterns
        self.advanced_patterns = {
            'fingerprinting': [
                r'canvas\.toDataURL',
                r'AudioContext',
                r'webkitAudioContext',
                r'navigator\.hardwareConcurrency',
                r'screen\.colorDepth',
                r'navigator\.deviceMemory'
            ],
            'webrtc_leaks': [
                r'RTCPeerConnection',
                r'webkitRTCPeerConnection',
                r'mozRTCPeerConnection'
            ],
            'storage_tracking': [
                r'localStorage\.setItem',
                r'sessionStorage\.setItem',
                r'indexedDB',
                r'document\.cookie'
            ],
            'timing_attacks': [
                r'performance\.now',
                r'performance\.timing',
                r'Date\.now'
            ]
        }

    async def fetch_with_performance_metrics(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """Fetch URL with detailed performance metrics"""
        start_time = time.time()

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config.get('scanning.request_timeout'))) as response:
                content = await response.text()

                metrics = {
                    'response_time': time.time() - start_time,
                    'status_code': response.status,
                    'content_length': len(content),
                    'headers': dict(response.headers),
                    'redirects': len(response.history),
                    'final_url': str(response.url)
                }

                return {'content': content, 'metrics': metrics}

        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return {'content': '', 'metrics': {'error': str(e)}}

    def detect_advanced_tracking(self, content: str, url: str) -> List[TrackerInfo]:
        """Detect advanced tracking techniques"""
        trackers = []

        # Canvas fingerprinting detection
        if re.search(r'canvas\.toDataURL|getContext\(["\']2d["\']\)', content, re.IGNORECASE):
            trackers.append(TrackerInfo(
                tracker_type='fingerprinting',
                domain=urlparse(url).netloc,
                source='canvas_fingerprinting',
                category='privacy_invasion',
                risk_level='high',
                purpose='device_fingerprinting',
                first_seen=datetime.now().isoformat(),
                details={'method': 'canvas_fingerprinting'}
            ))

        # WebRTC leak detection
        if re.search(r'RTCPeerConnection|webkitRTCPeerConnection', content, re.IGNORECASE):
            trackers.append(TrackerInfo(
                tracker_type='webrtc_leak',
                domain=urlparse(url).netloc,
                source='webrtc_detection',
                category='privacy_invasion',
                risk_level='high',
                purpose='ip_leak',
                first_seen=datetime.now().isoformat(),
                details={'method': 'webrtc_stun'}
            ))

        # Font fingerprinting
        if re.search(r'@font-face|fontface|measureText', content, re.IGNORECASE):
            trackers.append(TrackerInfo(
                tracker_type='fingerprinting',
                domain=urlparse(url).netloc,
                source='font_fingerprinting',
                category='privacy_invasion',
                risk_level='medium',
                purpose='font_fingerprinting',
                first_seen=datetime.now().isoformat(),
                details={'method': 'font_enumeration'}
            ))

        return trackers

    def analyze_request_patterns(self, requests: List[Dict[str, Any]]) -> List[TrackerInfo]:
        """Analyze network request patterns for tracking"""
        trackers = []
        suspicious_patterns = []

        for request in requests:
            url = request.get('url', '')
            parsed_url = urlparse(url)

            # Check for tracking parameters
            query_params = parse_qs(parsed_url.query)
            tracking_params = ['utm_', 'fbclid', 'gclid', '_ga', 'mc_eid']

            for param in query_params:
                if any(tp in param.lower() for tp in tracking_params):
                    suspicious_patterns.append(f"tracking_parameter:{param}")

            # Check for pixel-like requests (small images)
            if parsed_url.path.endswith(('.gif', '.png', '.jpg')) and 'pixel' in url.lower():
                trackers.append(TrackerInfo(
                    tracker_type='tracking_pixel',
                    domain=parsed_url.netloc,
                    source=url,
                    category='analytics',
                    risk_level='medium',
                    purpose='page_tracking',
                    first_seen=datetime.now().isoformat(),
                    details={'url': url, 'method': 'pixel_request'}
                ))

        return trackers

    async def scan_url_comprehensive(self, url: str) -> ScanResult:
        """Comprehensive scan of a single URL"""
        start_time = time.time()

        async with aiohttp.ClientSession(
            headers=self.config.get('headers'),
            timeout=aiohttp.ClientTimeout(total=self.config.get('scanning.request_timeout'))
        ) as session:

            # Fetch with metrics
            result = await self.fetch_with_performance_metrics(session, url)
            content = result['content']
            metrics = result['metrics']

            # Basic tracking detection (from original scanner)
            basic_trackers = self.detect_basic_tracking(content, url)

            # Advanced tracking detection
            advanced_trackers = self.detect_advanced_tracking(content, url)

            # JavaScript execution (if enabled)
            js_result = {}
            if self.config.get('javascript.enabled'):
                js_result = await scan_with_javascript(url)

            # Combine all trackers
            all_trackers = basic_trackers + advanced_trackers

            # Calculate privacy score
            privacy_score = self.calculate_privacy_score(all_trackers, metrics)

            # Risk assessment
            risk_assessment = self.assess_privacy_risks(all_trackers, url)

            # Performance metrics
            performance_metrics = {
                **metrics,
                'scan_duration': time.time() - start_time,
                'tracker_count': len(all_trackers),
                'js_enabled': self.config.get('javascript.enabled')
            }

            return ScanResult(
                url=url,
                timestamp=datetime.now().isoformat(),
                trackers=all_trackers,
                performance_metrics=performance_metrics,
                privacy_score=privacy_score,
                risk_assessment=risk_assessment
            )

    def detect_basic_tracking(self, content: str, url: str) -> List[TrackerInfo]:
        """Basic tracking detection (simplified from original)"""
        trackers = []
        soup = BeautifulSoup(content, 'html.parser')

        # Find tracking scripts
        scripts = soup.find_all('script')
        for script in scripts:
            src = script.get('src', '')
            if src:
                domain = urlparse(src).netloc
                if self.tracker_db and domain in self.tracker_db.trackers:
                    tracker_info = self.tracker_db.get_tracker_by_domain(domain)
                    if tracker_info:
                        trackers.append(TrackerInfo(
                            tracker_type='javascript',
                            domain=domain,
                            source=src,
                            category=tracker_info.category,
                            risk_level=tracker_info.risk_level,
                            purpose=tracker_info.description,
                            first_seen=tracker_info.first_seen,
                            details={'element': str(script)[:200]}
                        ))

        return trackers

    def calculate_privacy_score(self, trackers: List[TrackerInfo], metrics: Dict[str, Any]) -> int:
        """Calculate comprehensive privacy score"""
        base_score = 100

        # Deduct points based on tracker types and risk levels
        for tracker in trackers:
            if tracker.risk_level == 'high':
                base_score -= self.config.get('privacy.scoring_weights.high_risk_domain', 15)
            elif tracker.risk_level == 'medium':
                base_score -= self.config.get('privacy.scoring_weights.medium_risk_domain', 8)
            elif tracker.risk_level == 'low':
                base_score -= self.config.get('privacy.scoring_weights.low_risk_domain', 3)

            # Additional deductions for certain categories
            if tracker.category in ['advertising', 'social_advertising']:
                base_score -= self.config.get('privacy.scoring_weights.advertising_tracker', 10)
            elif tracker.category == 'privacy_invasion':
                base_score -= self.config.get('privacy.scoring_weights.privacy_invasion', 20)

        return max(0, base_score)

    def perform_domain_analysis(self, urls: List[str]) -> Dict[str, Any]:
        """Perform additional domain analysis and WHOIS lookups"""
        domain_info = {}
        for url in urls:
            try:
                domain = urlparse(url).netloc
                whois_info = whois.whois(domain)
                dns_info = dns.resolver.resolve(domain)
                domain_info[domain] = {
                    'whois': whois_info,
                    'dns': [str(record) for record in dns_info]
                }
            except Exception as e:
                logger.warning(f"Failed domain analysis for {url}: {e}")
                domain_info[domain] = {'error': str(e)}
        return domain_info

    def assess_privacy_risks(self, trackers: List[TrackerInfo], url: str) -> Dict[str, Any]:
        """Comprehensive privacy risk assessment"""
        risks = {
            'overall_risk': 'low',
            'specific_risks': [],
            'data_collection': [],
            'third_party_domains': set(),
            'tracking_methods': set()
        }

        high_risk_count = sum(1 for t in trackers if t.risk_level == 'high')
        medium_risk_count = sum(1 for t in trackers if t.risk_level == 'medium')

        # Determine overall risk
        if high_risk_count > self.config.get('privacy.risk_thresholds.high_count', 3) or any(t.category == 'privacy_invasion' for t in trackers):
            risks['overall_risk'] = 'high'
        elif high_risk_count > 0 or medium_risk_count > self.config.get('privacy.risk_thresholds.medium_count', 5):
            risks['overall_risk'] = 'medium'

        # Collect specific information
        for tracker in trackers:
            risks['third_party_domains'].add(tracker.domain)
            risks['tracking_methods'].add(tracker.tracker_type)

            if tracker.category == 'advertising':
                risks['data_collection'].append('behavioral_profiling')
            elif tracker.category == 'analytics':
                risks['data_collection'].append('usage_analytics')

        # Convert sets to lists for JSON serialization
        risks['third_party_domains'] = list(risks['third_party_domains'])
        risks['tracking_methods'] = list(risks['tracking_methods'])
        risks['data_collection'] = list(set(risks['data_collection']))

        return risks

    async def scan_multiple_urls(self, urls: List[str]) -> List[ScanResult]:
        """Scan multiple URLs concurrently"""
        semaphore = asyncio.Semaphore(self.config.get('scanning.concurrent_requests'))

        async def scan_with_semaphore(url):
            async with semaphore:
                return await self.scan_url_comprehensive(url)

        tasks = [scan_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scan {urls[i]}: {result}")
            else:
                valid_results.append(result)

        return valid_results

    def generate_intelligence_report(self, results: List[ScanResult]) -> Dict[str, Any]:
        """Generate comprehensive intelligence report"""
        report = {
            'scan_summary': {
                'total_urls': len(results),
                'scan_timestamp': datetime.now().isoformat(),
                'total_trackers': sum(len(r.trackers) for r in results),
                'average_privacy_score': sum(r.privacy_score for r in results) / len(results) if results else 0
            },
            'threat_intelligence': {},
            'recommendations': [],
            'compliance_status': {},
            'trends': {}
        }

        # Analyze threat intelligence
        all_domains = set()
        category_counts = {}

        for result in results:
            for tracker in result.trackers:
                all_domains.add(tracker.domain)
                category_counts[tracker.category] = category_counts.get(tracker.category, 0) + 1

        report['threat_intelligence'] = {
            'unique_tracking_domains': len(all_domains),
            'top_categories': dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'most_tracked_domains': list(all_domains)[:20]
        }

        return report
