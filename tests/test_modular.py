#!/usr/bin/env python3
"""
Tests for the modular PixelTracker structure

Tests that the new modular design works correctly with dependency injection.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from pixeltracker import BasicTrackingScanner, ConfigManager
from pixeltracker.models import ScanResult, TrackerInfo, PerformanceMetrics, PrivacyAnalysis, RiskLevel
from pixeltracker.interfaces import Fetcher, Parser, Analyzer
from datetime import datetime


class MockFetcher:
    """Mock fetcher for testing"""
    
    async def fetch(self, url: str, **kwargs):
        return {
            'content': '<html><img src="https://tracker.com/pixel.gif" width="1" height="1"></html>',
            'metrics': {
                'response_time': 0.5,
                'status_code': 200,
                'content_length': 100,
                'redirects': 0
            }
        }
    
    def set_headers(self, headers):
        pass
    
    def set_timeout(self, timeout):
        pass


class MockParser:
    """Mock parser for testing"""
    
    def parse(self, content: str, url: str = ""):
        return {
            'pixels': [{
                'src': 'https://tracker.com/pixel.gif',
                'width': '1',
                'height': '1',
                'element_type': 'img'
            }],
            'js_trackers': [],
            'meta_trackers': []
        }
    
    def find_tracking_pixels(self, content: str):
        return []
    
    def find_javascript_trackers(self, content: str):
        return []
    
    def find_meta_trackers(self, content: str):
        return []


class MockAnalyzer:
    """Mock analyzer for testing"""
    
    def analyze_privacy_impact(self, trackers, **kwargs):
        return {
            'privacy_score': 75,
            'risk_level': RiskLevel.MEDIUM,
            'detected_categories': [],
            'high_risk_domains': [],
            'recommendations': ['Test recommendation']
        }
    
    def calculate_privacy_score(self, trackers, **kwargs):
        return 75
    
    def assess_risks(self, trackers, url):
        return {
            'overall_risk': RiskLevel.MEDIUM,
            'high_risk_trackers': 0,
            'medium_risk_trackers': 1
        }


@pytest.mark.asyncio
async def test_basic_scanner_with_mocks():
    """Test BasicTrackingScanner with mock services"""
    # Create configuration
    config = ConfigManager()
    config.database.enabled = False  # Disable database for testing
    
    # Create scanner with mock services
    scanner = BasicTrackingScanner(
        config_manager=config,
        fetcher=MockFetcher(),
        parser=MockParser(),
        analyzer=MockAnalyzer()
    )
    
    # Test scanning
    result = await scanner.scan_url("https://example.com")
    
    # Verify result
    assert isinstance(result, ScanResult)
    assert result.url == "https://example.com"
    assert result.error is None
    assert result.tracker_count == 1
    assert result.privacy_analysis.privacy_score == 75
    assert result.scan_type == "basic"


def test_config_manager():
    """Test configuration manager functionality"""
    config = ConfigManager()
    
    # Test getting values
    assert config.get("scanning.rate_limit_delay") == 1.0
    assert config.get("javascript.enabled") == False
    
    # Test setting values
    config.set("scanning.rate_limit_delay", 2.0)
    assert config.get("scanning.rate_limit_delay") == 2.0
    
    # Test validation
    assert config.validate() == True
    
    # Test invalid configuration
    config.set("scanning.rate_limit_delay", -1.0)
    assert config.validate() == False


def test_dependency_injection():
    """Test that dependency injection works correctly"""
    config = ConfigManager()
    mock_fetcher = MockFetcher()
    mock_parser = MockParser()
    
    scanner = BasicTrackingScanner(
        config_manager=config,
        fetcher=mock_fetcher,
        parser=mock_parser
    )
    
    # Verify the injected services are used
    assert scanner.fetcher == mock_fetcher
    assert scanner.parser == mock_parser
    assert scanner.config_manager == config


def test_models_serialization():
    """Test that models can be serialized/deserialized"""
    from pixeltracker.models import TrackerInfo, TrackerCategory, RiskLevel
    
    # Create tracker info
    tracker = TrackerInfo(
        tracker_type="test",
        domain="example.com",
        source="test",
        category=TrackerCategory.ANALYTICS,
        risk_level=RiskLevel.MEDIUM,
        purpose="testing",
        first_seen=datetime.now().isoformat()
    )
    
    # Test serialization
    tracker_dict = tracker.to_dict()
    assert isinstance(tracker_dict, dict)
    assert tracker_dict['domain'] == "example.com"
    
    # Test deserialization
    tracker2 = TrackerInfo.from_dict(tracker_dict)
    assert tracker2.domain == tracker.domain
    assert tracker2.category == tracker.category


if __name__ == "__main__":
    pytest.main([__file__])
