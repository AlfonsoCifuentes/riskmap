#!/usr/bin/env python3
"""
Script para probar todos los endpoints de la API y verificar que devuelven JSON válido
"""

import requests
import json
import time
from datetime import datetime

# Lista de endpoints críticos que el frontend usa
ENDPOINTS = [
    '/api/articles',
    '/api/hero-article',
    '/api/statistics',
    '/api/groq/analysis',
    '/api/alerts',
    '/api/analytics/conflicts',
    '/api/analytics/geojson',
    '/api/analytics/trends',
    '/api/vision/mosaic-positioning'
]

BASE_URL = 'http://localhost:8050'

def test_endpoint(endpoint):
    """Probar un endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Probando: {endpoint}")
    
    try:
        response = requests.get(url, timeout=10)
        
        # Verificar status code
        print(f"   Status: {response.status_code}")
        
        # Verificar content-type
        content_type = response.headers.get('Content-Type', 'No Content-Type')
        print(f"   Content-Type: {content_type}")
        
        if response.status_code == 200:
            # Intentar parsear JSON
            try:
                data = response.json()
                print(f"   ✅ JSON válido")
                print(f"   Claves: {list(data.keys()) if isinstance(data, dict) else 'No es dict'}")
                
                # Verificar si tiene campo success
                if isinstance(data, dict) and 'success' in data:
                    print(f"   Success: {data.get('success')}")
                    if not data.get('success'):
                        print(f"   Error: {data.get('error', 'No error message')}")
                
            except json.JSONDecodeError:
                print(f"   ❌ ERROR: No es JSON válido")
                print(f"   Contenido: {response.text[:200]}...")
                
        else:
            print(f"   ❌ ERROR: Status {response.status_code}")
            print(f"   Contenido: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ TIMEOUT: El endpoint tardó más de 10 segundos")
    except requests.exceptions.ConnectionError:
        print(f"   🔌 ERROR: No se puede conectar al servidor")
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")

def main():
    print(f"🚀 Iniciando pruebas de endpoints - {datetime.now()}")
    print(f"Servidor base: {BASE_URL}")
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Servidor respondiendo en {BASE_URL}")
    except:
        print(f"❌ ERROR: Servidor no responde en {BASE_URL}")
        return
    
    # Probar cada endpoint
    for endpoint in ENDPOINTS:
        test_endpoint(endpoint)
        time.sleep(0.5)  # Pequeña pausa entre requests
    
    print(f"\n🏁 Pruebas completadas - {datetime.now()}")

if __name__ == "__main__":
    main()
