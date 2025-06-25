# PixelTracker - Advanced Tracking Detection Suite

A comprehensive Python toolkit for detecting tracking pixels, JavaScript trackers, and privacy invasive technologies across websites. PixelTracker combines basic detection capabilities with advanced machine learning and behavioral analysis to provide deep insights into web tracking.

## 🚀 Features

### Core Detection Capabilities
- **Tracking Pixel Detection**: Identifies 1x1 pixel images, hidden iframes, base64 encoded pixels, and other tracking pixel patterns
- **JavaScript Tracker Detection**: Finds external scripts and inline JavaScript code from 100+ tracking patterns
- **Meta Tag Analysis**: Detects tracking verification tags and social media meta tags
- **CSS Background Tracking**: Identifies tracking pixels loaded via CSS background images
- **Advanced Fingerprinting Detection**: Canvas fingerprinting, WebRTC leaks, font enumeration
- **Comprehensive Domain Database**: Includes 150+ known tracking domains across all major platforms

### Enhanced Scanning (New!)
- **Machine Learning Analysis**: Optional ML-powered domain clustering and behavioral analysis
- **Asynchronous Scanning**: Concurrent requests for faster bulk scanning
- **JavaScript Execution**: Browser automation for dynamic content analysis
- **Performance Metrics**: Detailed timing and response analysis
- **Intelligence Database**: SQLite storage for tracking patterns and scan history

### Configuration & Management
- **Flexible Configuration**: YAML/JSON configuration files with validation
- **Rate Limiting**: Configurable delays to respect target servers
- **Session Management**: Connection pooling and retry strategies
- **Logging System**: Comprehensive logging with file and console output
- **Dependency Management**: Tiered requirements (core, ML, enterprise)

### Reporting & Analysis
- **Privacy Scoring**: Advanced privacy impact assessment (0-100 scale)
- **Risk Categorization**: Low/Medium/High risk level classification
- **Interactive HTML Reports**: Beautiful dashboards with detailed breakdowns
- **Multiple Export Formats**: JSON, HTML, CSV output options
- **Batch Processing**: Scan multiple URLs with aggregate statistics
- **Threat Intelligence**: Behavioral analysis and anomaly detection

## 🛠️ Installation

### Quick Start (Core Features)
```bash
# Install core dependencies only
pip install -r requirements-core.txt
```

### Full Installation (All Features)
```bash
# Install core + ML dependencies
pip install -r requirements-core.txt
pip install -r requirements-ml.txt
```

### Enterprise Installation
```bash
# Install all dependencies including monitoring and databases
pip install -r requirements-enterprise.txt
```

### Verify Installation
```bash
python pixeltracker.py info --dependencies
```

## 📟 Usage

### Unified CLI Tool (Recommended)
PixelTracker now includes a unified CLI tool that combines both basic and enhanced scanning capabilities:

#### Basic Scanning
```bash
# Simple scan
python pixeltracker.py scan example.com

# Multiple URLs with verbose output
python pixeltracker.py scan example.com facebook.com --verbose

# Save results to file
python pixeltracker.py scan example.com --output results.json

# Generate detailed HTML report
python pixeltracker.py scan example.com --detailed-report report.html
```

#### Enhanced Scanning (with ML and Advanced Features)
```bash
# Enhanced scan with machine learning
python pixeltracker.py scan --enhanced example.com

# Enhanced scan with JavaScript execution
python pixeltracker.py scan --enhanced --enable-js example.com

# High-speed concurrent scanning
python pixeltracker.py scan --enhanced --concurrent 20 example.com facebook.com google.com

# Custom rate limiting
python pixeltracker.py scan --rate-limit 0.5 example.com
```

#### Configuration Management
```bash
# Create sample configuration file
python pixeltracker.py config --create-sample myconfig.yaml

# Validate configuration
python pixeltracker.py config --validate myconfig.yaml

# Show default configuration
python pixeltracker.py config --show-defaults

# Use custom configuration
python pixeltracker.py scan --config myconfig.yaml example.com
```

#### System Information
```bash
# Check dependencies
python pixeltracker.py info --dependencies

# Show tracked domains count
python pixeltracker.py info --domains
```

### Legacy Scripts (Still Available)
The original scanners can still be used directly:

```bash
# Basic scanner
python tracking_pixel_scanner.py example.com --verbose

# Enhanced scanner
python enhanced_tracking_scanner.py --enable-js example.com
```

## What It Detects

### Tracking Pixels
- 1x1 pixel images (width=1, height=1)
- 0x0 pixel images  
- Base64 encoded tracking pixels
- Images with tracking-related URLs
- Images inside `<noscript>` tags
- Hidden iframes
- CSS background image trackers

