#!/usr/bin/env python3
"""
Comprehensive Tracker Database
Contains extensive patterns and intelligence for tracking detection
"""

import re
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class TrackerPattern:
    """Represents a tracker pattern with metadata"""
    name: str
    category: str
    risk_level: str  # low, medium, high, critical
    patterns: List[str]
    domains: List[str]
    description: str
    data_types: List[str]  # What type of data it collects
    gdpr_relevant: bool
    ccpa_relevant: bool
    detection_method: str  # javascript, pixel, meta, css, network
    evasion_techniques: List[str]
    first_seen: str
    last_updated: str

class TrackerDatabase:
    """Comprehensive database of tracking patterns and intelligence"""

    def __init__(self):
        self.trackers = {}
        self.patterns_compiled = {}
        self.load_tracker_database()
        self.compile_patterns()

    def load_tracker_database(self, db_path: str = "tracker_database.json"):
        """Load comprehensive tracker database from a JSON file"""
        try:
            with open(db_path, 'r') as f:
                tracker_data = json.load(f)

            for tracker_id, data in tracker_data.items():
                self.trackers[tracker_id] = TrackerPattern(**data)

        except FileNotFoundError:
            print(f"Warning: Tracker database file not found at {db_path}. Using empty database.")
        except json.JSONDecodeError:
            print(f"Warning: Could not decode tracker database file at {db_path}. Using empty database.")
        except Exception as e:
            print(f"Warning: An unexpected error occurred while loading the tracker database: {e}")

    def compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        for tracker_id, tracker in self.trackers.items():
            self.patterns_compiled[tracker_id] = [
                re.compile(pattern, re.IGNORECASE) for pattern in tracker.patterns
            ]

    def detect_trackers(self, content: str, url: str = "") -> List[Dict[str, Any]]:
        """Detect trackers in content using comprehensive pattern matching"""
        detected = []

        for tracker_id, tracker in self.trackers.items():
            matches = []

            # Check compiled patterns
            for i, pattern in enumerate(self.patterns_compiled[tracker_id]):
                if pattern.search(content):
                    matches.append({
                        'pattern': tracker.patterns[i],
                        'type': 'regex_match'
                    })

            # Check domain presence in URL or content
            for domain in tracker.domains:
                if domain in content or domain in url:
                    matches.append({
                        'pattern': domain,
                        'type': 'domain_match'
                    })

            if matches:
                detected.append({
                    'tracker_id': tracker_id,
                    'name': tracker.name,
                    'category': tracker.category,
                    'risk_level': tracker.risk_level,
                    'description': tracker.description,
                    'matches': matches,
                    'data_types': tracker.data_types,
                    'gdpr_relevant': tracker.gdpr_relevant,
                    'ccpa_relevant': tracker.ccpa_relevant,
                    'evasion_techniques': tracker.evasion_techniques
                })

        return detected

    def get_tracker_by_domain(self, domain: str) -> Optional[TrackerPattern]:
        """Get tracker information by domain"""
        for tracker in self.trackers.values():
            if domain in tracker.domains:
                return tracker
        return None

    def get_trackers_by_category(self, category: str) -> List[TrackerPattern]:
        """Get all trackers in a specific category"""
        return [tracker for tracker in self.trackers.values() if tracker.category == category]

    def get_high_risk_trackers(self) -> List[TrackerPattern]:
        """Get all high-risk and critical trackers"""
        return [tracker for tracker in self.trackers.values() if tracker.risk_level in ['high', 'critical']]

    def export_database(self, format: str = 'json') -> str:
        """Export tracker database in specified format"""
        if format == 'json':
            return json.dumps({
                tracker_id: asdict(tracker) for tracker_id, tracker in self.trackers.items()
            }, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        categories = {}
        risk_levels = {}
        detection_methods = {}

        for tracker in self.trackers.values():
            categories[tracker.category] = categories.get(tracker.category, 0) + 1
            risk_levels[tracker.risk_level] = risk_levels.get(tracker.risk_level, 0) + 1
            detection_methods[tracker.detection_method] = detection_methods.get(tracker.detection_method, 0) + 1

        total_domains = sum(len(tracker.domains) for tracker in self.trackers.values())
        total_patterns = sum(len(tracker.patterns) for tracker in self.trackers.values())

        return {
            'total_trackers': len(self.trackers),
            'total_domains': total_domains,
            'total_patterns': total_patterns,
            'categories': categories,
            'risk_levels': risk_levels,
            'detection_methods': detection_methods,
            'gdpr_relevant_count': sum(1 for t in self.trackers.values() if t.gdpr_relevant),
            'ccpa_relevant_count': sum(1 for t in self.trackers.values() if t.ccpa_relevant)
        }

# Global instance
tracker_db = TrackerDatabase()
