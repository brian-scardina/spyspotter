#!/usr/bin/env python3
"""
Tracking Pixel Scanner
A tool to scan URLs for tracking pixels and report findings.
"""

import requests
import argparse
import re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any
from datetime import datetime
import os
import time
import random
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import our comprehensive tracker database
try:
    from pixeltracker.tracker_database import tracker_db
except ImportError:
    print("Warning: Could not import tracker database. Using fallback patterns.")
    tracker_db = None

class TrackingPixelScanner:
    def __init__(self, rate_limit_delay=1.0):
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.session = self._create_session()
        self.logger = logging.getLogger(__name__)
        
        self.tracking_domains = [
            # Google/Alphabet
            'google-analytics.com',
            'googletagmanager.com',
            'googlesyndication.com',
            'doubleclick.net',
            'googleadservices.com',
            'google.com/analytics',
            'gstatic.com',
            'youtube.com/api',
            
            # Facebook/Meta
            'facebook.com',
            'connect.facebook.net',
            'facebook.net',
            'instagram.com',
            'fbcdn.net',
            
            # Amazon
            'amazon-adsystem.com',
            'adsystem.amazon.com',
            'amazonaws.com',
            'cloudfront.net',
            
            # Microsoft
            'bing.com',
            'bing.net',
            'bingads.com',
            'msn.com',
            'live.com',
            'microsoft.com',
            
            # Social Media
            'linkedin.com',
            'twitter.com',
            'pinterest.com',
            'snapchat.com',
            'tiktok.com',
            'reddit.com',
            'tumblr.com',
            
            # Analytics & Metrics
            'hotjar.com',
            'fullstory.com',
            'mixpanel.com',
            'segment.com',
            'amplitude.com',
            'kissmetrics.com',
            'heap.io',
            'logrocket.com',
            'quantserve.com',
            'scorecardresearch.com',
            'chartbeat.com',
            'newrelic.com',
            'bugsnag.com',
            'sentry.io',
            'rollbar.com',
            'raygun.io',
            
            # A/B Testing & Optimization
            'optimizely.com',
            'vwo.com',
            'unbounce.com',
            'convertkit.com',
            'launchrock.com',
            
            # Heatmaps & User Experience
            'crazyegg.com',
            'mouseflow.com',
            'inspectlet.com',
            'usabilla.com',
            'userreport.com',
            'userzoom.com',
            
            # Customer Support & Feedback
            'uservoice.com',
            'zendesk.com',
            'intercom.io',
            'drift.com',
            'olark.com',
            'zopim.com',
            'livechatinc.com',
            'freshworks.com',
            'helpscout.com',
            
            # Marketing Automation
            'hubspot.com',
            'marketo.com',
            'pardot.com',
            'salesforce.com',
            'mailchimp.com',
            'constantcontact.com',
            'aweber.com',
            'getresponse.com',
            'activecampaign.com',
            'drip.com',
            'klaviyo.com',
            
            # Adobe
            'adobe.com',
            'omniture.com',
            'demdex.net',
            'everesttech.net',
            
            # Content & Native Advertising
            'outbrain.com',
            'taboola.com',
            'revcontent.com',
            'mgid.com',
            'gravity.com',
            'zemanta.com',
            
            # Ad Networks & Exchanges
            'bluekai.com',
            'adroll.com',
            'criteo.com',
            'openx.net',
            'rubiconproject.com',
            'smartadserver.com',
            'adform.net',
            'adzerk.net',
            'quantcast.com',
            'smaato.net',
            'yieldbot.com',
            'contextweb.com',
            'casalemedia.com',
            'turn.com',
            'rlcdn.com',
            'serving-sys.com',
            'eyeota.net',
            'exelator.com',
            'addthis.com',
            'sharethis.com',
            
            # Verification & Fraud Prevention
            'doubleverify.com',
            'ias.net',
            'moat.com',
            'whiteops.com',
            'pixalate.com',
            
            # Data Management Platforms
            'crwdcntrl.net',
            'mathtag.com',
            'adsymptotic.com',
            'adnxs.com',
            'amazonaws.com',
            
            # CDNs often used for tracking
            'cloudflare.com',
            'akamai.com',
            'fastly.com',
            'maxcdn.com',
            
            # Email tracking
            'mailgun.com',
            'sendgrid.com',
            'mandrill.com',
            'postmark.com',
            
            # Other tracking services
            'yahoo.com',
            'yandex.com',
            'baidu.com',
            'naver.com',
            'branch.io',
            'appsflyer.com',
            'adjust.com',
            'kochava.com',
            'singular.net',
            'tenjin.io'
        ]
        
        self.pixel_patterns = [
            r'<img[^>]*src=["\'][^"\']*\.(gif|png|jpg|jpeg)\?[^"\']*["\'][^>]*>',
            r'<img[^>]*width=["\']1["\'][^>]*height=["\']1["\'][^>]*>',
            r'<img[^>]*height=["\']1["\'][^>]*width=["\']1["\'][^>]*>',
            r'<iframe[^>]*width=["\']1["\'][^>]*height=["\']1["\'][^>]*>',
            r'<iframe[^>]*height=["\']1["\'][^>]*width=["\']1["\'][^>]*>',
            r'<noscript>.*?<img.*?</noscript>'
        ]

    def _create_session(self):
        """Create a requests session with retry strategy and connection pooling."""
        session = requests.Session()
        
        # Set up retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_random_user_agent(self):
        """Get a random user agent to avoid detection."""
        return random.choice(self.user_agents)

    def fetch_page(self, url: str) -> str:
        """Fetch the HTML content of a webpage with rate limiting and improved error handling."""
        try:
            # Apply rate limiting
            self._wait_for_rate_limit()
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Successfully fetched {url} (Status: {response.status_code})")
            return response.text
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout fetching {url}")
            return ""
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error fetching {url}")
            return ""
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error fetching {url}: {e}")
            return ""
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return ""

    def find_tracking_pixels(self, html_content: str) -> List[Dict[str, Any]]:
        """Find potential tracking pixels in HTML content."""
        pixels = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all img and iframe tags
        elements = soup.find_all(['img', 'iframe'])
        
        for element in elements:
            pixel_info = self.analyze_element(element)
            if pixel_info:
                pixels.append(pixel_info)
        
        # Also check for pixels in noscript tags
        noscript_tags = soup.find_all('noscript')
        for noscript in noscript_tags:
            noscript_elements = noscript.find_all(['img', 'iframe'])
            for element in noscript_elements:
                pixel_info = self.analyze_element(element, in_noscript=True)
                if pixel_info:
                    pixels.append(pixel_info)
        
        # Check for base64 encoded pixels
        base64_pixels = self.find_base64_pixels(soup)
        pixels.extend(base64_pixels)
        
        return pixels

    def analyze_element(self, element, in_noscript=False) -> Dict[str, Any]:
        """Analyze an HTML element to determine if it's a tracking pixel."""
        src = element.get('src', '')
        width = element.get('width', '')
        height = element.get('height', '')
        
        # Check for 1x1 pixel dimensions
        is_1x1_pixel = (
            (width == '1' and height == '1') or
            (width == '0' and height == '0') or
            ('width: 1px' in element.get('style', '')) or
            ('height: 1px' in element.get('style', ''))
        )
        
        # Check if src contains tracking domain
        tracking_domain = None
        for domain in self.tracking_domains:
            if domain in src:
                tracking_domain = domain
                break
        
        # Check for suspicious URL patterns
        has_tracking_params = any(param in src.lower() for param in [
            'utm_', 'track', 'pixel', 'beacon', 'analytics', 'event', 'campaign'
        ])
        
        # Determine if this looks like a tracking pixel
        is_likely_tracking = (
            is_1x1_pixel or
            tracking_domain or
            has_tracking_params or
            in_noscript
        )
        
        if is_likely_tracking:
            return {
                'element_type': element.name,
                'src': src,
                'width': width,
                'height': height,
                'is_1x1_pixel': is_1x1_pixel,
                'tracking_domain': tracking_domain,
                'has_tracking_params': has_tracking_params,
                'in_noscript': in_noscript,
                'full_element': str(element)
            }
        
        return None

    def find_base64_pixels(self, soup) -> List[Dict[str, Any]]:
        """Find base64 encoded tracking pixels."""
        base64_pixels = []
        
        # Look for base64 encoded images
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            if 'data:image' in src and 'base64' in src:
                # Check if it's a 1x1 pixel or very small
                width = img.get('width', '')
                height = img.get('height', '')
                if (width == '1' and height == '1') or len(src) < 200:
                    base64_pixels.append({
                        'element_type': 'img',
                        'src': src[:100] + '...' if len(src) > 100 else src,
                        'width': width,
                        'height': height,
                        'is_base64': True,
                        'tracking_type': 'base64_pixel',
                        'full_element': str(img)
                    })
        
        return base64_pixels

    def find_meta_tracking(self, soup) -> List[Dict[str, Any]]:
        """Find tracking-related meta tags."""
        meta_trackers = []
        
        # Common tracking meta tags
        tracking_meta_names = [
            'google-site-verification',
            'facebook-domain-verification',
            'msvalidate.01',
            'pinterest-site-verification',
            'yandex-verification',
            'baidu-site-verification'
        ]
        
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            # Check for tracking verification tags
            if name in tracking_meta_names or property_attr in tracking_meta_names:
                meta_trackers.append({
                    'type': 'verification_meta',
                    'name': name or property_attr,
                    'content': content,
                    'element': str(meta)
                })
            
            # Check for Open Graph and Twitter Card tracking
            elif property_attr.startswith(('og:', 'twitter:', 'fb:')):
                meta_trackers.append({
                    'type': 'social_meta',
                    'property': property_attr,
                    'content': content,
                    'element': str(meta)
                })
        
        return meta_trackers

    def find_css_tracking(self, soup) -> List[Dict[str, Any]]:
        """Find CSS-based tracking (background images, etc.)."""
        css_trackers = []
        
        # Check style tags for background images
        style_tags = soup.find_all('style')
        for style in style_tags:
            content = style.string or ''
            
            # Look for background-image URLs
            bg_image_pattern = r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)'
            matches = re.findall(bg_image_pattern, content, re.IGNORECASE)
            
            for match in matches:
                # Check if it's from a tracking domain
                for domain in self.tracking_domains:
                    if domain in match:
                        css_trackers.append({
                            'type': 'css_background',
                            'url': match,
                            'domain': domain,
                            'element': str(style)
                        })
                        break
        
        # Check inline styles
        elements_with_style = soup.find_all(attrs={'style': True})
        for element in elements_with_style:
            style = element.get('style', '')
            if 'background-image' in style:
                bg_image_pattern = r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)'
                matches = re.findall(bg_image_pattern, style, re.IGNORECASE)
                
                for match in matches:
                    for domain in self.tracking_domains:
                        if domain in match:
                            css_trackers.append({
                                'type': 'inline_css_background',
                                'url': match,
                                'domain': domain,
                                'element': str(element)
                            })
                            break
        
        return css_trackers

    def find_comprehensive_trackers(self, html_content: str, url: str = "") -> List[Dict[str, Any]]:
        """Find trackers using the comprehensive tracker database."""
        if tracker_db is None:
            return []
        
        detected_trackers = tracker_db.detect_trackers(html_content, url)
        
        # Convert to our format
        formatted_trackers = []
        for tracker in detected_trackers:
            formatted_trackers.append({
                'type': 'comprehensive_tracker',
                'tracker_id': tracker['tracker_id'],
                'name': tracker['name'],
                'category': tracker['category'],
                'risk_level': tracker['risk_level'],
                'description': tracker['description'],
                'data_types': tracker['data_types'],
                'gdpr_relevant': tracker['gdpr_relevant'],
                'ccpa_relevant': tracker['ccpa_relevant'],
                'matches': tracker['matches'],
                'evasion_techniques': tracker['evasion_techniques']
            })
        
        return formatted_trackers

    def find_javascript_trackers(self, html_content: str) -> List[Dict[str, Any]]:
        """Find JavaScript-based tracking code."""
        trackers = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all script tags
        scripts = soup.find_all('script')
        
        for script in scripts:
            src = script.get('src', '')
            content = script.string or ''
            
            # Check for tracking domains in script sources
            for domain in self.tracking_domains:
                if domain in src:
                    trackers.append({
                        'type': 'external_script',
                        'domain': domain,
                        'src': src,
                        'element': str(script)
                    })
                    break
            
            # Check for tracking code patterns in script content
            tracking_patterns = [
                # Google Analytics & Tag Manager
                r'ga\(.*?\)',
                r'gtag\(.*?\)',
                r'_gaq\.push',
                r'dataLayer\.push',
                r'GoogleAnalyticsObject',
                r'gtm\.',
                
                # Facebook/Meta
                r'fbq\(.*?\)',
                r'_fbq\.',
                r'facebook\.com/tr',
                
                # Adobe Analytics
                r's\.t\(',
                r's\.tl\(',
                r'adobe_mc',
                r'omtrdc\.net',
                r'demdex\.net',
                
                # Mixpanel
                r'mixpanel\.',
                r'mp_track',
                
                # Amplitude
                r'amplitude\.',
                r'logEvent',
                
                # Segment
                r'analytics\.track',
                r'analytics\.page',
                r'analytics\.identify',
                
                # Hotjar
                r'hj\(',
                r'hotjar',
                
                # FullStory
                r'FS\.',
                r'fullstory',
                
                # HubSpot
                r'_hsq\.push',
                r'hubspot',
                
                # Intercom
                r'Intercom\(',
                r'intercom_settings',
                
                # Drift
                r'drift\.load',
                r'drift\.track',
                
                # Optimizely
                r'optimizely',
                r'optly',
                
                # Crazy Egg
                r'crazyegg',
                r'CE_API',
                
                # Heap
                r'heap\.track',
                r'heap\.identify',
                
                # Kissmetrics
                r'_kmq\.push',
                r'kissmetrics',
                
                # LogRocket
                r'LogRocket',
                r'logrocket',
                
                # New Relic
                r'NREUM',
                r'newrelic',
                
                # Sentry
                r'Sentry\.',
                r'sentry',
                
                # Rollbar
                r'Rollbar',
                r'rollbar',
                
                # Bugsnag
                r'Bugsnag',
                r'bugsnag',
                
                # Pinterest
                r'pintrk\(',
                r'pinterest',
                
                # Twitter
                r'twq\(',
                r'twitter',
                
                # LinkedIn
                r'_linkedin_partner_id',
                r'linkedin',
                
                # Snapchat
                r'snaptr\(',
                r'snapchat',
                
                # TikTok
                r'ttq\.',
                r'tiktok',
                
                # Quantcast
                r'_qevents',
                r'quantcast',
                
                # Chartbeat
                r'_sf_async_config',
                r'chartbeat',
                
                # Score Card Research
                r'COMSCORE',
                r'scorecardresearch',
                
                # Microsoft/Bing
                r'uetq\.push',
                r'bing',
                
                # VWO
                r'_vwo_code',
                r'vwo',
                
                # Branch
                r'branch\.',
                
                # AppsFlyer
                r'appsflyer',
                
                # Adjust
                r'Adjust',
                
                # Generic tracking patterns
                r'track\(',
                r'pageview',
                r'event\(',
                r'identify\(',
                r'utm_',
                r'pixel',
                r'beacon'
            ]
            
            for pattern in tracking_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    trackers.append({
                        'type': 'inline_script',
                        'pattern': pattern,
                        'content_snippet': content[:200] + '...' if len(content) > 200 else content
                    })
        
        return trackers

    def analyze_privacy_impact(self, domains, pixels, js_trackers, meta_trackers, css_trackers) -> Dict[str, Any]:
        """Analyze the privacy impact of detected trackers."""
        
        # Categorize tracking services
        categories = {
            'advertising': ['google-analytics.com', 'googletagmanager.com', 'doubleclick.net', 'facebook.com', 
                           'connect.facebook.net', 'criteo.com', 'outbrain.com', 'taboola.com', 'adroll.com'],
            'analytics': ['mixpanel.com', 'amplitude.com', 'segment.com', 'chartbeat.com', 'quantcast.com'],
            'social_media': ['twitter.com', 'linkedin.com', 'pinterest.com', 'snapchat.com', 'tiktok.com'],
            'performance': ['newrelic.com', 'sentry.io', 'rollbar.com', 'bugsnag.com'],
            'user_experience': ['hotjar.com', 'fullstory.com', 'crazyegg.com', 'mouseflow.com', 'optimizely.com'],
            'marketing': ['hubspot.com', 'marketo.com', 'mailchimp.com', 'salesforce.com']
        }
        
        detected_categories = set()
        high_risk_domains = []
        
        for domain in domains:
            for category, category_domains in categories.items():
                if any(cat_domain in domain for cat_domain in category_domains):
                    detected_categories.add(category)
                    if category in ['advertising', 'social_media']:
                        high_risk_domains.append(domain)
        
        # Calculate privacy score (0-100, lower is worse for privacy)
        privacy_score = 100
        privacy_score -= len(pixels) * 5  # Each pixel reduces score by 5
        privacy_score -= len([t for t in js_trackers if t['type'] == 'external_script']) * 8  # External scripts are worse
        privacy_score -= len([t for t in js_trackers if t['type'] == 'inline_script']) * 3  # Inline scripts less severe
        privacy_score -= len(high_risk_domains) * 10  # High-risk domains are very bad
        privacy_score = max(0, privacy_score)  # Don't go below 0
        
        return {
            'privacy_score': privacy_score,
            'risk_level': 'Low' if privacy_score > 80 else 'Medium' if privacy_score > 50 else 'High',
            'detected_categories': list(detected_categories),
            'high_risk_domains': high_risk_domains,
            'recommendations': self.get_privacy_recommendations(detected_categories, high_risk_domains)
        }
    
    def get_privacy_recommendations(self, categories, high_risk_domains) -> List[str]:
        """Generate privacy recommendations based on detected tracking."""
        recommendations = []
        
        if 'advertising' in categories:
            recommendations.append("Consider using ad blockers or privacy-focused browsers")
            recommendations.append("Review and adjust ad personalization settings")
        
        if 'social_media' in categories:
            recommendations.append("Disable social media tracking in browser settings")
            recommendations.append("Use privacy extensions to block social media trackers")
        
        if high_risk_domains:
            recommendations.append("High-risk tracking domains detected - consider VPN usage")
        
        if 'analytics' in categories:
            recommendations.append("Analytics tracking detected - consider opting out if possible")
        
        if not recommendations:
            recommendations.append("Minimal tracking detected - privacy impact is low")
        
        return recommendations

    def generate_detailed_report(self, results: List[Dict[str, Any]], output_format='html') -> str:
        """Generate a detailed report in HTML or enhanced JSON format."""
        
        if output_format == 'html':
            return self.generate_html_report(results)
        else:
            return self.generate_enhanced_json_report(results)
    
    def generate_html_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate an HTML report with detailed analysis."""
        
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tracking Pixel Scanner - Detailed Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .url-section {{ margin-bottom: 40px; border: 1px solid #ddd; border-radius: 8px; padding: 20px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .summary-card .number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .privacy-score {{ padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .privacy-low {{ background: #d4edda; border-left: 4px solid #28a745; }}
        .privacy-medium {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
        .privacy-high {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .tracker-section {{ margin: 20px 0; }}
        .tracker-item {{ background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .tracker-type {{ font-weight: bold; color: #007bff; margin-bottom: 5px; }}
        .domain-list {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }}
        .domain-badge {{ background: #e9ecef; padding: 5px 10px; border-radius: 15px; font-size: 12px; }}
        .high-risk {{ background: #f8d7da; color: #721c24; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .code {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; overflow-x: auto; }}
        .recommendations {{ background: #e7f3ff; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Tracking Pixel Scanner Report</h1>
            <p class="timestamp">Generated on: {timestamp}</p>
        </div>
        
        {content}
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
            <p>Report generated by Tracking Pixel Scanner</p>
        </div>
    </div>
</body>
</html>'''
        
        content = ""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for result in results:
            if 'error' in result:
                content += f'<div class="url-section"><h2>❌ {result.get("url", "Unknown URL")}</h2><p>Error: {result["error"]}</p></div>'
                continue
            
            privacy = result.get('privacy_analysis', {})
            
            content += f'''
            <div class="url-section">
                <h2>🌐 {result['url']}</h2>
                
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>📊 Tracking Pixels</h3>
                        <div class="number">{result['pixel_count']}</div>
                    </div>
                    <div class="summary-card">
                        <h3>🔧 JavaScript Trackers</h3>
                        <div class="number">{result['js_tracker_count']}</div>
                    </div>
                    <div class="summary-card">
                        <h3>🏷️ Meta Tag Trackers</h3>
                        <div class="number">{result['meta_tracker_count']}</div>
                    </div>
                    <div class="summary-card">
                        <h3>🎨 CSS Trackers</h3>
                        <div class="number">{result['css_tracker_count']}</div>
                    </div>
                    <div class="summary-card">
                        <h3>📈 Total Trackers</h3>
                        <div class="number">{result['summary']['total_trackers']}</div>
                    </div>
                </div>
                
                <div class="privacy-score privacy-{privacy.get('risk_level', 'medium').lower()}">
                    <h3>🔒 Privacy Analysis</h3>
                    <p><strong>Privacy Score:</strong> {privacy.get('privacy_score', 'N/A')}/100</p>
                    <p><strong>Risk Level:</strong> {privacy.get('risk_level', 'Unknown')}</p>
                    <p><strong>Categories Detected:</strong> {', '.join(privacy.get('detected_categories', []))}</p>
                </div>
                
                <div class="domain-list">
                    <strong>Tracking Domains:</strong>
            '''
            
            for domain in result['summary']['domains_found']:
                risk_class = 'high-risk' if domain in privacy.get('high_risk_domains', []) else ''
                content += f'<span class="domain-badge {risk_class}">{domain}</span>'
            
            content += '</div>'
            
            # Add detailed tracker information
            if result['tracking_pixels']:
                content += '<div class="tracker-section"><h3>📊 Tracking Pixels Details</h3>'
                for pixel in result['tracking_pixels']:
                    content += f'''
                    <div class="tracker-item">
                        <div class="tracker-type">Pixel: {pixel.get('element_type', 'Unknown')}</div>
                        <p><strong>Source:</strong> {pixel.get('src', 'N/A')[:100]}...</p>
                        <p><strong>Domain:</strong> {pixel.get('tracking_domain', 'Unknown')}</p>
                        <p><strong>1x1 Pixel:</strong> {pixel.get('is_1x1_pixel', False)}</p>
                    </div>
                    '''
                content += '</div>'
            
            # Add recommendations
            if privacy.get('recommendations'):
                content += '<div class="recommendations"><h3>💡 Privacy Recommendations</h3><ul>'
                for rec in privacy['recommendations']:
                    content += f'<li>{rec}</li>'
                content += '</ul></div>'
            
            content += '</div>'
        
        return html_template.format(timestamp=timestamp, content=content)
    
    def generate_enhanced_json_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate an enhanced JSON report with additional analytics."""
        
        # Calculate aggregate statistics
        total_sites = len(results)
        total_trackers = sum(r.get('summary', {}).get('total_trackers', 0) for r in results)
        all_domains = set()
        
        for result in results:
            all_domains.update(result.get('summary', {}).get('domains_found', []))
        
        aggregate_stats = {
            'total_sites_scanned': total_sites,
            'total_trackers_found': total_trackers,
            'unique_tracking_domains': len(all_domains),
            'average_trackers_per_site': total_trackers / total_sites if total_sites > 0 else 0,
            'most_common_domains': list(all_domains)[:10],  # Top 10 most common
            'scan_timestamp': datetime.now().isoformat()
        }
        
        enhanced_report = {
            'report_metadata': {
                'generated_by': 'Tracking Pixel Scanner',
                'version': '2.0',
                'scan_date': datetime.now().isoformat()
            },
            'aggregate_statistics': aggregate_stats,
            'detailed_results': results
        }
        
        return json.dumps(enhanced_report, indent=2)

    def scan_url(self, url: str) -> Dict[str, Any]:
        """Scan a URL for tracking pixels and return results."""
        print(f"Scanning {url}...")
        
        html_content = self.fetch_page(url)
        if not html_content:
            return {'error': 'Failed to fetch page content'}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Run all detection methods
        pixels = self.find_tracking_pixels(html_content)
        js_trackers = self.find_javascript_trackers(html_content)
        meta_trackers = self.find_meta_tracking(soup)
        css_trackers = self.find_css_tracking(soup)
        comprehensive_trackers = self.find_comprehensive_trackers(html_content, url)
        
        # Combine all tracking domains found
        all_domains = []
        all_domains.extend([p.get('tracking_domain') for p in pixels if p.get('tracking_domain')])
        all_domains.extend([t.get('domain') for t in js_trackers if t.get('domain')])
        all_domains.extend([t.get('domain') for t in css_trackers if t.get('domain')])
        
        return {
            'url': url,
            'scan_timestamp': datetime.now().isoformat(),
            'pixel_count': len(pixels),
            'js_tracker_count': len(js_trackers),
            'meta_tracker_count': len(meta_trackers),
            'css_tracker_count': len(css_trackers),
            'tracking_pixels': pixels,
            'javascript_trackers': js_trackers,
            'meta_trackers': meta_trackers,
            'css_trackers': css_trackers,
            'summary': {
                'total_trackers': len(pixels) + len(js_trackers) + len(meta_trackers) + len(css_trackers),
                'domains_found': list(set(filter(None, all_domains))),
                'tracking_types': {
                    'pixels': len(pixels),
                    'javascript': len(js_trackers),
                    'meta_tags': len(meta_trackers),
                    'css_background': len(css_trackers)
                }
            },
            'privacy_analysis': self.analyze_privacy_impact(all_domains, pixels, js_trackers, meta_trackers, css_trackers)
        }

