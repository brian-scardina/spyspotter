#!/usr/bin/env python3
"""
PixelTracker Test Suite

Comprehensive test suite for PixelTracker including unit tests, integration tests,
performance tests, and benchmarks.
"""

# Test configuration and utilities
TEST_CONFIG = {
    'coverage_threshold': 85,
    'benchmark_threshold': 2.0,  # seconds
    'memory_threshold': 100,  # MB
}

# Test data and fixtures
TEST_URLS = [
    'https://example.com',
    'https://google.com',
    'https://facebook.com',
    'https://twitter.com',
]

# Common test utilities
def get_test_config():
    """Get test configuration"""
    return TEST_CONFIG.copy()

def get_test_urls():
    """Get list of test URLs"""
    return TEST_URLS.copy()

__all__ = ['TEST_CONFIG', 'TEST_URLS', 'get_test_config', 'get_test_urls']
