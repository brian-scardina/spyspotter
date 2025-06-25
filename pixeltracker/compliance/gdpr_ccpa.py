#!/usr/bin/env python3
"""
GDPR/CCPA Compliance Module

Provides compliance checking, data retention analysis, personally-identifiable
information detection, and consent mechanism analysis.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from enum import Enum

logger = logging.getLogger(__name__)


class ComplianceRegulation(str, Enum):
    """Compliance regulations"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    PIPEDA = "pipeda"
    LGPD = "lgpd"


class DataProcessingLawfulness(str, Enum):
    """GDPR Article 6 lawful bases"""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class PIICategory(str, Enum):
    """Categories of personally identifiable information"""
    EMAIL = "email"
    PHONE = "phone"
    IP_ADDRESS = "ip_address"
    USER_ID = "user_id"
    DEVICE_ID = "device_id"
    LOCATION = "location"
    BIOMETRIC = "biometric"
    FINANCIAL = "financial"
    HEALTH = "health"
    BEHAVIORAL = "behavioral"


@dataclass
class PIIDetection:
    """Detected personally identifiable information"""
    category: PIICategory
    pattern: str
    confidence: float
    location: str  # URL parameter, cookie, etc.
    value_hash: str  # Hashed value for tracking without storing PII
    regulation_relevant: List[ComplianceRegulation] = field(default_factory=list)


@dataclass
class ConsentMechanism:
    """Detected consent mechanism"""
    type: str  # banner, modal, checkbox, etc.
    explicit: bool  # True if explicit consent, False if implied
    granular: bool  # True if allows granular choices
    withdrawal_available: bool  # True if withdrawal mechanism found
    location: str  # CSS selector or description
    text_snippet: str  # Relevant text content


@dataclass
class DataRetentionPolicy:
    """Data retention policy information"""
    stated_period: Optional[str] = None
    category: Optional[str] = None  # analytics, marketing, etc.
    legal_basis: Optional[DataProcessingLawfulness] = None
    automated_deletion: bool = False
    user_control: bool = False


@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    url: str
    timestamp: str
    regulations_applicable: List[ComplianceRegulation]
    pii_detected: List[PIIDetection]
    consent_mechanisms: List[ConsentMechanism]
    data_retention_policies: List[DataRetentionPolicy]
    privacy_policy_found: bool
    cookie_policy_found: bool
    compliance_score: int  # 0-100
    violations: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'url': self.url,
            'timestamp': self.timestamp,
            'regulations_applicable': [r.value for r in self.regulations_applicable],
            'pii_detected': [
                {
                    'category': p.category.value,
                    'pattern': p.pattern,
                    'confidence': p.confidence,
                    'location': p.location,
                    'value_hash': p.value_hash,
                    'regulation_relevant': [r.value for r in p.regulation_relevant]
                }
                for p in self.pii_detected
            ],
            'consent_mechanisms': [
                {
                    'type': c.type,
                    'explicit': c.explicit,
                    'granular': c.granular,
                    'withdrawal_available': c.withdrawal_available,
                    'location': c.location,
                    'text_snippet': c.text_snippet
                }
                for c in self.consent_mechanisms
            ],
            'data_retention_policies': [
                {
                    'stated_period': p.stated_period,
                    'category': p.category,
                    'legal_basis': p.legal_basis.value if p.legal_basis else None,
                    'automated_deletion': p.automated_deletion,
                    'user_control': p.user_control
                }
                for p in self.data_retention_policies
            ],
            'privacy_policy_found': self.privacy_policy_found,
            'cookie_policy_found': self.cookie_policy_found,
            'compliance_score': self.compliance_score,
            'violations': self.violations,
            'recommendations': self.recommendations
        }


