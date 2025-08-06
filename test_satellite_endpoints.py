#!/usr/bin/env python3
"""
Test específico para los nuevos endpoints satelitales
"""

import requests
import time

def test_satellite_endpoints():
    print("🛰️ TESTING NEW SATELLITE ENDPOINTS")
    print("=" * 50)
    
    base_url = "http://localhost:8050"
    
    # Test 1: Trigger analysis
    print("🚀 Testing /api/satellite/trigger-analysis...")
    try:
        response = requests.post(f"{base_url}/api/satellite/trigger-analysis", 
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text[:500]}...")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Trigger successful: {data}")
                
                if 'analysis_id' in data:
                    analysis_id = data['analysis_id']
                    print(f"📝 Analysis ID: {analysis_id}")
                    
                    # Test 2: Check progress
                    print("\n📊 Testing /api/satellite/analysis-progress...")
                    time.sleep(2)
                    progress_response = requests.get(f"{base_url}/api/satellite/analysis-progress/{analysis_id}")
                    print(f"Progress status code: {progress_response.status_code}")
                    print(f"Progress response: {progress_response.text}")
                    
                else:
                    print("❌ No analysis_id in response")
            except Exception as json_error:
                print(f"❌ JSON parse error: {json_error}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_satellite_endpoints()
