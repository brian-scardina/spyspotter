#!/usr/bin/env python3
"""
End-to-end integration tests for PixelTracker

Tests the complete scanning pipeline using a lightweight aiohttp test server
that serves dynamic pages with and without trackers.
"""

import pytest
import asyncio
from aiohttp import web, ClientSession
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from pixeltracker import BasicTrackingScanner, EnhancedTrackingScanner, ConfigManager
from tests.fixtures.html_fixtures import get_fixture, get_all_fixtures


class TestPixelTrackerIntegration(AioHTTPTestCase):
    """Integration tests using aiohttp test server"""

    async def get_application(self):
        """Create test application with various tracker scenarios"""
        app = web.Application()
        
        # Add routes for different test scenarios
        app.router.add_get('/clean', self.handle_clean_page)
        app.router.add_get('/basic-tracker', self.handle_basic_tracker)
        app.router.add_get('/multiple-trackers', self.handle_multiple_trackers)
        app.router.add_get('/javascript-trackers', self.handle_javascript_trackers)
        app.router.add_get('/meta-trackers', self.handle_meta_trackers)
        app.router.add_get('/iframe-trackers', self.handle_iframe_trackers)
        app.router.add_get('/complex-page', self.handle_complex_page)
        app.router.add_get('/social-media', self.handle_social_media)
        app.router.add_get('/ecommerce', self.handle_ecommerce)
        app.router.add_get('/dynamic/{tracker_count}', self.handle_dynamic_trackers)
        
        return app

    async def handle_clean_page(self, request):
        """Serve clean page without trackers"""
        return web.Response(
            text=get_fixture('clean_page'),
            content_type='text/html'
        )

    async def handle_basic_tracker(self, request):
        """Serve page with basic tracking pixel"""
        return web.Response(
            text=get_fixture('basic_pixel'),
            content_type='text/html'
        )

    async def handle_multiple_trackers(self, request):
        """Serve page with multiple tracking pixels"""
        return web.Response(
            text=get_fixture('multiple_pixels'),
            content_type='text/html'
        )

    async def handle_javascript_trackers(self, request):
        """Serve page with JavaScript trackers"""
        return web.Response(
            text=get_fixture('javascript_trackers'),
            content_type='text/html'
        )

    async def handle_meta_trackers(self, request):
        """Serve page with meta tag trackers"""
        return web.Response(
            text=get_fixture('meta_trackers'),
            content_type='text/html'
        )

    async def handle_iframe_trackers(self, request):
        """Serve page with iframe trackers"""
        return web.Response(
            text=get_fixture('iframe_trackers'),
            content_type='text/html'
        )

    async def handle_complex_page(self, request):
        """Serve complex page with mixed tracker types"""
        return web.Response(
            text=get_fixture('complex_page'),
            content_type='text/html'
        )

    async def handle_social_media(self, request):
        """Serve page with social media trackers"""
        return web.Response(
            text=get_fixture('social_media'),
            content_type='text/html'
        )

    async def handle_ecommerce(self, request):
        """Serve page with e-commerce trackers"""
        return web.Response(
            text=get_fixture('ecommerce'),
            content_type='text/html'
        )

    async def handle_dynamic_trackers(self, request):
        """Dynamically generate page with specified number of trackers"""
        tracker_count = int(request.match_info['tracker_count'])
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dynamic Trackers Test</title>
        </head>
        <body>
            <h1>Dynamic Test Page</h1>
            <p>This page contains {count} tracking pixels.</p>
        """.format(count=tracker_count)
        
        # Add tracking pixels dynamically
        for i in range(tracker_count):
            html += f'<img src="https://tracker{i}.example.com/pixel.gif" width="1" height="1" style="display:none;">\n'
        
        html += """
        </body>
        </html>
        """
        
        return web.Response(
            text=html,
            content_type='text/html'
        )

    @unittest_run_loop
    @pytest.mark.integration
    async def test_clean_page_scan(self):
        """Test scanning a clean page with no trackers"""
        config = ConfigManager()
        config.database.enabled = False  # Disable database for testing
        
        scanner = BasicTrackingScanner(config_manager=config)
        
        url = str(self.server.make_url('/clean'))
        result = await scanner.scan_url(url)
        
        assert result is not None
        assert result.url == url
        assert result.tracker_count == 0
        assert result.error is None

    @unittest_run_loop
    @pytest.mark.integration
    async def test_basic_tracker_scan(self):
        """Test scanning a page with basic tracking pixel"""
        config = ConfigManager()
        config.database.enabled = False
        
        scanner = BasicTrackingScanner(config_manager=config)
        
        url = str(self.server.make_url('/basic-tracker'))
        result = await scanner.scan_url(url)
        
        assert result is not None
        assert result.url == url
        assert result.tracker_count >= 1
        assert result.error is None

    @unittest_run_loop
    @pytest.mark.integration
    async def test_multiple_trackers_scan(self):
        """Test scanning a page with multiple tracking pixels"""
        config = ConfigManager()
        config.database.enabled = False
        
        scanner = BasicTrackingScanner(config_manager=config)
        
        url = str(self.server.make_url('/multiple-trackers'))
        result = await scanner.scan_url(url)
        
        assert result is not None
        assert result.url == url
        assert result.tracker_count >= 3  # Should detect multiple trackers
        assert result.error is None

    @unittest_run_loop
    @pytest.mark.integration
    async def test_enhanced_scanner_vs_basic(self):
        """Test enhanced scanner detects more trackers than basic scanner"""
        config = ConfigManager()
        config.database.enabled = False
        
        basic_scanner = BasicTrackingScanner(config_manager=config)
        enhanced_scanner = EnhancedTrackingScanner(config_manager=config)
        
        url = str(self.server.make_url('/complex-page'))
        
        basic_result = await basic_scanner.scan_url(url)
        enhanced_result = await enhanced_scanner.scan_url(url)
        
        assert basic_result is not None
        assert enhanced_result is not None
        assert enhanced_result.tracker_count >= basic_result.tracker_count

    @unittest_run_loop
    @pytest.mark.integration
    async def test_dynamic_tracker_count(self):
        """Test dynamic tracker count detection"""
        config = ConfigManager()
        config.database.enabled = False
        
        scanner = BasicTrackingScanner(config_manager=config)
        
        # Test with different tracker counts
        for count in [0, 1, 5, 10]:
            url = str(self.server.make_url(f'/dynamic/{count}'))
            result = await scanner.scan_url(url)
            
            assert result is not None
            assert result.url == url
            assert result.tracker_count == count
            assert result.error is None

    @unittest_run_loop
    @pytest.mark.integration
    async def test_error_handling(self):
        """Test error handling for invalid URLs"""
        config = ConfigManager()
        config.database.enabled = False
        
        scanner = BasicTrackingScanner(config_manager=config)
        
        # Test with invalid URL
        url = str(self.server.make_url('/nonexistent'))
        result = await scanner.scan_url(url)
        
        assert result is not None
        assert result.url == url
        assert result.error is not None
        assert result.tracker_count == 0

    @unittest_run_loop
    @pytest.mark.integration
    async def test_concurrent_scanning(self):
        """Test concurrent scanning of multiple URLs"""
        config = ConfigManager()
        config.database.enabled = False
        
        scanner = BasicTrackingScanner(config_manager=config)
        
        urls = [
            str(self.server.make_url('/clean')),
            str(self.server.make_url('/basic-tracker')),
            str(self.server.make_url('/multiple-trackers')),
            str(self.server.make_url('/dynamic/3')),
        ]
        
        # Scan all URLs concurrently
        tasks = [scanner.scan_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        assert len(results) == len(urls)
        
        # Verify all scans completed successfully
        for i, result in enumerate(results):
            assert not isinstance(result, Exception)
            assert result.url == urls[i]
            assert result.error is None

    @unittest_run_loop
    @pytest.mark.integration
    async def test_scan_performance_metrics(self):
        """Test that performance metrics are collected"""
        config = ConfigManager()
        config.database.enabled = False
        
        scanner = BasicTrackingScanner(config_manager=config)
        
        url = str(self.server.make_url('/complex-page'))
        result = await scanner.scan_url(url)
        
        assert result is not None
        assert result.performance_metrics is not None
        assert result.performance_metrics.page_load_time > 0
        assert result.scan_duration > 0

    @unittest_run_loop
    @pytest.mark.integration
    async def test_privacy_analysis(self):
        """Test that privacy analysis is performed"""
        config = ConfigManager()
        config.database.enabled = False
        
        scanner = BasicTrackingScanner(config_manager=config)
        
        url = str(self.server.make_url('/social-media'))
        result = await scanner.scan_url(url)
        
        assert result is not None
        assert result.privacy_analysis is not None
        assert result.privacy_analysis.privacy_score >= 0
        assert result.privacy_analysis.privacy_score <= 100


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI functionality"""

    @pytest.mark.slow
    def test_cli_basic_scan(self):
        """Test basic CLI scanning functionality"""
        # This would test the CLI interface
        # Implementation depends on the actual CLI structure
        pass

    @pytest.mark.slow
    def test_cli_enhanced_scan(self):
        """Test enhanced CLI scanning functionality"""
        # This would test the enhanced CLI interface
        # Implementation depends on the actual CLI structure
        pass

    @pytest.mark.slow
    def test_cli_batch_scan(self):
        """Test CLI batch scanning functionality"""
        # This would test batch scanning via CLI
        # Implementation depends on the actual CLI structure
        pass


if __name__ == "__main__":
    pytest.main([__file__])
