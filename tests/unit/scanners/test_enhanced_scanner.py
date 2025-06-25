import pytest
from pixeltracker import EnhancedTrackingScanner, ConfigManager
from unittest.mock import patch, MagicMock

@pytest.mark.unit
def test_enhanced_scanner_initialization():
    """Test enhanced scanner initialization with default config"""
    config = ConfigManager()
    scanner = EnhancedTrackingScanner(config_manager=config)
    assert scanner is not None

@pytest.mark.unit
@patch("pixeltracker.scanners.enhanced.EnhancedTrackingScanner.scan_url")
def test_enhanced_scan_functionality(mock_scan_url):
    """Test the enhanced scan functionality with a mocked scan_url method"""
    mock_scan_url.return_value = MagicMock(tracker_count=10)
    scanner = EnhancedTrackingScanner(config_manager=ConfigManager())
    result = scanner.scan_url("http://example.com")
    assert result.tracker_count == 10
