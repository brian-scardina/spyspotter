#!/usr/bin/env python3
"""
Export utility for the comprehensive tracker database
"""

import json
import argparse
from tracker_database import tracker_db

def export_database(format_type='json', output_file=None):
    """Export the tracker database in specified format"""
    
    if format_type == 'json':
        data = tracker_db.export_database('json')
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(data)
            print(f"✅ Database exported to {output_file}")
        else:
            print(data)
    
    elif format_type == 'summary':
        # Export a human-readable summary
        stats = tracker_db.get_statistics()
        
        summary = f"""
🗄️  PixelTracker Database Summary
================================

📊 Statistics:
   Total Trackers: {stats['total_trackers']}
   Total Domains: {stats['total_domains']}
   Total Patterns: {stats['total_patterns']}
   GDPR Relevant: {stats['gdpr_relevant_count']}
   CCPA Relevant: {stats['ccpa_relevant_count']}

📂 Categories:
"""
        
        for category, count in stats['categories'].items():
            summary += f"   {category.replace('_', ' ').title()}: {count}\n"
        
        summary += f"\n⚠️  Risk Levels:\n"
        for risk, count in stats['risk_levels'].items():
            summary += f"   {risk.title()}: {count}\n"
        
        summary += f"\n🎯 High-Risk Trackers:\n"
        high_risk = tracker_db.get_high_risk_trackers()
        for tracker in high_risk:
            summary += f"   {tracker.name} ({tracker.category}) - {tracker.risk_level} risk\n"
        
        summary += f"\n🔍 Detection Methods:\n"
        for method, count in stats['detection_methods'].items():
            summary += f"   {method.replace('_', ' ').title()}: {count}\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(summary)
            print(f"✅ Summary exported to {output_file}")
        else:
            print(summary)
    
    elif format_type == 'csv':
        # Export as CSV for spreadsheet analysis
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Tracker ID', 'Name', 'Category', 'Risk Level', 'Description',
            'Domains', 'Pattern Count', 'GDPR Relevant', 'CCPA Relevant',
            'Data Types', 'Evasion Techniques', 'First Seen'
        ])
        
        # Data rows
        for tracker_id, tracker in tracker_db.trackers.items():
            writer.writerow([
                tracker_id,
                tracker.name,
                tracker.category,
                tracker.risk_level,
                tracker.description,
                ';'.join(tracker.domains),
                len(tracker.patterns),
                tracker.gdpr_relevant,
                tracker.ccpa_relevant,
                ';'.join(tracker.data_types),
                ';'.join(tracker.evasion_techniques),
                tracker.first_seen
            ])
        
        csv_data = output.getvalue()
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(csv_data)
            print(f"✅ CSV exported to {output_file}")
        else:
            print(csv_data)

def main():
    parser = argparse.ArgumentParser(description='Export PixelTracker Database')
    parser.add_argument('--format', choices=['json', 'summary', 'csv'], default='summary',
                       help='Export format (default: summary)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    export_database(args.format, args.output)

if __name__ == "__main__":
    main()
