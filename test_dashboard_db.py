#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión del dashboard con la base de datos
"""

import requests
import json
import time

def test_dashboard_endpoints():
    """Probar los nuevos endpoints del dashboard"""
    base_url = "http://127.0.0.1:8050"
    
    print("🧪 Probando endpoints del dashboard...")
    
    # Probar endpoint de estadísticas
    try:
        print("\n1. Probando /api/statistics...")
        response = requests.get(f"{base_url}/api/statistics", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Estadísticas: {data}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error conectando: {e}")
    
    # Probar endpoint de artículos
    try:
        print("\n2. Probando /api/articles...")
        response = requests.get(f"{base_url}/api/articles?limit=5", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Artículos encontrados: {data.get('total', 0)}")
            if data.get('articles'):
                for i, article in enumerate(data['articles'][:2], 1):
                    print(f"   📰 {i}. {article.get('title', 'Sin título')[:60]}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error conectando: {e}")
    
    # Probar endpoint de artículo héroe
    try:
        print("\n3. Probando /api/hero-article...")
        response = requests.get(f"{base_url}/api/hero-article", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Artículo héroe: {data.get('article', {}).get('title', 'Sin título')[:60]}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error conectando: {e}")
    
    # Probar dashboard principal
    try:
        print("\n4. Probando /dashboard...")
        response = requests.get(f"{base_url}/dashboard", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Dashboard carga correctamente")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error conectando: {e}")
    
    print("\n✅ Pruebas completadas!")
    print("\n💡 Instrucciones:")
    print("1. Asegúrate de que app_BUENA.py está ejecutándose")
    print("2. Abre http://127.0.0.1:8050/dashboard en tu navegador")
    print("3. Verifica que los datos mostrados son reales de la base de datos")

if __name__ == '__main__':
    test_dashboard_endpoints()