class PIIDetector:
    """Detects personally identifiable information in URLs and content"""
    
    def __init__(self):
        self.patterns = {
            PIICategory.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'email[=:]([^&\s]+)',
                r'user_email[=:]([^&\s]+)'
            ],
            PIICategory.PHONE: [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                r'\+\d{1,3}[-.\s]?\d{3,14}',
                r'phone[=:]([^&\s]+)'
            ],
            PIICategory.IP_ADDRESS: [
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                r'ip[=:]([^&\s]+)',
                r'user_ip[=:]([^&\s]+)'
            ],
            PIICategory.USER_ID: [
                r'user_id[=:]([^&\s]+)',
                r'uid[=:]([^&\s]+)',
                r'customer_id[=:]([^&\s]+)'
            ],
            PIICategory.DEVICE_ID: [
                r'device_id[=:]([^&\s]+)',
                r'device_fingerprint[=:]([^&\s]+)',
                r'browser_id[=:]([^&\s]+)'
            ],
            PIICategory.LOCATION: [
                r'lat[=:]([^&\s]+)',
                r'lon[=:]([^&\s]+)',
                r'location[=:]([^&\s]+)',
                r'gps[=:]([^&\s]+)'
            ]
        }
    
    def detect_in_url(self, url: str) -> List[PIIDetection]:
        """Detect PII in URL parameters"""
        detections = []
        
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # Check URL parameters
            for param, values in params.items():
                for value in values:
                    for category, patterns in self.patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, f"{param}={value}", re.IGNORECASE):
                                detections.append(PIIDetection(
                                    category=category,
                                    pattern=pattern,
                                    confidence=0.8,
                                    location=f"URL parameter: {param}",
                                    value_hash=hash(value),
                                    regulation_relevant=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA]
                                ))
            
            # Check URL path
            for category, patterns in self.patterns.items():
                for pattern in patterns:
                    if re.search(pattern, parsed.path, re.IGNORECASE):
                        detections.append(PIIDetection(
                            category=category,
                            pattern=pattern,
                            confidence=0.6,
                            location="URL path",
                            value_hash=hash(parsed.path),
                            regulation_relevant=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA]
                        ))
        
        except Exception as e:
            logger.error(f"Error detecting PII in URL {url}: {e}")
        
        return detections
    
    def detect_in_content(self, content: str, location: str = "page content") -> List[PIIDetection]:
        """Detect PII in page content"""
        detections = []
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    detections.append(PIIDetection(
                        category=category,
                        pattern=pattern,
                        confidence=0.7,
                        location=location,
                        value_hash=hash(match.group()),
                        regulation_relevant=[ComplianceRegulation.GDPR, ComplianceRegulation.CCPA]
                    ))
        
        return detections


class ConsentDetector:
    """Detects consent mechanisms and cookie banners"""
    
    def __init__(self):
        self.consent_indicators = [
            # Cookie banner indicators
            r'cookie.{0,20}consent',
            r'accept.{0,20}cookies',
            r'cookie.{0,20}policy',
            r'privacy.{0,20}settings',
            
            # GDPR consent indicators
            r'gdpr.{0,20}consent',
            r'data.{0,20}processing',
            r'legitimate.{0,20}interest',
            
            # Consent management platforms
            r'cookiebot',
            r'onetrust',
            r'cookiepro',
            r'trustarc',
            r'didomi'
        ]
        
        self.withdrawal_indicators = [
            r'withdraw.{0,20}consent',
            r'opt.{0,20}out',
            r'unsubscribe',
            r'manage.{0,20}preferences'
        ]
    
    def detect_consent_mechanisms(self, html_content: str) -> List[ConsentMechanism]:
        """Detect consent mechanisms in HTML content"""
        mechanisms = []
        
        # Look for cookie banners and consent managers
        for pattern in self.consent_indicators:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 100)
                end = min(len(html_content), match.end() + 100)
                context = html_content[start:end]
                
                # Determine if consent is explicit
                explicit = any(word in context.lower() for word in ['click', 'accept', 'agree', 'consent'])
                
                # Check for granular controls
                granular = any(word in context.lower() for word in ['settings', 'preferences', 'manage', 'customize'])
                
                # Check for withdrawal mechanism
                withdrawal = any(re.search(w, context, re.IGNORECASE) for w in self.withdrawal_indicators)
                
                mechanisms.append(ConsentMechanism(
                    type="cookie_banner",
                    explicit=explicit,
                    granular=granular,
                    withdrawal_available=withdrawal,
                    location="HTML content",
                    text_snippet=context.strip()[:200]
                ))
        
        return mechanisms


