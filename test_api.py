#!/usr/bin/env python3
"""
Test script for PixelTracker API

Simple test to verify API endpoints are working correctly.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api"

def test_api():
    """Run basic API tests"""
    
    print("Testing PixelTracker API...")
    
    # Test 1: Get statistics (should work even with empty database)
    print("\n1. Testing /api/stats endpoint...")
    try:
        response = requests.get(f"{API_BASE}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ Stats endpoint working. Total scans: {stats.get('total_scans', 0)}")
        else:
            print(f"✗ Stats endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Stats endpoint error: {e}")
    
    # Test 2: Get results (should return empty list initially)
    print("\n2. Testing /api/results endpoint...")
    try:
        response = requests.get(f"{API_BASE}/results")
        if response.status_code == 200:
            results = response.json()
            print(f"✓ Results endpoint working. Found {len(results)} results")
        else:
            print(f"✗ Results endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Results endpoint error: {e}")
    
    # Test 3: Start a scan
    print("\n3. Testing /api/scan endpoint...")
    scan_data = {
        "url": "https://example.com",
        "scan_type": "basic",
        "enable_javascript": False
    }
    
    try:
        response = requests.post(f"{API_BASE}/scan", json=scan_data)
        if response.status_code == 200:
            scan_response = response.json()
            scan_id = scan_response.get('scan_id')
            print(f"✓ Scan started successfully. Scan ID: {scan_id}")
            
            # Test 4: Check scan result
            print("\n4. Testing scan result retrieval...")
            time.sleep(2)  # Wait a bit for scan to start
            
            result_response = requests.get(f"{API_BASE}/scan/{scan_id}")
            if result_response.status_code == 200:
                result = result_response.json()
                print(f"✓ Scan result retrieved. Status: {result.get('status')}")
            else:
                print(f"✗ Scan result failed: {result_response.status_code}")
                
        else:
            print(f"✗ Scan endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Scan endpoint error: {e}")
    
    print("\nAPI test completed!")

if __name__ == "__main__":
    test_api()
