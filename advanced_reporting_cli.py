#!/usr/bin/env python3
"""
CLI tool for PixelTracker Advanced Reporting & Analytics

This script demonstrates the advanced reporting features including:
- PDF report generation
- Scheduled reporting with Celery
- Privacy Impact Index calculation
- Trend analysis
- Multi-format exports (CSV, Parquet, Excel)
- Prometheus metrics
- Slack/Email notifications
"""

import argparse
import json
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add the pixeltracker module to the path
sys.path.insert(0, str(Path(__file__).parent))

from pixeltracker.services.advanced_reporter import (
    AdvancedReporterService, 
    ReportConfiguration, 
    PrivacyImpactIndex
)
from pixeltracker.services.scheduled_reporter import (
    ScheduledReporterService,
    ScheduleConfiguration,
    AggregationJob
)
from pixeltracker.models import ScanResult, TrackerInfo, PrivacyAnalysis, PerformanceMetrics, RiskLevel, TrackerCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_data() -> List[ScanResult]:
    """Create sample scan results for demonstration"""
    sample_results = []
    
    # Sample URLs and data
    sample_urls = [
        "https://example.com",
        "https://news-site.com", 
        "https://ecommerce-store.com",
        "https://social-media.com",
        "https://analytics-heavy-site.com"
    ]
    
    for i, url in enumerate(sample_urls):
        # Create sample trackers
        trackers = []
        tracker_count = 3 + (i * 2)  # Varying number of trackers
        
        for j in range(tracker_count):
            tracker = TrackerInfo(
                tracker_type=["tracking_pixel", "analytics", "advertising", "social_media"][j % 4],
                domain=f"tracker{j}.example.com",
                method="img_src",
                category=TrackerCategory.ANALYTICS if j % 2 == 0 else TrackerCategory.ADVERTISING,
                risk_level=RiskLevel.MEDIUM if j % 3 == 0 else RiskLevel.HIGH,
                metadata={"detected_at": datetime.now().isoformat()}
            )
            trackers.append(tracker)
        
        # Create privacy analysis
        privacy_score = max(20, 100 - (tracker_count * 8))  # More trackers = lower score
        risk_level = RiskLevel.LOW if privacy_score > 80 else (
            RiskLevel.MEDIUM if privacy_score > 60 else RiskLevel.HIGH
        )
        
        privacy_analysis = PrivacyAnalysis(
            privacy_score=privacy_score,
            risk_level=risk_level,
            detected_categories=[tracker.category for tracker in trackers[:3]],
            recommendations=[
                "Consider reducing third-party trackers",
                "Implement consent management",
                "Review data collection practices"
            ]
        )
        
        # Create performance metrics
        performance = PerformanceMetrics(
            page_load_time=2.5 + (i * 0.5),
            dom_content_loaded=1.2 + (i * 0.2),
            first_contentful_paint=1.8 + (i * 0.3),
            network_requests=50 + (tracker_count * 5),
            data_transferred=1024 * (100 + tracker_count * 20)
        )
        
        # Create scan result
        result = ScanResult(
            url=url,
            timestamp=datetime.now().isoformat(),
            trackers=trackers,
            performance_metrics=performance,
            privacy_analysis=privacy_analysis,
            scan_duration=3.2 + (i * 0.8),
            scan_type="advanced",
            javascript_enabled=True
        )
        
        sample_results.append(result)
    
    return sample_results

def generate_pdf_report(config: Dict[str, Any], output_path: str):
    """Generate a PDF report"""
    logger.info("Generating PDF report...")
    
    # Create sample data
    results = create_sample_data()
    
    # Initialize reporter
    reporter = AdvancedReporterService(config)
    
    # Create report configuration
    report_config = ReportConfiguration(
        include_charts=True,
        include_trends=True,
        include_recommendations=True,
        company_name="Sample Company Analysis",
        chart_style="modern",
        color_scheme="blue"
    )
    
    # Generate PDF
    success = reporter.generate_pdf_report(results, output_path, report_config)
    
    if success:
        logger.info(f"PDF report generated successfully: {output_path}")
        
        # Also calculate and display Privacy Impact Index
        privacy_index = reporter.calculate_privacy_impact_index(results)
        logger.info(f"Privacy Impact Index: {privacy_index.score} ({privacy_index.risk_category})")
        logger.info(f"Compliance Score: {privacy_index.compliance_score}")
        
    else:
        logger.error("Failed to generate PDF report")

