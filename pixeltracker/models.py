#!/usr/bin/env python3
"""
Data models and type definitions for PixelTracker

Defines the core data structures used throughout the system with proper
type hints and validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrackerCategory(str, Enum):
    """Tracker category enumeration"""
    ANALYTICS = "analytics"
    ADVERTISING = "advertising"
    SOCIAL_ADVERTISING = "social_advertising"
    USER_EXPERIENCE = "user_experience"
    OPTIMIZATION = "optimization"
    MARKETING_AUTOMATION = "marketing_automation"
    PERFORMANCE = "performance"
    PRIVACY_INVASION = "privacy_invasion"
    E_COMMERCE = "e_commerce"
    UNKNOWN = "unknown"


class DetectionMethod(str, Enum):
    """Detection method enumeration"""
    JAVASCRIPT = "javascript"
    PIXEL = "pixel"
    META = "meta"
    CSS = "css"
    NETWORK = "network"
    FINGERPRINTING = "fingerprinting"


@dataclass
class TrackerPattern:
    """Represents a tracker pattern with metadata"""
    name: str
    category: TrackerCategory
    risk_level: RiskLevel
    patterns: List[str]
    domains: List[str]
    description: str
    data_types: List[str]
    gdpr_relevant: bool
    ccpa_relevant: bool
    detection_method: DetectionMethod
    evasion_techniques: List[str]
    first_seen: str
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackerPattern':
        """Create from dictionary"""
        # Convert string enums back to enum values
        if isinstance(data.get('category'), str):
            data['category'] = TrackerCategory(data['category'])
        if isinstance(data.get('risk_level'), str):
            data['risk_level'] = RiskLevel(data['risk_level'])
        if isinstance(data.get('detection_method'), str):
            data['detection_method'] = DetectionMethod(data['detection_method'])
        
        return cls(**data)


@dataclass
class TrackerInfo:
    """Information about a detected tracker"""
    tracker_type: str
    domain: str
    source: str
    category: TrackerCategory
    risk_level: RiskLevel
    purpose: str
    first_seen: str
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackerInfo':
        """Create from dictionary"""
        if isinstance(data.get('category'), str):
            data['category'] = TrackerCategory(data['category'])
        if isinstance(data.get('risk_level'), str):
            data['risk_level'] = RiskLevel(data['risk_level'])
        
        return cls(**data)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a scan"""
    response_time: float
    content_length: int
    status_code: int
    redirects: int
    dns_lookup_time: Optional[float] = None
    connect_time: Optional[float] = None
    ssl_handshake_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class PrivacyAnalysis:
    """Privacy analysis results"""
    privacy_score: int
    risk_level: RiskLevel
    detected_categories: List[TrackerCategory]
    high_risk_domains: List[str]
    recommendations: List[str]
    compliance_status: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ScanResult:
    """Complete scan result for a URL"""
    url: str
    timestamp: str
    trackers: List[TrackerInfo]
    performance_metrics: PerformanceMetrics
    privacy_analysis: PrivacyAnalysis
    scan_duration: float
    scan_type: Literal["basic", "enhanced"] = "basic"
    javascript_enabled: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        # Convert enum values to strings for JSON serialization
        for tracker in result['trackers']:
            if hasattr(tracker['category'], 'value'):
                tracker['category'] = tracker['category'].value
            if hasattr(tracker['risk_level'], 'value'):
                tracker['risk_level'] = tracker['risk_level'].value
        
        if hasattr(result['privacy_analysis']['risk_level'], 'value'):
            result['privacy_analysis']['risk_level'] = result['privacy_analysis']['risk_level'].value
        
        for i, category in enumerate(result['privacy_analysis']['detected_categories']):
            if hasattr(category, 'value'):
                result['privacy_analysis']['detected_categories'][i] = category.value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanResult':
        """Create from dictionary"""
        # Convert tracker data
        trackers = []
        for tracker_data in data.get('trackers', []):
            trackers.append(TrackerInfo.from_dict(tracker_data))
        
        # Convert privacy analysis
        privacy_data = data.get('privacy_analysis', {})
        if isinstance(privacy_data.get('risk_level'), str):
            privacy_data['risk_level'] = RiskLevel(privacy_data['risk_level'])
        
        detected_categories = []
        for cat in privacy_data.get('detected_categories', []):
            if isinstance(cat, str):
                detected_categories.append(TrackerCategory(cat))
            else:
                detected_categories.append(cat)
        privacy_data['detected_categories'] = detected_categories
        
        privacy_analysis = PrivacyAnalysis(**privacy_data)
        
        # Convert performance metrics
        perf_data = data.get('performance_metrics', {})
        performance_metrics = PerformanceMetrics(**perf_data)
        
        # Create result
        result_data = {
            'url': data['url'],
            'timestamp': data['timestamp'],
            'trackers': trackers,
            'performance_metrics': performance_metrics,
            'privacy_analysis': privacy_analysis,
            'scan_duration': data['scan_duration'],
            'scan_type': data.get('scan_type', 'basic'),
            'javascript_enabled': data.get('javascript_enabled', False),
            'error': data.get('error')
        }
        
        return cls(**result_data)
    
    @property
    def tracker_count(self) -> int:
        """Total number of trackers found"""
        return len(self.trackers)
    
    @property
    def high_risk_tracker_count(self) -> int:
        """Number of high-risk trackers"""
        return len([t for t in self.trackers if t.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
    
    @property
    def unique_domains(self) -> List[str]:
        """List of unique domains found"""
        return list(set(tracker.domain for tracker in self.trackers))
    
    @property
    def categories_detected(self) -> List[TrackerCategory]:
        """List of unique categories detected"""
        return list(set(tracker.category for tracker in self.trackers))


@dataclass
class ScanConfiguration:
    """Configuration for a scan operation"""
    enable_javascript: bool = False
    enable_ml_analysis: bool = False
    enable_advanced_fingerprinting: bool = False
    rate_limit_delay: float = 1.0
    request_timeout: float = 30.0
    max_retries: int = 3
    concurrent_requests: int = 10
    user_agent: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    follow_redirects: bool = True
    verify_ssl: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class IntelligenceReport:
    """Comprehensive intelligence report"""
    scan_summary: Dict[str, Any]
    threat_intelligence: Dict[str, Any]
    recommendations: List[str]
    compliance_status: Dict[str, Any]
    trends: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# Type aliases for better readability
URLList = List[str]
TrackerList = List[TrackerInfo]
ScanResults = List[ScanResult]
ConfigDict = Dict[str, Any]

# Constants
DEFAULT_USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Risk score thresholds
PRIVACY_SCORE_THRESHOLDS = {
    RiskLevel.LOW: 80,
    RiskLevel.MEDIUM: 50,
    RiskLevel.HIGH: 20,
    RiskLevel.CRITICAL: 0
}