class DataRetentionAnalyzer:
    """Analyzes data retention policies and practices"""
    
    def __init__(self):
        self.retention_patterns = [
            r'retain.{0,30}(\d+).{0,10}(days?|months?|years?)',
            r'delete.{0,30}after.{0,10}(\d+).{0,10}(days?|months?|years?)',
            r'store.{0,30}for.{0,10}(\d+).{0,10}(days?|months?|years?)',
            r'keep.{0,30}(\d+).{0,10}(days?|months?|years?)'
        ]
        
        self.legal_basis_patterns = {
            DataProcessingLawfulness.CONSENT: [r'with.{0,10}your.{0,10}consent', r'based.{0,10}on.{0,10}consent'],
            DataProcessingLawfulness.CONTRACT: [r'contract', r'agreement', r'terms.{0,10}of.{0,10}service'],
            DataProcessingLawfulness.LEGAL_OBLIGATION: [r'legal.{0,10}obligation', r'compliance', r'regulatory'],
            DataProcessingLawfulness.LEGITIMATE_INTERESTS: [r'legitimate.{0,10}interest']
        }
    
    def analyze_retention_policies(self, content: str) -> List[DataRetentionPolicy]:
        """Analyze data retention policies in content"""
        policies = []
        
        for pattern in self.retention_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extract retention period
                period_text = match.group()
                
                # Determine legal basis
                legal_basis = None
                context = content[max(0, match.start()-200):min(len(content), match.end()+200)]
                
                for basis, basis_patterns in self.legal_basis_patterns.items():
                    if any(re.search(p, context, re.IGNORECASE) for p in basis_patterns):
                        legal_basis = basis
                        break
                
                policies.append(DataRetentionPolicy(
                    stated_period=period_text,
                    legal_basis=legal_basis,
                    automated_deletion='automatically' in context.lower(),
                    user_control=any(word in context.lower() for word in ['delete', 'remove', 'control'])
                ))
        
        return policies


