#!/usr/bin/env python3
"""
PixelTracker Test Runner

Comprehensive test runner that executes all test suites with proper configuration
and reporting. Supports different test modes and output formats.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture_output, text=True)
    if capture_output:
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
    return result.returncode == 0


def run_unit_tests(coverage=True, parallel=False):
    """Run unit tests"""
    print("\n🧪 Running Unit Tests")
    print("=" * 50)
    
    cmd = ["pytest", "tests/unit/", "-v", "--tb=short", "-m", "unit"]
    
    if coverage:
        cmd.extend(["--cov=pixeltracker", "--cov-report=term-missing"])
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    return run_command(cmd, capture_output=False)


def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running Integration Tests")
    print("=" * 50)
    
    cmd = ["pytest", "tests/integration/", "-v", "--tb=short", "-m", "integration"]
    return run_command(cmd, capture_output=False)


def run_performance_tests(benchmark_only=True):
    """Run performance tests"""
    print("\n⚡ Running Performance Tests")
    print("=" * 50)
    
    if benchmark_only:
        cmd = ["pytest", "tests/performance/", "-v", "--benchmark-only", 
               "--benchmark-sort=mean", "--benchmark-columns=min,max,mean,stddev"]
    else:
        cmd = ["pytest", "tests/performance/", "-v", "--tb=short", "-m", "performance"]
    
    return run_command(cmd, capture_output=False)


def run_coverage_report():
    """Generate comprehensive coverage report"""
    print("\n📊 Generating Coverage Report")
    print("=" * 50)
    
    # Generate terminal report
    cmd = ["pytest", "tests/", "--cov=pixeltracker", "--cov-report=term-missing", 
           "--cov-report=xml", "--cov-fail-under=85"]
    success = run_command(cmd, capture_output=False)
    
    # Generate HTML report
    if success:
        print("\nGenerating HTML coverage report...")
        cmd = ["pytest", "tests/", "--cov=pixeltracker", "--cov-report=html"]
        run_command(cmd)
        print("✅ HTML coverage report generated in htmlcov/")
    
    return success


def run_benchmarks():
    """Run comprehensive benchmarks"""
    print("\n🏃 Running Benchmarks")
    print("=" * 50)
    
    # Run pytest benchmarks
    print("Running pytest benchmarks...")
    cmd = ["pytest", "tests/performance/", "--benchmark-only", 
           "--benchmark-save=baseline", "--benchmark-save-data"]
    success = run_command(cmd, capture_output=False)
    
    # Run ASV benchmarks if available
    if os.path.exists("asv.conf.json"):
        print("\nRunning ASV benchmarks...")
        try:
            run_command(["asv", "machine", "--yes"])
            run_command(["asv", "run", "--show-stderr"])
            print("✅ ASV benchmarks completed")
        except FileNotFoundError:
            print("ASV not installed, skipping ASV benchmarks")
    
    return success


def run_linting():
    """Run code linting and formatting checks"""
    print("\n🔍 Running Code Quality Checks")
    print("=" * 50)
    
    success = True
    
    # Run ruff checks
    print("Running ruff checks...")
    if not run_command(["ruff", "check", "pixeltracker/", "tests/"]):
        success = False
    
    # Run mypy
    print("\nRunning mypy type checking...")
    if not run_command(["mypy", "pixeltracker/", "--ignore-missing-imports"]):
        success = False
    
    return success


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="PixelTracker Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmarks")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (exclude slow tests)")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    
    args = parser.parse_args()
    
    if not any([args.unit, args.integration, args.performance, args.coverage, 
                args.benchmark, args.lint, args.all, args.fast]):
        # Default: run unit and integration tests
        args.unit = True
        args.integration = True
    
    success = True
    
    print("🔍 PixelTracker Test Runner")
    print("=" * 50)
    print(f"Python: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Run selected test suites
    if args.all or args.unit:
        if not run_unit_tests(coverage=not args.no_coverage, parallel=args.parallel):
            success = False
    
    if args.all or args.integration:
        if not run_integration_tests():
            success = False
    
    if args.all or args.performance:
        if not run_performance_tests():
            success = False
    
    if args.fast:
        print("\n⚡ Running Fast Tests Only")
        print("=" * 50)
        cmd = ["pytest", "tests/", "-v", "--tb=short", "-m", "not slow"]
        if not args.no_coverage:
            cmd.extend(["--cov=pixeltracker", "--cov-report=term-missing"])
        if not run_command(cmd, capture_output=False):
            success = False
    
    if args.coverage:
        if not run_coverage_report():
            success = False
    
    if args.benchmark:
        if not run_benchmarks():
            success = False
    
    if args.all or args.lint:
        if not run_linting():
            success = False
    
    # Final summary
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
