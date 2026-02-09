#!/usr/bin/env python3
"""
Examine the actual API responses to understand undefined values in frontend
"""

import requests
import json
from datetime import datetime

def examine_api_responses():
    """Examine all satellite API responses in detail"""
    
    print("🔍 EXAMINING SATELLITE API RESPONSES")
    print("="*60)
    
    base_url = "http://localhost:5001"
    
    endpoints = {
        'critical-alerts': '/api/satellite/critical-alerts',
        'gallery-images': '/api/satellite/gallery-images',
        'analysis-timeline': '/api/satellite/analysis-timeline', 
        'evolution-predictions': '/api/satellite/evolution-predictions'
    }
    
    for name, endpoint in endpoints.items():
        print(f"\n📡 ENDPOINT: {name}")
        print("-" * 40)
        
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Pretty print the response structure
                    print("✅ Response Structure:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "...")
                    
                    # Analyze specific fields that might be causing undefined
                    if name == 'critical-alerts' and 'alerts' in data:
                        print(f"\n🚨 Critical Alerts Analysis:")
                        for i, alert in enumerate(data['alerts'][:2]):
                            print(f"  Alert {i+1}:")
                            for key, value in alert.items():
                                print(f"    {key}: {value}")
                    
                    elif name == 'gallery-images' and 'images' in data:
                        print(f"\n📷 Gallery Images Analysis:")
                        for i, image in enumerate(data['images'][:2]):
                            print(f"  Image {i+1}:")
                            for key, value in image.items():
                                print(f"    {key}: {value}")
                    
                    elif name == 'analysis-timeline' and 'timeline' in data:
                        print(f"\n⏰ Timeline Analysis:")
                        for i, event in enumerate(data['timeline'][:2]):
                            print(f"  Event {i+1}:")
                            for key, value in event.items():
                                print(f"    {key}: {value}")
                    
                    elif name == 'evolution-predictions' and 'predictions' in data:
                        print(f"\n📈 Predictions Analysis:")
                        for i, pred in enumerate(data['predictions'][:2]):
                            print(f"  Prediction {i+1}:")
                            for key, value in pred.items():
                                print(f"    {key}: {value}")
                
                except json.JSONDecodeError:
                    print("❌ Invalid JSON response")
                    print(f"Raw response: {response.text[:200]}...")
            else:
                print(f"❌ HTTP Error {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print("🔌 Server not responding - check if RISKMAP.py is running")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Analysis completed at {datetime.now().isoformat()}")

if __name__ == "__main__":
    examine_api_responses()