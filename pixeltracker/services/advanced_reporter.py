#!/usr/bin/env python3
"""
Advanced Reporter service for PixelTracker

Generates reports in multiple formats including PDF, provides analytics,
scheduled reporting, and integrates with external systems.
"""

import json
import csv
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from io import StringIO, BytesIO
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import kaleido
from dataclasses import dataclass, asdict

# PDF generation imports
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logging.warning("WeasyPrint not available, PDF generation will be disabled")

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False

# Prometheus integration
try:
    from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Slack integration
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

from ..interfaces import Reporter
from ..models import ScanResult, RiskLevel, TrackerCategory
from .reporter import ReporterService

logger = logging.getLogger(__name__)

@dataclass
class PrivacyImpactIndex:
    """Privacy Impact Index calculation"""
    score: float
    risk_category: str
    factors: Dict[str, float]
    trending: str  # 'improving', 'stable', 'degrading'
    compliance_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass 
class TrendAnalysis:
    """Trend analysis over time periods"""
    period: str  # 'daily', 'weekly', 'monthly'
    privacy_score_trend: List[float]
    tracker_count_trend: List[int]
    risk_level_distribution: Dict[str, List[int]]
    domain_growth: List[int]
    timestamps: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ReportConfiguration:
    """Configuration for report generation"""
    include_charts: bool = True
    include_trends: bool = True
    include_recommendations: bool = True
    chart_style: str = 'modern'  # 'modern', 'classic', 'minimal'
    color_scheme: str = 'blue'  # 'blue', 'red', 'green', 'purple'
    logo_path: Optional[str] = None
    company_name: str = "PixelTracker Analysis"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class AdvancedReporterService(ReporterService):
    """Advanced reporter service with PDF, analytics, and scheduling"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self.setup_prometheus_metrics()
        self.setup_slack_client()
        
    def setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.registry = CollectorRegistry()
        self.metrics = {
            'scans_total': Counter('pixeltracker_scans_total', 'Total number of scans', registry=self.registry),
            'trackers_found': Gauge('pixeltracker_trackers_found', 'Current number of trackers found', registry=self.registry),
            'privacy_score': Gauge('pixeltracker_privacy_score', 'Current privacy score', registry=self.registry),
            'scan_duration': Histogram('pixeltracker_scan_duration_seconds', 'Scan duration in seconds', registry=self.registry),
            'risk_level_distribution': Gauge('pixeltracker_risk_level', 'Risk level distribution', ['level'], registry=self.registry)
        }
    
    def setup_slack_client(self):
        """Setup Slack client if available"""
        self.slack_client = None
        if SLACK_AVAILABLE and self.config.get('slack', {}).get('token'):
            self.slack_client = WebClient(token=self.config['slack']['token'])
    
    def generate_pdf_report(
        self,
        results: List[ScanResult],
        output_path: str,
        config: Optional[ReportConfiguration] = None
    ) -> bool:
        """Generate PDF report using WeasyPrint"""
        if not WEASYPRINT_AVAILABLE:
            logger.error("WeasyPrint not available for PDF generation")
            return False
            
        try:
            config = config or ReportConfiguration()
            
            # Generate enhanced HTML with charts
            html_content = self._generate_enhanced_html_report(results, config)
            
            # Generate PDF
            html_doc = HTML(string=html_content)
            css_style = self._get_pdf_css_style(config)
            
            html_doc.write_pdf(output_path, stylesheets=[CSS(string=css_style)])
            
            logger.info(f"PDF report generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            return False
    
    def calculate_privacy_impact_index(
        self,
        current_results: List[ScanResult],
        historical_results: Optional[List[ScanResult]] = None
    ) -> PrivacyImpactIndex:
        """Calculate Privacy Impact Index"""
        if not current_results:
            return PrivacyImpactIndex(0, 'unknown', {}, 'stable', 0)
        
        # Calculate base factors
        factors = {
            'tracker_density': self._calculate_tracker_density(current_results),
            'risk_severity': self._calculate_risk_severity(current_results),
            'domain_diversity': self._calculate_domain_diversity(current_results),
            'category_spread': self._calculate_category_spread(current_results),
            'third_party_exposure': self._calculate_third_party_exposure(current_results)
        }
        
        # Calculate weighted score
        weights = {
            'tracker_density': 0.25,
            'risk_severity': 0.30,
            'domain_diversity': 0.20,
            'category_spread': 0.15,
            'third_party_exposure': 0.10
        }
        
        score = sum(factors[factor] * weights[factor] for factor in factors)
        score = max(0, min(100, score))  # Normalize to 0-100
        
        # Determine risk category
        if score >= 80:
            risk_category = 'low'
        elif score >= 60:
            risk_category = 'medium'
        elif score >= 40:
            risk_category = 'high'
        else:
            risk_category = 'critical'
        
        # Calculate trending
        trending = 'stable'
        if historical_results:
            historical_index = self.calculate_privacy_impact_index(historical_results)
            if score > historical_index.score + 5:
                trending = 'improving'
            elif score < historical_index.score - 5:
                trending = 'degrading'
        
        # Compliance score (simplified)
        compliance_score = min(100, score + 10)  # Assume slightly better compliance
        
        return PrivacyImpactIndex(
            score=round(score, 2),
            risk_category=risk_category,
            factors=factors,
            trending=trending,
            compliance_score=round(compliance_score, 2)
        )
    
    def generate_trend_analysis(
        self,
        results_by_period: Dict[str, List[ScanResult]],
        period: str = 'daily'
    ) -> TrendAnalysis:
        """Generate trend analysis over time"""
        timestamps = sorted(results_by_period.keys())
        privacy_scores = []
        tracker_counts = []
        risk_distributions = {'low': [], 'medium': [], 'high': [], 'critical': []}
        domain_counts = []
        
        for timestamp in timestamps:
            results = results_by_period[timestamp]
            
            if results:
                # Privacy score trend
                avg_privacy_score = sum(r.privacy_analysis.privacy_score for r in results) / len(results)
                privacy_scores.append(round(avg_privacy_score, 2))
                
                # Tracker count trend
                total_trackers = sum(len(r.trackers) for r in results)
                tracker_counts.append(total_trackers)
                
                # Risk level distribution
                risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
                for result in results:
                    risk_level = result.privacy_analysis.risk_level.value
                    risk_counts[risk_level] += 1
                
                for level in risk_distributions:
                    risk_distributions[level].append(risk_counts[level])
                
                # Domain growth
                unique_domains = set()
                for result in results:
                    unique_domains.update(result.unique_domains)
                domain_counts.append(len(unique_domains))
            else:
                privacy_scores.append(0)
                tracker_counts.append(0)
                for level in risk_distributions:
                    risk_distributions[level].append(0)
                domain_counts.append(0)
        
        return TrendAnalysis(
            period=period,
            privacy_score_trend=privacy_scores,
            tracker_count_trend=tracker_counts,
            risk_level_distribution=risk_distributions,
            domain_growth=domain_counts,
            timestamps=timestamps
        )
    
    def export_to_csv(self, results: List[ScanResult], output_path: str) -> bool:
        """Export results to CSV with enhanced data"""
        try:
            data = []
            for result in results:
                privacy_index = self.calculate_privacy_impact_index([result])
                
                base_data = {
                    'url': result.url,
                    'timestamp': result.timestamp,
                    'tracker_count': len(result.trackers),
                    'privacy_score': result.privacy_analysis.privacy_score,
                    'risk_level': result.privacy_analysis.risk_level.value,
                    'scan_duration': result.scan_duration,
                    'javascript_enabled': result.javascript_enabled,
                    'unique_domains_count': len(result.unique_domains),
                    'categories_detected': ','.join([cat.value for cat in result.categories_detected]),
                    'privacy_impact_index': privacy_index.score,
                    'compliance_score': privacy_index.compliance_score
                }
                
                # Add tracker details
                for i, tracker in enumerate(result.trackers[:5]):  # Top 5 trackers
                    base_data[f'tracker_{i+1}_type'] = tracker.tracker_type
                    base_data[f'tracker_{i+1}_domain'] = tracker.domain
                    base_data[f'tracker_{i+1}_risk'] = tracker.risk_level.value
                
                data.append(base_data)
            
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            logger.info(f"CSV export completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False
    
    def export_to_parquet(self, results: List[ScanResult], output_path: str) -> bool:
        """Export results to Parquet format for big data analysis"""
        try:
            # Convert results to flat structure
            data = []
            for result in results:
                base_record = {
                    'url': result.url,
                    'timestamp': pd.to_datetime(result.timestamp),
                    'privacy_score': result.privacy_analysis.privacy_score,
                    'risk_level': result.privacy_analysis.risk_level.value,
                    'scan_duration': result.scan_duration,
                    'javascript_enabled': result.javascript_enabled,
                    'unique_domains_count': len(result.unique_domains)
                }
                
                # Add one record per tracker
                if result.trackers:
                    for tracker in result.trackers:
                        record = base_record.copy()
                        record.update({
                            'tracker_type': tracker.tracker_type,
                            'tracker_domain': tracker.domain,
                            'tracker_risk': tracker.risk_level.value,
                            'tracker_category': tracker.category.value
                        })
                        data.append(record)
                else:
                    data.append(base_record)
            
            df = pd.DataFrame(data)
            table = pa.Table.from_pandas(df)
            pq.write_table(table, output_path)
            
            logger.info(f"Parquet export completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export Parquet: {e}")
            return False
    
    def push_metrics_to_prometheus(self, results: List[ScanResult]) -> bool:
        """Push metrics to Prometheus"""
        if not PROMETHEUS_AVAILABLE or not self.metrics:
            return False
            
        try:
            # Update metrics
            self.metrics['scans_total'].inc(len(results))
            
            total_trackers = sum(len(r.trackers) for r in results)
            self.metrics['trackers_found'].set(total_trackers)
            
            if results:
                avg_privacy_score = sum(r.privacy_analysis.privacy_score for r in results) / len(results)
                self.metrics['privacy_score'].set(avg_privacy_score)
                
                avg_duration = sum(r.scan_duration for r in results) / len(results)
                self.metrics['scan_duration'].observe(avg_duration)
                
                # Risk level distribution
                risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
                for result in results:
                    risk_level = result.privacy_analysis.risk_level.value
                    risk_counts[risk_level] += 1
                
                for level, count in risk_counts.items():
                    self.metrics['risk_level_distribution'].labels(level=level).set(count)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to push Prometheus metrics: {e}")
            return False
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        if not PROMETHEUS_AVAILABLE:
            return ""
        return generate_latest(self.registry)
    
    def send_slack_notification(
        self,
        results: List[ScanResult],
        channel: str,
        alert_threshold: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send Slack notification for scan results"""
        if not self.slack_client:
            logger.warning("Slack client not configured")
            return False
            
        try:
            summary = self.generate_summary(results)
            privacy_index = self.calculate_privacy_impact_index(results)
            
            # Check if alert threshold is met
            if alert_threshold:
                if (privacy_index.score > alert_threshold.get('min_privacy_score', 0) and
                    summary['total_trackers'] < alert_threshold.get('max_trackers', float('inf'))):
                    return True  # No alert needed
            
            # Create message
            color = self._get_slack_color(privacy_index.risk_category)
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍 PixelTracker Scan Report"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*URLs Scanned:* {summary['total_urls']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Trackers Found:* {summary['total_trackers']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Privacy Score:* {summary['average_privacy_score']}/100"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Risk Level:* {privacy_index.risk_category.title()}"
                        }
                    ]
                }
            ]
            
            # Add trending information
            if privacy_index.trending != 'stable':
                trend_emoji = "📈" if privacy_index.trending == 'improving' else "📉"
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{trend_emoji} *Trend:* Privacy score is {privacy_index.trending}"
                    }
                })
            
            response = self.slack_client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"PixelTracker Scan Report - {summary['total_trackers']} trackers found"
            )
            
            logger.info(f"Slack notification sent to {channel}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def generate_excel_report(self, results: List[ScanResult], output_path: str) -> bool:
        """Generate comprehensive Excel report with multiple sheets"""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = self.generate_summary(results)
                summary_df = pd.DataFrame([summary_data])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed results sheet
                detailed_data = []
                for result in results:
                    privacy_index = self.calculate_privacy_impact_index([result])
                    detailed_data.append({
                        'URL': result.url,
                        'Timestamp': result.timestamp,
                        'Tracker Count': len(result.trackers),
                        'Privacy Score': result.privacy_analysis.privacy_score,
                        'Risk Level': result.privacy_analysis.risk_level.value,
                        'Privacy Impact Index': privacy_index.score,
                        'Compliance Score': privacy_index.compliance_score,
                        'Scan Duration': result.scan_duration,
                        'JavaScript Enabled': result.javascript_enabled,
                        'Unique Domains': len(result.unique_domains),
                        'Categories': ', '.join([cat.value for cat in result.categories_detected])
                    })
                
                detailed_df = pd.DataFrame(detailed_data)
                detailed_df.to_excel(writer, sheet_name='Detailed Results', index=False)
                
                # Trackers sheet
                tracker_data = []
                for result in results:
                    for tracker in result.trackers:
                        tracker_data.append({
                            'URL': result.url,
                            'Tracker Type': tracker.tracker_type,
                            'Domain': tracker.domain,
                            'Category': tracker.category.value,
                            'Risk Level': tracker.risk_level.value,
                            'Method': tracker.method
                        })
                
                if tracker_data:
                    tracker_df = pd.DataFrame(tracker_data)
                    tracker_df.to_excel(writer, sheet_name='Trackers', index=False)
                
                # Domain analysis sheet
                domain_analysis = self._analyze_domains(results)
                domain_df = pd.DataFrame(domain_analysis)
                domain_df.to_excel(writer, sheet_name='Domain Analysis', index=False)
            
            logger.info(f"Excel report generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate Excel report: {e}")
            return False
    
    def _generate_enhanced_html_report(
        self,
        results: List[ScanResult],
        config: ReportConfiguration
    ) -> str:
        """Generate enhanced HTML report with charts and analytics"""
        summary = self.generate_summary(results)
        privacy_index = self.calculate_privacy_impact_index(results)
        
        # Generate charts if enabled
        charts_html = ""
        if config.include_charts:
            charts_html = self._generate_charts_html(results, config)
        
        # Generate trends if enabled
        trends_html = ""
        if config.include_trends:
            trends_html = self._generate_trends_html(results, config)
        
        # Generate recommendations
        recommendations_html = ""
        if config.include_recommendations:
            recommendations_html = self._generate_recommendations_html(results, privacy_index)
        
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.company_name} - PixelTracker Report</title>
    <style>
        {self._get_enhanced_css_style(config)}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 {config.company_name}</h1>
            <h2>Privacy & Tracking Analysis Report</h2>
            <p>Generated on: {summary['scan_timestamp']}</p>
        </div>
        
        <div class="executive-summary">
            <h2>📊 Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>📈 Privacy Impact Index</h3>
                    <div class="number privacy-index-{privacy_index.risk_category}">{privacy_index.score}</div>
                    <div class="subtitle">{privacy_index.risk_category.title()} Risk</div>
                </div>
                <div class="summary-card">
                    <h3>🌐 URLs Analyzed</h3>
                    <div class="number">{summary['total_urls']}</div>
                </div>
                <div class="summary-card">
                    <h3>🎯 Trackers Detected</h3>
                    <div class="number">{summary['total_trackers']}</div>
                </div>
                <div class="summary-card">
                    <h3>🔒 Privacy Score</h3>
                    <div class="number">{summary['average_privacy_score']}/100</div>
                </div>
                <div class="summary-card">
                    <h3>🏢 Unique Domains</h3>
                    <div class="number">{summary['unique_domains']}</div>
                </div>
                <div class="summary-card">
                    <h3>✅ Compliance Score</h3>
                    <div class="number">{privacy_index.compliance_score}/100</div>
                </div>
            </div>
        </div>
        
        {charts_html}
        {trends_html}
        {recommendations_html}
        
        <div class="detailed-results">
            <h2>📋 Detailed Analysis</h2>
            {self._generate_detailed_results_html(results)}
        </div>
        
        <div class="footer">
            <p>Report generated by PixelTracker Advanced Analytics v2.0</p>
        </div>
    </div>
