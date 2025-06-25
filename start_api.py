#!/usr/bin/env python3
"""
Startup script for PixelTracker API and Dashboard

This script starts the FastAPI server and optionally builds the React dashboard.
"""

import os
import sys
import subprocess
import argparse
import time
import signal
from pathlib import Path

def install_dependencies():
    """Install Python and Node.js dependencies"""
    print("Installing Python dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-api.txt"], check=True)
    
    dashboard_path = Path("api/dashboard")
    if dashboard_path.exists():
        print("Installing Node.js dependencies...")
        subprocess.run(["npm", "install"], cwd=dashboard_path, check=True)

def build_dashboard():
    """Build the React dashboard"""
    dashboard_path = Path("api/dashboard")
    if dashboard_path.exists():
        print("Building React dashboard...")
        subprocess.run(["npm", "run", "build"], cwd=dashboard_path, check=True)
        print("Dashboard built successfully!")
    else:
        print("Dashboard directory not found, skipping build")

def start_api(host="0.0.0.0", port=8000, reload=True):
    """Start the FastAPI server"""
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--host", host,
        "--port", str(port),
    ]
    
    if reload:
        cmd.append("--reload")
    
    print(f"Starting PixelTracker API on http://{host}:{port}")
    print("API Documentation will be available at /docs")
    print("Dashboard will be available at /")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down...")

def main():
    parser = argparse.ArgumentParser(description="Start PixelTracker API and Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--skip-install", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-build", action="store_true", help="Skip dashboard build")
    
    args = parser.parse_args()
    
    try:
        if not args.skip_install:
            install_dependencies()
        
        if not args.skip_build:
            build_dashboard()
        
        start_api(args.host, args.port, not args.no_reload)
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutdown complete")

if __name__ == "__main__":
    main()
