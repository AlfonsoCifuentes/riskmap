#!/usr/bin/env python3
"""
Test simple del endpoint después de las correcciones
"""

import requests
import json

def test_endpoint():
    """Test básico del endpoint"""
    print("🌐 Testing endpoint /api/articles...")
    
    try:
        response = requests.get('http://localhost:5001/api/articles', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Articles returned: {len(articles)}")
            
            if len(articles) > 0:
                first = articles[0]
                print(f"\n📰 Sample article:")
                print(f"  ID: {first.get('id')}")
                print(f"  Title: {first.get('title', '')[:50]}...")
                print(f"  Summary: {first.get('summary', '')[:50]}...")
                print(f"  Image: {first.get('image_url', '')}")
                
                if '<think>' in first.get('summary', ''):
                    print("  ❌ PROBLEMA: Summary contiene <think>")
                else:
                    print("  ✅ Summary limpio")
                    
                if 'picsum.photos' in first.get('image_url', ''):
                    print("  ✅ Usando placeholder corregido")
                elif first.get('image_url', '').startswith('http'):
                    print("  ✅ Imagen válida")
                else:
                    print("  ❌ Problema con imagen")
            
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_endpoint()