#!/usr/bin/env python3
"""
Unit tests for PixelTracker services using HTTP mocking

Tests all service classes using mocked HTTP responses to ensure
predictable and fast test execution.
"""

import pytest
import responses
import requests_mock
from unittest.mock import Mock, patch, AsyncMock
from pixeltracker.services.network import NetworkService
from pixeltracker.services.parser import HTMLParserService
from pixeltracker.services.analyzer import AnalyzerService
from pixeltracker.services.reporter import ReporterService
from pixeltracker.services.storage import StorageService
from pixeltracker.models import TrackerInfo, RiskLevel, TrackerCategory
from tests.fixtures.html_fixtures import get_fixture


@pytest.mark.unit
@pytest.mark.mock
class TestNetworkServiceMocked:
    """Test NetworkService with mocked HTTP responses"""

    def setup_method(self):
        self.network_service = NetworkService()

    @responses.activate
    def test_fetch_with_responses(self):
        """Test HTTP fetching using responses mock"""
        # Mock successful response
        responses.add(
            responses.GET,
            'https://example.com',
            body=get_fixture('basic_pixel'),
            status=200,
            content_type='text/html'
        )
        
        response = self.network_service.fetch('https://example.com')
        
        assert response.status_code == 200
        assert 'tracking pixel' in response.text.lower()

    def test_fetch_with_requests_mock(self):
        """Test HTTP fetching using requests-mock"""
        with requests_mock.Mocker() as m:
            m.get('https://example.com', text=get_fixture('multiple_pixels'))
            
            response = self.network_service.fetch('https://example.com')
            
            assert response.status_code == 200
            assert 'multiple trackers' in response.text.lower()

    @responses.activate
    def test_fetch_error_handling(self):
        """Test error handling for HTTP requests"""
        # Mock 404 response
        responses.add(
            responses.GET,
            'https://example.com/notfound',
            status=404
        )
        
        with pytest.raises(Exception):
            self.network_service.fetch('https://example.com/notfound')

    @responses.activate
    def test_fetch_with_headers(self):
        """Test fetching with custom headers"""
        responses.add(
            responses.GET,
            'https://example.com',
            body='<html><body>Test</body></html>',
            status=200
        )
        
        headers = {'User-Agent': 'PixelTracker/Test'}
        response = self.network_service.fetch('https://example.com', headers=headers)
        
        assert response.status_code == 200
        # Verify headers were sent (would need to check request in real implementation)


@pytest.mark.unit
class TestHTMLParserService:
    """Test HTMLParserService with various HTML fixtures"""

    def setup_method(self):
        self.parser = HTMLParserService()

    def test_parse_clean_page(self):
        """Test parsing a clean page with no trackers"""
        result = self.parser.parse(get_fixture('clean_page'))
        
        assert result is not None
        assert len(result.get('pixels', [])) == 0
        assert len(result.get('js_trackers', [])) == 0

    def test_parse_basic_pixel(self):
        """Test parsing page with basic tracking pixel"""
        result = self.parser.parse(get_fixture('basic_pixel'))
        
        assert result is not None
        pixels = result.get('pixels', [])
        assert len(pixels) >= 1
        
        # Verify pixel attributes
        pixel = pixels[0]
        assert pixel['width'] == '1'
        assert pixel['height'] == '1'
        assert 'tracker.example.com' in pixel['src']

    def test_parse_multiple_pixels(self):
        """Test parsing page with multiple tracking pixels"""
        result = self.parser.parse(get_fixture('multiple_pixels'))
        
        assert result is not None
        pixels = result.get('pixels', [])
        assert len(pixels) >= 3  # Should detect multiple trackers

    def test_parse_javascript_trackers(self):
        """Test parsing page with JavaScript trackers"""
        result = self.parser.parse(get_fixture('javascript_trackers'))
        
        assert result is not None
        js_trackers = result.get('js_trackers', [])
        assert len(js_trackers) >= 1

    def test_parse_meta_trackers(self):
        """Test parsing page with meta tag trackers"""
        result = self.parser.parse(get_fixture('meta_trackers'))
        
        assert result is not None
        meta_trackers = result.get('meta_trackers', [])
        assert len(meta_trackers) >= 1

    def test_parse_iframe_trackers(self):
        """Test parsing page with iframe trackers"""
        result = self.parser.parse(get_fixture('iframe_trackers'))
        
        assert result is not None
        # Implementation would need to detect iframe trackers

    def test_parse_complex_page(self):
        """Test parsing complex page with mixed tracker types"""
        result = self.parser.parse(get_fixture('complex_page'))
        
        assert result is not None
        # Should detect multiple types of trackers
        total_trackers = (
            len(result.get('pixels', [])) +
            len(result.get('js_trackers', [])) +
            len(result.get('meta_trackers', []))
        )
        assert total_trackers > 0

    def test_parse_invalid_html(self):
        """Test parsing invalid or malformed HTML"""
        invalid_html = "<html><body><img src='invalid'><p>unclosed"
        result = self.parser.parse(invalid_html)
        
        # Should handle gracefully without crashing
        assert result is not None

    def test_parse_empty_content(self):
        """Test parsing empty content"""
        result = self.parser.parse("")
        
        assert result is not None
        assert len(result.get('pixels', [])) == 0


