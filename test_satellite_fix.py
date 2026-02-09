#!/usr/bin/env python3
"""
Test the fixed satellite API endpoints to verify they're no longer returning 500 errors
"""

import requests
import json
import time

def test_satellite_endpoints():
    """Test all satellite API endpoints"""
    
    base_url = "http://localhost:5001"
    
    endpoints = [
        '/api/satellite/critical-alerts',
        '/api/satellite/gallery-images', 
        '/api/satellite/analysis-timeline',
        '/api/satellite/evolution-predictions'
    ]
    
    print("🧪 Testing satellite API endpoints...")
    print("="*60)
    
    all_success = True
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS - Status: {response.status_code}")
                
                # Try to parse JSON
                try:
                    data = response.json()
                    if data.get('success'):
                        print(f"  📊 Response: success=True")
                        
                        # Show specific data for each endpoint
                        if 'alerts' in data:
                            print(f"     Alerts: {len(data['alerts'])}")
                        elif 'images' in data:
                            print(f"     Images: {len(data['images'])}")
                        elif 'timeline' in data:
                            print(f"     Timeline entries: {len(data['timeline'])}")
                        elif 'predictions' in data:
                            print(f"     Predictions: {len(data['predictions'])}")
                    else:
                        print(f"  ⚠️  Response success=False: {data.get('error', 'No error message')}")
                        
                except json.JSONDecodeError:
                    print(f"  ⚠️  Invalid JSON response")
                    print(f"     Response: {response.text[:200]}...")
                    
            else:
                print(f"  ❌ FAILED - Status: {response.status_code}")
                print(f"     Response: {response.text[:200]}...")
                all_success = False
                
        except requests.exceptions.ConnectionError:
            print(f"  🔌 SERVER NOT RUNNING - Cannot connect to {base_url}")
            print(f"     Please ensure RISKMAP.py server is running")
            all_success = False
            
        except requests.exceptions.Timeout:
            print(f"  ⏱️  TIMEOUT - Endpoint took too long to respond")
            all_success = False
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            all_success = False
    
    print("\n" + "="*60)
    if all_success:
        print("🎉 ALL SATELLITE ENDPOINTS WORKING!")
        print("✅ 500 errors have been fixed")
    else:
        print("⚠️  Some endpoints still have issues")
        print("🔧 Check server status and logs for more details")
    
    return all_success

if __name__ == "__main__":
    test_satellite_endpoints()