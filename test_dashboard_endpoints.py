#!/usr/bin/env python3
"""
Test script to verify all dashboard endpoints are working correctly
and returning real data instead of mock/demo data.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8050"

def test_endpoint(endpoint, description):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"🔍 Testing: {description}")
    print(f"Endpoint: {endpoint}")
    print('='*60)
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if isinstance(data, dict):
                if 'success' in data:
                    print(f"🎯 Success: {data['success']}")
                
                # Check for real data indicators
                real_data_indicators = []
                
                # Hero article checks
                if 'article' in data and isinstance(data['article'], dict):
                    article = data['article']
                    if 'id' in article and isinstance(article['id'], int):
                        real_data_indicators.append(f"Hero has real ID: {article['id']}")
                    if 'title' in article and 'picsum.photos' not in str(article.get('image', '')):
                        real_data_indicators.append("Hero has real title and non-demo image")
                
                # Statistics checks  
                if 'statistics' in data:
                    stats = data['statistics']
                    if isinstance(stats, dict):
                        real_data_indicators.append(f"Real stats: {len(stats)} metrics")
                        for key, value in stats.items():
                            if isinstance(value, int) and value > 0:
                                real_data_indicators.append(f"{key}: {value}")
                
                # Articles checks
                if 'articles' in data and isinstance(data['articles'], list):
                    articles = data['articles']
                    if len(articles) > 0:
                        real_data_indicators.append(f"{len(articles)} real articles found")
                        
                        # Check first article for real data
                        first_article = articles[0]
                        if 'id' in first_article and isinstance(first_article['id'], int):
                            real_data_indicators.append(f"First article has real ID: {first_article['id']}")
                        
                        # Check for non-demo images
                        real_images = [a for a in articles[:5] if 'image' in a or 'image_url' in a]
                        demo_images = [a for a in real_images if 'picsum.photos' in str(a.get('image', '') + a.get('image_url', ''))]
                        real_data_indicators.append(f"Real images: {len(real_images) - len(demo_images)}/{len(real_images)}")
                
                # Mosaic checks
                if 'mosaic' in data and isinstance(data['mosaic'], list):
                    mosaic = data['mosaic']
                    if len(mosaic) > 0:
                        real_data_indicators.append(f"{len(mosaic)} mosaic articles")
                        # Check for real IDs
                        real_ids = [a for a in mosaic if 'id' in a and isinstance(a['id'], int)]
                        real_data_indicators.append(f"Mosaic real IDs: {len(real_ids)}/{len(mosaic)}")
                
                # Deduplication checks
                if 'stats' in data and 'duplicates_removed' in data['stats']:
                    stats = data['stats']
                    real_data_indicators.append(f"Deduplication: {stats['duplicates_removed']} removed, {stats['unique_articles']} unique")
                
                if real_data_indicators:
                    print("🎯 REAL DATA INDICATORS:")
                    for indicator in real_data_indicators:
                        print(f"   ✓ {indicator}")
                else:
                    print("⚠️ NO REAL DATA INDICATORS FOUND - May be using mock/demo data")
                
                # Print sample data
                if len(str(data)) < 1000:
                    print("\n📄 SAMPLE RESPONSE:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:800] + "...")
                else:
                    print(f"\n📏 Response size: {len(str(data))} chars (too large to display)")
                    
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT - Endpoint took too long (>30s)")
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR - Backend may be down")
    except Exception as e:
        print(f"💥 ERROR: {e}")

def main():
    print("🔍 DASHBOARD ENDPOINTS TEST")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test all dashboard endpoints
    endpoints = [
        ("/api/hero-article", "Hero Article"),
        ("/api/statistics", "Dashboard Statistics"),
        ("/api/articles?limit=5", "Regular Articles (5)"),
        ("/api/articles/deduplicated?hours=24", "Deduplicated Articles (24h)"),
        ("/api/articles/latest?limit=5", "Latest Articles (5)"),
        ("/api/articles/high-risk?limit=3", "High Risk Articles (3)"),
    ]
    
    for endpoint, description in endpoints:
        test_endpoint(endpoint, description)
        time.sleep(1)  # Small delay between requests
    
    print(f"\n{'='*60}")
    print("🏁 TEST COMPLETED")
    print("If all endpoints show 'REAL DATA INDICATORS', the dashboard should display real data.")
    print("If you see 'NO REAL DATA INDICATORS' or mock data, there may be an issue.")
    print('='*60)

if __name__ == "__main__":
    main()
