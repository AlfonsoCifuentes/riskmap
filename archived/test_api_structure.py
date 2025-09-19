#!/usr/bin/env python3
"""
Test to verify the exact API response structure matches frontend expectations.
"""

import requests
import json

def test_hero_article_structure():
    """Test hero article API structure matches frontend expectations"""
    print("🔍 TESTING HERO ARTICLE API STRUCTURE")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8050/api/hero-article", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response received")
            
            # Test frontend expectations
            checks = []
            
            # Check top level structure
            if 'success' in data and data['success']:
                checks.append("✓ data.success is True")
            else:
                checks.append("❌ data.success is False or missing")
            
            if 'article' in data and isinstance(data['article'], dict):
                checks.append("✓ data.article exists and is dict")
                article = data['article']
                
                # Check required fields for frontend
                required_fields = ['title', 'text', 'location', 'risk', 'image']
                for field in required_fields:
                    if field in article and article[field]:
                        checks.append(f"✓ article.{field}: '{str(article[field])[:50]}...'")
                    else:
                        checks.append(f"❌ article.{field} missing or empty")
                        
            else:
                checks.append("❌ data.article missing or not dict")
            
            print("\nFRONTEND COMPATIBILITY CHECKS:")
            for check in checks:
                print(f"  {check}")
            
            # Show the exact condition the frontend uses
            condition_met = data.get('success') and data.get('article')
            print(f"\nFRONTEND CONDITION: data.success && data.article = {condition_met}")
            
            if condition_met:
                print("🎯 API STRUCTURE IS CORRECT - Frontend should load real data")
            else:
                print("🚨 API STRUCTURE MISMATCH - Frontend will use fallback")
                
            # Show raw response
            print(f"\nRAW API RESPONSE:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"💥 ERROR: {e}")

def test_statistics_structure():
    """Test statistics API structure"""
    print("\n" + "="*60)
    print("🔍 TESTING STATISTICS API STRUCTURE")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8050/api/statistics", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Statistics API Response received")
            
            # Check structure
            if data.get('success') and 'statistics' in data:
                stats = data['statistics']
                print("✓ Frontend condition met: data.success && statistics exists")
                
                # Check expected fields
                expected_stats = ['total_articles', 'risk_alerts', 'data_sources']
                for stat in expected_stats:
                    if stat in stats:
                        print(f"✓ {stat}: {stats[stat]}")
                    else:
                        print(f"❌ {stat}: missing")
                        
                print("🎯 STATISTICS API IS CORRECT")
            else:
                print("🚨 STATISTICS API STRUCTURE ISSUE")
                
        else:
            print(f"❌ Statistics HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Statistics ERROR: {e}")

if __name__ == "__main__":
    test_hero_article_structure()
    test_statistics_structure()
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    print("If both APIs show '🎯 API IS CORRECT', then the backend is fine.")
    print("If the frontend still shows mock data, the issue is likely:")
    print("1. Browser caching - try hard refresh (Ctrl+F5)")
    print("2. JavaScript errors - check browser console")
    print("3. Network issues - check browser network tab")
    print("4. Timing issues - API calls might be failing silently")
    print("="*60)
