#!/usr/bin/env python3
"""
Reporter service for PixelTracker

Generates reports in various formats (HTML, JSON, CSV, etc.)
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from ..interfaces import Reporter
from ..models import ScanResult
import logging

logger = logging.getLogger(__name__)


class ReporterService(Reporter):
    """Reporter service for generating various output formats"""
    
    def generate_report(
        self, 
        results: List[ScanResult], 
        format: str = "json"
    ) -> str:
        """Generate report in specified format"""
        if format.lower() == "json":
            return self._generate_json_report(results)
        elif format.lower() == "html":
            return self._generate_html_report(results)
        elif format.lower() == "csv":
            return self._generate_csv_report(results)
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    def generate_summary(self, results: List[ScanResult]) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not results:
            return {
                'total_urls': 0,
                'total_trackers': 0,
                'average_privacy_score': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        total_trackers = sum(len(result.trackers) for result in results)
        privacy_scores = [result.privacy_analysis.privacy_score for result in results]
        avg_privacy_score = sum(privacy_scores) / len(privacy_scores)
        
        # Collect all unique domains
        all_domains = set()
        for result in results:
            all_domains.update(result.unique_domains)
        
        # Risk level distribution
        risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for result in results:
            risk_level = result.privacy_analysis.risk_level.value
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        return {
            'total_urls': len(results),
            'total_trackers': total_trackers,
            'unique_domains': len(all_domains),
            'average_privacy_score': round(avg_privacy_score, 2),
            'risk_distribution': risk_distribution,
            'scan_timestamp': datetime.now().isoformat(),
            'top_domains': list(all_domains)[:10]
        }
    
    def export_data(
        self, 
        results: List[ScanResult], 
        format: str,
        output_path: str
    ) -> bool:
        """Export data to file"""
        try:
            report_content = self.generate_report(results, format)
            
            with open(output_path, 'w') as f:
                f.write(report_content)
            
            logger.info(f"Report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False
    
    def _generate_json_report(self, results: List[ScanResult]) -> str:
        """Generate JSON format report"""
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_results': len(results),
                'report_version': '2.0'
            },
            'summary': self.generate_summary(results),
            'results': [result.to_dict() for result in results]
        }
        
        return json.dumps(report_data, indent=2, default=str)
    
    def _generate_html_report(self, results: List[ScanResult]) -> str:
        """Generate HTML format report"""
        summary = self.generate_summary(results)
        
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PixelTracker Report</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }}
        .header {{ 
            text-align: center; 
            border-bottom: 2px solid #333; 
            padding-bottom: 20px; 
            margin-bottom: 30px; 
        }}
        .summary {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-bottom: 30px; 
        }}
        .summary-card {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 6px; 
            text-align: center; 
        }}
        .summary-card h3 {{ 
            margin: 0 0 10px 0; 
            color: #333; 
        }}
        .summary-card .number {{ 
            font-size: 24px; 
            font-weight: bold; 
            color: #007bff; 
        }}
        .result-item {{ 
            margin: 20px 0; 
            padding: 15px; 
            border: 1px solid #ddd; 
            border-radius: 6px; 
        }}
        .risk-low {{ background-color: #d4edda; }}
        .risk-medium {{ background-color: #fff3cd; }}
        .risk-high {{ background-color: #f8d7da; }}
        .risk-critical {{ background-color: #f5c6cb; }}
        .trackers-list {{ 
            margin-top: 10px; 
        }}
        .tracker {{ 
            background: #f8f9fa; 
            padding: 5px 10px; 
            margin: 5px 0; 
            border-radius: 3px; 
            font-size: 12px; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 PixelTracker Report</h1>
            <p>Generated on: {timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>📊 Total URLs</h3>
                <div class="number">{total_urls}</div>
            </div>
            <div class="summary-card">
                <h3>🎯 Total Trackers</h3>
                <div class="number">{total_trackers}</div>
            </div>
            <div class="summary-card">
                <h3>🌐 Unique Domains</h3>
                <div class="number">{unique_domains}</div>
            </div>
            <div class="summary-card">
                <h3>🔒 Avg Privacy Score</h3>
                <div class="number">{avg_privacy_score}</div>
            </div>
        </div>
        
        <h2>📋 Scan Results</h2>
        {results_content}
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
            <p>Report generated by PixelTracker v2.0</p>
        </div>
    </div>
</body>
</html>'''
        
        # Generate results content
        results_content = ""
        for result in results:
            risk_class = f"risk-{result.privacy_analysis.risk_level.value}"
            
            trackers_html = ""
            for tracker in result.trackers[:5]:  # Show first 5 trackers
                trackers_html += f'<div class="tracker">{tracker.tracker_type}: {tracker.domain} ({tracker.risk_level.value})</div>'
            
            if len(result.trackers) > 5:
                trackers_html += f'<div class="tracker">... and {len(result.trackers) - 5} more</div>'
            
            results_content += f'''
            <div class="result-item {risk_class}">
                <h3>🌐 {result.url}</h3>
                <p><strong>Trackers Found:</strong> {len(result.trackers)}</p>
                <p><strong>Privacy Score:</strong> {result.privacy_analysis.privacy_score}/100</p>
                <p><strong>Risk Level:</strong> {result.privacy_analysis.risk_level.value.title()}</p>
                <p><strong>Scan Duration:</strong> {result.scan_duration:.2f}s</p>
                <div class="trackers-list">
                    {trackers_html}
                </div>
            </div>
            '''
        
        return html_template.format(
            timestamp=summary['scan_timestamp'],
            total_urls=summary['total_urls'],
            total_trackers=summary['total_trackers'],
            unique_domains=summary['unique_domains'],
            avg_privacy_score=summary['average_privacy_score'],
            results_content=results_content
        )
    
    def _generate_csv_report(self, results: List[ScanResult]) -> str:
        """Generate CSV format report"""
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'URL', 'Timestamp', 'Tracker Count', 'Privacy Score', 
            'Risk Level', 'Scan Duration', 'JavaScript Enabled',
            'Top Domains', 'Categories'
        ])
        
        # Write data rows
        for result in results:
            top_domains = ', '.join(result.unique_domains[:3])
            categories = ', '.join([cat.value for cat in result.categories_detected])
            
            writer.writerow([
                result.url,
                result.timestamp,
                result.tracker_count,
                result.privacy_analysis.privacy_score,
                result.privacy_analysis.risk_level.value,
                round(result.scan_duration, 2),
                result.javascript_enabled,
                top_domains,
                categories
            ])
        
        return output.getvalue()
