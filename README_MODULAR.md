# PixelTracker 2.0 - Modular Architecture

This document describes the new modular architecture of PixelTracker, focusing on the refactored `pixeltracker/` package with clean interfaces, dependency injection, and comprehensive type hints.

## 🏗️ Architecture Overview

The new PixelTracker follows a modular, service-oriented architecture with clear separation of concerns:

```
pixeltracker/
├── __init__.py              # Package exports
├── interfaces.py            # Abstract interfaces and protocols
├── models.py               # Data models with type hints
├── config.py               # Configuration management
├── services/               # Core service implementations
│   ├── __init__.py
│   ├── network.py          # Network/HTTP operations
│   ├── parser.py           # HTML parsing and analysis
│   ├── storage.py          # Data persistence
│   ├── analyzer.py         # Privacy impact analysis
│   └── reporter.py         # Report generation
└── scanners/               # Scanner implementations
    ├── __init__.py
    ├── basic.py            # Basic tracking scanner
    └── enhanced.py         # Enhanced scanner with ML
```

## 🎯 Key Features

### ✅ Dependency Injection
All services implement clear interfaces, enabling easy testing and customization:

```python
# Use default services
scanner = BasicTrackingScanner()

# Or inject custom implementations
scanner = BasicTrackingScanner(
    fetcher=CustomNetworkService(),
    parser=CustomParser(),
    analyzer=MLAnalyzer()
)
```

### ✅ Type Safety
Comprehensive type hints throughout with mypy validation:

```python
async def scan_url(self, url: str) -> ScanResult:
    """Scan URL with full type safety"""
    ...
```

### ✅ Clean Interfaces
Protocol-based interfaces for easy mocking and testing:

```python
class Fetcher(Protocol):
    async def fetch(self, url: str, **kwargs) -> Dict[str, Any]: ...
    def set_headers(self, headers: Dict[str, str]) -> None: ...
```

### ✅ Configuration Management
Type-safe configuration with validation:

```python
config = ConfigManager()
config.set("scanning.rate_limit_delay", 1.5)
config.validate()  # Type checking and validation
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from pixeltracker import BasicTrackingScanner

async def main():
    scanner = BasicTrackingScanner()
    result = await scanner.scan_url("https://example.com")
    
    print(f"Found {result.tracker_count} trackers")
    print(f"Privacy score: {result.privacy_analysis.privacy_score}/100")

asyncio.run(main())
```

### Custom Configuration

```python
from pixeltracker import ConfigManager, BasicTrackingScanner

# Load custom config
config = ConfigManager("my_config.yaml")

# Or create programmatically
config = ConfigManager()
config.scanning.rate_limit_delay = 2.0
config.scanning.concurrent_requests = 3
config.javascript.enabled = True

scanner = BasicTrackingScanner(config_manager=config)
```

### Dependency Injection

```python
from pixeltracker.services import NetworkService, HTMLParserService

# Create custom services
custom_fetcher = NetworkService(scan_config)
custom_parser = HTMLParserService()

# Inject into scanner
scanner = BasicTrackingScanner(
    fetcher=custom_fetcher,
    parser=custom_parser
)
```

## 🧪 Testing

The modular design makes testing straightforward with mock services:

```python
class MockFetcher:
    async def fetch(self, url: str, **kwargs):
        return {'content': '<html>test</html>', 'metrics': {}}

scanner = BasicTrackingScanner(fetcher=MockFetcher())
```

Run tests:
```bash
pytest tests/test_modular.py -v
```

## 🔧 Development Tools

### Type Checking
```bash
mypy pixeltracker/
```

### Linting
```bash
ruff pixeltracker/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## 📊 Core Interfaces

### Fetcher
Handles HTTP requests and content fetching:
- `fetch(url)` - Fetch content from URL
- `set_headers()` - Configure request headers
- `set_timeout()` - Set request timeout

### Parser  
Parses HTML content for tracking elements:
- `parse(content, url)` - Main parsing method
- `find_tracking_pixels()` - Find pixel trackers
- `find_javascript_trackers()` - Find JS trackers

### Storage
Handles data persistence:
- `store_result()` - Store scan results
- `retrieve_results()` - Query stored results
- `store_tracker_pattern()` - Store tracker patterns

### Analyzer
Analyzes privacy impact:
- `analyze_privacy_impact()` - Full privacy analysis
- `calculate_privacy_score()` - Calculate 0-100 score
- `assess_risks()` - Risk assessment

### Reporter
Generates reports in various formats:
- `generate_report()` - Create formatted reports
- `export_data()` - Export to files
- `generate_summary()` - Create summaries

## 🎨 Configuration Structure

```yaml
scanning:
  rate_limit_delay: 1.0
  request_timeout: 30.0
  concurrent_requests: 10

javascript:
  enabled: false
  wait_time: 3.0

detection:
  sensitivity: medium
  enable_ml_clustering: false

privacy:
  scoring_weights:
    tracking_pixel: 5
    external_script: 8

output:
  formats: [json, html]
  include_raw_html: false

database:
  enabled: true
  path: "pixeltracker.db"
```

## 📈 Migration from Legacy

The new modular structure maintains backward compatibility while providing enhanced capabilities:

### Legacy Usage (still works)
```python
from tracking_pixel_scanner import TrackingPixelScanner
scanner = TrackingPixelScanner()
```

### New Modular Usage  
```python
from pixeltracker import BasicTrackingScanner
scanner = BasicTrackingScanner()
```

## 🛠️ Extending the System

### Custom Service Implementation

```python
from pixeltracker.interfaces import Parser
from typing import List, Dict, Any

class MyCustomParser(Parser):
    def parse(self, content: str, url: str = "") -> Dict[str, Any]:
        # Custom parsing logic
        return {"pixels": [], "js_trackers": []}
    
    def find_tracking_pixels(self, content: str) -> List[Dict[str, Any]]:
        # Custom pixel detection
        return []

# Use in scanner
scanner = BasicTrackingScanner(parser=MyCustomParser())
```

### Custom Analyzer

```python
from pixeltracker.interfaces import Analyzer

class MLAnalyzer(Analyzer):
    def analyze_privacy_impact(self, trackers, **kwargs):
        # Advanced ML-based analysis
        return {"privacy_score": 85, "risk_level": "low"}

scanner = BasicTrackingScanner(analyzer=MLAnalyzer())
```

## 📚 Examples

See the `examples/` directory for complete usage examples:
- `basic_usage.py` - Basic scanning and configuration
- `custom_services.py` - Dependency injection examples
- `advanced_analysis.py` - Advanced analysis features

## 🔍 Development Workflow

1. **Setup environment**:
   ```bash
   pip install -r requirements-core.txt
   pre-commit install
   ```

2. **Run type checking**:
   ```bash
   mypy pixeltracker/
   ```

3. **Run linting**:
   ```bash
   ruff pixeltracker/
   ```

4. **Run tests**:
   ```bash
   pytest tests/ -v --cov=pixeltracker
   ```

5. **Format code**:
   ```bash
   black pixeltracker/
   isort pixeltracker/
   ```

This modular architecture provides a solid foundation for future enhancements while maintaining clean, testable, and type-safe code.
