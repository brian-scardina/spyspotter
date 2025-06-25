#!/usr/bin/env python3
"""
Scheduled Reporter service for PixelTracker

Handles automated report generation, aggregation, and notifications
using Celery for task scheduling and background processing.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

try:
    from celery import Celery, Task
    from celery.schedules import crontab
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logging.warning("Celery not available, scheduled reporting will be disabled")

try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    from email.mime.base import MimeBase
    from email import encoders
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

from ..models import ScanResult
from .advanced_reporter import AdvancedReporterService, ReportConfiguration, PrivacyImpactIndex, TrendAnalysis
from ..persistence.repositories import ScanResultRepository

logger = logging.getLogger(__name__)

@dataclass
class ScheduleConfiguration:
    """Configuration for scheduled reports"""
    report_name: str
    schedule_type: str  # 'daily', 'weekly', 'monthly'
    schedule_time: str  # '09:00' for daily, 'monday' for weekly, '1' for monthly
    output_formats: List[str] = None  # ['pdf', 'excel', 'csv']
    recipients: List[str] = None  # Email recipients
    slack_channels: List[str] = None  # Slack channels
    include_trends: bool = True
    include_charts: bool = True
    company_name: str = "PixelTracker Analysis"
    retention_days: int = 30  # How long to keep generated reports
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ['pdf', 'html']
        if self.recipients is None:
            self.recipients = []
        if self.slack_channels is None:
            self.slack_channels = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AggregationJob:
    """Configuration for data aggregation jobs"""
    job_name: str
    aggregation_period: str  # 'hourly', 'daily', 'weekly'
    metrics_to_aggregate: List[str]  # ['privacy_scores', 'tracker_counts', 'risk_distribution']
    output_table: str  # Database table or file prefix
    retention_period: int = 90  # Days to keep aggregated data
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ScheduledReporterService:
    """Service for scheduled reporting and aggregation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.setup_celery()
        self.setup_email()
        self.reporter = AdvancedReporterService(config)
        self.repository = ScanResultRepository()
        
    def setup_celery(self):
        """Setup Celery for task scheduling"""
        if not CELERY_AVAILABLE:
            self.celery_app = None
            return
            
        # Create Celery app
        self.celery_app = Celery('pixeltracker_scheduler')
        
        # Configure Celery
        celery_config = self.config.get('celery', {})
        broker_url = celery_config.get('broker_url', 'redis://localhost:6379/0')
        result_backend = celery_config.get('result_backend', 'redis://localhost:6379/0')
        
        self.celery_app.conf.update(
            broker_url=broker_url,
            result_backend=result_backend,
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            beat_schedule={}
        )
        
        # Register tasks
        self.register_tasks()
    
    def setup_email(self):
        """Setup email configuration"""
        self.email_config = self.config.get('email', {})
        self.smtp_server = self.email_config.get('smtp_server')
        self.smtp_port = self.email_config.get('smtp_port', 587)
        self.smtp_username = self.email_config.get('username')
        self.smtp_password = self.email_config.get('password')
        self.from_email = self.email_config.get('from_email')
    
    def register_tasks(self):
        """Register Celery tasks"""
        if not self.celery_app:
            return
            
        @self.celery_app.task(bind=True)
        def generate_scheduled_report(self, schedule_config_dict: Dict[str, Any]):
            """Task to generate a scheduled report"""
            try:
                schedule_config = ScheduleConfiguration(**schedule_config_dict)
                return self._generate_scheduled_report_task(schedule_config)
            except Exception as e:
                logger.error(f"Failed to generate scheduled report: {e}")
                self.retry(countdown=60, max_retries=3)
        
        @self.celery_app.task(bind=True)
        def aggregate_data(self, aggregation_config_dict: Dict[str, Any]):
            """Task to aggregate data"""
            try:
                aggregation_config = AggregationJob(**aggregation_config_dict)
                return self._aggregate_data_task(aggregation_config)
            except Exception as e:
                logger.error(f"Failed to aggregate data: {e}")
                self.retry(countdown=60, max_retries=3)
        
        @self.celery_app.task(bind=True)
        def cleanup_old_reports(self, retention_days: int = 30):
            """Task to clean up old report files"""
            try:
                return self._cleanup_old_reports_task(retention_days)
            except Exception as e:
                logger.error(f"Failed to cleanup old reports: {e}")
        
        @self.celery_app.task(bind=True)
        def send_trend_alerts(self, alert_config_dict: Dict[str, Any]):
            """Task to analyze trends and send alerts if thresholds are exceeded"""
            try:
                return self._send_trend_alerts_task(alert_config_dict)
            except Exception as e:
                logger.error(f"Failed to send trend alerts: {e}")
        
        # Store task references
        self.generate_scheduled_report_task = generate_scheduled_report
        self.aggregate_data_task = aggregate_data
        self.cleanup_old_reports_task = cleanup_old_reports
        self.send_trend_alerts_task = send_trend_alerts
    
    def schedule_report(self, schedule_config: ScheduleConfiguration) -> bool:
        """Schedule a recurring report"""
        if not self.celery_app:
            logger.error("Celery not available for scheduling")
            return False
        
        try:
            # Convert schedule configuration to crontab
            if schedule_config.schedule_type == 'daily':
                hour, minute = map(int, schedule_config.schedule_time.split(':'))
                schedule = crontab(hour=hour, minute=minute)
            elif schedule_config.schedule_type == 'weekly':
                day_of_week = {
                    'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4,
                    'friday': 5, 'saturday': 6, 'sunday': 0
                }[schedule_config.schedule_time.lower()]
                schedule = crontab(hour=9, minute=0, day_of_week=day_of_week)
            elif schedule_config.schedule_type == 'monthly':
                day_of_month = int(schedule_config.schedule_time)
                schedule = crontab(hour=9, minute=0, day_of_month=day_of_month)
            else:
                raise ValueError(f"Unsupported schedule type: {schedule_config.schedule_type}")
            
            # Add to beat schedule
            task_name = f"scheduled_report_{schedule_config.report_name}"
            self.celery_app.conf.beat_schedule[task_name] = {
                'task': 'generate_scheduled_report',
                'schedule': schedule,
                'args': [schedule_config.to_dict()]
            }
            
            logger.info(f"Scheduled report '{schedule_config.report_name}' configured")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule report: {e}")
            return False
    
    def schedule_aggregation(self, aggregation_config: AggregationJob) -> bool:
        """Schedule a data aggregation job"""
        if not self.celery_app:
            logger.error("Celery not available for scheduling")
            return False
        
        try:
            # Convert aggregation period to crontab
            if aggregation_config.aggregation_period == 'hourly':
                schedule = crontab(minute=0)  # Every hour
            elif aggregation_config.aggregation_period == 'daily':
                schedule = crontab(hour=1, minute=0)  # Daily at 1 AM
            elif aggregation_config.aggregation_period == 'weekly':
                schedule = crontab(hour=2, minute=0, day_of_week=0)  # Weekly on Sunday at 2 AM
            else:
                raise ValueError(f"Unsupported aggregation period: {aggregation_config.aggregation_period}")
            
            # Add to beat schedule
            task_name = f"aggregation_{aggregation_config.job_name}"
            self.celery_app.conf.beat_schedule[task_name] = {
                'task': 'aggregate_data',
                'schedule': schedule,
                'args': [aggregation_config.to_dict()]
            }
            
            logger.info(f"Aggregation job '{aggregation_config.job_name}' scheduled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule aggregation: {e}")
            return False
    
    def _generate_scheduled_report_task(self, schedule_config: ScheduleConfiguration) -> Dict[str, Any]:
        """Generate a scheduled report"""
        try:
            # Get data for the report period
            end_date = datetime.now()
            if schedule_config.schedule_type == 'daily':
                start_date = end_date - timedelta(days=1)
            elif schedule_config.schedule_type == 'weekly':
                start_date = end_date - timedelta(weeks=1)
            elif schedule_config.schedule_type == 'monthly':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=1)
            
            # Fetch scan results from repository
            results = self.repository.get_results_by_date_range(start_date, end_date)
            
            if not results:
                logger.warning(f"No data found for report '{schedule_config.report_name}'")
                return {"status": "no_data", "message": "No scan results found for the specified period"}
            
            # Create report configuration
            report_config = ReportConfiguration(
                include_charts=schedule_config.include_charts,
                include_trends=schedule_config.include_trends,
                company_name=schedule_config.company_name
            )
            
            # Generate reports in requested formats
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = Path(self.config.get('reports_dir', 'reports'))
            report_dir.mkdir(exist_ok=True)
            
            generated_files = []
            
            for format_type in schedule_config.output_formats:
                filename = f"{schedule_config.report_name}_{timestamp}.{format_type}"
                filepath = report_dir / filename
                
                if format_type == 'pdf':
                    success = self.reporter.generate_pdf_report(results, str(filepath), report_config)
                elif format_type == 'excel':
                    success = self.reporter.generate_excel_report(results, str(filepath))
                elif format_type == 'csv':
                    success = self.reporter.export_to_csv(results, str(filepath))
                elif format_type == 'parquet':
                    success = self.reporter.export_to_parquet(results, str(filepath))
                elif format_type == 'html':
                    html_content = self.reporter._generate_enhanced_html_report(results, report_config)
                    with open(filepath, 'w') as f:
                        f.write(html_content)
                    success = True
                else:
                    logger.warning(f"Unsupported format: {format_type}")
                    continue
                
                if success:
                    generated_files.append(str(filepath))
            
            # Send notifications
            notification_results = []
            
            # Email notifications
            if schedule_config.recipients and generated_files:
                email_success = self._send_email_notification(
                    schedule_config, results, generated_files
                )
                notification_results.append({"type": "email", "success": email_success})
            
            # Slack notifications
            if schedule_config.slack_channels:
                for channel in schedule_config.slack_channels:
                    slack_success = self.reporter.send_slack_notification(
                        results, channel
                    )
                    notification_results.append({
                        "type": "slack", 
                        "channel": channel, 
                        "success": slack_success
                    })
            
            # Push metrics to Prometheus
            metrics_success = self.reporter.push_metrics_to_prometheus(results)
            
            return {
                "status": "success",
                "report_name": schedule_config.report_name,
                "generated_files": generated_files,
                "notifications": notification_results,
                "metrics_pushed": metrics_success,
                "scan_results_count": len(results),
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error in scheduled report generation: {e}")
            return {"status": "error", "message": str(e)}
    
    def _aggregate_data_task(self, aggregation_config: AggregationJob) -> Dict[str, Any]:
        """Aggregate data for analytics"""
        try:
            # Determine aggregation period
            end_date = datetime.now()
            if aggregation_config.aggregation_period == 'hourly':
                start_date = end_date - timedelta(hours=1)
                period_format = "%Y-%m-%d %H:00:00"
            elif aggregation_config.aggregation_period == 'daily':
                start_date = end_date - timedelta(days=1)
                period_format = "%Y-%m-%d"
            elif aggregation_config.aggregation_period == 'weekly':
                start_date = end_date - timedelta(weeks=1)
                period_format = "%Y-W%U"  # Week format
            else:
                start_date = end_date - timedelta(days=1)
                period_format = "%Y-%m-%d"
            
            # Fetch data
            results = self.repository.get_results_by_date_range(start_date, end_date)
            
            if not results:
                return {"status": "no_data", "period": start_date.strftime(period_format)}
            
            # Perform aggregations
            aggregated_data = {}
            period_key = start_date.strftime(period_format)
            
            if 'privacy_scores' in aggregation_config.metrics_to_aggregate:
                privacy_scores = [r.privacy_analysis.privacy_score for r in results]
                aggregated_data['privacy_scores'] = {
                    'avg': sum(privacy_scores) / len(privacy_scores),
                    'min': min(privacy_scores),
                    'max': max(privacy_scores),
                    'count': len(privacy_scores)
                }
            
            if 'tracker_counts' in aggregation_config.metrics_to_aggregate:
                tracker_counts = [len(r.trackers) for r in results]
                aggregated_data['tracker_counts'] = {
                    'total': sum(tracker_counts),
                    'avg': sum(tracker_counts) / len(tracker_counts),
                    'max': max(tracker_counts),
                    'count': len(tracker_counts)
                }
            
            if 'risk_distribution' in aggregation_config.metrics_to_aggregate:
                risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
                for result in results:
                    risk_level = result.privacy_analysis.risk_level.value
                    risk_counts[risk_level] += 1
                aggregated_data['risk_distribution'] = risk_counts
            
            if 'domain_analysis' in aggregation_config.metrics_to_aggregate:
                domain_stats = self.reporter._analyze_domains(results)
                aggregated_data['top_domains'] = domain_stats[:10]  # Top 10 domains
            
            # Store aggregated data
            self._store_aggregated_data(
                aggregation_config.output_table,
                period_key,
                aggregated_data
            )
            
            return {
                "status": "success",
                "job_name": aggregation_config.job_name,
                "period": period_key,
                "aggregated_metrics": list(aggregated_data.keys()),
                "source_records": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error in data aggregation: {e}")
            return {"status": "error", "message": str(e)}
    
    def _cleanup_old_reports_task(self, retention_days: int) -> Dict[str, Any]:
        """Clean up old report files"""
        try:
            report_dir = Path(self.config.get('reports_dir', 'reports'))
            if not report_dir.exists():
                return {"status": "no_directory"}
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cleaned_files = []
            
            for file_path in report_dir.iterdir():
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        try:
                            file_path.unlink()
                            cleaned_files.append(str(file_path))
                        except Exception as e:
                            logger.error(f"Failed to delete {file_path}: {e}")
            
            return {
                "status": "success",
                "cleaned_files": len(cleaned_files),
                "retention_days": retention_days
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_trend_alerts_task(self, alert_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends and send alerts if thresholds are exceeded"""
        try:
            # Get recent data for trend analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Last week
            
            current_results = self.repository.get_results_by_date_range(
                end_date - timedelta(days=1), end_date
            )
            historical_results = self.repository.get_results_by_date_range(
                start_date, end_date - timedelta(days=1)
            )
            
            if not current_results or not historical_results:
                return {"status": "insufficient_data"}
            
            # Calculate current and historical privacy impact indices
            current_index = self.reporter.calculate_privacy_impact_index(current_results)
            historical_index = self.reporter.calculate_privacy_impact_index(historical_results)
            
            alerts_triggered = []
            
            # Check thresholds
            privacy_degradation_threshold = alert_config.get('privacy_degradation_threshold', 10)
            tracker_increase_threshold = alert_config.get('tracker_increase_threshold', 20)
            
            # Privacy score degradation alert
            if current_index.score < historical_index.score - privacy_degradation_threshold:
                alerts_triggered.append({
                    "type": "privacy_degradation",
                    "current_score": current_index.score,
                    "historical_score": historical_index.score,
                    "degradation": historical_index.score - current_index.score
                })
            
            # Tracker count increase alert
            current_avg_trackers = sum(len(r.trackers) for r in current_results) / len(current_results)
            historical_avg_trackers = sum(len(r.trackers) for r in historical_results) / len(historical_results)
            
            tracker_increase_pct = ((current_avg_trackers - historical_avg_trackers) / historical_avg_trackers) * 100
            
            if tracker_increase_pct > tracker_increase_threshold:
                alerts_triggered.append({
                    "type": "tracker_increase",
                    "current_avg": current_avg_trackers,
                    "historical_avg": historical_avg_trackers,
                    "increase_percent": tracker_increase_pct
                })
            
            # Send alerts if any were triggered
            if alerts_triggered and alert_config.get('recipients'):
                self._send_alert_email(alert_config, alerts_triggered)
            
            return {
                "status": "success",
                "alerts_triggered": len(alerts_triggered),
                "alerts": alerts_triggered
            }
            
        except Exception as e:
            logger.error(f"Error in trend alerts: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_email_notification(
        self,
        schedule_config: ScheduleConfiguration,
        results: List[ScanResult],
        file_paths: List[str]
    ) -> bool:
        """Send email notification with report attachments"""
        if not EMAIL_AVAILABLE or not self.smtp_server:
            logger.warning("Email not configured")
            return False
        
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(schedule_config.recipients)
            msg['Subject'] = f"PixelTracker Report: {schedule_config.report_name}"
            
            # Generate summary for email body
            summary = self.reporter.generate_summary(results)
            privacy_index = self.reporter.calculate_privacy_impact_index(results)
            
            body = f"""
Dear Team,

Your scheduled PixelTracker report "{schedule_config.report_name}" is ready.

Summary:
- URLs Analyzed: {summary['total_urls']}
- Trackers Found: {summary['total_trackers']}
- Privacy Score: {summary['average_privacy_score']}/100
- Risk Level: {privacy_index.risk_category.title()}
- Privacy Impact Index: {privacy_index.score}

The detailed reports are attached to this email.

Best regards,
PixelTracker Automated Reporting System
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Attach report files
            for file_path in file_paths:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MimeBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {len(schedule_config.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_alert_email(self, alert_config: Dict[str, Any], alerts: List[Dict[str, Any]]) -> bool:
        """Send alert email for trend analysis"""
        if not EMAIL_AVAILABLE or not self.smtp_server:
            return False
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(alert_config['recipients'])
            msg['Subject'] = "🚨 PixelTracker Trend Alert"
            
            body = "Dear Team,\n\nThe following privacy/tracking trend alerts have been triggered:\n\n"
            
            for alert in alerts:
                if alert['type'] == 'privacy_degradation':
                    body += f"⚠️ Privacy Score Degradation:\n"
                    body += f"   Current: {alert['current_score']:.2f}\n"
                    body += f"   Previous: {alert['historical_score']:.2f}\n"
                    body += f"   Degradation: {alert['degradation']:.2f} points\n\n"
                
                elif alert['type'] == 'tracker_increase':
                    body += f"📈 Tracker Count Increase:\n"
                    body += f"   Current Average: {alert['current_avg']:.2f}\n"
                    body += f"   Previous Average: {alert['historical_avg']:.2f}\n"
                    body += f"   Increase: {alert['increase_percent']:.1f}%\n\n"
            
            body += "Please review the latest scan results and take appropriate action.\n\n"
            body += "Best regards,\nPixelTracker Alert System"
            
            msg.attach(MimeText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False
    
    def _store_aggregated_data(self, output_table: str, period_key: str, data: Dict[str, Any]):
        """Store aggregated data to database or file"""
        try:
            # For now, store as JSON file - in production, use database
            aggregation_dir = Path(self.config.get('aggregation_dir', 'aggregations'))
            aggregation_dir.mkdir(exist_ok=True)
            
            output_file = aggregation_dir / f"{output_table}_{period_key}.json"
            
            with open(output_file, 'w') as f:
                json.dump({
                    'period': period_key,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f, indent=2, default=str)
            
            logger.info(f"Aggregated data stored: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to store aggregated data: {e}")
    
    def get_scheduled_tasks(self) -> Dict[str, Any]:
        """Get information about currently scheduled tasks"""
        if not self.celery_app:
            return {"error": "Celery not available"}
        
        return {
            "beat_schedule": dict(self.celery_app.conf.beat_schedule),
            "active_schedules": len(self.celery_app.conf.beat_schedule)
        }
    
    def remove_scheduled_task(self, task_name: str) -> bool:
        """Remove a scheduled task"""
        if not self.celery_app:
            return False
        
        try:
            if task_name in self.celery_app.conf.beat_schedule:
                del self.celery_app.conf.beat_schedule[task_name]
                logger.info(f"Removed scheduled task: {task_name}")
                return True
            else:
                logger.warning(f"Task not found: {task_name}")
                return False
        except Exception as e:
            logger.error(f"Failed to remove task: {e}")
            return False
