#!/usr/bin/env python3
"""
Script para diagnosticar problemas específicos en el endpoint /api/articles
"""
import requests
import time
import json

BASE_URL = "http://localhost:5001"

def test_articles_endpoint():
    print("🔍 Diagnosticando endpoint /api/articles...")
    
    # Test with different parameters to identify the issue
    test_cases = [
        {'params': {'limit': 5}, 'name': 'Límite pequeño (5 artículos)'},
        {'params': {'limit': 10}, 'name': 'Límite medio (10 artículos)'},
        {'params': {'limit': 25}, 'name': 'Límite estándar (25 artículos)'},
        {'params': {'limit': 5, 'smart_layout': 'false'}, 'name': 'Sin smart layout (5 artículos)'},
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        try:
            start_time = time.time()
            response = requests.get(
                f"{BASE_URL}/api/articles",
                params=test_case['params'],
                timeout=30
            )
            end_time = time.time()
            
            duration = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                articles_count = len(data.get('articles', []))
                print(f"   ✅ SUCCESS: {articles_count} artículos en {duration:.2f}s")
                
                # Check if translation is working
                if articles_count > 0:
                    first_article = data['articles'][0]
                    title = first_article.get('title', '')
                    print(f"   📰 Ejemplo: {title[:60]}...")
                    
                    # Check for translation indicators
                    if any(word in title.lower() for word in ['the', 'and', 'of', 'to', 'in']):
                        print("   ⚠️  Posible artículo no traducido detectado")
                
            else:
                print(f"   ❌ FAILED: Status {response.status_code}")
                print(f"   🕒 Tiempo transcurrido: {duration:.2f}s")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT después de 30 segundos")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def test_related_endpoints():
    """Test related endpoints to see if the problem is systemic"""
    print("\n" + "="*50)
    print("🔍 Testing endpoints relacionados...")
    
    endpoints = [
        '/api/status',
        '/api/hero-article', 
        '/api/articles/deduplicated'
    ]
    
    for endpoint in endpoints:
        print(f"\n🧪 Testing {endpoint}...")
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            end_time = time.time()
            
            duration = end_time - start_time
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS en {duration:.2f}s")
                
                try:
                    data = response.json()
                    if 'articles' in data:
                        count = len(data['articles'])
                        print(f"   📊 Contiene {count} artículos")
                except:
                    pass
            else:
                print(f"   ❌ FAILED: Status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def check_database_status():
    """Check if database has articles"""
    print("\n" + "="*50)
    print("🔍 Verificando estado de la base de datos...")
    
    try:
        import sqlite3
        conn = sqlite3.connect("./data/geopolitical_intel.db")
        cursor = conn.cursor()
        
        # Check total articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        print(f"📊 Total artículos en DB: {total}")
        
        # Check processed articles
        cursor.execute("SELECT COUNT(*) FROM articles WHERE processed = 1")
        processed = cursor.fetchone()[0]
        print(f"🧠 Artículos procesados: {processed}")
        
        # Check articles with images
        cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ''")
        with_images = cursor.fetchone()[0]
        print(f"🖼️  Artículos con imágenes: {with_images}")
        
        # Check recent articles
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-1 day')")
        recent = cursor.fetchone()[0]
        print(f"📅 Artículos recientes (24h): {recent}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando DB: {e}")

if __name__ == "__main__":
    print("RiskMap /api/articles Diagnostic Tool")
    print("="*50)
    
    check_database_status()
    test_articles_endpoint()
    test_related_endpoints()
    
    print("\n" + "="*50)
    print("✅ Diagnóstico completo")