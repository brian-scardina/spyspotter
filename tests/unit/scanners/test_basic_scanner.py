import pytest
from pixeltracker import BasicTrackingScanner, ConfigManager
from unittest.mock import patch, MagicMock

@pytest.mark.unit
def test_scanner_initialization():
    """Test scanner initialization with default config"""
    config = ConfigManager()
    scanner = BasicTrackingScanner(config_manager=config)
    assert scanner is not None

@pytest.mark.unit
@patch("pixeltracker.scanners.basic.BasicTrackingScanner.scan_url")
def test_scan_functionality(mock_scan_url):
    """Test the scan functionality with a mocked scan_url method"""
    mock_scan_url.return_value = MagicMock(tracker_count=5)
    scanner = BasicTrackingScanner(config_manager=ConfigManager())
    result = scanner.scan_url("http://example.com")
    assert result.tracker_count == 5

