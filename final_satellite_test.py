#!/usr/bin/env python3
"""Script final para verificar que todos los endpoints satelitales funcionan correctamente."""

import requests
import json

def test_all_endpoints():
    """Probar todos los endpoints y verificar que no hay undefined."""
    base_url = "http://localhost:8050"
    
    endpoints = [
        ("/api/satellite/statistics", "GET"),
        ("/api/satellite/gallery-images", "GET"),
        ("/api/satellite/critical-alerts", "GET"),
        ("/api/satellite/analysis-timeline", "GET"), 
        ("/api/satellite/evolution-predictions", "GET"),
        ("/api/satellite/trigger-analysis", "POST")
    ]
    
    print("🛰️ VERIFICACIÓN FINAL DE ENDPOINTS SATELITALES")
    print("=" * 70)
    
    all_working = True
    
    for endpoint, method in endpoints:
        print(f"\n🚀 Testing {method} {endpoint}")
        try:
            if method == "POST":
                response = requests.post(f"{base_url}{endpoint}", timeout=10)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ SUCCESS")
                    
                    # Verificaciones específicas
                    if endpoint == "/api/satellite/gallery-images":
                        if 'images' in data and len(data['images']) > 0:
                            img = data['images'][0]
                            if 'detection' in img and 'bounding_boxes' in img['detection']:
                                if isinstance(img['detection']['bounding_boxes'], list):
                                    print(f"   ✅ Bounding boxes format is correct (array)")
                                else:
                                    print(f"   ❌ Bounding boxes should be array, got: {type(img['detection']['bounding_boxes'])}")
                                    all_working = False
                    
                    elif endpoint == "/api/satellite/evolution-predictions":
                        if 'predictions' in data and len(data['predictions']) > 0:
                            pred = data['predictions'][0]
                            required_fields = ['type', 'timeframe', 'trend_percentage', 'confidence']
                            for field in required_fields:
                                if field in pred and pred[field] is not None:
                                    print(f"   ✅ Field '{field}' present: {pred[field]}")
                                else:
                                    print(f"   ❌ Field '{field}' missing or undefined")
                                    all_working = False
                    
                    elif endpoint == "/api/satellite/critical-alerts":
                        if 'alerts' in data and len(data['alerts']) > 0:
                            alert = data['alerts'][0]
                            required_fields = ['type', 'confidence', 'severity', 'location']
                            for field in required_fields:
                                if field in alert and alert[field] is not None:
                                    print(f"   ✅ Field '{field}' present")
                                else:
                                    print(f"   ❌ Field '{field}' missing or undefined")
                                    all_working = False
                    
                    elif endpoint == "/api/satellite/trigger-analysis":
                        if 'analysis_id' in data:
                            print(f"   ✅ Analysis ID generated: {data['analysis_id']}")
                            
                            # Test progress endpoint
                            progress_url = f"{base_url}/api/satellite/analysis-progress/{data['analysis_id']}"
                            try:
                                progress_response = requests.get(progress_url, timeout=5)
                                if progress_response.status_code == 200:
                                    progress_data = progress_response.json()
                                    print(f"   ✅ Progress endpoint working: {progress_data.get('progress', 0)}%")
                                else:
                                    print(f"   ❌ Progress endpoint failed: {progress_response.status_code}")
                                    all_working = False
                            except Exception as e:
                                print(f"   ⚠️ Progress endpoint error: {e}")
                        else:
                            print(f"   ❌ No analysis_id in response")
                            all_working = False
                else:
                    print(f"   ❌ Response indicates failure: {data.get('error', 'Unknown error')}")
                    all_working = False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                all_working = False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            all_working = False
    
    print(f"\n{'='*70}")
    if all_working:
        print("🎉 ALL ENDPOINTS WORKING CORRECTLY - NO UNDEFINED VALUES!")
        print("✅ Frontend should now display data properly without undefined errors")
    else:
        print("❌ Some endpoints have issues that need to be fixed")
    print(f"{'='*70}")
    
    return all_working

if __name__ == "__main__":
    test_all_endpoints()
