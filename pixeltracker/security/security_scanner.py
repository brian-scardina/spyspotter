#!/usr/bin/env python3
"""
Security Scanner Module

Provides security assessment functionality including HTTPS usage analysis,
Content Security Policy (CSP) header inspection, and insecure request detection.
"""

import re
import ssl
import socket
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta

try:
    import requests
    import ssl
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    SECURITY_DEPS_AVAILABLE = True
except ImportError:
    SECURITY_DEPS_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecurityLevel(str):
    """Security level enumeration"""
    SECURE = "secure"
    WARNING = "warning"
    VULNERABLE = "vulnerable"
    CRITICAL = "critical"


@dataclass
class SSLCertificateInfo:
    """SSL certificate information"""
    subject: str
    issuer: str
    valid_from: str
    valid_to: str
    is_valid: bool
    is_expired: bool
    days_until_expiry: int
    signature_algorithm: str
    key_size: Optional[int] = None
    san_domains: List[str] = field(default_factory=list)


@dataclass
class CSPDirective:
    """Content Security Policy directive"""
    name: str
    values: List[str]
    allows_unsafe_inline: bool = False
    allows_unsafe_eval: bool = False
    allows_data_urls: bool = False
    security_level: SecurityLevel = SecurityLevel.SECURE


@dataclass
class CSPAnalysis:
    """Content Security Policy analysis results"""
    present: bool
    directives: List[CSPDirective]
    security_score: int  # 0-100
    violations: List[str]
    recommendations: List[str]
    report_only: bool = False


@dataclass
class MixedContentIssue:
    """Mixed content security issue"""
    resource_url: str
    resource_type: str  # script, stylesheet, image, etc.
    severity: SecurityLevel
    context: str  # Where it was found


@dataclass
class SecurityHeader:
    """Security header analysis"""
    name: str
    value: Optional[str]
    present: bool
    security_level: SecurityLevel
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SecurityScanResult:
    """Complete security scan result"""
    url: str
    timestamp: str
    https_enabled: bool
    ssl_certificate: Optional[SSLCertificateInfo]
    csp_analysis: CSPAnalysis
    security_headers: List[SecurityHeader]
    mixed_content_issues: List[MixedContentIssue]
    insecure_requests: List[str]
    overall_security_score: int
    security_level: SecurityLevel
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'url': self.url,
            'timestamp': self.timestamp,
            'https_enabled': self.https_enabled,
            'ssl_certificate': {
                'subject': self.ssl_certificate.subject,
                'issuer': self.ssl_certificate.issuer,
                'valid_from': self.ssl_certificate.valid_from,
                'valid_to': self.ssl_certificate.valid_to,
                'is_valid': self.ssl_certificate.is_valid,
                'is_expired': self.ssl_certificate.is_expired,
                'days_until_expiry': self.ssl_certificate.days_until_expiry,
                'signature_algorithm': self.ssl_certificate.signature_algorithm,
                'key_size': self.ssl_certificate.key_size,
                'san_domains': self.ssl_certificate.san_domains
            } if self.ssl_certificate else None,
            'csp_analysis': {
                'present': self.csp_analysis.present,
                'directives': [
                    {
                        'name': d.name,
                        'values': d.values,
                        'allows_unsafe_inline': d.allows_unsafe_inline,
                        'allows_unsafe_eval': d.allows_unsafe_eval,
                        'allows_data_urls': d.allows_data_urls,
                        'security_level': d.security_level
                    }
                    for d in self.csp_analysis.directives
                ],
                'security_score': self.csp_analysis.security_score,
                'violations': self.csp_analysis.violations,
                'recommendations': self.csp_analysis.recommendations,
                'report_only': self.csp_analysis.report_only
            },
            'security_headers': [
                {
                    'name': h.name,
                    'value': h.value,
                    'present': h.present,
                    'security_level': h.security_level,
                    'recommendations': h.recommendations
                }
                for h in self.security_headers
            ],
            'mixed_content_issues': [
                {
                    'resource_url': m.resource_url,
                    'resource_type': m.resource_type,
                    'severity': m.severity,
                    'context': m.context
                }
                for m in self.mixed_content_issues
            ],
            'insecure_requests': self.insecure_requests,
            'overall_security_score': self.overall_security_score,
            'security_level': self.security_level,
            'recommendations': self.recommendations
        }