@pytest.mark.unit
class TestAnalyzerService:
    """Test AnalyzerService functionality"""

    def setup_method(self):
        self.analyzer = AnalyzerService()

    def test_analyze_no_trackers(self):
        """Test analysis with no trackers"""
        trackers = []
        result = self.analyzer.analyze_privacy_impact(trackers)
        
        assert result is not None
        assert result['privacy_score'] == 100  # Perfect score with no trackers
        assert result['risk_level'] == RiskLevel.LOW

    def test_analyze_single_tracker(self):
        """Test analysis with a single tracker"""
        trackers = [
            TrackerInfo(
                tracker_type="pixel",
                domain="analytics.google.com",
                source="https://analytics.google.com/collect",
                category=TrackerCategory.ANALYTICS,
                risk_level=RiskLevel.LOW,
                purpose="Analytics",
                first_seen="2024-01-01T00:00:00Z"
            )
        ]
        
        result = self.analyzer.analyze_privacy_impact(trackers)
        
        assert result is not None
        assert result['privacy_score'] < 100  # Score should be reduced
        assert len(result['detected_categories']) > 0

    def test_analyze_multiple_trackers(self):
        """Test analysis with multiple trackers"""
        trackers = [
            TrackerInfo(
                tracker_type="pixel",
                domain="facebook.com",
                source="https://facebook.com/tr",
                category=TrackerCategory.SOCIAL,
                risk_level=RiskLevel.MEDIUM,
                purpose="Social tracking",
                first_seen="2024-01-01T00:00:00Z"
            ),
            TrackerInfo(
                tracker_type="script",
                domain="doubleclick.net",
                source="https://doubleclick.net/pixel",
                category=TrackerCategory.ADVERTISING,
                risk_level=RiskLevel.HIGH,
                purpose="Advertising",
                first_seen="2024-01-01T00:00:00Z"
            )
        ]
        
        result = self.analyzer.analyze_privacy_impact(trackers)
        
        assert result is not None
        assert result['privacy_score'] < 70  # Should be lower with multiple trackers
        assert len(result['detected_categories']) == 2
        assert len(result['high_risk_domains']) > 0

    def test_analyze_high_risk_trackers(self):
        """Test analysis with high-risk trackers"""
        trackers = [
            TrackerInfo(
                tracker_type="script",
                domain="malicious-tracker.com",
                source="https://malicious-tracker.com/track",
                category=TrackerCategory.ADVERTISING,
                risk_level=RiskLevel.CRITICAL,
                purpose="Unknown",
                first_seen="2024-01-01T00:00:00Z"
            )
        ]
        
        result = self.analyzer.analyze_privacy_impact(trackers)
        
        assert result is not None
        assert result['privacy_score'] < 50  # Very low score for critical risk
        assert result['risk_level'] == RiskLevel.HIGH
        assert len(result['recommendations']) > 0


@pytest.mark.unit
class TestReporterService:
    """Test ReporterService functionality"""

    def setup_method(self):
        self.reporter = ReporterService()

    def test_generate_text_report(self):
        """Test generating text report"""
        scan_results = [
            Mock(
                url="https://example.com",
                tracker_count=3,
                privacy_analysis=Mock(privacy_score=75),
                scan_duration=1.5
            )
        ]
        
        report = self.reporter.generate_text_report(scan_results)
        
        assert report is not None
        assert "example.com" in report
        assert "3" in report  # tracker count
        assert "75" in report  # privacy score

    def test_generate_json_report(self):
        """Test generating JSON report"""
        scan_results = [
            Mock(
                url="https://example.com",
                tracker_count=2,
                to_dict=lambda: {"url": "https://example.com", "tracker_count": 2}
            )
        ]
        
        report = self.reporter.generate_json_report(scan_results)
        
        assert report is not None
        # Would need to parse JSON and verify structure

    def test_generate_html_report(self):
        """Test generating HTML report"""
        scan_results = [
            Mock(
                url="https://example.com",
                tracker_count=1,
                privacy_analysis=Mock(privacy_score=90)
            )
        ]
        
        report = self.reporter.generate_html_report(scan_results)
        
        assert report is not None
        assert "<html>" in report.lower()
        assert "example.com" in report


@pytest.mark.unit
class TestStorageService:
    """Test StorageService functionality"""

    def setup_method(self):
        self.storage = StorageService()

    @patch('builtins.open')
    def test_save_results_json(self, mock_open):
        """Test saving results to JSON file"""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        results = [
            Mock(to_dict=lambda: {"url": "https://example.com", "tracker_count": 1})
        ]
        
        self.storage.save_results(results, "results.json", format="json")
        
        mock_open.assert_called_once_with("results.json", 'w')
        mock_file.write.assert_called()

    @patch('builtins.open')
    def test_save_results_csv(self, mock_open):
        """Test saving results to CSV file"""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        results = [
            Mock(
                url="https://example.com",
                tracker_count=1,
                privacy_analysis=Mock(privacy_score=90)
            )
        ]
        
        self.storage.save_results(results, "results.csv", format="csv")
        
        mock_open.assert_called_once_with("results.csv", 'w', newline='')

    @patch('pixeltracker.services.storage.sqlite3')
    def test_save_to_database(self, mock_sqlite):
        """Test saving results to database"""
        mock_conn = Mock()
        mock_sqlite.connect.return_value = mock_conn
        
        results = [
            Mock(
                url="https://example.com",
                tracker_count=1,
                timestamp="2024-01-01T00:00:00Z"
            )
        ]
        
        self.storage.save_to_database(results, "test.db")
        
        mock_sqlite.connect.assert_called_once_with("test.db")
        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
