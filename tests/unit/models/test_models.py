#!/usr/bin/env python3
"""
Unit tests for PixelTracker models

Tests that cover all model functionality including serialization,
deserialization, validation, and edge cases.
"""

import pytest
from datetime import datetime
from pixeltracker.models import TrackerInfo, ScanResult, TrackerPattern, PerformanceMetrics, PrivacyAnalysis, RiskLevel, TrackerCategory


@pytest.mark.unit
class TestTrackerInfo:
    """Test cases for TrackerInfo model"""

    def test_tracker_info_creation(self):
        """Test basic TrackerInfo creation"""
        tracker = TrackerInfo(
            tracker_type="pixel",
            domain="example.com",
            source="https://example.com/pixel.gif",
            category=TrackerCategory.ANALYTICS,
            risk_level=RiskLevel.MEDIUM,
            purpose="Analytics tracking",
            first_seen=datetime.now().isoformat()
        )
        
        assert tracker.tracker_type == "pixel"
        assert tracker.domain == "example.com"
        assert tracker.category == TrackerCategory.ANALYTICS
        assert tracker.risk_level == RiskLevel.MEDIUM

    def test_tracker_info_serialization(self):
        """Test TrackerInfo serialization to dict"""
        tracker = TrackerInfo(
            tracker_type="pixel",
            domain="example.com",
            source="https://example.com/pixel.gif",
            category=TrackerCategory.ANALYTICS,
            risk_level=RiskLevel.MEDIUM,
            purpose="Analytics tracking",
            first_seen=datetime.now().isoformat()
        )
        
        tracker_dict = tracker.to_dict()
        assert isinstance(tracker_dict, dict)
        assert tracker_dict['domain'] == "example.com"
        assert tracker_dict['tracker_type'] == "pixel"

    def test_tracker_info_deserialization(self):
        """Test TrackerInfo deserialization from dict"""
        tracker_dict = {
            'tracker_type': 'pixel',
            'domain': 'example.com',
            'source': 'https://example.com/pixel.gif',
            'category': TrackerCategory.ANALYTICS,
            'risk_level': RiskLevel.MEDIUM,
            'purpose': 'Analytics tracking',
            'first_seen': datetime.now().isoformat()
        }
        
        tracker = TrackerInfo.from_dict(tracker_dict)
        assert tracker.domain == "example.com"
        assert tracker.tracker_type == "pixel"


@pytest.mark.unit
class TestScanResult:
    """Test cases for ScanResult model"""

    def test_scan_result_creation(self):
        """Test basic ScanResult creation"""
        result = ScanResult(
            url="https://example.com",
            timestamp=datetime.now(),
            scan_duration=1.5,
            tracker_count=5,
            trackers=[],
            privacy_analysis=PrivacyAnalysis(
                privacy_score=75,
                risk_level=RiskLevel.MEDIUM,
                detected_categories=[],
                high_risk_domains=[],
                recommendations=[]
            ),
            performance_metrics=PerformanceMetrics(
                page_load_time=2.3,
                total_requests=10,
                data_transferred=1024
            ),
            scan_type="basic",
            error=None
        )
        
        assert result.url == "https://example.com"
        assert result.tracker_count == 5
        assert result.privacy_analysis.privacy_score == 75

    def test_scan_result_with_error(self):
        """Test ScanResult with error condition"""
        result = ScanResult(
            url="https://invalid-url.com",
            timestamp=datetime.now(),
            scan_duration=0.5,
            tracker_count=0,
            trackers=[],
            privacy_analysis=None,
            performance_metrics=None,
            scan_type="basic",
            error="Failed to fetch URL"
        )
        
        assert result.error == "Failed to fetch URL"
        assert result.tracker_count == 0


@pytest.mark.unit
class TestTrackerPattern:
    """Test cases for TrackerPattern model"""

    def test_tracker_pattern_creation(self):
        """Test basic TrackerPattern creation"""
        pattern = TrackerPattern(
            name="Google Analytics",
            patterns=["google-analytics.com", "googletagmanager.com"],
            category=TrackerCategory.ANALYTICS,
            risk_level=RiskLevel.LOW,
            description="Google Analytics tracking"
        )
        
        assert pattern.name == "Google Analytics"
        assert len(pattern.patterns) == 2
        assert pattern.category == TrackerCategory.ANALYTICS


@pytest.mark.unit
class TestPrivacyAnalysis:
    """Test cases for PrivacyAnalysis model"""

    def test_privacy_analysis_creation(self):
        """Test basic PrivacyAnalysis creation"""
        analysis = PrivacyAnalysis(
            privacy_score=80,
            risk_level=RiskLevel.LOW,
            detected_categories=[TrackerCategory.ANALYTICS],
            high_risk_domains=["tracker.com"],
            recommendations=["Consider blocking tracker.com"]
        )
        
        assert analysis.privacy_score == 80
        assert analysis.risk_level == RiskLevel.LOW
        assert len(analysis.detected_categories) == 1


@pytest.mark.unit
class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics model"""

    def test_performance_metrics_creation(self):
        """Test basic PerformanceMetrics creation"""
        metrics = PerformanceMetrics(
            page_load_time=2.5,
            total_requests=15,
            data_transferred=2048
        )
        
        assert metrics.page_load_time == 2.5
        assert metrics.total_requests == 15
        assert metrics.data_transferred == 2048


@pytest.mark.unit
class TestEnums:
    """Test cases for enum types"""

    def test_risk_level_enum(self):
        """Test RiskLevel enum values"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_tracker_category_enum(self):
        """Test TrackerCategory enum values"""
        assert TrackerCategory.ANALYTICS.value == "analytics"
        assert TrackerCategory.ADVERTISING.value == "advertising"
        assert TrackerCategory.SOCIAL.value == "social"
        assert TrackerCategory.FUNCTIONAL.value == "functional"


if __name__ == "__main__":
    pytest.main([__file__])
