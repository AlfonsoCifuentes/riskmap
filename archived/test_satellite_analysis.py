#!/usr/bin/env python3
"""
Test script for satellite analysis endpoint
Verifica que el sistema satelital funcione correctamente
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_satellite_analysis():
    """Test satellite analysis endpoint"""
    print("🛰️ Testing Satellite Analysis System")
    print("=" * 50)
    
    base_url = "http://localhost:8050"
    
    # Test coordinates (ejemplo: Siria - zona de conflicto conocida)
    test_data = {
        "latitude": 36.2021,
        "longitude": 37.1343,
        "location": "Aleppo, Siria",
        "analysis_type": "conflict_monitoring",
        "area_km2": 25,
        "resolution": "10m"
    }
    
    print(f"📍 Testing coordinates: {test_data['latitude']}, {test_data['longitude']}")
    print(f"🌍 Location: {test_data['location']}")
    print(f"📏 Area: {test_data['area_km2']} km²")
    print()
    
    try:
        # Step 1: Request satellite analysis
        print("1️⃣ Requesting satellite analysis...")
        response = requests.post(
            f"{base_url}/api/satellite/analyze",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Satellite analysis request successful!")
                print(f"📋 Task ID: {result.get('task_id')}")
                print(f"🎯 Status: {result.get('status')}")
                print(f"🏭 Provider: {result.get('provider')}")
                print(f"⏰ Timestamp: {result.get('timestamp')}")
                print()
                
                # Wait a moment for processing
                print("⏳ Waiting for analysis to process...")
                time.sleep(3)
                
            else:
                print(f"❌ Analysis request failed: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
        
        # Step 2: Check satellite results
        print("2️⃣ Checking satellite analysis results...")
        response = requests.get(f"{base_url}/api/satellite/results?limit=5")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                analyses = result['analyses']
                print(f"✅ Found {len(analyses)} satellite analyses")
                
                if analyses:
                    latest = analyses[0]
                    print(f"📊 Latest Analysis:")
                    print(f"   📍 Location: {latest.get('location')}")
                    print(f"   📡 Status: {latest.get('status')}")
                    print(f"   🔍 Type: {latest.get('analysis_type')}")
                    print(f"   ⏰ Created: {latest.get('created_at')}")
                    
                    if latest.get('completed_at'):
                        print(f"   ✅ Completed: {latest.get('completed_at')}")
                        print(f"   📈 Confidence: {latest.get('confidence_score', 0):.1%}")
                    
                    print()
                else:
                    print("⚠️ No analyses found")
                    
            else:
                print(f"❌ Failed to get results: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
        
        # Step 3: Test conflicts endpoint (should include satellite zones)
        print("3️⃣ Testing conflicts endpoint with satellite integration...")
        response = requests.get(f"{base_url}/api/analytics/conflicts")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                conflicts = result.get('conflicts', [])
                satellite_zones = result.get('satellite_zones', [])
                
                print(f"✅ Found {len(conflicts)} conflicts")
                print(f"🛰️ Found {len(satellite_zones)} satellite zones")
                
                if conflicts:
                    high_risk = [c for c in conflicts if c.get('risk_level') == 'high']
                    print(f"⚠️ High risk conflicts: {len(high_risk)}")
                
                if satellite_zones:
                    print("🎯 Satellite zones ready for analysis")
                    for zone in satellite_zones[:3]:  # Show first 3
                        print(f"   📍 {zone.get('location', 'Unknown')}")
                
                print()
            else:
                print(f"❌ Conflicts API failed: {result.get('error')}")
                print(f"💡 Suggestion: {result.get('suggestion', 'No suggestions')}")
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
        
        # Step 4: Test page access
        print("4️⃣ Testing satellite analysis page access...")
        response = requests.get(f"{base_url}/satellite-analysis")
        
        if response.status_code == 200:
            print("✅ Satellite analysis page accessible")
        else:
            print(f"❌ Page access failed: HTTP {response.status_code}")
        
        print()
        print("🎉 Satellite Analysis System Test Complete!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the Flask app is running on localhost:8050")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_frontend_integration():
    """Test frontend integration by checking if dashboard loads correctly"""
    print("\n🖥️ Testing Frontend Integration")
    print("=" * 30)
    
    base_url = "http://localhost:8050"
    
    try:
        # Test dashboard page
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Dashboard page loads correctly")
            
            # Check if satellite functions are present
            content = response.text
            if 'triggerSatelliteAnalysis' in content:
                print("✅ Satellite trigger functions found in frontend")
            else:
                print("⚠️ Satellite trigger functions not found in frontend")
                
            if 'requestSatelliteImage' in content:
                print("✅ Satellite request functions found in frontend")
            else:
                print("⚠️ Satellite request functions not found in frontend")
                
            if 'leaflet' in content.lower():
                print("✅ Leaflet map integration found")
            else:
                print("⚠️ Leaflet map integration not found")
                
        else:
            print(f"❌ Dashboard failed to load: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend test error: {str(e)}")

if __name__ == "__main__":
    print(f"🔬 Satellite Analysis System Test")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_satellite_analysis()
    test_frontend_integration()
    
    if success:
        print("\n🎯 All tests passed! Satellite analysis system is working.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the logs above.")
        sys.exit(1)
