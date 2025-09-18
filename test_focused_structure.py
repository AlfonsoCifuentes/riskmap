#!/usr/bin/env python3
"""
Focused test to isolate exactly where the tuple issue occurs in the API endpoints.
"""

import requests
import json

def test_hero_article_structure():
    """Test the hero article endpoint specifically."""
    try:
        print("🔍 Testing /api/hero-article endpoint specifically...")
        response = requests.get("http://localhost:5001/api/hero-article", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return
            
        data = response.json()
        if not data.get('success'):
            print(f"❌ API returned success=False: {data}")
            return
        
        # Print the entire response structure
        print("📄 FULL RESPONSE STRUCTURE:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Check the article structure
        article = data.get('article', {})
        print("\n🔍 ARTICLE STRUCTURE ANALYSIS:")
        for key, value in article.items():
            print(f"  {key}: {type(value).__name__} = {repr(value)}")
            
            # Specifically check for list/tuple structures
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                if isinstance(value[0], str) and isinstance(value[1], str):
                    print(f"    ⚠️  This looks like a translation tuple: ({value[0]}, {value[1]})")
        
    except Exception as e:
        print(f"❌ Error testing hero article: {e}")

def test_articles_endpoint():
    """Test the articles endpoint structure."""
    try:
        print("\n🔍 Testing /api/articles endpoint specifically...")
        response = requests.get("http://localhost:5001/api/articles", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return
            
        data = response.json()
        if not data.get('success'):
            print(f"❌ API returned success=False: {data}")
            return
        
        articles = data.get('articles', [])
        if articles:
            print(f"\n🔍 FIRST ARTICLE STRUCTURE ANALYSIS:")
            article = articles[0]
            for key, value in article.items():
                print(f"  {key}: {type(value).__name__} = {repr(value)}")
                
                # Specifically check for list/tuple structures
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    if isinstance(value[0], str) and isinstance(value[1], str):
                        print(f"    ⚠️  This looks like a translation tuple: ({value[0]}, {value[1]})")
        
    except Exception as e:
        print(f"❌ Error testing articles: {e}")

def main():
    """Run focused testing."""
    print("🚀 FOCUSED API STRUCTURE TEST")
    print("=" * 50)
    
    # Test server connectivity first
    try:
        response = requests.get("http://localhost:5001/api/status", timeout=10)
        if response.status_code != 200:
            print("❌ Server is not running or not responding properly")
            return
    except:
        print("❌ Cannot connect to server at http://localhost:5001")
        return
    
    print("✅ Server is running and accessible")
    
    # Test specific endpoints
    test_hero_article_structure()
    test_articles_endpoint()
    
    print("\n📊 TEST COMPLETE")

if __name__ == "__main__":
    main()