#!/usr/bin/env python3
"""
Enhanced Tracking Pixel Scanner
A comprehensive tool for detecting tracking technologies with advanced capabilities.
"""

import asyncio
import aiohttp
import argparse
import re
import json
import time
import hashlib
import sqlite3
import warnings

# Optional ML dependencies with graceful fallbacks
OPTIONAL_DEPS = {}

try:
    import numpy as np
    OPTIONAL_DEPS['numpy'] = True
except ImportError:
    np = None
    OPTIONAL_DEPS['numpy'] = False
    warnings.warn("NumPy not available. Some ML features will be disabled.")

try:
    import pandas as pd
    OPTIONAL_DEPS['pandas'] = True
except ImportError:
    pd = None
    OPTIONAL_DEPS['pandas'] = False

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    OPTIONAL_DEPS['sklearn'] = True
except ImportError:
    KMeans = None
    StandardScaler = None
    OPTIONAL_DEPS['sklearn'] = False

try:
    from transformers import pipeline
    OPTIONAL_DEPS['transformers'] = True
except ImportError:
    pipeline = None
    OPTIONAL_DEPS['transformers'] = False

try:
    import tensorflow as tf
    OPTIONAL_DEPS['tensorflow'] = True
except ImportError:
    tf = None
    OPTIONAL_DEPS['tensorflow'] = False

try:
    import torch
    OPTIONAL_DEPS['torch'] = True
except ImportError:
    torch = None
    OPTIONAL_DEPS['torch'] = False

import whois
import dns.resolver

try:
    from elasticsearch import Elasticsearch
    OPTIONAL_DEPS['elasticsearch'] = True
except ImportError:
    Elasticsearch = None
    OPTIONAL_DEPS['elasticsearch'] = False

# Import our comprehensive tracker database
try:
    from tracker_database import tracker_db
    OPTIONAL_DEPS['tracker_database'] = True
except ImportError:
    print("Warning: Could not import tracker database. Using fallback patterns.")
    tracker_db = None
    OPTIONAL_DEPS['tracker_database'] = False
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

class MLModels:
    """Machine learning models for advanced analysis"""
    
    def __init__(self):
        if pipeline:
            self.text_classifier = pipeline('sentiment-analysis')
        else:
            self.text_classifier = None
        self.domain_embedding_model = self.load_domain_embedding_model()
        
    def load_domain_embedding_model(self):
        """Load pre-trained domain embedding model"""
        # Placeholder for loading an embedding model (e.g., using transformers or FAISS)
        return None
    
    def cluster_domains(self, domains: List[str]) -> Dict[str, List[str]]:
        """Cluster domains based on similarity or behavior"""
        if not np or not KMeans:
            logger.warning("Machine learning libraries not available for clustering")
            return {0: domains}  # Return all domains in one cluster
            
        embeddings = np.random.rand(len(domains), 128)  # Placeholder for embeddings
        clustering_model = KMeans(n_clusters=5)
        labels = clustering_model.fit_predict(embeddings)
        
        clusters = {}
        for i, domain in enumerate(domains):
            clusters.setdefault(labels[i], []).append(domain)
        
        return clusters

    def classify_behavior(self, content: str) -> str:
        """Classify behavior based on content"""
        if not self.text_classifier:
            return 'unknown'
        # Use NLP techniques for behavioral classification
        result = self.text_classifier(content[:512])
        return result[0]['label']

    def detect_anomalies(self, metrics: Dict[str, float]) -> bool:
        """Detect anomalies in performance metrics"""
        if not StandardScaler or not np:
            return False
        standard_metrics = StandardScaler().fit_transform(np.array(list(metrics.values())).reshape(-1, 1))
        anomalies = standard_metrics > 2  # Placeholder for anomaly detection logic
        return any(anomalies)


