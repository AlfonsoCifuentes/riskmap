#!/usr/bin/env python3
"""
Test script to verify all translation fixes are working properly
and that the backend returns strings instead of tuples.
"""

import requests
import json
import time
from typing import Dict, Any

def test_endpoint_response_structure(endpoint: str, expected_keys: list = None) -> bool:
    """Test that an endpoint returns proper string values, not tuples."""
    try:
        print(f"\n🔍 Testing {endpoint}...")
        response = requests.get(f"http://localhost:5001{endpoint}", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
        data = response.json()
        if not data.get('success'):
            print(f"❌ API returned success=False: {data}")
            return False
            
        print(f"✅ {endpoint} - Status OK")
        
        # Check for tuple structures in the response
        def check_for_tuples(obj, path=""):
            """Recursively check for tuple-like structures in JSON response."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], str):
                        print(f"⚠️  Possible tuple found at {current_path}: {value}")
                        return True
                    elif check_for_tuples(value, current_path):
                        return True
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    if check_for_tuples(item, current_path):
                        return True
            return False
        
        if check_for_tuples(data):
            print(f"❌ {endpoint} - Found tuple-like structures in response")
            return False
        
        # Specific checks for article endpoints
        if 'articles' in data:
            for i, article in enumerate(data['articles'][:3]):  # Check first 3 articles
                if 'title' in article:
                    if not isinstance(article['title'], str):
                        print(f"❌ Article {i} title is not a string: {type(article['title'])}")
                        return False
                    if not article['title']:  # Empty string check
                        print(f"⚠️  Article {i} has empty title")
        
        if 'article' in data:
            article = data['article']
            if 'title' in article:
                if not isinstance(article['title'], str):
                    print(f"❌ Hero article title is not a string: {type(article['title'])}")
                    return False
        
        print(f"✅ {endpoint} - All data structures are valid")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error testing {endpoint}: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error testing {endpoint}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error testing {endpoint}: {e}")
        return False

def test_translation_endpoint():
    """Test the translation endpoint specifically."""
    try:
        print(f"\n🔍 Testing /api/translate endpoint...")
        
        test_data = {
            "text": "This is a test message for translation",
            "target_language": "es"
        }
        
        response = requests.post(
            "http://localhost:5001/api/translate", 
            json=test_data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Translation endpoint error {response.status_code}: {response.text}")
            return False
            
        data = response.json()
        if not data.get('success'):
            print(f"❌ Translation API returned success=False: {data}")
            return False
        
        translated_text = data.get('translated_text')
        if not isinstance(translated_text, str):
            print(f"❌ Translation result is not a string: {type(translated_text)}")
            return False
            
        print(f"✅ Translation endpoint - Returned valid string: '{translated_text[:50]}...'")
        return True
        
    except Exception as e:
        print(f"❌ Error testing translation endpoint: {e}")
        return False

def main():
    """Run comprehensive backend testing."""
    print("🚀 Starting comprehensive backend translation fix verification...")
    print("=" * 70)
    
    # Test server connectivity first
    try:
        response = requests.get("http://localhost:5001/api/status", timeout=10)
        if response.status_code != 200:
            print("❌ Server is not running or not responding properly")
            print("Please start the server with: python app_BUENA.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server at http://localhost:5001")
        print("Please start the server with: python app_BUENA.py")
        return
    
    print("✅ Server is running and accessible")
    
    # Test all main endpoints
    endpoints_to_test = [
        "/api/articles",
        "/api/hero-article", 
        "/api/articles/deduplicated"
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        result = test_endpoint_response_structure(endpoint)
        results.append((endpoint, result))
        time.sleep(1)  # Brief pause between requests
    
    # Test translation endpoint
    translation_result = test_translation_endpoint()
    results.append(("/api/translate", translation_result))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for endpoint, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {endpoint}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The translation system is working correctly.")
        print("✅ All endpoints return proper string values instead of tuples.")
        print("✅ Frontend should now load without JavaScript errors.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        
    print("\n🔧 If frontend still shows errors, please check browser console.")

if __name__ == "__main__":
    main()