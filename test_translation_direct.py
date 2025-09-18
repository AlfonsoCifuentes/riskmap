#!/usr/bin/env python3
"""
Direct test of the translation system in the running application.
"""

import requests
import json

def test_translation_endpoint_direct():
    """Test the translation endpoint directly."""
    try:
        print("🧪 DIRECT TRANSLATION TEST")
        print("=" * 50)
        
        # Test with simple text
        test_data = {
            "text": "Hello world",
            "target_language": "es"
        }
        
        response = requests.post(
            "http://localhost:5001/api/translate", 
            json=test_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Raw Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"JSON Data: {json.dumps(data, indent=2)}")
                
                translated_text = data.get('translated_text')
                print(f"Translated text type: {type(translated_text)}")
                print(f"Translated text value: {repr(translated_text)}")
                
                if isinstance(translated_text, list):
                    print("❌ PROBLEM: Translation result is a list!")
                    print(f"   List contents: {translated_text}")
                elif isinstance(translated_text, str):
                    print("✅ Translation result is correctly a string")
                else:
                    print(f"❌ PROBLEM: Translation result is {type(translated_text)}")
            
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing translation: {e}")

def test_simple_endpoint():
    """Test a simple endpoint to see basic data structure."""
    try:
        print("\n🧪 SIMPLE ENDPOINT TEST")
        print("=" * 50)
        
        response = requests.get("http://localhost:5001/api/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status endpoint works: {data.get('status')}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing status: {e}")

if __name__ == "__main__":
    test_simple_endpoint()
    test_translation_endpoint_direct()