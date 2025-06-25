#!/usr/bin/env python3
"""
PixelTracker Setup and Quick Start Script
Helps users get started with PixelTracker
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.7+"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version.split()[0]} detected")
        return True

def install_dependencies(requirements_file):
    """Install dependencies from requirements file"""
    try:
        print(f"📦 Installing dependencies from {requirements_file}...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                      check=True, capture_output=True, text=True)
        # Include test dependencies if the requirements file is main
        if requirements_file == 'requirements.txt':
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"], 
                          check=True, capture_output=True, text=True)
        print(f"✅ Dependencies from {requirements_file} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Requirements file {requirements_file} not found")
        return False

def run_quick_test():
    """Run a quick test to verify installation"""
    try:
        print("🧪 Running quick test...")
        result = subprocess.run([sys.executable, "pixeltracker.py", "info", "--dependencies"], 
                               capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Quick test passed - all core dependencies available")
            return True
        else:
            print("⚠️  Some dependencies may be missing:")
            print(result.stdout)
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out")
        return False
    except Exception as e:
        print(f"⚠️  Test failed: {e}")
        return False

def create_sample_config():
    """Create a sample configuration file"""
    try:
        print("📝 Creating sample configuration...")
        subprocess.run([sys.executable, "pixeltracker.py", "config", "--create-sample", "config.yaml"], 
                      check=True, capture_output=True, text=True)
        print("✅ Sample configuration created: config.yaml")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Could not create sample configuration")
        return False

def show_quick_start():
    """Show quick start instructions"""
    print("\n" + "="*60)
    print("🚀 PIXELTRACKER QUICK START")
    print("="*60)
    print()
    print("Basic usage:")
    print("  python3 pixeltracker.py scan example.com")
    print()
    print("Enhanced scanning:")
    print("  python3 pixeltracker.py scan --enhanced example.com")
    print()
    print("Multiple URLs with detailed report:")
    print("  python3 pixeltracker.py scan example.com facebook.com --detailed-report report.html")
    print()
    print("With custom configuration:")
    print("  python3 pixeltracker.py scan --config config.yaml example.com")
    print()
    print("Check dependencies:")
    print("  python3 pixeltracker.py info --dependencies")
    print()
    print("For more options:")
    print("  python3 pixeltracker.py --help")
    print("  python3 pixeltracker.py scan --help")
    print()
    print("📚 Documentation: Check README.md for detailed usage")
    print("="*60)

def main():
    """Main setup function"""
    print("🔍 PixelTracker Setup")
    print("===================")
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Ask user what they want to install
    print("\nSelect installation type:")
    print("1. Core features only (recommended for most users)")
    print("2. Core + ML features (for advanced analysis)")
    print("3. Full enterprise installation")
    print("4. Skip installation and run tests only")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    install_success = True
    
    if choice == "1":
        install_success = install_dependencies("requirements-core.txt")
    elif choice == "2":
        install_success = (install_dependencies("requirements-core.txt") and 
                          install_dependencies("requirements-ml.txt"))
    elif choice == "3":
        install_success = install_dependencies("requirements-enterprise.txt")
    elif choice == "4":
        print("⏭️  Skipping installation...")
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    if not install_success and choice != "4":
        print("\n⚠️  Installation had issues, but you can still try running tests")
    
    # Run quick test
    print()
    test_success = run_quick_test()
    
    # Create sample config
    print()
    create_sample_config()
    
    # Show quick start guide
    print()
    show_quick_start()
    
    # Final status
    print()
    if install_success and test_success:
        print("🎉 Setup completed successfully!")
        print("✅ Ready to start scanning for tracking pixels")
    elif test_success:
        print("🎉 Core functionality is working!")
        print("⚠️  Some optional features may not be available")
    else:
        print("⚠️  Setup completed with warnings")
        print("📝 Check the dependency status above and install missing packages")
        print("💡 You can still use basic features that are available")

if __name__ == "__main__":
    main()