def export_data(config: Dict[str, Any], format_type: str, output_path: str):
    """Export data in various formats"""
    logger.info(f"Exporting data to {format_type} format...")
    
    # Create sample data
    results = create_sample_data()
    
    # Initialize reporter
    reporter = AdvancedReporterService(config)
    
    success = False
    if format_type.lower() == 'csv':
        success = reporter.export_to_csv(results, output_path)
    elif format_type.lower() == 'parquet':
        success = reporter.export_to_parquet(results, output_path)
    elif format_type.lower() == 'excel':
        success = reporter.generate_excel_report(results, output_path)
    else:
        logger.error(f"Unsupported export format: {format_type}")
        return
    
    if success:
        logger.info(f"Data exported successfully: {output_path}")
    else:
        logger.error(f"Failed to export data to {format_type}")

def setup_scheduled_reporting(config: Dict[str, Any]):
    """Setup scheduled reporting with Celery"""
    logger.info("Setting up scheduled reporting...")
    
    scheduler = ScheduledReporterService(config)
    
    if not scheduler.celery_app:
        logger.error("Celery not available. Please install celery and redis.")
        return
    
    # Configure daily report
    daily_schedule = ScheduleConfiguration(
        report_name="daily_privacy_report",
        schedule_type="daily",
        schedule_time="09:00",
        output_formats=["pdf", "csv", "html"],
        recipients=config.get('email', {}).get('default_recipients', []),
        slack_channels=config.get('slack', {}).get('default_channels', []),
        include_trends=True,
        include_charts=True,
        company_name="PixelTracker Analytics"
    )
    
    success = scheduler.schedule_report(daily_schedule)
    if success:
        logger.info("Daily report scheduled successfully")
    
    # Configure weekly aggregation
    weekly_aggregation = AggregationJob(
        job_name="weekly_analytics",
        aggregation_period="weekly",
        metrics_to_aggregate=[
            "privacy_scores", 
            "tracker_counts", 
            "risk_distribution", 
            "domain_analysis"
        ],
        output_table="weekly_summary"
    )
    
    success = scheduler.schedule_aggregation(weekly_aggregation)
    if success:
        logger.info("Weekly aggregation scheduled successfully")
    
    # Display scheduled tasks
    tasks = scheduler.get_scheduled_tasks()
    logger.info(f"Active scheduled tasks: {tasks.get('active_schedules', 0)}")

def push_prometheus_metrics(config: Dict[str, Any]):
    """Push metrics to Prometheus"""
    logger.info("Pushing metrics to Prometheus...")
    
    # Create sample data
    results = create_sample_data()
    
    # Initialize reporter
    reporter = AdvancedReporterService(config)
    
    # Push metrics
    success = reporter.push_metrics_to_prometheus(results)
    
    if success:
        logger.info("Metrics pushed to Prometheus successfully")
        
        # Get metrics in text format
        metrics_text = reporter.get_prometheus_metrics()
        if metrics_text:
            logger.info("Current metrics:")
            print(metrics_text)
    else:
        logger.warning("Prometheus not available or metrics push failed")

def send_slack_notification(config: Dict[str, Any], channel: str):
    """Send a test Slack notification"""
    logger.info(f"Sending Slack notification to {channel}...")
    
    # Create sample data
    results = create_sample_data()
    
    # Initialize reporter
    reporter = AdvancedReporterService(config)
    
    success = reporter.send_slack_notification(results, channel)
    
    if success:
        logger.info("Slack notification sent successfully")
    else:
        logger.warning("Slack notification failed - check configuration")

