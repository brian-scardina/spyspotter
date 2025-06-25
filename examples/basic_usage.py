#!/usr/bin/env python3
"""
Example usage of the new modular PixelTracker API

Demonstrates how to use the refactored scanner with dependency injection
and clean interfaces.
"""

import asyncio
from pixeltracker import BasicTrackingScanner, ConfigManager


async def basic_scan_example():
    """Basic scanning example"""
    # Create configuration
    config = ConfigManager()
    config.scanning.rate_limit_delay = 0.5  # Faster scanning for demo
    config.scanning.concurrent_requests = 3
    
    # Create scanner with default services
    scanner = BasicTrackingScanner(config_manager=config)
    
    # Scan a single URL
    print("🔍 Scanning single URL...")
    result = await scanner.scan_url("https://example.com")
    
    if result.error:
        print(f"❌ Error: {result.error}")
    else:
        print(f"✅ Found {result.tracker_count} trackers")
        print(f"🔒 Privacy score: {result.privacy_analysis.privacy_score}/100")
        print(f"⚠️  Risk level: {result.privacy_analysis.risk_level.value}")
    
    # Scan multiple URLs
    print("\n🔍 Scanning multiple URLs...")
    urls = [
        "https://example.com",
        "https://github.com",
        "https://stackoverflow.com"
    ]
    
    results = await scanner.scan_multiple_urls(urls)
    
    for result in results:
        print(f"📊 {result.url}: {result.tracker_count} trackers")
    
    # Generate report
    print("\n📋 Generating HTML report...")
    html_report = await scanner.generate_report(results, format="html")
    
    with open("scan_report.html", "w") as f:
        f.write(html_report)
    
    print("✅ Report saved to scan_report.html")


async def custom_services_example():
    """Example with custom service implementations"""
    from pixeltracker.services import NetworkService, HTMLParserService
    from pixeltracker.models import ScanConfiguration
    
    # Create custom configuration
    config = ConfigManager()
    scan_config = config.get_scan_configuration()
    scan_config.rate_limit_delay = 2.0  # Slower for respectful scanning
    
    # Create custom services
    custom_fetcher = NetworkService(scan_config)
    custom_parser = HTMLParserService()
    
    # Create scanner with custom services (dependency injection)
    scanner = BasicTrackingScanner(
        config_manager=config,
        fetcher=custom_fetcher,
        parser=custom_parser
    )
    
    print("🔍 Using custom services...")
    result = await scanner.scan_url("https://example.com")
    print(f"✅ Scan completed with custom services: {result.tracker_count} trackers")


def config_management_example():
    """Example of configuration management"""
    # Create configuration manager
    config = ConfigManager()
    
    # Modify settings using dot notation
    config.set("scanning.rate_limit_delay", 1.5)
    config.set("privacy.scoring_weights.tracking_pixel", 8)
    config.set("javascript.enabled", True)
    
    # Validate configuration
    if config.validate():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration validation failed")
    
    # Save configuration
    config.save_config("my_config.yaml")
    print("📁 Configuration saved to my_config.yaml")
    
    # Load configuration
    config2 = ConfigManager("my_config.yaml")
    print(f"⚙️  Loaded rate limit: {config2.get('scanning.rate_limit_delay')}")


async def main():
    """Run all examples"""
    print("🚀 PixelTracker Modular API Examples")
    print("=" * 50)
    
    await basic_scan_example()
    
    print("\n" + "=" * 50)
    await custom_services_example()
    
    print("\n" + "=" * 50)
    config_management_example()


if __name__ == "__main__":
    asyncio.run(main())
