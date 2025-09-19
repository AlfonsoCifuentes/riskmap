#!/usr/bin/env python3
"""
Test del endpoint de deduplicación para debug
"""

import requests
import json
from datetime import datetime

def test_deduplication_endpoint():
    print("🧪 PROBANDO ENDPOINT DE DEDUPLICACIÓN")
    print("=" * 50)
    
    try:
        # Test del endpoint de deduplicación
        print("📞 Llamando a /api/articles/deduplicated...")
        response = requests.get("http://localhost:8050/api/articles/deduplicated?hours=24", timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            
            if data.get('success'):
                print(f"🎯 Hero: {data.get('hero', {}).get('title', 'No title')[:50]}...")
                print(f"📰 Artículos del mosaico: {len(data.get('mosaic', []))}")
                
                # Mostrar algunos ejemplos del mosaico
                mosaic = data.get('mosaic', [])
                for i, article in enumerate(mosaic[:3]):
                    risk = article.get('risk_level', article.get('risk', 'unknown'))
                    print(f"  {i+1}. [{risk.upper()}] {article.get('title', 'Sin título')[:40]}...")
                
                # Estadísticas
                stats = data.get('stats', {})
                print(f"📊 Estadísticas:")
                print(f"  - Total procesados: {stats.get('total_processed', 0)}")
                print(f"  - Duplicados removidos: {stats.get('duplicates_removed', 0)}")
                print(f"  - Únicos: {stats.get('unique_articles', 0)}")
                
            else:
                print(f"❌ Error en response: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(response.text[:500])
    
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor (¿está corriendo app_BUENA.py?)")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_hero_endpoint():
    print("\n🦸 PROBANDO ENDPOINT HERO")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:8050/api/hero-article", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            
            if data.get('success'):
                article = data.get('article', {})
                print(f"🎯 Título: {article.get('title', 'Sin título')[:50]}...")
                print(f"⚠️ Riesgo: {article.get('risk', 'unknown').upper()}")
                print(f"📍 Ubicación: {article.get('location', 'Sin ubicación')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_summary_endpoint():
    print("\n📝 PROBANDO ENDPOINT SUMMARY")
    print("=" * 35)
    
    try:
        # Probar con un ID de artículo que existe
        response = requests.get("http://localhost:8050/api/article/1/summary", timeout=10)
        print(f"Status Code (ID=1): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            
            if data.get('success'):
                summary = data.get('summary', '')
                print(f"📝 Resumen: {summary[:100]}...")
            else:
                print(f"❌ Error: {data.get('error', 'Unknown')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_deduplication_endpoint()
    test_hero_endpoint()
    test_summary_endpoint()
    
    print(f"\n⏰ Test completado: {datetime.now().strftime('%H:%M:%S')}")
