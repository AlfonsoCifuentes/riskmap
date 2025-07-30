#!/usr/bin/env python3

import requests
import json

def test_ai_analysis():
    print("🧪 Testing AI analysis endpoint...")
    try:
        response = requests.get('http://127.0.0.1:5000/api/ai_analysis', timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AI analysis endpoint working")
            print(f"Response keys: {list(data.keys())}")
            if 'analysis_html' in data:
                print(f"Analysis HTML length: {len(data['analysis_html'])}")
            if 'headline' in data:
                print(f"Headline: {data['headline'][:100]}...")
        else:
            print("❌ AI analysis endpoint failed")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Request failed: {e}")

if __name__ == "__main__":
    test_ai_analysis()
