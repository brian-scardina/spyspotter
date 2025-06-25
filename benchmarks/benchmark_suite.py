#!/usr/bin/env python3
"""
ASV benchmark suite for PixelTracker

Long-term performance tracking and regression detection using ASV.
These benchmarks track performance over time across different commits.
"""

import asyncio
from pixeltracker import BasicTrackingScanner, EnhancedTrackingScanner, ConfigManager
from pixeltracker.services.parser import HTMLParserService


class ScannerBenchmarks:
    """Scanner performance benchmarks"""
    
    def setup(self):
        self.config = ConfigManager()
        self.config.database.enabled = False
        self.basic_scanner = BasicTrackingScanner(config_manager=self.config)
        self.enhanced_scanner = EnhancedTrackingScanner(config_manager=self.config)
    
    def time_basic_scanner_scan(self):
        """Time basic scanner scan operation"""
        return self.basic_scanner.scan_url("https://example.com")
    
    def time_enhanced_scanner_scan(self):
        """Time enhanced scanner scan operation"""
        return self.enhanced_scanner.scan_url("https://example.com")
    
    def peakmem_basic_scanner_scan(self):
        """Measure peak memory usage during basic scan"""
        return self.basic_scanner.scan_url("https://example.com")
    
    def peakmem_enhanced_scanner_scan(self):
        """Measure peak memory usage during enhanced scan"""
        return self.enhanced_scanner.scan_url("https://example.com")


class ParsingBenchmarks:
    """HTML parsing performance benchmarks"""
    
    def setup(self):
        self.parser = HTMLParserService()
        
        # Sample HTML content for benchmarking
        self.simple_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <h1>Test Page</h1>
            <img src="https://tracker.com/pixel.gif" width="1" height="1">
        </body>
        </html>
        """
        
        # Complex HTML with multiple trackers
        self.complex_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Complex Test</title>
            <script src="https://www.googletagmanager.com/gtag/js"></script>
        </head>
        <body>
            <h1>Complex Page</h1>
        """
        
        # Add 100 tracking pixels
        for i in range(100):
            self.complex_html += f'<img src="https://tracker{i}.com/pixel.gif" width="1" height="1">\n'
        
        self.complex_html += """
            <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
        </body>
        </html>
        """
    
    def time_parse_simple_html(self):
        """Time parsing of simple HTML"""
        return self.parser.parse(self.simple_html)
    
    def time_parse_complex_html(self):
        """Time parsing of complex HTML with many trackers"""
        return self.parser.parse(self.complex_html)
    
    def peakmem_parse_complex_html(self):
        """Measure peak memory usage during complex HTML parsing"""
        return self.parser.parse(self.complex_html)


class ConcurrencyBenchmarks:
    """Concurrency and scalability benchmarks"""
    
    def setup(self):
        self.config = ConfigManager()
        self.config.database.enabled = False
        self.scanner = BasicTrackingScanner(config_manager=self.config)
    
    def time_concurrent_scans_5(self):
        """Time 5 concurrent scans"""
        async def scan_multiple():
            tasks = []
            for i in range(5):
                tasks.append(self.scanner.scan_url(f"https://example{i}.com"))
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        return asyncio.run(scan_multiple())
    
    def time_concurrent_scans_10(self):
        """Time 10 concurrent scans"""
        async def scan_multiple():
            tasks = []
            for i in range(10):
                tasks.append(self.scanner.scan_url(f"https://example{i}.com"))
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        return asyncio.run(scan_multiple())
    
    def time_concurrent_scans_20(self):
        """Time 20 concurrent scans"""
        async def scan_multiple():
            tasks = []
            for i in range(20):
                tasks.append(self.scanner.scan_url(f"https://example{i}.com"))
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        return asyncio.run(scan_multiple())
    
    def peakmem_concurrent_scans_20(self):
        """Measure peak memory usage during 20 concurrent scans"""
        async def scan_multiple():
            tasks = []
            for i in range(20):
                tasks.append(self.scanner.scan_url(f"https://example{i}.com"))
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        return asyncio.run(scan_multiple())


class InitializationBenchmarks:
    """Object initialization benchmarks"""
    
    def time_config_manager_init(self):
        """Time ConfigManager initialization"""
        return ConfigManager()
    
    def time_basic_scanner_init(self):
        """Time BasicTrackingScanner initialization"""
        config = ConfigManager()
        return BasicTrackingScanner(config_manager=config)
    
    def time_enhanced_scanner_init(self):
        """Time EnhancedTrackingScanner initialization"""
        config = ConfigManager()
        return EnhancedTrackingScanner(config_manager=config)
    
    def time_html_parser_init(self):
        """Time HTMLParserService initialization"""
        return HTMLParserService()


class ScalabilityBenchmarks:
    """Scalability tests with varying input sizes"""
    
    params = [10, 50, 100, 500, 1000]
    param_names = ['tracker_count']
    
    def setup(self, tracker_count):
        self.parser = HTMLParserService()
        
        # Generate HTML with specified number of trackers
        self.html = """
        <!DOCTYPE html>
        <html>
        <head><title>Scalability Test</title></head>
        <body>
            <h1>Scalability Test Page</h1>
        """
        
        for i in range(tracker_count):
            self.html += f'<img src="https://tracker{i}.com/pixel.gif" width="1" height="1">\n'
        
        self.html += """
        </body>
        </html>
        """
    
    def time_parse_variable_trackers(self, tracker_count):
        """Time parsing HTML with variable number of trackers"""
        return self.parser.parse(self.html)
    
    def peakmem_parse_variable_trackers(self, tracker_count):
        """Measure peak memory usage with variable tracker count"""
        return self.parser.parse(self.html)
