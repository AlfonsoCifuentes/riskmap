#!/usr/bin/env python3
"""
Debug endpoint mapping directo
"""

import requests
import json

def test_direct_api_debug():
    """Test API response directly."""
    try:
        print("🔄 DEBUGGING API MAPPING")
        print("="*50)
        
        response = requests.get('http://localhost:5001/api/articles?limit=3')
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return
        
        data = response.json()
        articles = data.get('articles', [])
        
        print(f"📊 API returned {len(articles)} articles")
        print()
        
        for i, article in enumerate(articles, 1):
            print(f"{i}. Article Analysis:")
            print(f"   ID: {article.get('id')}")
            print(f"   Title: {article.get('title', 'NO TITLE')[:50]}...")
            print(f"   'image' field: {article.get('image', 'MISSING')}")
            print(f"   'image_url' field: {article.get('image_url', 'MISSING')}")
            
            # Check all fields for image
            image_fields = [k for k in article.keys() if 'image' in k.lower()]
            print(f"   All image fields: {image_fields}")
            
            # Show field values 
            for field in image_fields:
                value = article.get(field)
                if value:
                    print(f"   {field}: {value[:60]}...")
                else:
                    print(f"   {field}: NULL/EMPTY")
            
            print()
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_direct_api_debug()