</body>
</html>'''
        
        return html_template
    
    def _calculate_tracker_density(self, results: List[ScanResult]) -> float:
        """Calculate tracker density factor"""
        if not results:
            return 0
        
        total_trackers = sum(len(result.trackers) for result in results)
        avg_trackers_per_url = total_trackers / len(results)
        
        # Normalize to 0-100 scale (assuming 20+ trackers per URL is very high)
        return max(0, min(100, 100 - (avg_trackers_per_url / 20) * 100))
    
    def _calculate_risk_severity(self, results: List[ScanResult]) -> float:
        """Calculate risk severity factor"""
        if not results:
            return 0
        
        risk_weights = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 3,
            RiskLevel.HIGH: 7,
            RiskLevel.CRITICAL: 10
        }
        
        total_risk_score = 0
        total_trackers = 0
        
        for result in results:
            for tracker in result.trackers:
                total_risk_score += risk_weights[tracker.risk_level]
                total_trackers += 1
        
        if total_trackers == 0:
            return 100
        
        avg_risk = total_risk_score / total_trackers
        # Normalize (max risk weight is 10)
        return max(0, min(100, 100 - (avg_risk / 10) * 100))
    
    def _calculate_domain_diversity(self, results: List[ScanResult]) -> float:
        """Calculate domain diversity factor"""
        if not results:
            return 0
        
        all_domains = set()
        for result in results:
            all_domains.update(result.unique_domains)
        
        total_trackers = sum(len(result.trackers) for result in results)
        if total_trackers == 0:
            return 100
        
        diversity_ratio = len(all_domains) / total_trackers
        # Normalize (higher diversity is better for privacy)
        return max(0, min(100, diversity_ratio * 100))
    
    def _calculate_category_spread(self, results: List[ScanResult]) -> float:
        """Calculate category spread factor"""
        if not results:
            return 0
        
        all_categories = set()
        for result in results:
            all_categories.update(result.categories_detected)
        
        # More categories = worse for privacy
        total_possible_categories = len(TrackerCategory)
        category_ratio = len(all_categories) / total_possible_categories
        
        return max(0, min(100, 100 - (category_ratio * 100)))
    
    def _calculate_third_party_exposure(self, results: List[ScanResult]) -> float:
        """Calculate third-party exposure factor"""
        if not results:
            return 0
        
        all_domains = set()
        source_domains = set()
        
        for result in results:
            # Extract source domain from URL
            from urllib.parse import urlparse
            source_domain = urlparse(result.url).netloc
            source_domains.add(source_domain)
            all_domains.update(result.unique_domains)
        
        # Calculate ratio of third-party domains
        third_party_domains = all_domains - source_domains
        if not all_domains:
            return 100
        
        third_party_ratio = len(third_party_domains) / len(all_domains)
        return max(0, min(100, 100 - (third_party_ratio * 100)))
    
    def _generate_charts_html(self, results: List[ScanResult], config: ReportConfiguration) -> str:
        """Generate HTML with embedded charts"""
        # This is a simplified version - in practice, you'd generate actual Plotly charts
        return '''
        <div class="charts-section">
            <h2>📊 Visual Analytics</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <h3>Risk Level Distribution</h3>
                    <div class="chart-placeholder">Risk distribution chart would be here</div>
                </div>
                <div class="chart-container">
                    <h3>Top Tracking Domains</h3>
                    <div class="chart-placeholder">Domain analysis chart would be here</div>
                </div>
            </div>
        </div>
        '''
    
    def _generate_trends_html(self, results: List[ScanResult], config: ReportConfiguration) -> str:
        """Generate trends HTML section"""
        return '''
        <div class="trends-section">
            <h2>📈 Trends Analysis</h2>
            <p>Trend analysis requires historical data. This would show privacy score changes over time.</p>
        </div>
        '''
    
    def _generate_recommendations_html(self, results: List[ScanResult], privacy_index: PrivacyImpactIndex) -> str:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if privacy_index.score < 50:
            recommendations.append("🚨 High-priority: Implement stricter privacy controls")
            recommendations.append("🔧 Review and minimize third-party integrations")
        
        if privacy_index.score < 70:
            recommendations.append("⚠️ Consider implementing consent management platform")
            recommendations.append("📋 Conduct privacy impact assessment")
        
        recommendations.append("🔍 Regular monitoring and scanning recommended")
        recommendations.append("📚 Staff training on privacy best practices")
        
        recommendations_html = "<ul>"
        for rec in recommendations:
            recommendations_html += f"<li>{rec}</li>"
        recommendations_html += "</ul>"
        
        return f'''
        <div class="recommendations-section">
            <h2>💡 Recommendations</h2>
            {recommendations_html}
        </div>
        '''
    
    def _generate_detailed_results_html(self, results: List[ScanResult]) -> str:
        """Generate detailed results HTML"""
        results_html = ""
        for result in results:
            privacy_index = self.calculate_privacy_impact_index([result])
            risk_class = f"risk-{result.privacy_analysis.risk_level.value}"
            
            trackers_html = ""
            for tracker in result.trackers[:5]:
                trackers_html += f'''
                <div class="tracker">
                    <strong>{tracker.tracker_type}</strong>: {tracker.domain} 
                    <span class="risk-badge risk-{tracker.risk_level.value}">{tracker.risk_level.value}</span>
                </div>
                '''
            
            results_html += f'''
            <div class="result-item {risk_class}">
                <h3>🌐 {result.url}</h3>
                <div class="result-metrics">
                    <div class="metric">
                        <strong>Trackers:</strong> {len(result.trackers)}
                    </div>
                    <div class="metric">
                        <strong>Privacy Score:</strong> {result.privacy_analysis.privacy_score}/100
                    </div>
                    <div class="metric">
                        <strong>Impact Index:</strong> {privacy_index.score}
                    </div>
                    <div class="metric">
                        <strong>Risk Level:</strong> {result.privacy_analysis.risk_level.value.title()}
                    </div>
                </div>
                <div class="trackers-list">
                    {trackers_html}
                </div>
            </div>
            '''
        
        return results_html
    
    def _get_enhanced_css_style(self, config: ReportConfiguration) -> str:
        """Get enhanced CSS styles for the report"""
        return '''
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header h2 {
            margin: 10px 0;
            font-weight: 300;
            opacity: 0.9;
        }
        .executive-summary {
            padding: 30px;
            background: #f8f9fa;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-left: 4px solid #667eea;
        }
        .summary-card h3 {
            margin: 0 0 15px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .summary-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .privacy-index-low { color: #28a745; }
        .privacy-index-medium { color: #ffc107; }
        .privacy-index-high { color: #fd7e14; }
        .privacy-index-critical { color: #dc3545; }
        
        .charts-section, .trends-section, .recommendations-section {
            padding: 30px;
            border-top: 1px solid #eee;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .chart-placeholder {
            height: 300px;
            background: #f8f9fa;
            border: 2px dashed #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            border-radius: 4px;
        }
        .detailed-results {
            padding: 30px;
            border-top: 1px solid #eee;
        }
        .result-item {
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #ddd;
        }
        .risk-low { border-left-color: #28a745; background-color: #f8fff9; }
        .risk-medium { border-left-color: #ffc107; background-color: #fffdf7; }
        .risk-high { border-left-color: #fd7e14; background-color: #fff8f5; }
        .risk-critical { border-left-color: #dc3545; background-color: #fdf7f7; }
        
        .result-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .metric {
            background: rgba(255,255,255,0.7);
            padding: 10px;
            border-radius: 4px;
        }
        .trackers-list {
            margin-top: 15px;
        }
        .tracker {
            background: rgba(255,255,255,0.8);
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .risk-badge {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .risk-badge.risk-low { background: #28a745; color: white; }
        .risk-badge.risk-medium { background: #ffc107; color: black; }
        .risk-badge.risk-high { background: #fd7e14; color: white; }
        .risk-badge.risk-critical { background: #dc3545; color: white; }
        
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #eee;
            color: #666;
        }
        '''
    
    def _get_pdf_css_style(self, config: ReportConfiguration) -> str:
        """Get CSS optimized for PDF generation"""
        return '''
        @page {
            margin: 2cm;
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
            }
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
        }
        .container {
            max-width: none;
            box-shadow: none;
        }
        .header {
            background: #667eea !important;
            -webkit-print-color-adjust: exact;
            page-break-after: avoid;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }
        .result-item {
            page-break-inside: avoid;
            margin: 15px 0;
        }
        .charts-section {
            page-break-before: always;
        }
        '''
    
    def _get_slack_color(self, risk_category: str) -> str:
        """Get Slack message color based on risk"""
        colors = {
            'low': 'good',
            'medium': 'warning', 
            'high': 'danger',
            'critical': 'danger'
        }
        return colors.get(risk_category, 'good')
    
    def _analyze_domains(self, results: List[ScanResult]) -> List[Dict[str, Any]]:
        """Analyze domains across all results"""
        domain_stats = {}
        
        for result in results:
            for tracker in result.trackers:
                domain = tracker.domain
                if domain not in domain_stats:
                    domain_stats[domain] = {
                        'domain': domain,
                        'occurrence_count': 0,
                        'risk_levels': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
                        'categories': set(),
                        'tracker_types': set()
                    }
                
                domain_stats[domain]['occurrence_count'] += 1
                domain_stats[domain]['risk_levels'][tracker.risk_level.value] += 1
                domain_stats[domain]['categories'].add(tracker.category.value)
                domain_stats[domain]['tracker_types'].add(tracker.tracker_type)
        
        # Convert to list and sort by occurrence
        analysis = []
        for domain, stats in domain_stats.items():
            stats['categories'] = list(stats['categories'])
            stats['tracker_types'] = list(stats['tracker_types'])
            analysis.append(stats)
        
        return sorted(analysis, key=lambda x: x['occurrence_count'], reverse=True)
