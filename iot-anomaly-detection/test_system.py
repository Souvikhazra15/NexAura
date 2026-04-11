#!/usr/bin/env python3
"""
System verification and testing script
Run this after starting the backend to verify everything is working
"""

import requests
import json
import sys
from pathlib import Path

API_URL = "http://localhost:8000"
SAMPLE_CSV = Path(__file__).parent / "sample_data.csv"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_ok(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_fail(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def test_health():
    """Test /health endpoint"""
    print("\n" + "="*50)
    print("TEST 1: Health Check")
    print("="*50)
    
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_ok(f"Backend is running")
            print_info(f"Service: {data.get('service')}")
            print_info(f"Version: {data.get('version')}")
            return True
        else:
            print_fail(f"Unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_fail("Cannot connect to backend at " + API_URL)
        print_info("Make sure backend is running: python main.py")
        return False
    except Exception as e:
        print_fail(f"Error: {str(e)}")
        return False

def test_test_endpoint():
    """Test /test endpoint with sample data"""
    print("\n" + "="*50)
    print("TEST 2: Test Endpoint (Sample Data)")
    print("="*50)
    
    try:
        response = requests.post(f"{API_URL}/api/test", timeout=60)
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            required_keys = ['status', 'summary', 'metrics', 'anomalies']
            missing = [k for k in required_keys if k not in data]
            
            if missing:
                print_fail(f"Missing keys: {missing}")
                return False
            
            if data['status'] != 'success':
                print_fail(f"Status is not success: {data['status']}")
                return False
            
            print_ok("Test endpoint returned valid response")
            print_info(f"Anomalies detected: {data['summary'].get('anomalies_detected')}")
            print_info(f"Best model: {data['summary'].get('best_model')}")
            print_info(f"F1-Score: {data['metrics']['best_model_metrics'].get('f1_score', 'N/A'):.4f}")
            
            return True
        else:
            print_fail(f"Unexpected status code: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print_fail("Request timed out (processing took too long)")
        return False
    except Exception as e:
        print_fail(f"Error: {str(e)}")
        return False

def test_file_upload():
    """Test /upload endpoint with actual CSV file"""
    print("\n" + "="*50)
    print("TEST 3: File Upload (Real CSV)")
    print("="*50)
    
    if not SAMPLE_CSV.exists():
        print_fail(f"Sample CSV not found: {SAMPLE_CSV}")
        print_info("Expected location: " + str(SAMPLE_CSV))
        return False
    
    try:
        with open(SAMPLE_CSV, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{API_URL}/api/upload",
                files=files,
                timeout=120
            )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] != 'success':
                print_fail(f"Upload failed: {data.get('detail', 'Unknown error')}")
                return False
            
            print_ok(f"File uploaded and processed successfully")
            print_info(f"Total samples: {data['summary'].get('total_samples')}")
            print_info(f"Anomalies detected: {data['summary'].get('anomalies_detected')}")
            print_info(f"Anomaly rate: {data['summary'].get('anomaly_rate')}")
            print_info(f"Best model: {data['summary'].get('best_model')}")
            
            # Check metrics
            best_metrics = data['metrics']['best_model_metrics']
            print_info(f"  Precision: {best_metrics.get('precision', 0):.4f}")
            print_info(f"  Recall: {best_metrics.get('recall', 0):.4f}")
            print_info(f"  F1-Score: {best_metrics.get('f1_score', 0):.4f}")
            
            return True
        else:
            print_fail(f"Upload failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print_fail("Request timed out (file too large or processing slow)")
        return False
    except Exception as e:
        print_fail(f"Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}╔════════════════════════════════════════════════════════╗")
    print(f"║    Anomaly Detection System - Verification Suite      ║")
    print(f"╚════════════════════════════════════════════════════════╝{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Connecting to: {API_URL}{Colors.END}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Test Endpoint", test_test_endpoint()))
    results.append(("File Upload", test_file_upload()))
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ All tests passed! System is ready to use.{Colors.END}")
        print(f"\n{Colors.BLUE}Visit: http://localhost:3000 to use the system{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}✗ Some tests failed. Check the errors above.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