class SSLAnalyzer:
    """Analyzes SSL certificates and configurations"""
    
    def analyze_ssl_certificate(self, hostname: str, port: int = 443) -> Optional[SSLCertificateInfo]:
        """Analyze SSL certificate for a hostname"""
        if not SECURITY_DEPS_AVAILABLE:
            logger.warning("Security dependencies not available for SSL analysis")
            return None
        
        try:
            # Get certificate
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert = x509.load_der_x509_certificate(cert_der, default_backend())
            
            # Extract certificate information
            subject = cert.subject.rfc4514_string()
            issuer = cert.issuer.rfc4514_string()
            
            valid_from = cert.not_valid_before.isoformat()
            valid_to = cert.not_valid_after.isoformat()
            
            now = datetime.now()
            is_valid = cert.not_valid_before <= now <= cert.not_valid_after
            is_expired = now > cert.not_valid_after
            days_until_expiry = (cert.not_valid_after - now).days
            
            # Get signature algorithm
            signature_algorithm = cert.signature_algorithm_oid._name
            
            # Get key size
            key_size = None
            try:
                public_key = cert.public_key()
                if hasattr(public_key, 'key_size'):
                    key_size = public_key.key_size
            except:
                pass
            
            # Get SAN domains
            san_domains = []
            try:
                san_extension = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                san_domains = [name.value for name in san_extension.value]
            except:
                pass
            
            return SSLCertificateInfo(
                subject=subject,
                issuer=issuer,
                valid_from=valid_from,
                valid_to=valid_to,
                is_valid=is_valid,
                is_expired=is_expired,
                days_until_expiry=days_until_expiry,
                signature_algorithm=signature_algorithm,
                key_size=key_size,
                san_domains=san_domains
            )
            
        except Exception as e:
            logger.error(f"SSL certificate analysis failed for {hostname}: {e}")
            return None


class CSPAnalyzer:
    """Analyzes Content Security Policy headers"""
    
    def __init__(self):
        self.critical_directives = [
            'default-src', 'script-src', 'object-src', 'base-uri'
        ]
        
        self.unsafe_keywords = [
            "'unsafe-inline'", "'unsafe-eval'", "'unsafe-hashes'"
        ]
    
    def analyze_csp(self, csp_header: Optional[str], report_only: bool = False) -> CSPAnalysis:
        """Analyze Content Security Policy header"""
        if not csp_header:
            return CSPAnalysis(
                present=False,
                directives=[],
                security_score=0,
                violations=["No Content Security Policy found"],
                recommendations=[
                    "Implement Content Security Policy to prevent XSS attacks",
                    "Start with CSP in report-only mode for testing"
                ],
                report_only=False
            )
        
        # Parse CSP directives
        directives = []
        violations = []
        recommendations = []
        
        # Split by semicolon and parse each directive
        directive_parts = [d.strip() for d in csp_header.split(';') if d.strip()]
        
        for directive_part in directive_parts:
            parts = directive_part.split()
            if not parts:
                continue
                
            directive_name = parts[0]
            directive_values = parts[1:] if len(parts) > 1 else []
            
            # Analyze directive security
            allows_unsafe_inline = "'unsafe-inline'" in directive_values
            allows_unsafe_eval = "'unsafe-eval'" in directive_values
            allows_data_urls = "data:" in directive_values
            
            # Determine security level
            security_level = SecurityLevel.SECURE
            if allows_unsafe_inline or allows_unsafe_eval:
                security_level = SecurityLevel.VULNERABLE
            elif allows_data_urls:
                security_level = SecurityLevel.WARNING
            
            directives.append(CSPDirective(
                name=directive_name,
                values=directive_values,
                allows_unsafe_inline=allows_unsafe_inline,
                allows_unsafe_eval=allows_unsafe_eval,
                allows_data_urls=allows_data_urls,
                security_level=security_level
            ))
            
            # Check for violations
            if allows_unsafe_inline:
                violations.append(f"{directive_name} allows 'unsafe-inline'")
                recommendations.append(f"Remove 'unsafe-inline' from {directive_name} and use nonces or hashes")
            
            if allows_unsafe_eval:
                violations.append(f"{directive_name} allows 'unsafe-eval'")
                recommendations.append(f"Remove 'unsafe-eval' from {directive_name}")
        
        # Check for missing critical directives
        directive_names = [d.name for d in directives]
        for critical in self.critical_directives:
            if critical not in directive_names:
                violations.append(f"Missing critical directive: {critical}")
                recommendations.append(f"Add {critical} directive to CSP")
        
        # Calculate security score
        security_score = 100
        for violation in violations:
            if "unsafe-eval" in violation:
                security_score -= 25
            elif "unsafe-inline" in violation:
                security_score -= 15
            elif "Missing critical directive" in violation:
                security_score -= 10
            else:
                security_score -= 5
        
        security_score = max(0, security_score)
        
        return CSPAnalysis(
            present=True,
            directives=directives,
            security_score=security_score,
            violations=violations,
            recommendations=recommendations,
            report_only=report_only
        )