### JavaScript Trackers (70+ Patterns)
- **Google**: Analytics (ga, gtag, _gaq), Tag Manager (dataLayer), AdServices
- **Facebook/Meta**: Pixel (fbq), Connect scripts
- **Adobe**: Analytics (s.t, s.tl), Demdex, Omniture
- **Social Media**: Twitter (twq), LinkedIn, Pinterest (pintrk), Snapchat (snaptr), TikTok (ttq)
- **Analytics**: Mixpanel, Amplitude, Segment, Heap, Kissmetrics
- **User Experience**: Hotjar (hj), FullStory (FS), Crazy Egg, Mouseflow
- **Marketing**: HubSpot (_hsq), Marketo, Pardot, Mailchimp
- **Support**: Intercom, Drift, Zendesk, Olark
- **Performance**: New Relic (NREUM), Sentry, Rollbar, Bugsnag
- **A/B Testing**: Optimizely, VWO
- **Attribution**: Branch, AppsFlyer, Adjust
- **Generic**: track(), pageview, event(), utm_ parameters

### Meta Tag Tracking
- Site verification tags (Google, Facebook, Bing, Pinterest, Yandex, Baidu)
- Open Graph properties (og:*)
- Twitter Card metadata
- Facebook app IDs

### CSS-Based Tracking
- Background images from tracking domains
- Inline style tracking pixels
- External stylesheet references

### Comprehensive Domain Coverage (150+ Domains)
**Major Platforms:**
- Google/Alphabet: Analytics, Tag Manager, AdServices, DoubleClick
- Facebook/Meta: Pixel, Connect, Instagram
- Amazon: Ad System, CloudFront
- Microsoft: Bing Ads, MSN, Live
- Adobe: Analytics, Omniture, Demdex

**Analytics & Metrics:**
- Mixpanel, Amplitude, Segment, Heap, Quantcast, Chartbeat
- New Relic, Sentry, Rollbar, Bugsnag, LogRocket

**Social Media:**
- LinkedIn, Twitter, Pinterest, Snapchat, TikTok, Reddit, Tumblr

**Ad Networks:**
- Criteo, Outbrain, Taboola, Adroll, OpenX, Rubicon Project
- DoubleVerify, Moat, Quantcast, BlueKai

**Marketing Automation:**
- HubSpot, Marketo, Salesforce, Mailchimp, Klaviyo, ActiveCampaign

**User Experience:**
- Hotjar, FullStory, Crazy Egg, Mouseflow, Optimizely, VWO

**Support & Feedback:**
- Intercom, Drift, Zendesk, UserVoice, Olark, Freshworks

## Output Format

The tool provides both human-readable output and detailed JSON reports:

```
✅ https://example.com
   📊 Found 2 tracking pixels
   🔧 Found 3 JavaScript trackers
   🌐 Tracking domains: google-analytics.com, facebook.com
```

JSON output includes detailed information about each tracker found, including full HTML elements, tracking domains, and categorization.

## Detailed Reporting

The tool now includes comprehensive reporting features for in-depth analysis:

### HTML Reports
Generate beautiful, interactive HTML reports with:
- **Visual Dashboard**: Summary cards showing tracker counts by type
- **Privacy Analysis**: Privacy score (0-100) and risk level assessment
- **Category Detection**: Identifies advertising, analytics, social media, and other tracking categories
- **Domain Risk Assessment**: Highlights high-risk tracking domains
- **Privacy Recommendations**: Actionable advice based on detected trackers
- **Detailed Breakdowns**: Full element analysis with source URLs and patterns

### Enhanced JSON Reports
Produce comprehensive JSON reports featuring:
- **Aggregate Statistics**: Total sites scanned, trackers found, unique domains
- **Privacy Analysis**: Scoring and categorization of tracking risks
- **Metadata**: Scan timestamps, tool version, and report generation info
- **Complete Data**: All raw detection data for programmatic analysis

### Privacy Scoring System
The tool calculates a privacy score (0-100) based on:
- **Tracking Pixel Count**: Each pixel reduces the score
- **JavaScript Trackers**: External scripts penalized more heavily than inline
- **High-Risk Domains**: Advertising and social media trackers significantly impact score
- **Risk Categories**: Low (80+), Medium (50-80), High (<50)

### Example Report Output
```
📊 Scan Summary:
   🌐 Sites scanned: 2
   📈 Total trackers found: 55
   🎯 Unique tracking domains: 4
   📋 Detailed report: comprehensive_report.html
```

## Technical Details

- Uses BeautifulSoup for HTML parsing
- Requests library for HTTP fetching
- Regular expressions for pattern matching
- Handles both visible and hidden tracking elements
- Respects robots.txt and uses appropriate User-Agent headers

## Privacy Note

This tool is designed for legitimate security research, privacy auditing, and website analysis. Always respect website terms of service and applicable laws when using this tool.
