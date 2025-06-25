#!/usr/bin/env python3
"""
Test script for the comprehensive tracker database
"""

from tracker_database import tracker_db

def test_basic_functionality():
    """Test basic tracker database functionality"""
    print("🧪 Testing Comprehensive Tracker Database\n")
    
    # Test database statistics
    stats = tracker_db.get_statistics()
    print(f"📊 Database Statistics:")
    print(f"   Total trackers: {stats['total_trackers']}")
    print(f"   Total domains: {stats['total_domains']}")
    print(f"   Total patterns: {stats['total_patterns']}")
    print(f"   GDPR relevant: {stats['gdpr_relevant_count']}")
    print(f"   CCPA relevant: {stats['ccpa_relevant_count']}")
    
    # Test pattern detection
    print(f"\n🔍 Testing Pattern Detection:")
    
    # Test content with Google Analytics
    ga_content = """
    <script>
    gtag('config', 'GA_MEASUREMENT_ID');
    gtag('event', 'page_view');
    </script>
    """
    
    detected = tracker_db.detect_trackers(ga_content)
    print(f"   Google Analytics detection: {len(detected)} matches")
    for tracker in detected:
        print(f"      - {tracker['name']}: {tracker['category']} ({tracker['risk_level']} risk)")
    
    # Test content with Facebook Pixel
    fb_content = """
    <script>
    fbq('init', '123456789');
    fbq('track', 'PageView');
    </script>
    """
    
    detected = tracker_db.detect_trackers(fb_content)
    print(f"   Facebook Pixel detection: {len(detected)} matches")
    for tracker in detected:
        print(f"      - {tracker['name']}: {tracker['category']} ({tracker['risk_level']} risk)")
    
    # Test content with canvas fingerprinting
    canvas_content = """
    <script>
    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext('2d');
    var fingerprint = canvas.toDataURL();
    </script>
    """
    
    detected = tracker_db.detect_trackers(canvas_content)
    print(f"   Canvas fingerprinting detection: {len(detected)} matches")
    for tracker in detected:
        print(f"      - {tracker['name']}: {tracker['category']} ({tracker['risk_level']} risk)")
    
    # Test category filtering
    print(f"\n📂 Testing Category Filtering:")
    advertising_trackers = tracker_db.get_trackers_by_category('advertising')
    print(f"   Advertising trackers: {len(advertising_trackers)}")
    
    social_trackers = tracker_db.get_trackers_by_category('social_advertising')
    print(f"   Social advertising trackers: {len(social_trackers)}")
    
    privacy_invasion_trackers = tracker_db.get_trackers_by_category('privacy_invasion')
    print(f"   Privacy invasion trackers: {len(privacy_invasion_trackers)}")
    
    # Test risk level filtering
    print(f"\n⚠️  Testing Risk Level Filtering:")
    high_risk_trackers = tracker_db.get_high_risk_trackers()
    print(f"   High/Critical risk trackers: {len(high_risk_trackers)}")
    for tracker in high_risk_trackers[:5]:  # Show first 5
        print(f"      - {tracker.name}: {tracker.risk_level} risk")
    
    # Test domain lookup
    print(f"\n🌐 Testing Domain Lookup:")
    test_domains = ['google-analytics.com', 'facebook.com', 'hotjar.com']
    for domain in test_domains:
        tracker = tracker_db.get_tracker_by_domain(domain)
        if tracker:
            print(f"   {domain}: {tracker.name} ({tracker.category})")
        else:
            print(f"   {domain}: Not found")
    
    print(f"\n✅ All tests completed!")

if __name__ == "__main__":
    test_basic_functionality()