class MixedContentDetector:
    """Detects mixed content issues"""
    
    def __init__(self):
        self.resource_patterns = {
            'script': r'<script[^>]+src=["\']?http://[^"\'>\s]+',
            'stylesheet': r'<link[^>]+href=["\']?http://[^"\'>\s]+',
            'image': r'<img[^>]+src=["\']?http://[^"\'>\s]+',
            'iframe': r'<iframe[^>]+src=["\']?http://[^"\'>\s]+',
            'form': r'<form[^>]+action=["\']?http://[^"\'>\s]+',
            'ajax': r'ajax\([^)]*["\']http://[^"\']+',
            'fetch': r'fetch\([^)]*["\']http://[^"\']+',
        }
    
    def detect_mixed_content(self, url: str, html_content: str) -> List[MixedContentIssue]:
        """Detect mixed content issues in HTML"""
        issues = []
        
        # Only check if the main page is HTTPS
        if not url.startswith('https://'):
            return issues
        
        for resource_type, pattern in self.resource_patterns.items():
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            
            for match in matches:
                # Extract the HTTP URL
                http_url_match = re.search(r'http://[^"\'>\s]+', match.group())
                if http_url_match:
                    http_url = http_url_match.group()
                    
                    # Determine severity
                    severity = SecurityLevel.CRITICAL if resource_type in ['script', 'iframe'] else SecurityLevel.WARNING
                    
                    issues.append(MixedContentIssue(
                        resource_url=http_url,
                        resource_type=resource_type,
                        severity=severity,
                        context=match.group()[:100]
                    ))
        
        return issues