def analyze_trends(config: Dict[str, Any]):
    """Demonstrate trend analysis"""
    logger.info("Analyzing privacy trends...")
    
    # Create sample historical data
    results_by_period = {}
    base_date = datetime.now() - timedelta(days=7)
    
    for i in range(7):  # Last 7 days
        date_key = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        # Create varying data to show trends
        sample_results = create_sample_data()
        
        # Simulate degrading privacy over time
        for result in sample_results:
            result.privacy_analysis.privacy_score = max(
                30, 
                result.privacy_analysis.privacy_score - (i * 5)
            )
        
        results_by_period[date_key] = sample_results
    
    # Initialize reporter
    reporter = AdvancedReporterService(config)
    
    # Generate trend analysis
    trends = reporter.generate_trend_analysis(results_by_period, "daily")
    
    logger.info("Trend Analysis Results:")
    logger.info(f"Period: {trends.period}")
    logger.info(f"Privacy Score Trend: {trends.privacy_score_trend}")
    logger.info(f"Tracker Count Trend: {trends.tracker_count_trend}")
    logger.info(f"Domain Growth: {trends.domain_growth}")
    
    # Calculate Privacy Impact Index with historical data
    current_results = list(results_by_period.values())[-1]
    historical_results = []
    for results in list(results_by_period.values())[:-1]:
        historical_results.extend(results)
    
    privacy_index = reporter.calculate_privacy_impact_index(
        current_results, 
        historical_results
    )
    
    logger.info(f"Privacy Impact Index: {privacy_index.score}")
    logger.info(f"Trending: {privacy_index.trending}")
    logger.info(f"Risk Category: {privacy_index.risk_category}")

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file"""
    config_file = Path(config_path)
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            if config_file.suffix.lower() == '.json':
                return json.load(f)
            else:
                # Assume YAML
                try:
                    import yaml
                    return yaml.safe_load(f)
                except ImportError:
                    logger.error("PyYAML not installed, cannot load YAML config")
                    return {}
    else:
        logger.warning(f"Config file not found: {config_path}")
        return {}

def main():
    parser = argparse.ArgumentParser(
        description="PixelTracker Advanced Reporting & Analytics CLI"
    )
    
    parser.add_argument(
        '--config', 
        default='advanced_reporting_config.json',
        help='Configuration file path'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # PDF report command
    pdf_parser = subparsers.add_parser('pdf', help='Generate PDF report')
    pdf_parser.add_argument('--output', default='report.pdf', help='Output file path')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('format', choices=['csv', 'parquet', 'excel'], help='Export format')
    export_parser.add_argument('--output', required=True, help='Output file path')
    
    # Schedule command
    subparsers.add_parser('schedule', help='Setup scheduled reporting')
    
    # Prometheus command
    subparsers.add_parser('prometheus', help='Push metrics to Prometheus')
    
    # Slack command
    slack_parser = subparsers.add_parser('slack', help='Send Slack notification')
    slack_parser.add_argument('--channel', default='#general', help='Slack channel')
    
    # Trends command
    subparsers.add_parser('trends', help='Analyze privacy trends')
    
    # Demo command
    subparsers.add_parser('demo', help='Run full demonstration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Execute command
    try:
        if args.command == 'pdf':
            generate_pdf_report(config, args.output)
        
        elif args.command == 'export':
            export_data(config, args.format, args.output)
        
        elif args.command == 'schedule':
            setup_scheduled_reporting(config)
        
        elif args.command == 'prometheus':
            push_prometheus_metrics(config)
        
        elif args.command == 'slack':
            send_slack_notification(config, args.channel)
        
        elif args.command == 'trends':
            analyze_trends(config)
        
        elif args.command == 'demo':
            logger.info("Running full advanced reporting demonstration...")
            
            # Create output directory
            output_dir = Path('demo_outputs')
            output_dir.mkdir(exist_ok=True)
            
            # Generate reports in all formats
            generate_pdf_report(config, str(output_dir / 'demo_report.pdf'))
            export_data(config, 'csv', str(output_dir / 'demo_export.csv'))
            export_data(config, 'excel', str(output_dir / 'demo_report.xlsx'))
            export_data(config, 'parquet', str(output_dir / 'demo_data.parquet'))
            
            # Analyze trends
            analyze_trends(config)
            
            # Push Prometheus metrics
            push_prometheus_metrics(config)
            
            logger.info("Demonstration completed! Check the demo_outputs directory.")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
