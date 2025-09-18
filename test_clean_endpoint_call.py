#!/usr/bin/env python3
"""
Test clean endpoint
"""

import requests
import json

def test_clean_endpoint():
    try:
        response = requests.get('http://localhost:5002/api/articles/mosaic-clean')
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Clean endpoint funciona correctamente")
            print(f"Hero present: {data.get('hero') is not None}")
            print(f"Mosaic articles: {len(data.get('mosaic', []))}")
            
            # Verificar hero
            if data.get('hero'):
                hero = data['hero']
                print(f"\n🏆 HERO ARTICLE:")
                print(f"   Fields: {list(hero.keys())}")
                print(f"   Title: {hero.get('title', 'N/A')}")
                print(f"   Has summary: {'summary' in hero}")
                print(f"   Has content: {'content' in hero}")
                
            # Verificar primer artículo del mosaico
            if data.get('mosaic'):
                first = data['mosaic'][0]
                print(f"\n🎯 FIRST MOSAIC ARTICLE:")
                print(f"   Fields: {list(first.keys())}")
                print(f"   Title: {first.get('title', 'N/A')}")
                print(f"   Has summary: {'summary' in first}")
                print(f"   Has content: {'content' in first}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_clean_endpoint()