class ComplianceChecker:
    """Main compliance checker that orchestrates all compliance analysis"""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.consent_detector = ConsentDetector()
        self.retention_analyzer = DataRetentionAnalyzer()
    
    def check_compliance(
        self,
        url: str,
        html_content: str,
        tracking_data: Dict[str, Any]
    ) -> ComplianceReport:
        """Perform comprehensive compliance check"""
        
        # Detect PII
        pii_detections = []
        pii_detections.extend(self.pii_detector.detect_in_url(url))
        pii_detections.extend(self.pii_detector.detect_in_content(html_content))
        
        # Detect consent mechanisms
        consent_mechanisms = self.consent_detector.detect_consent_mechanisms(html_content)
        
        # Analyze data retention
        retention_policies = self.retention_analyzer.analyze_retention_policies(html_content)
        
        # Check for privacy and cookie policies
        privacy_policy_found = self._check_privacy_policy(html_content)
        cookie_policy_found = self._check_cookie_policy(html_content)
        
        # Determine applicable regulations
        regulations = self._determine_applicable_regulations(url, tracking_data)
        
        # Calculate compliance score and identify violations
        score, violations, recommendations = self._assess_compliance(
            pii_detections,
            consent_mechanisms,
            retention_policies,
            privacy_policy_found,
            cookie_policy_found,
            regulations
        )
        
        return ComplianceReport(
            url=url,
            timestamp=datetime.now().isoformat(),
            regulations_applicable=regulations,
            pii_detected=pii_detections,
            consent_mechanisms=consent_mechanisms,
            data_retention_policies=retention_policies,
            privacy_policy_found=privacy_policy_found,
            cookie_policy_found=cookie_policy_found,
            compliance_score=score,
            violations=violations,
            recommendations=recommendations
        )
    
    def _check_privacy_policy(self, content: str) -> bool:
        """Check if privacy policy is referenced"""
        patterns = [
            r'privacy.{0,20}policy',
            r'data.{0,20}protection',
            r'personal.{0,20}information'
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in patterns)
    
    def _check_cookie_policy(self, content: str) -> bool:
        """Check if cookie policy is referenced"""
        patterns = [
            r'cookie.{0,20}policy',
            r'cookie.{0,20}notice',
            r'cookie.{0,20}information'
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in patterns)
    
    def _determine_applicable_regulations(
        self,
        url: str,
        tracking_data: Dict[str, Any]
    ) -> List[ComplianceRegulation]:
        """Determine which regulations apply"""
        regulations = []
        
        # Always include GDPR for EU-facing sites
        regulations.append(ComplianceRegulation.GDPR)
        
        # Add CCPA for California-facing sites
        regulations.append(ComplianceRegulation.CCPA)
        
        # Could add geo-detection logic here
        
        return regulations
    
    def _assess_compliance(
        self,
        pii_detections: List[PIIDetection],
        consent_mechanisms: List[ConsentMechanism],
        retention_policies: List[DataRetentionPolicy],
        privacy_policy_found: bool,
        cookie_policy_found: bool,
        regulations: List[ComplianceRegulation]
    ) -> Tuple[int, List[str], List[str]]:
        """Assess compliance and generate score, violations, and recommendations"""
        
        score = 100
        violations = []
        recommendations = []
        
        # Check for PII without proper consent
        if pii_detections and not consent_mechanisms:
            score -= 30
            violations.append("PII detected without visible consent mechanism")
            recommendations.append("Implement cookie consent banner with clear opt-in")
        
        # Check for explicit consent
        if consent_mechanisms:
            explicit_consent = any(c.explicit for c in consent_mechanisms)
            if not explicit_consent:
                score -= 20
                violations.append("Consent mechanism appears to use implied consent")
                recommendations.append("Implement explicit consent requirements")
        
        # Check for granular consent
        if consent_mechanisms:
            granular_consent = any(c.granular for c in consent_mechanisms)
            if not granular_consent:
                score -= 15
                violations.append("No granular consent options detected")
                recommendations.append("Provide granular consent choices for different data uses")
        
        # Check for withdrawal mechanism
        if consent_mechanisms:
            withdrawal_available = any(c.withdrawal_available for c in consent_mechanisms)
            if not withdrawal_available:
                score -= 15
                violations.append("No consent withdrawal mechanism detected")
                recommendations.append("Provide clear way to withdraw consent")
        
        # Check for privacy policy
        if not privacy_policy_found:
            score -= 10
            violations.append("No privacy policy reference found")
            recommendations.append("Add link to privacy policy")
        
        # Check for data retention policies
        if not retention_policies:
            score -= 10
            violations.append("No data retention policies detected")
            recommendations.append("Clearly state data retention periods")
        
        return max(0, score), violations, recommendations


# CLI integration functions
def add_compliance_args(parser):
    """Add compliance checking arguments to CLI parser"""
    compliance_group = parser.add_argument_group('compliance')
    compliance_group.add_argument(
        '--compliance-check',
        action='store_true',
        help='Perform GDPR/CCPA compliance analysis'
    )
    compliance_group.add_argument(
        '--compliance-regulations',
        nargs='+',
        choices=['gdpr', 'ccpa', 'pipeda', 'lgpd'],
        default=['gdpr', 'ccpa'],
        help='Regulations to check compliance against'
    )
    compliance_group.add_argument(
        '--compliance-report',
        help='Output file for compliance report'
    )


def generate_compliance_report(
    url: str,
    html_content: str,
    tracking_data: Dict[str, Any],
    output_file: Optional[str] = None
) -> ComplianceReport:
    """Generate compliance report for a URL"""
    
    checker = ComplianceChecker()
    report = checker.check_compliance(url, html_content, tracking_data)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Compliance report saved to {output_file}")
    
    return report
