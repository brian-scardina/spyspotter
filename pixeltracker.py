#!/usr/bin/env python3
"""
PixelTracker - Unified CLI tool for tracking pixel detection
Combines both basic and enhanced scanners with improved configuration management
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

# Import our modules
try:
    from config import Config
    from tracking_pixel_scanner import TrackingPixelScanner
    from enhanced_tracking_scanner import EnhancedTrackingScanner
    from tracker_database import tracker_db
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required dependencies are installed.")
    # Try to continue without tracker_db
    tracker_db = None

def setup_logging(config: Config) -> None:
    """Setup logging based on configuration"""
    log_level = getattr(logging, config.get('logging.level', 'INFO').upper())
    log_file = config.get('logging.file', 'pixeltracker.log')
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")

def validate_urls(urls: List[str]) -> List[str]:
    """Validate and normalize URLs"""
    validated_urls = []
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        validated_urls.append(url)
    return validated_urls

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description='PixelTracker - Advanced tracking pixel detection tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  python pixeltracker.py scan example.com
  
  # Enhanced scan with JavaScript execution
  python pixeltracker.py scan --enhanced --enable-js example.com facebook.com
  
  # Scan with custom configuration
  python pixeltracker.py scan --config myconfig.yaml example.com
  
  # Generate sample configuration
  python pixeltracker.py config --create-sample config.yaml
  
  # Validate configuration
  python pixeltracker.py config --validate config.yaml
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan URLs for tracking pixels')
    scan_parser.add_argument('urls', nargs='+', help='URLs to scan')
    scan_parser.add_argument('--config', '-c', help='Configuration file path')
    scan_parser.add_argument('--output', '-o', help='Output file path')
    scan_parser.add_argument('--format', choices=['json', 'html', 'csv'], default='json', help='Output format')
    scan_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    scan_parser.add_argument('--enhanced', action='store_true', help='Use enhanced scanner with ML capabilities')
    scan_parser.add_argument('--enable-js', action='store_true', help='Enable JavaScript execution (enhanced mode only)')
    scan_parser.add_argument('--concurrent', type=int, help='Number of concurrent requests')
    scan_parser.add_argument('--rate-limit', type=float, help='Rate limit delay between requests (seconds)')
    scan_parser.add_argument('--detailed-report', help='Generate detailed HTML report')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('--create-sample', help='Create sample configuration file')
    config_group.add_argument('--validate', help='Validate configuration file')
    config_group.add_argument('--show-defaults', action='store_true', help='Show default configuration')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    info_parser.add_argument('--dependencies', action='store_true', help='Check dependencies')
    info_parser.add_argument('--domains', action='store_true', help='Show tracked domains count')
    
    return parser

async def run_enhanced_scan(config: Config, args) -> None:
    """Run enhanced scanner"""
    try:
        # Override config with command line arguments
        if args.enable_js:
            config.set('javascript.enabled', True)
        if args.concurrent:
            config.set('scanning.concurrent_requests', args.concurrent)
        if args.rate_limit:
            config.set('scanning.rate_limit_delay', args.rate_limit)
        
        scanner = EnhancedTrackingScanner(args.config)
        urls = validate_urls(args.urls)
        
        print(f"🚀 Starting enhanced scan of {len(urls)} URLs...")
        print(f"⚙️  JavaScript execution: {'enabled' if config.get('javascript.enabled') else 'disabled'}")
        print(f"🔧 Concurrent requests: {config.get('scanning.concurrent_requests', 10)}")
        
        # Perform scans
        results = await scanner.scan_multiple_urls(urls)
        
        # Generate intelligence report
        intelligence_report = scanner.generate_intelligence_report(results)
        
        # Display results
        for result in results:
            print(f"\n✅ {result.url}")
            print(f"   🔍 Trackers found: {len(result.trackers)}")
            print(f"   🔒 Privacy score: {result.privacy_score}/100")
            print(f"   ⚠️  Risk level: {result.risk_assessment['overall_risk']}")
            
            if args.verbose:
                for tracker in result.trackers[:3]:  # Show first 3 trackers
                    print(f"      🎯 {tracker.tracker_type}: {tracker.domain} ({tracker.risk_level} risk)")
        
        print(f"\n📊 Total trackers found: {intelligence_report['scan_summary']['total_trackers']}")
        print(f"🎯 Unique tracking domains: {intelligence_report['threat_intelligence']['unique_tracking_domains']}")
        
        # Save results if requested
        if args.output:
            import json
            from dataclasses import asdict
            
            output_data = {
                'results': [asdict(result) for result in results],
                'intelligence_report': intelligence_report
            }
            
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            print(f"💾 Results saved to {args.output}")
        
    except Exception as e:
        logging.error(f"Enhanced scan failed: {e}")
        sys.exit(1)

def run_basic_scan(config: Config, args) -> None:
    """Run basic scanner"""
    try:
        # Apply command line overrides
        rate_limit = args.rate_limit if args.rate_limit else config.get('scanning.rate_limit_delay', 1.0)
        
        scanner = TrackingPixelScanner(rate_limit_delay=rate_limit)
        urls = validate_urls(args.urls)
        
        print(f"🚀 Starting basic scan of {len(urls)} URLs...")
        print(f"⏱️  Rate limit delay: {rate_limit}s")
        
        results = []
        for url in urls:
            result = scanner.scan_url(url)
            results.append(result)
            
            # Display summary
            if 'error' in result:
                print(f"❌ Error scanning {url}: {result['error']}")
            else:
                print(f"✅ {url}")
                print(f"   📊 Found {result['pixel_count']} tracking pixels")
                print(f"   🔧 Found {result['js_tracker_count']} JavaScript trackers")
                print(f"   🏷️  Found {result['meta_tracker_count']} meta tag trackers")
                print(f"   📈 Total trackers: {result['summary']['total_trackers']}")
                
                privacy = result.get('privacy_analysis', {})
                print(f"   🔒 Privacy score: {privacy.get('privacy_score', 'N/A')}/100")
                print(f"   ⚠️  Risk level: {privacy.get('risk_level', 'Unknown')}")
                
                if args.verbose and result['summary']['domains_found']:
                    print(f"   🌐 Domains: {', '.join(result['summary']['domains_found'][:5])}")
        
        # Generate detailed report if requested
        if args.detailed_report:
            detailed_content = scanner.generate_detailed_report(results, 'html')
            with open(args.detailed_report, 'w') as f:
                f.write(detailed_content)
            print(f"📋 Detailed report saved to {args.detailed_report}")
        
        # Save results if requested
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Results saved to {args.output}")
        
    except Exception as e:
        logging.error(f"Basic scan failed: {e}")
        sys.exit(1)

def handle_config_command(args) -> None:
    """Handle configuration management commands"""
    if args.create_sample:
        config = Config()
        config.create_sample_config(args.create_sample)
    
    elif args.validate:
        config = Config(args.validate)
        if config.validate():
            print(f"✅ Configuration file {args.validate} is valid")
        else:
            print(f"❌ Configuration file {args.validate} has errors")
            sys.exit(1)
    
    elif args.show_defaults:
        import json
        config = Config()
        print(json.dumps(config.config, indent=2))

def handle_info_command(args) -> None:
    """Handle info command"""
    if args.dependencies:
        print("📦 Checking dependencies...")
        
        # Check core dependencies
        core_deps = {
            'requests': 'requests',
            'beautifulsoup4': 'bs4',
            'lxml': 'lxml',
            'aiohttp': 'aiohttp',
            'pyyaml': 'yaml'
        }
        missing_core = []
        
        for dep_name, module_name in core_deps.items():
            try:
                __import__(module_name)
                print(f"  ✅ {dep_name}")
            except ImportError:
                print(f"  ❌ {dep_name}")
                missing_core.append(dep_name)
        
        # Check optional ML dependencies
        print("\n🤖 Optional ML dependencies:")
        ml_deps = ['numpy', 'pandas', 'scikit-learn', 'tensorflow', 'torch']
        
        for dep in ml_deps:
            try:
                __import__(dep.replace('-', '_'))
                print(f"  ✅ {dep}")
            except ImportError:
                print(f"  ⚠️  {dep} (optional)")
        
        if missing_core:
            print(f"\n❌ Missing core dependencies: {', '.join(missing_core)}")
            print("Install with: pip install -r requirements-core.txt")
            sys.exit(1)
        else:
            print("\n✅ All core dependencies available")
    
    elif args.domains:
        scanner = TrackingPixelScanner()
        print(f"📊 Tracking {len(scanner.tracking_domains)} known domains")
        print("🎯 Top 10 domains:")
        for i, domain in enumerate(scanner.tracking_domains[:10], 1):
            print(f"  {i:2d}. {domain}")
        
        # Show comprehensive database statistics if available
        if tracker_db:
            print("\n🗄️  Comprehensive Tracker Database:")
            stats = tracker_db.get_statistics()
            print(f"   📈 Total tracker patterns: {stats['total_trackers']}")
            print(f"   🌐 Total domains: {stats['total_domains']}")
            print(f"   🔍 Total detection patterns: {stats['total_patterns']}")
            print(f"   🔒 GDPR relevant: {stats['gdpr_relevant_count']}")
            print(f"   🏛️  CCPA relevant: {stats['ccpa_relevant_count']}")
            
            print("\n📊 Categories:")
            for category, count in stats['categories'].items():
                print(f"   {category}: {count}")
            
            print("\n⚠️  Risk Levels:")
            for risk, count in stats['risk_levels'].items():
                print(f"   {risk}: {count}")

async def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Load configuration
    config = Config(args.config if hasattr(args, 'config') else None)
    
    # Setup logging
    setup_logging(config)
    
    # Validate configuration
    if not config.validate():
        print("❌ Configuration validation failed")
        sys.exit(1)
    
    # Handle commands
    if args.command == 'scan':
        if args.enhanced:
            await run_enhanced_scan(config, args)
        else:
            run_basic_scan(config, args)
    
    elif args.command == 'config':
        handle_config_command(args)
    
    elif args.command == 'info':
        handle_info_command(args)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
