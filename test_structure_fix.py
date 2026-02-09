#!/usr/bin/env python3
"""
Comprehensive test to verify satellite API data structure fixes
"""

import requests
import json
from datetime import datetime

def test_satellite_api_structure():
    """Test all satellite API endpoints for correct data structure"""
    
    print("🧪 COMPREHENSIVE SATELLITE API STRUCTURE TEST")
    print("="*60)
    
    base_url = "http://localhost:5001"
    all_tests_passed = True
    
    # Test critical alerts structure
    print("\n1️⃣ TESTING CRITICAL ALERTS STRUCTURE")
    print("-"*40)
    
    try:
        response = requests.get(f"{base_url}/api/satellite/critical-alerts", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('alerts'):
                alert = data['alerts'][0]
                
                # Check required frontend fields
                required_fields = ['title', 'description', 'timestamp', 'severity']
                missing_fields = [field for field in required_fields if field not in alert]
                
                if not missing_fields:
                    print("✅ Critical alerts structure: CORRECT")
                    print(f"   Sample: {alert['title']} - {alert['description'][:50]}...")
                else:
                    print(f"❌ Missing fields: {missing_fields}")
                    all_tests_passed = False
            else:
                print("❌ No alerts data returned")
                all_tests_passed = False
        else:
            print(f"❌ HTTP {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"❌ Error: {e}")
        all_tests_passed = False
    
    # Test gallery images structure  
    print("\n2️⃣ TESTING GALLERY IMAGES STRUCTURE")
    print("-"*40)
    
    try:
        response = requests.get(f"{base_url}/api/satellite/gallery-images", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('images'):
                image = data['images'][0]
                
                # Check required frontend fields
                required_fields = ['url', 'region', 'date', 'coordinates', 'detections']
                missing_fields = [field for field in required_fields if field not in image]
                
                if not missing_fields:
                    print("✅ Gallery images structure: CORRECT")
                    print(f"   Sample: {image['region']} - {image['detections']} detections")
                else:
                    print(f"❌ Missing fields: {missing_fields}")
                    print(f"   Available fields: {list(image.keys())}")
                    all_tests_passed = False
            else:
                print("❌ No images data returned")
                all_tests_passed = False
        else:
            print(f"❌ HTTP {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"❌ Error: {e}")
        all_tests_passed = False
    
    # Test timeline structure
    print("\n3️⃣ TESTING TIMELINE STRUCTURE")
    print("-"*40)
    
    try:
        response = requests.get(f"{base_url}/api/satellite/analysis-timeline", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('timeline'):
                event = data['timeline'][0]
                
                # Check required frontend fields
                required_fields = ['timestamp', 'description']
                missing_fields = [field for field in required_fields if field not in event]
                
                if not missing_fields:
                    print("✅ Timeline structure: CORRECT")
                    print(f"   Sample: {event['timestamp']} - {event['description'][:50]}...")
                else:
                    print(f"❌ Missing fields: {missing_fields}")
                    print(f"   Available fields: {list(event.keys())}")
                    all_tests_passed = False
            else:
                print("❌ No timeline data returned")
                all_tests_passed = False
        else:
            print(f"❌ HTTP {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"❌ Error: {e}")
        all_tests_passed = False
    
    # Test predictions structure
    print("\n4️⃣ TESTING PREDICTIONS STRUCTURE")
    print("-"*40)
    
    try:
        response = requests.get(f"{base_url}/api/satellite/evolution-predictions", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('predictions'):
                pred = data['predictions'][0]
                
                # Check required frontend fields
                required_fields = ['region', 'prediction', 'confidence', 'timeframe', 'risk_level']
                missing_fields = [field for field in required_fields if field not in pred]
                
                if not missing_fields:
                    print("✅ Predictions structure: CORRECT")
                    print(f"   Sample: {pred['region']} - {pred['prediction'][:50]}...")
                else:
                    print(f"❌ Missing fields: {missing_fields}")
                    print(f"   Available fields: {list(pred.keys())}")
                    all_tests_passed = False
            else:
                print("❌ No predictions data returned")
                all_tests_passed = False
        else:
            print(f"❌ HTTP {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"❌ Error: {e}")
        all_tests_passed = False
    
    # Summary
    print("\n" + "="*60)
    if all_tests_passed:
        print("🎉 ALL STRUCTURE TESTS PASSED!")
        print("✅ Satellite frontend should now display data correctly")
        print("✅ No more 'undefined' values expected")
    else:
        print("⚠️ SOME STRUCTURE TESTS FAILED")
        print("🔧 Server restart required to apply data structure fixes")
        print("💡 After restart, all undefined values should be resolved")
    
    print(f"\n⏰ Test completed at {datetime.now().isoformat()}")
    return all_tests_passed

if __name__ == "__main__":
    test_satellite_api_structure()