def main():
    parser = argparse.ArgumentParser(description='Scan URLs for tracking pixels')
    parser.add_argument('urls', nargs='+', help='URLs to scan')
    parser.add_argument('--output', '-o', help='Output file for results (JSON format)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--detailed-report', '-d', help='Generate detailed HTML or enhanced JSON report (specify filename)')
    parser.add_argument('--report-format', choices=['html', 'json'], default='html', help='Format for detailed report (default: html)')
    
    args = parser.parse_args()
    
    scanner = TrackingPixelScanner()
    results = []
    
    for url in args.urls:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = scanner.scan_url(url)
        results.append(result)
        
        # Print summary
        if 'error' in result:
            print(f"❌ Error scanning {url}: {result['error']}")
        else:
            print(f"✅ {url}")
            print(f"   📊 Found {result['pixel_count']} tracking pixels")
            print(f"   🔧 Found {result['js_tracker_count']} JavaScript trackers")
            print(f"   🏷️  Found {result['meta_tracker_count']} meta tag trackers")
            print(f"   🎨 Found {result['css_tracker_count']} CSS trackers")
            print(f"   📈 Total trackers: {result['summary']['total_trackers']}")
            print(f"   🌐 Tracking domains: {', '.join(result['summary']['domains_found']) if result['summary']['domains_found'] else 'None'}")
            
            if args.verbose:
                for pixel in result['tracking_pixels']:
                    print(f"   🎯 Pixel: {pixel.get('src', 'N/A')[:80]}...")
                for tracker in result['javascript_trackers']:
                    if tracker['type'] == 'external_script':
                        print(f"   📜 JS Tracker: {tracker['domain']}")
                    elif tracker['type'] == 'inline_script':
                        print(f"   📜 JS Pattern: {tracker['pattern']}")
                for meta in result['meta_trackers']:
                    print(f"   🏷️  Meta: {meta['type']} - {meta.get('name', meta.get('property', 'N/A'))}")
                for css in result['css_trackers']:
                    print(f"   🎨 CSS: {css['type']} - {css['domain']}")
        print()
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    
    # Generate detailed report if requested
    if args.detailed_report:
        detailed_content = scanner.generate_detailed_report(results, args.report_format)
        with open(args.detailed_report, 'w') as f:
            f.write(detailed_content)
        print(f"📋 Detailed {args.report_format.upper()} report saved to {args.detailed_report}")
        
        # Show privacy summary
        total_trackers = sum(r.get('summary', {}).get('total_trackers', 0) for r in results if 'summary' in r)
        unique_domains = set()
        for result in results:
            if 'summary' in result:
                unique_domains.update(result['summary']['domains_found'])
        
        print(f"\n📊 Scan Summary:")
        print(f"   🌐 Sites scanned: {len(results)}")
        print(f"   📈 Total trackers found: {total_trackers}")
        print(f"   🎯 Unique tracking domains: {len(unique_domains)}")
        print(f"   📋 Detailed report: {args.detailed_report}")

if __name__ == '__main__':
    main()