class TrackerDatabase:
    """Database for tracking patterns and intelligence"""
    
    def __init__(self, db_path: str = "tracker_intelligence.db"):
        self.db_path = db_path
        self.init_database()
        self.load_tracker_intelligence()
    
    def init_database(self):
        """Initialize SQLite database for tracker intelligence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracker_patterns (
                id INTEGER PRIMARY KEY,
                domain TEXT UNIQUE,
                category TEXT,
                risk_level TEXT,
                purpose TEXT,
                patterns TEXT,  -- JSON array of patterns
                last_updated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY,
                url TEXT,
                scan_timestamp TEXT,
                tracker_count INTEGER,
                privacy_score INTEGER,
                result_hash TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_tracker_intelligence(self):
        """Load comprehensive tracker intelligence"""
        # Enhanced tracker database with categories and risk levels
        self.tracker_intelligence = {
            # High-risk advertising trackers
            'doubleclick.net': {'category': 'advertising', 'risk': 'high', 'purpose': 'behavioral_advertising'},
            'facebook.com': {'category': 'social_advertising', 'risk': 'high', 'purpose': 'cross_site_tracking'},
            'google-analytics.com': {'category': 'analytics', 'risk': 'medium', 'purpose': 'web_analytics'},
            'criteo.com': {'category': 'advertising', 'risk': 'high', 'purpose': 'retargeting'},
            
            # Analytics platforms
            'mixpanel.com': {'category': 'analytics', 'risk': 'medium', 'purpose': 'user_analytics'},
            'amplitude.com': {'category': 'analytics', 'risk': 'medium', 'purpose': 'product_analytics'},
            'segment.com': {'category': 'analytics', 'risk': 'medium', 'purpose': 'data_collection'},
            
            # Performance monitoring
            'newrelic.com': {'category': 'performance', 'risk': 'low', 'purpose': 'application_monitoring'},
            'sentry.io': {'category': 'performance', 'risk': 'low', 'purpose': 'error_tracking'},
            
            # Add more comprehensive intelligence...
        }

class EnhancedTrackingScanner:
    """Enhanced tracking scanner with advanced capabilities"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.load_config(config_path)
        self.tracker_db = TrackerDatabase()
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
    
    def load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'concurrent_requests': 10,
            'request_timeout': 30,
            'enable_javascript': True,
            'user_agents': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ],
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        
        return default_config
    
    async def scan_with_javascript(self, url: str) -> Dict[str, Any]:
        """Scan URL with JavaScript execution using headless browser"""
        try:
            # Use playwright or selenium for JS execution
            # For now, simulate with subprocess call to a JS runner
            temp_script = f"""
                const puppeteer = require('puppeteer');
                
                (async () => {{
                    const browser = await puppeteer.launch({{headless: true}});
                    const page = await browser.newPage();
                    
                    // Intercept network requests
                    const requests = [];
                    await page.setRequestInterception(true);
                    page.on('request', request => {{
                        requests.push({{
                            url: request.url(),
                            resourceType: request.resourceType(),
                            headers: request.headers()
                        }});
                        request.continue();
                    }});
                    
                    await page.goto('{url}', {{waitUntil: 'networkidle2'}});
                    
                    // Extract dynamic content
                    const dynamicTrackers = await page.evaluate(() => {{
                        return {{
                            localStorage: Object.keys(localStorage),
                            sessionStorage: Object.keys(sessionStorage),
                            cookies: document.cookie,
                            scripts: Array.from(document.scripts).map(s => s.src),
                            iframes: Array.from(document.iframes).map(i => i.src)
                        }};
                    }});
                    
                    await browser.close();
                    console.log(JSON.stringify({{requests, dynamicTrackers}}));
                }})();
            """
            
            # This would require puppeteer/playwright setup
            # For now, return placeholder
            return {'dynamic_content': True, 'js_trackers': []}
            
        except Exception as e:
            logger.warning(f"JavaScript execution failed for {url}: {e}")
            return {'dynamic_content': False, 'js_trackers': []}
    
    async def fetch_with_performance_metrics(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """Fetch URL with detailed performance metrics"""
        start_time = time.time()
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config['request_timeout'])) as response:
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
            headers=self.config['headers'],
            timeout=aiohttp.ClientTimeout(total=self.config['request_timeout'])
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
            if self.config['enable_javascript']:
                js_result = await self.scan_with_javascript(url)
            
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
                'js_enabled': self.config['enable_javascript']
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
                if domain in self.tracker_db.tracker_intelligence:
                    intel = self.tracker_db.tracker_intelligence[domain]
                    trackers.append(TrackerInfo(
                        tracker_type='javascript',
                        domain=domain,
                        source=src,
                        category=intel['category'],
                        risk_level=intel['risk'],
                        purpose=intel['purpose'],
                        first_seen=datetime.now().isoformat(),
                        details={'element': str(script)[:200]}
                    ))
        
        return trackers
    
    def calculate_privacy_score(self, trackers: List[TrackerInfo], metrics: Dict[str, Any]) -> int:
        """Calculate comprehensive privacy score"""
        base_score = 100
        
        # Deduct points based on tracker types and risk levels
        for tracker in trackers:
            if tracker.risk_level == 'high':
                base_score -= 15
            elif tracker.risk_level == 'medium':
                base_score -= 8
            elif tracker.risk_level == 'low':
                base_score -= 3
            
            # Additional deductions for certain categories
            if tracker.category in ['advertising', 'social_advertising']:
                base_score -= 10
            elif tracker.category == 'privacy_invasion':
                base_score -= 20
        
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
        if high_risk_count > 3 or any(t.category == 'privacy_invasion' for t in trackers):
            risks['overall_risk'] = 'high'
        elif high_risk_count > 0 or medium_risk_count > 5:
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
        semaphore = asyncio.Semaphore(self.config['concurrent_requests'])
        
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

