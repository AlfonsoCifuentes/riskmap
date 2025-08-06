#!/usr/bin/env python3
"""
Test script para verificar que la función triggerSatelliteAnalysis funciona correctamente
"""

import requests
import time
import json

def test_satellite_analysis():
    print("🛰️ TESTING SATELLITE ANALYSIS FUNCTIONALITY")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Trigger analysis
    print("🚀 Testing trigger analysis endpoint...")
    try:
        response = requests.post(f"{base_url}/api/satellite/trigger-analysis", 
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Trigger successful: {data}")
            
            if 'analysis_id' in data:
                analysis_id = data['analysis_id']
                print(f"📝 Analysis ID: {analysis_id}")
                
                # Test 2: Check progress
                print("📊 Testing progress endpoint...")
                progress_response = requests.get(f"{base_url}/api/satellite/analysis-progress/{analysis_id}")
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    print(f"✅ Progress check successful: {progress_data}")
                else:
                    print(f"❌ Progress check failed: {progress_response.status_code}")
                    print(f"Response: {progress_response.text}")
            
        else:
            print(f"❌ Trigger failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure app_BUENA.py is running on port 5000")
    except Exception as e:
        print(f"❌ Error testing satellite analysis: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_satellite_analysis()
