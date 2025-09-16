#!/usr/bin/env python3
"""
Script para verificar qué endpoints están registrados en Flask
"""

import requests
import json

def test_missing_endpoints():
    """Probar los endpoints específicos que faltan"""
    
    base_url = "http://localhost:5001"
    
    print("🔍 PROBANDO ENDPOINTS ESPECÍFICOS QUE FALTAN")
    print("=" * 60)
    
    # Lista de endpoints específicos que están fallando
    missing_endpoints = [
        "/api/news/conflicts",
        "/api/analytics/conflicts", 
        "/api/analytics/geojson",
        "/about",
        "/dashboard", 
        "/multivariate"
    ]
    
    for endpoint in missing_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"📍 {endpoint}")
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                # Mostrar un fragmento de la respuesta
                response_text = response.text[:150]
                print(f"   Response: {response_text}...")
            else:
                print(f"   ✅ Funciona correctamente")
            print()
                
        except requests.exceptions.RequestException as e:
            print(f"🔌 {endpoint} → Error: {e}")
            print()
    
    # También probar algunas imágenes que aparecen en los errores
    print("🖼️ PROBANDO IMÁGENES QUE APARECEN EN LOS ERRORES")
    print("=" * 60)
    
    image_urls = [
        "/data/images/mosaic_3090_1685e1ef.jpg",
        "/data/images/article_3091_650756a9.jpg",
        "/data/images/article_2979_0af77df1.jpg"
    ]
    
    for image_url in image_urls:
        try:
            response = requests.get(f"{base_url}{image_url}", timeout=5)
            print(f"🖼️ {image_url}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Imagen disponible")
            else:
                print(f"   ❌ Imagen no encontrada")
            print()
                
        except requests.exceptions.RequestException as e:
            print(f"🔌 {image_url} → Error: {e}")
            print()

if __name__ == "__main__":
    test_missing_endpoints()
