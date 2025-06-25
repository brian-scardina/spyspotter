# PixelTracker Testing Infrastructure

This document describes the comprehensive testing infrastructure implemented for PixelTracker.

## Overview

The testing infrastructure provides 100% coverage of pure logic through unit tests, HTTP mocking for predictable testing, integration tests with a test server, and performance benchmarks with regression thresholds.

## Test Structure

```
tests/
├── __init__.py                     # Test package configuration
├── test_runner.py                  # Comprehensive test runner
├── pytest.ini                     # Pytest configuration
├── unit/                           # Unit tests (100% coverage goal)
│   ├── models/                     # Model tests
│   │   └── test_models.py         # TrackerInfo, ScanResult, etc.
│   ├── services/                   # Service tests with mocking
│   │   ├── test_network_service.py # HTTP mocking with responses
│   │   └── test_services_mocked.py # All services with mocks
│   └── scanners/                   # Scanner tests
│       ├── test_basic_scanner.py   # BasicTrackingScanner tests
│       └── test_enhanced_scanner.py # EnhancedTrackingScanner tests
├── integration/                    # End-to-end integration tests
│   └── test_e2e_scanning.py       # aiohttp test server scenarios
├── performance/                    # Performance and benchmark tests
│   └── test_benchmarks.py         # pytest-benchmark tests
├── fixtures/                       # Test data and HTML fixtures
│   └── html_fixtures.py           # HTML samples with various trackers
└── legacy/                         # Existing test files
    ├── test_basic.py
    └── test_modular.py
```

## Testing Components

### 1. Unit Tests (100% Coverage)

**Location**: `tests/unit/`

- **Models**: Complete testing of all data models including serialization/deserialization
- **Services**: All service classes tested with mocked dependencies
- **Scanners**: Scanner logic tested with dependency injection
- **Coverage Target**: 100% of pure logic, 85% minimum threshold

**Key Features**:
- Uses `pytest` as the test framework
- `pytest-cov` for coverage reporting
- Comprehensive mocking with `unittest.mock`
- Parametrized tests for edge cases

### 2. HTTP Mocking

**Libraries Used**:
- `responses` - For requests library mocking
- `requests-mock` - Alternative HTTP mocking
- `aioresponses` - For async HTTP mocking

**HTML Fixtures**:
- Basic tracking pixels
- Multiple tracker scenarios
- JavaScript-based trackers
- Meta tag trackers
- iframe trackers
- Social media trackers
- E-commerce trackers
- Clean pages (no trackers)

**Location**: `tests/fixtures/html_fixtures.py`

### 3. Integration Tests

**Location**: `tests/integration/test_e2e_scanning.py`

**Features**:
- Lightweight `aiohttp` test server
- Dynamic page generation with configurable tracker counts
- End-to-end scanning pipeline testing
- Concurrent scanning tests
- Error handling validation
- CLI integration tests (framework ready)

**Test Scenarios**:
- Clean pages (no trackers)
- Single tracker detection
- Multiple tracker detection
- Complex pages with mixed tracker types
- Dynamic tracker count validation
- Error handling for invalid URLs
- Performance metrics collection

### 4. Performance & Benchmark Tests

**Location**: `tests/performance/test_benchmarks.py`

**Tools Used**:
- `pytest-benchmark` - For micro-benchmarks
- `asv` (Airspeed Velocity) - For long-term performance tracking
- `memory-profiler` - For memory usage analysis
- `psutil` - For system resource monitoring

**Benchmark Categories**:
- **Scanning Performance**: Basic vs Enhanced scanner timing
- **Memory Usage**: Single scan and multi-scan memory profiling
- **Scalability**: Large HTML parsing, high concurrency
- **Regression Thresholds**: Automated performance regression detection

**ASV Configuration**:
- Configuration file: `asv.conf.json`
- Benchmark suite: `benchmarks/benchmark_suite.py`
- Tracks performance across commits and Python versions

### 5. Automation & CI/CD

