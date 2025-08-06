#!/usr/bin/env python3
"""
Script para probar los endpoints del frontend
"""

import requests
import json

def test_endpoint(url, description):
    """Test a single endpoint"""
    try:
        print(f"\n🔍 Testing {description}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            if 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ Success: {data.get('success')}")
                    if 'articles' in data:
                        print(f"   📰 Articles: {len(data['articles'])}")
                    if 'mosaic' in data:
                        print(f"   🎨 Mosaic: {len(data['mosaic'])}")
                    if 'hero' in data:
                        print(f"   🏆 Hero: {'Yes' if data['hero'] else 'No'}")
                else:
                    print(f"   ⚠️ Success=False: {data.get('error', 'Unknown error')}")
            else:
                print(f"   📄 Content-Length: {len(response.text)}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

def main():
    print("🚀 Testing RiskMap Frontend Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8050"
    
    # Test endpoints
    endpoints = [
        (f"{base_url}/", "Homepage"),
        (f"{base_url}/api/articles?limit=5", "Regular Articles"),
        (f"{base_url}/api/hero-article", "Hero Article"),
        (f"{base_url}/api/articles/deduplicated?hours=24", "Deduplicated Articles"),
        (f"{base_url}/api/groq/analysis", "AI Analysis"),
        (f"{base_url}/api/statistics", "Statistics"),
    ]
    
    for url, description in endpoints:
        test_endpoint(url, description)
    
    print("\n" + "=" * 50)
    print("🏁 Testing complete!")

if __name__ == "__main__":
    main()