class SecurityHeaderAnalyzer:
    """Analyzes security headers"""
    
    def __init__(self):
        self.expected_headers = {
            'Strict-Transport-Security': {
                'required': True,
                'secure_patterns': [r'max-age=\d+', r'includeSubDomains'],
                'description': 'HSTS header enforces HTTPS'
            },
            'X-Content-Type-Options': {
                'required': True,
                'secure_values': ['nosniff'],
                'description': 'Prevents MIME type sniffing'
            },
            'X-Frame-Options': {
                'required': True,
                'secure_values': ['DENY', 'SAMEORIGIN'],
                'description': 'Prevents clickjacking attacks'
            },
            'X-XSS-Protection': {
                'required': False,
                'secure_values': ['1; mode=block'],
                'description': 'Legacy XSS protection'
            },
            'Referrer-Policy': {
                'required': True,
                'secure_values': ['strict-origin-when-cross-origin', 'no-referrer', 'same-origin'],
                'description': 'Controls referrer information'
            },
            'Permissions-Policy': {
                'required': False,
                'description': 'Controls browser features'
            }
        }
    
    def analyze_security_headers(self, headers: Dict[str, str]) -> List[SecurityHeader]:
        """Analyze security headers"""
        header_results = []
        
        for header_name, config in self.expected_headers.items():
            header_value = headers.get(header_name)
            present = header_value is not None
            
            if present:
                # Analyze header value
                security_level = self._assess_header_security(header_name, header_value, config)
                recommendations = self._get_header_recommendations(header_name, header_value, config)
            else:
                security_level = SecurityLevel.VULNERABLE if config.get('required') else SecurityLevel.WARNING
                recommendations = [f"Add {header_name} header: {config['description']}"]
            
            header_results.append(SecurityHeader(
                name=header_name,
                value=header_value,
                present=present,
                security_level=security_level,
                recommendations=recommendations
            ))
        
        return header_results
    
    def _assess_header_security(self, name: str, value: str, config: Dict) -> SecurityLevel:
        """Assess security level of a header value"""
        if 'secure_values' in config:
            if value in config['secure_values']:
                return SecurityLevel.SECURE
            else:
                return SecurityLevel.WARNING
        
        if 'secure_patterns' in config:
            if all(re.search(pattern, value) for pattern in config['secure_patterns']):
                return SecurityLevel.SECURE
            else:
                return SecurityLevel.WARNING
        
        return SecurityLevel.SECURE
    
    def _get_header_recommendations(self, name: str, value: str, config: Dict) -> List[str]:
        """Get recommendations for improving header security"""
        recommendations = []
        
        if name == 'Strict-Transport-Security':
            if 'includeSubDomains' not in value:
                recommendations.append("Add 'includeSubDomains' to HSTS header")
            if 'preload' not in value:
                recommendations.append("Consider adding 'preload' to HSTS header")
        
        elif name == 'Content-Security-Policy':
            if "'unsafe-inline'" in value:
                recommendations.append("Remove 'unsafe-inline' from CSP")
            if "'unsafe-eval'" in value:
                recommendations.append("Remove 'unsafe-eval' from CSP")
        
        return recommendations


