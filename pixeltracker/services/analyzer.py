#!/usr/bin/env python3
"""
Analyzer service for PixelTracker

Provides analysis of scan results, calculates privacy scores,
and assesses risks.
"""

from typing import List, Dict, Any
from ..interfaces import Analyzer
from ..models import TrackerInfo, PrivacyAnalysis, RiskLevel
import logging

logger = logging.getLogger(__name__)


class AnalyzerService(Analyzer):
    """Analyzer service for privacy impact assessment"""
    
    def analyze_privacy_impact(
        self, 
        trackers: List[TrackerInfo], 
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze the privacy impact of detected trackers"""
        high_risk_domains = [t.domain for t in trackers if t.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        detected_categories = list(set(t.category for t in trackers))
        
        # Generate recommendations
        recommendations = []
        if high_risk_domains:
            recommendations.append("Consider using privacy-focused tools and reviewing browser settings.")
        
        return {
            'privacy_score': self.calculate_privacy_score(trackers),
            'risk_level': self.assess_risks(trackers, kwargs.get('url', ''))['overall_risk'],
            'detected_categories': detected_categories,
            'high_risk_domains': high_risk_domains,
            'recommendations': recommendations
        }


    def calculate_privacy_score(
        self, 
        trackers: List[TrackerInfo], 
        **kwargs
    ) -> int:
        """Calculate a privacy score based on detected trackers"""
        base_score = 100
        
        for tracker in trackers:
            if tracker.risk_level == RiskLevel.HIGH:
                base_score -= 15
            elif tracker.risk_level == RiskLevel.MEDIUM:
                base_score -= 10
            elif tracker.risk_level == RiskLevel.LOW:
                base_score -= 5
        
        return max(base_score, 0)


    def assess_risks(
        self, 
        trackers: List[TrackerInfo], 
        url: str
    ) -> Dict[str, Any]:
        """Determine the overall risk level based on trackers"""
        high_risk_count = sum(1 for t in trackers if t.risk_level == RiskLevel.HIGH)
        medium_risk_count = sum(1 for t in trackers if t.risk_level == RiskLevel.MEDIUM)
        
        risk_level = RiskLevel.LOW
        
        if high_risk_count >= 2:
            risk_level = RiskLevel.HIGH
        elif medium_risk_count >= 3:
            risk_level = RiskLevel.MEDIUM
        
        return {
            'overall_risk': risk_level,
            'high_risk_trackers': high_risk_count,
            'medium_risk_trackers': medium_risk_count
        }

