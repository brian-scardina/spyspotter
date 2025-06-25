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
        self.domain_index = {}
        self.category_index = {}
        self.load_tracker_database()
        self.compile_patterns()
    
    def load_tracker_database(self):
        """Load comprehensive tracker database"""
        
        # Google/Alphabet Ecosystem
        self.trackers['google_analytics'] = TrackerPattern(
            name="Google Analytics",
            category="analytics",
            risk_level="medium",
            patterns=[
                r'ga\s*\(\s*["\']send["\']',
                r'gtag\s*\(\s*["\']config["\']',
                r'gtag\s*\(\s*["\']event["\']',
                r'_gaq\.push',
                r'GoogleAnalyticsObject',
                r'google-analytics\.com/analytics\.js',
                r'google-analytics\.com/ga\.js',
                r'google-analytics\.com/collect',
                r'gtm\.start',
                r'dataLayer\.push'
            ],
            domains=['google-analytics.com', 'googletagmanager.com', 'googlesyndication.com'],
            description="Google's web analytics service",
            data_types=['page_views', 'user_behavior', 'demographics', 'interests'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['server_side_proxy', 'custom_domain'],
            first_seen="2005-11-14",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['google_ads'] = TrackerPattern(
            name="Google Ads / DoubleClick",
            category="advertising",
            risk_level="high",
            patterns=[
                r'googletag\.cmd\.push',
                r'googletag\.display',
                r'doubleclick\.net',
                r'googleadservices\.com',
                r'gpt\.js',
                r'conversion\.js',
                r'gtag\s*\(\s*["\']conversion["\']'
            ],
            domains=['doubleclick.net', 'googleadservices.com', 'googlesyndication.com'],
            description="Google's advertising and remarketing platform",
            data_types=['ad_targeting', 'conversion_tracking', 'remarketing', 'audience_segmentation'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['first_party_data', 'cookieless_tracking'],
            first_seen="2007-04-13",
            last_updated=datetime.now().isoformat()
        )
        
        # Facebook/Meta Ecosystem
        self.trackers['facebook_pixel'] = TrackerPattern(
            name="Facebook Pixel",
            category="social_advertising",
            risk_level="high",
            patterns=[
                r'fbq\s*\(\s*["\']init["\']',
                r'fbq\s*\(\s*["\']track["\']',
                r'fbq\s*\(\s*["\']trackCustom["\']',
                r'facebook\.com/tr',
                r'connect\.facebook\.net',
                r'_fbp',
                r'_fbc'
            ],
            domains=['facebook.com', 'connect.facebook.net', 'facebook.net'],
            description="Facebook's conversion tracking and advertising pixel",
            data_types=['conversion_tracking', 'custom_audiences', 'lookalike_audiences', 'cross_device_tracking'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['conversions_api', 'server_side_events'],
            first_seen="2013-10-01",
            last_updated=datetime.now().isoformat()
        )
        
        # Adobe Analytics/Marketing Cloud
        self.trackers['adobe_analytics'] = TrackerPattern(
            name="Adobe Analytics",
            category="analytics",
            risk_level="medium",
            patterns=[
                r's\.t\s*\(',
                r's\.tl\s*\(',
                r'omtrdc\.net',
                r'demdex\.net',
                r'adobe_mc',
                r'AppMeasurement',
                r'sitecatalyst',
                r'everesttech\.net'
            ],
            domains=['omtrdc.net', 'demdex.net', 'everesttech.net', '2o7.net'],
            description="Adobe's enterprise analytics platform",
            data_types=['user_analytics', 'attribution', 'audience_management', 'real_time_data'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['first_party_cookies', 'device_cooperative'],
            first_seen="1996-11-01",
            last_updated=datetime.now().isoformat()
        )
        
        # Social Media Platforms
        self.trackers['twitter_ads'] = TrackerPattern(
            name="Twitter Ads",
            category="social_advertising",
            risk_level="high",
            patterns=[
                r'twq\s*\(\s*["\']init["\']',
                r'twq\s*\(\s*["\']track["\']',
                r'analytics\.twitter\.com',
                r'static\.ads-twitter\.com'
            ],
            domains=['analytics.twitter.com', 'ads-twitter.com', 't.co'],
            description="Twitter's advertising and conversion tracking",
            data_types=['conversion_tracking', 'audience_insights', 'engagement_metrics'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['mobile_app_events'],
            first_seen="2013-04-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['linkedin_insight'] = TrackerPattern(
            name="LinkedIn Insight Tag",
            category="social_advertising",
            risk_level="medium",
            patterns=[
                r'_linkedin_partner_id',
                r'snap\.licdn\.com',
                r'linkedin\.com/li\.lms-analytics'
            ],
            domains=['snap.licdn.com', 'linkedin.com'],
            description="LinkedIn's conversion tracking for B2B advertising",
            data_types=['b2b_targeting', 'professional_demographics', 'conversion_tracking'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['first_party_data_matching'],
            first_seen="2016-05-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['pinterest_tag'] = TrackerPattern(
            name="Pinterest Tag",
            category="social_advertising",
            risk_level="medium",
            patterns=[
                r'pintrk\s*\(\s*["\']load["\']',
                r'pintrk\s*\(\s*["\']track["\']',
                r'ct\.pinterest\.com'
            ],
            domains=['ct.pinterest.com', 'pinterest.com'],
            description="Pinterest's conversion tracking pixel",
            data_types=['shopping_behavior', 'interest_targeting', 'conversion_tracking'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['enhanced_match'],
            first_seen="2016-02-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['snapchat_pixel'] = TrackerPattern(
            name="Snapchat Pixel",
            category="social_advertising",
            risk_level="medium",
            patterns=[
                r'snaptr\s*\(\s*["\']init["\']',
                r'snaptr\s*\(\s*["\']track["\']',
                r'tr\.snapchat\.com'
            ],
            domains=['tr.snapchat.com', 'sc-static.net'],
            description="Snapchat's advertising pixel for mobile-first audience",
            data_types=['mobile_behavior', 'demographic_targeting', 'app_events'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['snap_pixel_advanced_matching'],
            first_seen="2016-10-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['tiktok_pixel'] = TrackerPattern(
            name="TikTok Pixel",
            category="social_advertising",
            risk_level="high",
            patterns=[
                r'ttq\.load',
                r'ttq\.page',
                r'ttq\.track',
                r'analytics\.tiktok\.com'
            ],
            domains=['analytics.tiktok.com', 'tiktok.com'],
            description="TikTok's advertising pixel for Gen Z targeting",
            data_types=['video_engagement', 'mobile_behavior', 'trend_analytics'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['events_api'],
            first_seen="2019-03-01",
            last_updated=datetime.now().isoformat()
        )
        
        # Analytics Platforms
        self.trackers['mixpanel'] = TrackerPattern(
            name="Mixpanel",
            category="analytics",
            risk_level="medium",
            patterns=[
                r'mixpanel\.init',
                r'mixpanel\.track',
                r'mixpanel\.identify',
                r'mp_track',
                r'api\.mixpanel\.com'
            ],
            domains=['api.mixpanel.com', 'cdn.mxpnl.com'],
            description="Product analytics and user behavior tracking",
            data_types=['event_tracking', 'user_journeys', 'funnel_analysis', 'cohort_analysis'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['identity_resolution'],
            first_seen="2009-04-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['amplitude'] = TrackerPattern(
            name="Amplitude",
            category="analytics",
            risk_level="medium",
            patterns=[
                r'amplitude\.getInstance',
                r'amplitude\.logEvent',
                r'amplitude\.setUserId',
                r'api\.amplitude\.com'
            ],
            domains=['api.amplitude.com', 'cdn.amplitude.com'],
            description="Product intelligence and behavioral analytics",
            data_types=['user_behavior', 'retention_analysis', 'behavioral_cohorts'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['cross_platform_identification'],
            first_seen="2012-01-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['segment'] = TrackerPattern(
            name="Segment",
            category="analytics",
            risk_level="medium",
            patterns=[
                r'analytics\.track',
                r'analytics\.page',
                r'analytics\.identify',
                r'analytics\.alias',
                r'api\.segment\.io',
                r'cdn\.segment\.com'
            ],
            domains=['api.segment.io', 'cdn.segment.com'],
            description="Customer data platform and analytics infrastructure",
            data_types=['unified_customer_profiles', 'event_streaming', 'audience_management'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['server_side_libraries'],
            first_seen="2011-10-01",
            last_updated=datetime.now().isoformat()
        )
        
        # User Experience and Heatmap Tools
        self.trackers['hotjar'] = TrackerPattern(
            name="Hotjar",
            category="user_experience",
            risk_level="high",
            patterns=[
                r'hj\s*\(',
                r'hotjar',
                r'static\.hotjar\.com',
                r'insights\.hotjar\.com'
            ],
            domains=['static.hotjar.com', 'insights.hotjar.com', 'vars.hotjar.com'],
            description="Heatmaps, session recordings, and user feedback",
            data_types=['session_recordings', 'heatmaps', 'form_analytics', 'feedback'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['ip_anonymization'],
            first_seen="2014-11-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['fullstory'] = TrackerPattern(
            name="FullStory",
            category="user_experience",
            risk_level="high",
            patterns=[
                r'FS\.',
                r'fullstory',
                r'\.fullstory\.com'
            ],
            domains=['fullstory.com', 'edge.fullstory.com'],
            description="Digital experience analytics with session replay",
            data_types=['session_recordings', 'user_interactions', 'error_tracking'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['privacy_controls'],
            first_seen="2014-01-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['crazyegg'] = TrackerPattern(
            name="Crazy Egg",
            category="user_experience",
            risk_level="medium",
            patterns=[
                r'crazyegg',
                r'CE_API',
                r'dnn506yrbagrg\.cloudfront\.net'
            ],
            domains=['crazyegg.com', 'dnn506yrbagrg.cloudfront.net'],
            description="Heatmap and A/B testing platform",
            data_types=['click_tracking', 'heatmaps', 'scroll_maps'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['cookieless_tracking'],
            first_seen="2006-01-01",
            last_updated=datetime.now().isoformat()
        )
        
        # A/B Testing and Optimization
        self.trackers['optimizely'] = TrackerPattern(
            name="Optimizely",
            category="optimization",
            risk_level="medium",
            patterns=[
                r'optimizely',
                r'optly',
                r'cdn\.optimizely\.com',
                r'logx\.optimizely\.com'
            ],
            domains=['cdn.optimizely.com', 'logx.optimizely.com', 'optimizely.com'],
            description="A/B testing and experimentation platform",
            data_types=['experiment_data', 'conversion_tracking', 'user_segmentation'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['edge_side_experiments'],
            first_seen="2010-01-01",
            last_updated=datetime.now().isoformat()
        )
        
        # Marketing Automation
        self.trackers['hubspot'] = TrackerPattern(
            name="HubSpot",
            category="marketing_automation",
            risk_level="medium",
            patterns=[
                r'_hsq\.push',
                r'hubspot',
                r'js\.hs-scripts\.com',
                r'forms\.hubspot\.com'
            ],
            domains=['js.hs-scripts.com', 'forms.hubspot.com', 'hubspot.com'],
            description="Inbound marketing and CRM platform",
            data_types=['lead_tracking', 'email_engagement', 'form_submissions'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['progressive_profiling'],
            first_seen="2006-06-01",
            last_updated=datetime.now().isoformat()
        )
        
        # Performance Monitoring
        self.trackers['newrelic'] = TrackerPattern(
            name="New Relic",
            category="performance",
            risk_level="low",
            patterns=[
                r'NREUM',
                r'newrelic',
                r'js-agent\.newrelic\.com'
            ],
            domains=['js-agent.newrelic.com', 'bam.nr-data.net'],
            description="Application performance monitoring",
            data_types=['performance_metrics', 'error_tracking', 'user_timing'],
            gdpr_relevant=False,
            ccpa_relevant=False,
            detection_method="javascript",
            evasion_techniques=['custom_attributes'],
            first_seen="2008-01-01",
            last_updated=datetime.now().isoformat()
        )
        
        # Privacy Invasive Techniques
        self.trackers['canvas_fingerprinting'] = TrackerPattern(
            name="Canvas Fingerprinting",
            category="privacy_invasion",
            risk_level="critical",
            patterns=[
                r'canvas\.toDataURL',
                r'getContext\s*\(\s*["\']2d["\']',
                r'canvas\.getImageData',
                r'measureText'
            ],
            domains=[],
            description="Browser fingerprinting via canvas element",
            data_types=['device_fingerprint', 'browser_fingerprint'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['noise_injection', 'permission_prompts'],
            first_seen="2012-01-01",
            last_updated=datetime.now().isoformat()
        )
        
        self.trackers['webrtc_leak'] = TrackerPattern(
            name="WebRTC IP Leak",
            category="privacy_invasion",
            risk_level="critical",
            patterns=[
                r'RTCPeerConnection',
                r'webkitRTCPeerConnection',
                r'mozRTCPeerConnection'
            ],
            domains=[],
            description="IP address detection via WebRTC STUN servers",
            data_types=['real_ip_address', 'network_information'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['webrtc_blocking'],
            first_seen="2013-01-01",
            last_updated=datetime.now().isoformat()
        )
        
        # Ad Networks and Exchanges
        self.trackers['criteo'] = TrackerPattern(
            name="Criteo",
            category="advertising",
            risk_level="high",
            patterns=[
                r'criteo',
                r'cas\.criteo\.com',
                r'static\.criteo\.net'
            ],
            domains=['cas.criteo.com', 'static.criteo.net', 'dis.criteo.com'],
            description="Personalized retargeting platform",
            data_types=['shopping_behavior', 'product_affinity', 'purchase_intent'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['first_party_data'],
            first_seen="2005-01-01",
            last_updated=datetime.now().isoformat()
        )
        
        # Additional patterns for emerging trackers
        self.trackers['tiktok_shop_pixel'] = TrackerPattern(
            name="TikTok Shop Pixel",
            category="e_commerce",
            risk_level="high",
            patterns=[
                r'ttq\.track\s*\(\s*["\']CompletePayment["\']',
                r'ttq\.track\s*\(\s*["\']AddToCart["\']',
                r'shop\.tiktok\.com'
            ],
            domains=['shop.tiktok.com', 'analytics.tiktok.com'],
            description="TikTok's e-commerce tracking pixel",
            data_types=['purchase_behavior', 'shopping_cart', 'product_views'],
            gdpr_relevant=True,
            ccpa_relevant=True,
            detection_method="javascript",
            evasion_techniques=['server_side_api'],
            first_seen="2021-01-01",
            last_updated=datetime.now().isoformat()
        )

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
