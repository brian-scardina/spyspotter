#!/usr/bin/env python3
"""
Performance and benchmark tests for PixelTracker

Uses pytest-benchmark to measure scan speed, memory usage, and concurrency performance.
Sets regression thresholds to ensure performance doesn't degrade over time.
"""

import pytest
import asyncio
import psutil
import os
from memory_profiler import profile
from pixeltracker import BasicTrackingScanner, EnhancedTrackingScanner, ConfigManager
from pixeltracker.services.parser import HTMLParserService
from tests.fixtures.html_fixtures import get_fixture, get_all_fixtures


@pytest.mark.performance
class TestScanningPerformance:
    """Performance tests for scanning operations"""

    def setup_method(self):
        """Setup test environment"""
        self.config = ConfigManager()
        self.config.database.enabled = False  # Disable database for benchmarks
        self.basic_scanner = BasicTrackingScanner(config_manager=self.config)
        self.enhanced_scanner = EnhancedTrackingScanner(config_manager=self.config)

    def test_basic_scanner_benchmark(self, benchmark):
        """Benchmark basic scanner performance"""
        url = "https://example.com"
        
        # Benchmark should complete within 2 seconds
        result = benchmark.pedantic(
            self.basic_scanner.scan_url,
            args=(url,),
            iterations=5,
            rounds=3
        )
        
        # Performance assertions
        assert benchmark.stats.stats.mean < 2.0  # Mean should be under 2 seconds
        assert result is not None

    def test_enhanced_scanner_benchmark(self, benchmark):
        """Benchmark enhanced scanner performance"""
        url = "https://example.com"
        
        # Enhanced scanner should complete within 5 seconds
        result = benchmark.pedantic(
            self.enhanced_scanner.scan_url,
            args=(url,),
            iterations=3,
            rounds=2
        )
        
        # Performance assertions
        assert benchmark.stats.stats.mean < 5.0  # Mean should be under 5 seconds
        assert result is not None

    def test_html_parsing_benchmark(self, benchmark):
        """Benchmark HTML parsing performance"""
        parser = HTMLParserService()
        html_content = get_fixture('complex_page')
        
        # Parsing should be very fast
        result = benchmark.pedantic(
            parser.parse,
            args=(html_content,),
            iterations=100,
            rounds=10
        )
        
        # Performance assertions
        assert benchmark.stats.stats.mean < 0.1  # Should parse in under 0.1 seconds
        assert result is not None

    @pytest.mark.slow
    def test_concurrent_scanning_benchmark(self, benchmark):
        """Benchmark concurrent scanning performance"""
        urls = [
            "https://example.com",
            "https://google.com",
            "https://facebook.com",
            "https://twitter.com",
            "https://github.com"
        ]
        
        async def scan_multiple_urls():
            tasks = [self.basic_scanner.scan_url(url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Concurrent scanning should be faster than sequential
        result = benchmark.pedantic(
            asyncio.run,
            args=(scan_multiple_urls(),),
            iterations=2,
            rounds=2
        )
        
        # Performance assertions
        assert benchmark.stats.stats.mean < 10.0  # Should complete within 10 seconds
        assert len(result) == len(urls)


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage tests"""

    def setup_method(self):
        """Setup test environment"""
        self.config = ConfigManager()
        self.config.database.enabled = False
        self.scanner = BasicTrackingScanner(config_manager=self.config)

    def test_memory_usage_single_scan(self):
        """Test memory usage for single scan"""
        process = psutil.Process(os.getpid())
        
        # Measure memory before scan
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform scan
        result = self.scanner.scan_url("https://example.com")
        
        # Measure memory after scan
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50, f"Memory increase too high: {memory_increase}MB"
        assert result is not None

    @pytest.mark.slow
    def test_memory_usage_multiple_scans(self):
        """Test memory usage for multiple scans (memory leak detection)"""
        process = psutil.Process(os.getpid())
        
        # Measure memory before scans
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple scans
        urls = ["https://example.com"] * 10
        for url in urls:
            result = self.scanner.scan_url(url)
            assert result is not None
        
        # Measure memory after scans
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Memory increase should be reasonable even after multiple scans
        assert memory_increase < 100, f"Memory increase too high: {memory_increase}MB"

    @profile
    def test_memory_profiling_scan(self):
        """Detailed memory profiling for scan operation"""
        result = self.scanner.scan_url("https://example.com")
        assert result is not None


@pytest.mark.performance
class TestScalabilityBenchmarks:
    """Scalability and stress tests"""

    def setup_method(self):
        """Setup test environment"""
        self.config = ConfigManager()
        self.config.database.enabled = False
        self.scanner = BasicTrackingScanner(config_manager=self.config)

    @pytest.mark.slow
    def test_large_html_parsing_benchmark(self, benchmark):
        """Benchmark parsing of large HTML documents"""
        # Generate large HTML with many trackers
        large_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Large HTML Test</title>
        </head>
        <body>
            <h1>Large Test Page</h1>
        """
        
        # Add 1000 tracking pixels
        for i in range(1000):
            large_html += f'<img src="https://tracker{i}.example.com/pixel.gif" width="1" height="1" style="display:none;">\n'
        
        large_html += """
        </body>
        </html>
        """
        
        parser = HTMLParserService()
        
        # Parsing large HTML should still be reasonably fast
        result = benchmark.pedantic(
            parser.parse,
            args=(large_html,),
            iterations=5,
            rounds=2
        )
        
        # Performance assertions
        assert benchmark.stats.stats.mean < 1.0  # Should parse within 1 second
        assert result is not None
        assert len(result.get('pixels', [])) == 1000

    @pytest.mark.slow
    def test_concurrent_load_benchmark(self, benchmark):
        """Benchmark high concurrency load"""
        async def high_concurrency_scan():
            # Create 20 concurrent scans
            tasks = []
            for i in range(20):
                url = f"https://example{i}.com"
                tasks.append(self.scanner.scan_url(url))
            
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # High concurrency should still complete within reasonable time
        result = benchmark.pedantic(
            asyncio.run,
            args=(high_concurrency_scan(),),
            iterations=1,
            rounds=2
        )
        
        # Performance assertions
        assert benchmark.stats.stats.mean < 30.0  # Should complete within 30 seconds
        assert len(result) == 20


@pytest.mark.performance
class TestRegressionThresholds:
    """Regression threshold tests to ensure performance doesn't degrade"""

    def setup_method(self):
        """Setup test environment"""
        self.config = ConfigManager()
        self.config.database.enabled = False
        self.scanner = BasicTrackingScanner(config_manager=self.config)

    def test_scan_speed_regression(self, benchmark):
        """Ensure scan speed doesn't regress beyond threshold"""
        url = "https://example.com"
        
        result = benchmark(self.scanner.scan_url, url)
        
        # Regression threshold: scan should not take more than 3 seconds
        assert benchmark.stats.stats.min < 3.0, "Scan speed regression detected"
        assert result is not None

    def test_parsing_speed_regression(self, benchmark):
        """Ensure parsing speed doesn't regress beyond threshold"""
        parser = HTMLParserService()
        html_content = get_fixture('complex_page')
        
        result = benchmark(parser.parse, html_content)
        
        # Regression threshold: parsing should not take more than 0.05 seconds
        assert benchmark.stats.stats.min < 0.05, "Parsing speed regression detected"
        assert result is not None

    def test_memory_usage_regression(self):
        """Ensure memory usage doesn't regress beyond threshold"""
        process = psutil.Process(os.getpid())
        
        # Measure memory before scan
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform scan
        result = self.scanner.scan_url("https://example.com")
        
        # Measure memory after scan
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Regression threshold: memory increase should not exceed 30MB
        assert memory_increase < 30, f"Memory usage regression detected: {memory_increase}MB"
        assert result is not None


@pytest.mark.performance
class TestCustomBenchmarks:
    """Custom benchmark scenarios"""

    def setup_method(self):
        """Setup test environment"""
        self.config = ConfigManager()
        self.config.database.enabled = False

    def test_scanner_initialization_benchmark(self, benchmark):
        """Benchmark scanner initialization performance"""
        def create_scanner():
            return BasicTrackingScanner(config_manager=self.config)
        
        result = benchmark(create_scanner)
        
        # Scanner creation should be very fast
        assert benchmark.stats.stats.mean < 0.1
        assert result is not None

    def test_config_loading_benchmark(self, benchmark):
        """Benchmark configuration loading performance"""
        def create_config():
            return ConfigManager()
        
        result = benchmark(create_config)
        
        # Config loading should be very fast
        assert benchmark.stats.stats.mean < 0.05
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
