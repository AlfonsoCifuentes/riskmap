#!/usr/bin/env python3
"""
Debug hero article exclusion
"""

import requests
import json

def test_hero_exclusion():
    """Test hero article and its impact."""
    try:
        print("🦸 DEBUGGING HERO ARTICLE EXCLUSION")
        print("="*50)
        
        # Test hero article first
        print("🔄 Testing /api/hero-article...")
        hero_response = requests.get('http://localhost:5001/api/hero-article')
        
        if hero_response.status_code == 200:
            hero_data = hero_response.json()
            if hero_data and 'id' in hero_data:
                hero_id = hero_data['id']
                print(f"🦸 Hero article ID: {hero_id}")
                print(f"   Hero title: {hero_data.get('title', 'NO TITLE')[:50]}...")
                print(f"   Hero image: {'YES' if hero_data.get('image') else 'NO'}")
            else:
                print("🦸 No hero article found")
                hero_id = None
        else:
            print(f"❌ Hero endpoint error: {hero_response.status_code}")
            hero_id = None
        
        # Test articles without limit
        print("\n🔄 Testing /api/articles without filters...")
        articles_response = requests.get('http://localhost:5001/api/articles?limit=5')
        
        if articles_response.status_code == 200:
            articles_data = articles_response.json()
            articles = articles_data.get('articles', [])
            
            print(f"📊 Articles returned: {len(articles)}")
            print(f"   Layout data present: {'layout_data' in articles_data}")
            print(f"   Smart layout: {articles_data.get('smart_layout', False)}")
            
            print("\n📋 Article IDs and titles:")
            for i, article in enumerate(articles, 1):
                article_id = article.get('id')
                title = article.get('title', 'NO TITLE')[:40]
                has_image = 'YES' if article.get('image') else 'NO'
                print(f"   {i}. ID {article_id}: {title}... | Image: {has_image}")
                
                if article_id == hero_id:
                    print("      ⚠️  THIS IS THE HERO ARTICLE!")
        
        else:
            print(f"❌ Articles endpoint error: {articles_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_hero_exclusion()