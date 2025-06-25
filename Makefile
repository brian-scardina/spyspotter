# PixelTracker Makefile
# Comprehensive testing, benchmarking, and development commands

.PHONY: help test test-unit test-integration test-performance test-all benchmark coverage coverage-html coverage-badge clean install setup lint format docs security-scan compliance-check sbom security-audit

# Default target
help:
	@echo "PixelTracker Development Commands"
	@echo "================================="
	@echo ""
	@echo "Testing:"
	@echo "  test              - Run all tests"
	@echo "  test-unit         - Run unit tests only"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-performance  - Run performance tests only"
	@echo "  test-fast         - Run fast tests (excludes slow tests)"
	@echo "  test-parallel     - Run tests in parallel"
	@echo ""
	@echo "Benchmarking:"
	@echo "  benchmark         - Run pytest benchmarks"
	@echo "  benchmark-asv     - Run ASV benchmarks"
	@echo "  benchmark-compare - Compare benchmark results"
	@echo ""
	@echo "Coverage:"
	@echo "  coverage          - Generate coverage report"
	@echo "  coverage-html     - Generate HTML coverage report"
	@echo "  coverage-badge    - Generate coverage badge"
	@echo ""
	@echo "Development:"
	@echo "  install           - Install all dependencies"
	@echo "  setup             - Setup development environment"
	@echo "  lint              - Run code linting"
	@echo "  format            - Format code"
	@echo "  clean             - Clean build artifacts"
	@echo ""
	@echo "Documentation:"
	@echo "  docs              - Generate documentation"
	@echo ""
	@echo "Security:"
	@echo "  security-scan     - Run security scan on URLs"
	@echo "  compliance-check  - Check GDPR/CCPA compliance"
	@echo "  security-audit    - Comprehensive security audit"
	@echo "  sbom              - Generate Software Bill of Materials"

# Installation and Setup
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	@echo "✅ Dependencies installed"

setup: install
	@echo "Setting up development environment..."
	pre-commit install || echo "pre-commit not available, skipping"
	@echo "✅ Development environment ready"

# Testing Commands
test: test-unit test-integration
	@echo "✅ All tests completed"

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v --tb=short -m "unit" --cov=pixeltracker --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v --tb=short -m "integration"

test-performance:
	@echo "Running performance tests..."
	pytest tests/performance/ -v --tb=short -m "performance" --benchmark-skip

test-fast:
	@echo "Running fast tests..."
	pytest tests/ -v --tb=short -m "not slow" --cov=pixeltracker --cov-report=term-missing

test-parallel:
	@echo "Running tests in parallel..."
	pytest tests/ -v --tb=short -n auto --cov=pixeltracker --cov-report=term-missing

test-all: test test-performance
	@echo "✅ All tests (including performance) completed"

# Benchmarking Commands
benchmark:
	@echo "Running pytest benchmarks..."
	pytest tests/performance/ -v --benchmark-only --benchmark-sort=mean --benchmark-columns=min,max,mean,stddev,median,rounds,iterations

benchmark-save:
	@echo "Running and saving benchmark baseline..."
	pytest tests/performance/ --benchmark-only --benchmark-save=baseline --benchmark-save-data

benchmark-compare:
	@echo "Comparing benchmarks against baseline..."
	pytest tests/performance/ --benchmark-only --benchmark-compare=baseline --benchmark-compare-fail=mean:5%

benchmark-asv:
	@echo "Running ASV benchmarks..."
	asv machine --yes
	asv run --show-stderr
	asv publish
	asv preview

benchmark-asv-compare:
	@echo "Comparing ASV benchmarks..."
	asv compare HEAD HEAD~1

# Coverage Commands
coverage:
	@echo "Generating coverage report..."
	pytest tests/ --cov=pixeltracker --cov-report=term-missing --cov-report=xml --cov-fail-under=85

coverage-html:
	@echo "Generating HTML coverage report..."
	pytest tests/ --cov=pixeltracker --cov-report=html
	@echo "✅ HTML coverage report generated in htmlcov/"

coverage-badge:
	@echo "Generating coverage badge..."
	coverage-badge -o coverage.svg -f
	@echo "✅ Coverage badge generated: coverage.svg"

# Code Quality Commands
lint:
	@echo "Running code linting..."
	ruff check pixeltracker/ tests/
	mypy pixeltracker/ --ignore-missing-imports
	@echo "✅ Linting completed"

format:
	@echo "Formatting code..."
	ruff format pixeltracker/ tests/
	@echo "✅ Code formatted"

# Documentation Commands
docs:
	@echo "Generating documentation..."
	@mkdir -p docs
	@echo "Documentation generation not yet implemented"

# Cleanup Commands
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .asv/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Build artifacts cleaned"

# CI/CD Commands (for automated environments)
ci-test:
	@echo "Running CI test suite..."
	pytest tests/ -v --tb=short --cov=pixeltracker --cov-report=xml --cov-report=term --junit-xml=junit.xml

ci-benchmark:
	@echo "Running CI benchmarks..."
	pytest tests/performance/ --benchmark-only --benchmark-json=benchmark.json

# Development Helpers
watch-tests:
	@echo "Watching for changes and running tests..."
	pytest-watch tests/ -- --tb=short -q

install-dev:
	@echo "Installing development dependencies..."
	pip install -e .
	pip install -r requirements-test.txt
	pip install pre-commit ruff mypy coverage-badge pytest-watch
	@echo "✅ Development dependencies installed"

# Database and Migration Commands (if applicable)
migrate:
	@echo "Running database migrations..."
	# Add migration commands here if needed
	@echo "No migrations to run"

# Release Commands
release-check:
	@echo "Checking release readiness..."
	@$(MAKE) test-all
	@$(MAKE) lint
	@$(MAKE) coverage
	@echo "✅ Release checks passed"

# Environment Information
info:
	@echo "Environment Information"
	@echo "======================"
	@echo "Python version: $(shell python --version)"
	@echo "Pip version: $(shell pip --version)"
	@echo "Platform: $(shell python -c 'import platform; print(platform.platform())')"
	@echo "Working directory: $(shell pwd)"
	@echo ""
	@echo "Installed packages:"
	@pip list | grep -E "(pytest|pixeltracker|requests|beautifulsoup4)" || echo "Core packages not found"

# Performance monitoring
monitor:
	@echo "Starting performance monitoring..."
	@echo "This would start continuous performance monitoring"
	@echo "Implementation depends on monitoring infrastructure"
