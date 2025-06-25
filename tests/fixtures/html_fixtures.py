#!/usr/bin/env python3
"""
HTML fixtures for testing various tracker scenarios

Contains HTML templates with different types of tracking pixels and scripts
for comprehensive testing of tracker detection capabilities.
"""

# Basic tracking pixel
BASIC_TRACKING_PIXEL = """
<!DOCTYPE html>
<html>
<head>
    <title>Basic Tracking Pixel Test</title>
</head>
<body>
    <h1>Test Page</h1>
    <p>This page contains a basic tracking pixel.</p>
    <img src="https://tracker.example.com/pixel.gif" width="1" height="1" style="display:none;">
</body>
</html>
"""

# Multiple tracking pixels
MULTIPLE_TRACKING_PIXELS = """
<!DOCTYPE html>
<html>
<head>
    <title>Multiple Tracking Pixels Test</title>
</head>
<body>
    <h1>Test Page with Multiple Trackers</h1>
    <p>This page contains multiple tracking pixels.</p>
    <img src="https://analytics.google.com/collect" width="1" height="1" style="display:none;">
    <img src="https://facebook.com/tr" width="1" height="1" style="display:none;">
    <img src="https://doubleclick.net/pixel" width="1" height="1" style="display:none;">
</body>
</html>
"""

# JavaScript trackers
JAVASCRIPT_TRACKERS = """
<!DOCTYPE html>
<html>
<head>
    <title>JavaScript Trackers Test</title>
    <script>
        // Google Analytics
        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');
    </script>
</head>
<body>
    <h1>Test Page with JavaScript Trackers</h1>
    <p>This page contains JavaScript-based tracking.</p>
    <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
    <script>
        fbq('init', '1234567890');
        fbq('track', 'PageView');
    </script>
</body>
</html>
"""

# Meta tag trackers
META_TAG_TRACKERS = """
<!DOCTYPE html>
<html>
<head>
    <title>Meta Tag Trackers Test</title>
    <meta name="google-site-verification" content="abc123def456">
    <meta name="facebook-domain-verification" content="xyz789">
    <meta name="msvalidate.01" content="validation-code">
</head>
<body>
    <h1>Test Page with Meta Tag Trackers</h1>
    <p>This page contains meta tag verification trackers.</p>
</body>
</html>
"""

# Hidden iframe trackers
IFRAME_TRACKERS = """
<!DOCTYPE html>
<html>
<head>
    <title>Iframe Trackers Test</title>
</head>
<body>
    <h1>Test Page with Iframe Trackers</h1>
    <p>This page contains hidden iframe trackers.</p>
    <iframe src="https://tracker.example.com/track" width="0" height="0" style="display:none;"></iframe>
    <iframe src="https://doubleclick.net/activityi" width="1" height="1" frameborder="0" style="display:none;"></iframe>
</body>
</html>
"""

# Clean page with no trackers
CLEAN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Clean Page Test</title>
</head>
<body>
    <h1>Clean Test Page</h1>
    <p>This page contains no tracking pixels or scripts.</p>
    <img src="https://example.com/logo.png" alt="Logo">
    <script>
        console.log('This is a clean script');
    </script>
</body>
</html>
"""

# Complex page with mixed content
COMPLEX_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Complex Page Test</title>
    <meta name="google-site-verification" content="complex-verification">
    <script src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'GA_MEASUREMENT_ID');
    </script>
</head>
<body>
    <h1>Complex Test Page</h1>
    <p>This page contains various types of tracking mechanisms.</p>
    
    <!-- Tracking pixels -->
    <img src="https://analytics.google.com/collect?v=1&tid=UA-123456-1" width="1" height="1" style="display:none;">
    <img src="https://facebook.com/tr?id=123456789&ev=PageView" width="1" height="1" style="display:none;">
    
    <!-- JavaScript trackers -->
    <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
    <script>
        fbq('init', '123456789');
        fbq('track', 'PageView');
    </script>
    
    <!-- Hidden iframe -->
    <iframe src="https://doubleclick.net/activityi;src=123456;type=example" width="1" height="1" style="display:none;"></iframe>
    
    <!-- Regular content -->
    <img src="https://example.com/image.jpg" alt="Regular image">
    <script>
        // Regular JavaScript
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Page loaded');
        });
    </script>
</body>
</html>
"""

# Social media trackers
SOCIAL_MEDIA_TRACKERS = """
<!DOCTYPE html>
<html>
<head>
    <title>Social Media Trackers Test</title>
</head>
<body>
    <h1>Test Page with Social Media Trackers</h1>
    <p>This page contains social media tracking pixels.</p>
    
    <!-- Facebook Pixel -->
    <img src="https://www.facebook.com/tr?id=123456789&ev=PageView&noscript=1" width="1" height="1" style="display:none;">
    
    <!-- Twitter Pixel -->
    <img src="https://analytics.twitter.com/i/adsct?txn_id=123456&p_id=Twitter" width="1" height="1" style="display:none;">
    
    <!-- LinkedIn Insight Tag -->
    <img src="https://px.ads.linkedin.com/collect/?pid=123456&fmt=gif" width="1" height="1" style="display:none;">
    
    <!-- Pinterest Pixel -->
    <img src="https://ct.pinterest.com/v3/?tid=123456&event=pagevisit" width="1" height="1" style="display:none;">
</body>
</html>
"""

# E-commerce trackers
ECOMMERCE_TRACKERS = """
<!DOCTYPE html>
<html>
<head>
    <title>E-commerce Trackers Test</title>
</head>
<body>
    <h1>Test Page with E-commerce Trackers</h1>
    <p>This page contains e-commerce tracking pixels.</p>
    
    <!-- Amazon Pixel -->
    <img src="https://s.amazon-adsystem.com/iu3?pid=123456&cid=A123456789" width="1" height="1" style="display:none;">
    
    <!-- eBay Pixel -->
    <img src="https://rover.ebay.com/roverimp/0/0/9?trknvp=123456" width="1" height="1" style="display:none;">
    
    <!-- Shopify Pixel -->
    <img src="https://monorail-edge.shopifysvc.com/v1/produce?shop=example.myshopify.com" width="1" height="1" style="display:none;">
</body>
</html>
"""

# Fixture mapping for easy access
HTML_FIXTURES = {
    'basic_pixel': BASIC_TRACKING_PIXEL,
    'multiple_pixels': MULTIPLE_TRACKING_PIXELS,
    'javascript_trackers': JAVASCRIPT_TRACKERS,
    'meta_trackers': META_TAG_TRACKERS,
    'iframe_trackers': IFRAME_TRACKERS,
    'clean_page': CLEAN_PAGE,
    'complex_page': COMPLEX_PAGE,
    'social_media': SOCIAL_MEDIA_TRACKERS,
    'ecommerce': ECOMMERCE_TRACKERS,
}

def get_fixture(name):
    """Get HTML fixture by name"""
    return HTML_FIXTURES.get(name, CLEAN_PAGE)

def get_all_fixtures():
    """Get all HTML fixtures"""
    return HTML_FIXTURES
