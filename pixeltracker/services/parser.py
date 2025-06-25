#!/usr/bin/env python3
"""
HTML parser service for PixelTracker

Provides mechanisms to parse HTML content and find tracking elements.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any
from ..interfaces import Parser
import re
import logging

logger = logging.getLogger(__name__)


class HTMLParserService(Parser):
    """HTML parser service for detecting tracking components"""
    
    def __init__(self) -> None:
        self.tracking_domains = [
            'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
            'facebook.com', 'connect.facebook.net', 'criteo.com', 'mixpanel.com'
        ]
    
    def parse(self, content: str, url: str = "") -> Dict[str, Any]:
        """Parse HTML content for tracking elements"""
        return {
            'pixels': self.find_tracking_pixels(content),
            'js_trackers': self.find_javascript_trackers(content),
            'meta_trackers': self.find_meta_trackers(content)
        }

    def find_tracking_pixels(self, content: str) -> List[Dict[str, Any]]:
        """Find tracking pixels in HTML content"""
        soup = BeautifulSoup(content, 'html.parser')
        pixels = []
        
        # Find img tags that might be pixels
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            width = img.get('width', '')
            height = img.get('height', '')
            
            # Check for 1x1 pixels or tracking domains
            is_pixel = (width == '1' and height == '1') or any(domain in src for domain in self.tracking_domains)
            
            if is_pixel:
                pixels.append({
                    'element_type': 'img',
                    'src': src,
                    'width': width,
                    'height': height,
                    'is_1x1_pixel': width == '1' and height == '1',
                    'tracking_domain': next((d for d in self.tracking_domains if d in src), None)
                })
        
        return pixels

    def find_javascript_trackers(self, content: str) -> List[Dict[str, Any]]:
        """Find JavaScript-based tracking code"""
        soup = BeautifulSoup(content, 'html.parser')
        trackers = []
        scripts = soup.find_all('script')
        
        tracking_patterns = [
            r'ga\s*\(',  # Google Analytics
            r'fbq\s*\(',  # Facebook Pixel
            r'gtag\s*\(',  # Google gtag
            r'mixpanel\.',  # Mixpanel
            r'_gaq\.push',  # Legacy GA
        ]
        
        for script in scripts:
            script_src = script.get('src', '')
            script_content = script.string or ''
            
            # Check external scripts for tracking domains
            for domain in self.tracking_domains:
                if domain in script_src:
                    trackers.append({
                        'type': 'external_script',
                        'domain': domain,
                        'src': script_src
                    })
                    break
            
            # Check inline scripts for tracking patterns
            for pattern in tracking_patterns:
                if re.search(pattern, script_content, re.IGNORECASE):
                    trackers.append({
                        'type': 'inline_script',
                        'pattern': pattern,
                        'content_snippet': script_content[:100]
                    })
                    break
        
        return trackers

    def find_meta_trackers(self, content: str) -> List[Dict[str, Any]]:
        """Find meta tag trackers"""
        soup = BeautifulSoup(content, 'html.parser')
        meta_tags = soup.find_all('meta')
        meta_trackers = []
        
        tracking_meta_names = [
            'google-site-verification',
            'facebook-domain-verification',
            'msvalidate.01',
            'pinterest-site-verification'
        ]
        
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content_attr = meta.get('content', '')
            
            # Check for verification meta tags
            if name in tracking_meta_names or property_attr in tracking_meta_names:
                meta_trackers.append({
                    'type': 'verification_meta',
                    'name': name or property_attr,
                    'content': content_attr
                })
            
            # Check for Open Graph and social meta tags
            elif property_attr.startswith(('og:', 'twitter:', 'fb:')):
                meta_trackers.append({
                    'type': 'social_meta',
                    'property': property_attr,
                    'content': content_attr
                })
        
        return meta_trackers