**Makefile Commands**:
```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-performance  # Performance tests only
make benchmark         # Run benchmarks
make coverage          # Generate coverage report
make coverage-html     # HTML coverage report
make coverage-badge    # Generate coverage badge
make lint              # Code quality checks
make clean             # Clean build artifacts
```

**Test Runner**: `tests/test_runner.py`
- Comprehensive test execution
- Multiple test modes (unit, integration, performance)
- Parallel test execution
- Coverage reporting
- Benchmark execution

## Coverage & Quality

### Coverage Configuration

**Target**: 85% minimum, 100% goal for pure logic

**Configuration**: `pytest.ini`
```ini
[coverage:run]
source = pixeltracker
omit = */tests/*, */test_*, */__pycache__/*

[coverage:report]
exclude_lines = pragma: no cover, def __repr__, raise NotImplementedError
show_missing = True
precision = 2
```

### Performance Thresholds

**Regression Thresholds**:
- Basic scan: < 3 seconds
- Enhanced scan: < 5 seconds
- HTML parsing: < 0.05 seconds
- Memory usage: < 30MB increase per scan

## Dependencies

### Test Dependencies

**Core Testing**:
- `pytest>=7.0.0`
- `pytest-cov>=4.0.0`
- `pytest-asyncio>=0.21.0`
- `pytest-benchmark>=4.0.0`
- `pytest-xdist>=3.0.0` (parallel execution)

**HTTP Mocking**:
- `responses>=0.23.0`
- `requests-mock>=1.10.0`
- `aioresponses>=0.7.4`

**Performance Testing**:
- `asv>=0.5.1`
- `memory-profiler>=0.60.0`
- `psutil>=5.9.0`

**Test Utilities**:
- `factory-boy>=3.2.0` (test data generation)
- `faker>=18.0.0` (fake data)
- `freezegun>=1.2.0` (time mocking)

## Running Tests

### Basic Usage

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run performance benchmarks
make benchmark

# Run specific test types
make test-unit
make test-integration
make test-performance
```

### Advanced Usage

```bash
# Run tests in parallel
make test-parallel

# Run fast tests only (exclude slow tests)
make test-fast

# Generate HTML coverage report
make coverage-html

# Run with custom pytest options
pytest tests/ -v --tb=short -k "test_scanner"

# Run benchmarks with comparison
make benchmark-compare
```

### Test Runner Script

```bash
# Run comprehensive test suite
python3 tests/test_runner.py --all

# Run specific test types
python3 tests/test_runner.py --unit --integration
python3 tests/test_runner.py --performance --benchmark

# Run with options
python3 tests/test_runner.py --fast --parallel --no-coverage
```

## CI/CD Integration

The testing infrastructure is designed for CI/CD environments:

```bash
# CI test command
make ci-test

# CI benchmark command  
make ci-benchmark

# Release readiness check
make release-check
```

## Continuous Performance Monitoring

**ASV Setup**:
```bash
# Initialize ASV
asv machine --yes

# Run benchmarks
asv run

# Generate HTML report
asv publish
asv preview
```

**Benchmark Comparison**:
```bash
# Compare with previous commit
asv compare HEAD HEAD~1

# Compare with baseline
make benchmark-compare
```

## Best Practices

1. **Unit Tests**: Test pure logic, use dependency injection
2. **Integration Tests**: Test complete workflows, use test servers
3. **Performance Tests**: Set regression thresholds, monitor trends
4. **Mocking**: Use appropriate mocking libraries for HTTP requests
5. **Coverage**: Aim for 100% of business logic, exclude boilerplate
6. **Benchmarks**: Run regularly, track performance over time

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes project root
2. **Missing Dependencies**: Run `make install` or `pip install -r requirements-test.txt`
3. **Slow Tests**: Use `make test-fast` to exclude slow tests
4. **Coverage Issues**: Check excluded files in pytest.ini

### Performance Issues

1. **Memory Leaks**: Use memory profiling tests
2. **Slow Benchmarks**: Check regression thresholds
3. **Concurrency Issues**: Test with different concurrency levels

This testing infrastructure provides comprehensive coverage, performance monitoring, and quality assurance for the PixelTracker project.