class SecurityScanner:
    """Main security scanner class"""
    
    def __init__(self):
        self.ssl_analyzer = SSLAnalyzer()
        self.csp_analyzer = CSPAnalyzer()
        self.mixed_content_detector = MixedContentDetector()
        self.header_analyzer = SecurityHeaderAnalyzer()
    
    def scan_url(self, url: str) -> SecurityScanResult:
        """Perform comprehensive security scan of a URL"""
        logger.info(f"Starting security scan of {url}")
        
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        https_enabled = parsed_url.scheme == 'https'
        
        # Get page content and headers
        try:
            response = requests.get(url, timeout=30, verify=True)
            html_content = response.text
            headers = dict(response.headers)
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            html_content = ""
            headers = {}
        
        # SSL Certificate Analysis
        ssl_certificate = None
        if https_enabled:
            ssl_certificate = self.ssl_analyzer.analyze_ssl_certificate(hostname)
        
        # CSP Analysis
        csp_header = headers.get('Content-Security-Policy')
        csp_report_only = headers.get('Content-Security-Policy-Report-Only')
        csp_analysis = self.csp_analyzer.analyze_csp(
            csp_header or csp_report_only,
            report_only=bool(csp_report_only and not csp_header)
        )
        
        # Security Headers Analysis
        security_headers = self.header_analyzer.analyze_security_headers(headers)
        
        # Mixed Content Detection
        mixed_content_issues = self.mixed_content_detector.detect_mixed_content(url, html_content)
        
        # Detect insecure requests (basic check)
        insecure_requests = self._detect_insecure_requests(html_content)
        
        # Calculate overall security score
        overall_score, security_level, recommendations = self._calculate_overall_security(
            https_enabled,
            ssl_certificate,
            csp_analysis,
            security_headers,
            mixed_content_issues,
            insecure_requests
        )
        
        return SecurityScanResult(
            url=url,
            timestamp=datetime.now().isoformat(),
            https_enabled=https_enabled,
            ssl_certificate=ssl_certificate,
            csp_analysis=csp_analysis,
            security_headers=security_headers,
            mixed_content_issues=mixed_content_issues,
            insecure_requests=insecure_requests,
            overall_security_score=overall_score,
            security_level=security_level,
            recommendations=recommendations
        )
    
    def _detect_insecure_requests(self, html_content: str) -> List[str]:
        """Detect potentially insecure requests in HTML content"""
        insecure_patterns = [
            r'http://[^"\'\s>]+',  # Any HTTP URLs
            r'ws://[^"\'\s>]+',    # Insecure WebSocket URLs
        ]
        
        insecure_requests = []
        for pattern in insecure_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                insecure_requests.append(match.group())
        
        return list(set(insecure_requests))  # Remove duplicates
    
    def _calculate_overall_security(
        self,
        https_enabled: bool,
        ssl_certificate: Optional[SSLCertificateInfo],
        csp_analysis: CSPAnalysis,
        security_headers: List[SecurityHeader],
        mixed_content_issues: List[MixedContentIssue],
        insecure_requests: List[str]
    ) -> Tuple[int, SecurityLevel, List[str]]:
        """Calculate overall security score and recommendations"""
        
        score = 100
        recommendations = []
        
        # HTTPS check
        if not https_enabled:
            score -= 40
            recommendations.append("Enable HTTPS for the entire site")
        
        # SSL certificate check
        if ssl_certificate:
            if ssl_certificate.is_expired:
                score -= 30
                recommendations.append("SSL certificate has expired")
            elif ssl_certificate.days_until_expiry < 30:
                score -= 10
                recommendations.append("SSL certificate expires soon")
        
        # CSP check
        score += (csp_analysis.security_score - 100) * 0.3  # Weight CSP score
        recommendations.extend(csp_analysis.recommendations)
        
        # Security headers check
        missing_critical_headers = sum(1 for h in security_headers if not h.present and h.name in ['Strict-Transport-Security', 'X-Content-Type-Options'])
        score -= missing_critical_headers * 10
        
        for header in security_headers:
            recommendations.extend(header.recommendations)
        
        # Mixed content issues
        critical_mixed_content = sum(1 for issue in mixed_content_issues if issue.severity == SecurityLevel.CRITICAL)
        score -= critical_mixed_content * 15
        
        if mixed_content_issues:
            recommendations.append("Fix mixed content issues by using HTTPS for all resources")
        
        # Insecure requests
        if insecure_requests:
            score -= len(insecure_requests) * 5
            recommendations.append("Replace HTTP requests with HTTPS")
        
        # Determine security level
        score = max(0, min(100, score))
        
        if score >= 80:
            security_level = SecurityLevel.SECURE
        elif score >= 60:
            security_level = SecurityLevel.WARNING
        elif score >= 40:
            security_level = SecurityLevel.VULNERABLE
        else:
            security_level = SecurityLevel.CRITICAL
        
        return int(score), security_level, recommendations


# CLI integration functions
def add_security_scan_args(parser):
    """Add security scanning arguments to CLI parser"""
    security_group = parser.add_argument_group('security scanning')
    security_group.add_argument(
        '--security-scan',
        action='store_true',
        help='Perform comprehensive security scan'
    )
    security_group.add_argument(
        '--security-report',
        help='Output file for security report'
    )
    security_group.add_argument(
        '--check-ssl',
        action='store_true',
        help='Detailed SSL certificate analysis'
    )
    security_group.add_argument(
        '--check-csp',
        action='store_true',
        help='Analyze Content Security Policy'
    )
    security_group.add_argument(
        '--check-mixed-content',
        action='store_true',
        help='Detect mixed content issues'
    )


def perform_security_scan(url: str, output_file: Optional[str] = None) -> SecurityScanResult:
    """Perform security scan for a URL"""
    scanner = SecurityScanner()
    result = scanner.scan_url(url)
    
    if output_file:
        import json
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        logger.info(f"Security scan report saved to {output_file}")
    
    return result
