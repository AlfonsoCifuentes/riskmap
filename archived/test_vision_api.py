#!/usr/bin/env python3
"""
Simple debug script for vision API errors
"""
import requests
import json

def test_vision_api():
    base_url = "http://localhost:8050"
    article_ids = [1083, 1085, 1093, 1095, 1097, 1099, 1111]
    
    print("🔍 Testing Vision API endpoints...")
    print("="*50)
    
    for article_id in article_ids:
        try:
            # Test the get-analysis endpoint
            url = f"{base_url}/api/vision/get-analysis/{article_id}"
            print(f"\n📡 Testing: {url}")
            
            response = requests.get(url, timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('success', False)}")
                if data.get('is_fallback'):
                    print("⚠️  Using fallback data")
            elif response.status_code == 404:
                print("❌ Article not found")
                # Try to get article info
                info_url = f"{base_url}/api/articles/info/{article_id}"
                try:
                    info_response = requests.get(info_url, timeout=5)
                    print(f"Info API status: {info_response.status_code}")
                except:
                    print("Could not get article info")
            elif response.status_code == 500:
                print("❌ Internal server error")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print("Could not parse error response")
            else:
                print(f"❓ Unexpected status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed to {base_url}")
            break
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout for article {article_id}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*50)
    print("🏁 Test completed")

if __name__ == "__main__":
    test_vision_api()
