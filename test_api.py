#!/usr/bin/env python3
"""
Test API después del ajuste de filtros
"""

import requests
import json

def test_api():
    """Test the API endpoints."""
    try:
        # Test articles endpoint
        print("🔄 Testing /api/articles...")
        response = requests.get('http://localhost:5001/api/articles')
        data = response.json()
        
        articles = data.get('articles', [])
        print(f"📰 Articles returned: {len(articles)}")
        
        if articles:
            print("📋 Sample articles:")
            for i, article in enumerate(articles[:5]):
                title = article.get('title', 'No title')[:50]
                risk = article.get('risk_level', 'unknown')
                region = article.get('region', 'unknown')
                has_image = 'YES' if article.get('image') else 'NO'
                print(f"  {i+1}. {title}... | Risk: {risk} | Region: {region} | Image: {has_image}")
        
        # Test hero article
        print("\n🔄 Testing /api/hero-article...")
        response = requests.get('http://localhost:5001/api/hero-article')
        hero_data = response.json()
        
        if hero_data and 'title' in hero_data:
            print(f"🦸 Hero article: {hero_data['title'][:50]}...")
        
        # Test status
        print("\n🔄 Testing /api/status...")
        response = requests.get('http://localhost:5001/api/status')
        status_data = response.json()
        
        print(f"✅ System status: {status_data.get('status', 'unknown')}")
        print(f"🗄️  Database: {status_data.get('database', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_api()