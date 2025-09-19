#!/usr/bin/env python3
"""
Script de prueba completo para el dashboard multiidioma
"""

import requests
import json
from datetime import datetime

def test_dashboard_endpoints():
    """Prueba todos los endpoints principales del dashboard"""
    
    base_url = "http://127.0.0.1:5000"
    languages = ['en', 'es', 'de', 'fr', 'ru', 'zh']
    
    print("🧪 TESTING MULTILINGUAL DASHBOARD")
    print("=" * 50)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✅ Main page: {response.status_code}")
    except Exception as e:
        print(f"❌ Main page error: {e}")
        return
    
    # Test endpoints for each language
    endpoints = [
        '/api/summary',
        '/api/articles',
        '/api/ai_analysis',
        '/api/article-of-day',
        '/api/high_risk_articles',
        '/api/translate'
    ]
    
    results = {}
    
    for lang in languages:
        print(f"\n🌍 Testing language: {lang}")
        results[lang] = {}
        
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}?lang={lang}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    results[lang][endpoint] = {
                        'status': 'SUCCESS',
                        'has_data': bool(data),
                        'size': len(json.dumps(data))
                    }
                    print(f"  ✅ {endpoint}: OK ({len(json.dumps(data))} bytes)")
                    
                    # Special checks
                    if endpoint == '/api/articles' and 'articles' in data:
                        lang_articles = [a for a in data['articles'] if a.get('language') == lang]
                        print(f"     📰 Articles in {lang}: {len(lang_articles)}")
                        
                    elif endpoint == '/api/ai_analysis' and 'analysis' in data:
                        print(f"     🤖 AI analysis length: {len(data['analysis'])} chars")
                        
                else:
                    results[lang][endpoint] = {'status': 'ERROR', 'code': response.status_code}
                    print(f"  ❌ {endpoint}: {response.status_code}")
                    
            except Exception as e:
                results[lang][endpoint] = {'status': 'EXCEPTION', 'error': str(e)}
                print(f"  ⚠️  {endpoint}: {str(e)[:50]}")
    
    # Summary report
    print(f"\n📊 SUMMARY REPORT")
    print("=" * 50)
    
    for lang in languages:
        successful = sum(1 for r in results[lang].values() if r.get('status') == 'SUCCESS')
        total = len(endpoints)
        percentage = (successful / total) * 100
        print(f"{lang}: {successful}/{total} endpoints working ({percentage:.1f}%)")
    
    # Test database content
    print(f"\n💾 DATABASE CONTENT CHECK")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Total articles: {data.get('total_articles', 0)}")
            print(f"Languages: {data.get('languages_supported', 0)}")
            print(f"Recent articles: {data.get('articles_count', 0)}")
            
            # Check language distribution
            by_lang = data.get('articles_by_language', {})
            print("\nArticles by language:")
            for lang, count in sorted(by_lang.items(), key=lambda x: x[1], reverse=True):
                print(f"  {lang}: {count}")
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    
    # Test AI analysis specifically
    print(f"\n🤖 AI ANALYSIS DETAILED TEST")
    print("=" * 50)
    
    for lang in ['en', 'es']:
        try:
            response = requests.get(f"{base_url}/api/ai_analysis?lang={lang}", timeout=20)
            if response.status_code == 200:
                data = response.json()
                print(f"{lang} AI Analysis:")
                print(f"  ✅ Status: Working")
                print(f"  📝 Analysis length: {len(data.get('analysis', ''))}")
                print(f"  🏷️  Headline: {data.get('headline', 'N/A')[:50]}")
                print(f"  📅 Date: {data.get('published_date', 'N/A')}")
                print(f"  🔍 NLP Enhanced: {data.get('nlp_enhanced', False)}")
                print(f"  ⚠️  Risk Level: {data.get('risk_level', 'N/A')}")
            else:
                print(f"{lang} AI Analysis: ❌ Error {response.status_code}")
        except Exception as e:
            print(f"{lang} AI Analysis: ⚠️ Exception {str(e)[:50]}")
    
    print(f"\n✅ TEST COMPLETED at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    test_dashboard_endpoints()