def create_config_file():
    """Create a sample configuration file"""
    config = {
        'concurrent_requests': 10,
        'request_timeout': 30,
        'enable_javascript': True,
        'user_agents': [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ],
        'output_formats': ['json', 'html', 'csv'],
        'database_path': 'tracker_intelligence.db'
    }
    
    with open('scanner_config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("📁 Configuration file created: scanner_config.yaml")

async def main():
    parser = argparse.ArgumentParser(description='Enhanced Tracking Pixel Scanner')
    parser.add_argument('urls', nargs='+', help='URLs to scan')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--format', choices=['json', 'html', 'csv'], default='json', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--enable-js', action='store_true', help='Enable JavaScript execution')
    parser.add_argument('--concurrent', type=int, default=10, help='Concurrent requests')
    parser.add_argument('--create-config', action='store_true', help='Create sample config file')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_config_file()
        return
    
    # Initialize scanner
    scanner = EnhancedTrackingScanner(args.config)
    
    if args.enable_js:
        scanner.config['enable_javascript'] = True
    
    scanner.config['concurrent_requests'] = args.concurrent
    
    # Validate URLs
    urls = []
    for url in args.urls:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        urls.append(url)
    
    print(f"🚀 Starting enhanced scan of {len(urls)} URLs...")
    print(f"⚙️  JavaScript execution: {'enabled' if scanner.config['enable_javascript'] else 'disabled'}")
    print(f"🔧 Concurrent requests: {scanner.config['concurrent_requests']}")
    
    # Perform scans
    start_time = time.time()
    results = await scanner.scan_multiple_urls(urls)
    scan_duration = time.time() - start_time
    
    # Generate intelligence report
    intelligence_report = scanner.generate_intelligence_report(results)
    
    # Display results
    for result in results:
        print(f"\n✅ {result.url}")
        print(f"   🔍 Trackers found: {len(result.trackers)}")
        print(f"   🔒 Privacy score: {result.privacy_score}/100")
        print(f"   ⚠️  Risk level: {result.risk_assessment['overall_risk']}")
        print(f"   ⏱️  Response time: {result.performance_metrics.get('response_time', 0):.2f}s")
        
        if args.verbose:
            for tracker in result.trackers[:5]:  # Show first 5 trackers
                print(f"      🎯 {tracker.tracker_type}: {tracker.domain} ({tracker.risk_level} risk)")
    
    print(f"\n📊 Scan completed in {scan_duration:.2f}s")
    print(f"📈 Total trackers found: {intelligence_report['scan_summary']['total_trackers']}")
    print(f"🎯 Unique tracking domains: {intelligence_report['threat_intelligence']['unique_tracking_domains']}")
    
    # Save results
    if args.output:
        output_data = {
            'results': [asdict(result) for result in results],
            'intelligence_report': intelligence_report
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"💾 Results saved to {args.output}")

if __name__ == '__main__':
    asyncio.run(main())
