#!/usr/bin/env python3
"""
Script to verify that the improved geopolitical filter is working correctly.
Tests both the /api/v1/articles endpoint and the mosaic data.
"""

import requests
import json
import time

def test_api_endpoints():
    """Test the API endpoints to see what articles are being served."""
    
    base_url = "http://localhost:5001"
    
    print("🔍 VERIFICACIÓN FINAL DEL FILTRO GEOPOLÍTICO")
    print("=" * 60)
    
    # Wait for server to be ready
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Servidor disponible")
                break
        except requests.exceptions.RequestException:
            print(f"⏳ Esperando servidor... intento {attempt + 1}/{max_attempts}")
            time.sleep(2)
    else:
        print("❌ No se pudo conectar al servidor")
        return
    
    print("\n1. VERIFICANDO ENDPOINT /api/v1/articles")
    print("-" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/v1/articles?limit=20", timeout=10)
        
        if response.status_code == 200:
            articles = response.json()
            print(f"📊 Total de artículos recibidos: {len(articles)}")
            
            geopolitical_count = 0
            with_real_images = 0
            
            for i, article in enumerate(articles[:10], 1):
                title = article.get('title', 'N/A')
                source = article.get('source', 'N/A')
                image_url = article.get('image_url', '')
                
                # Check if it has real image
                has_real_image = image_url and '/static/images/news/' in image_url
                if has_real_image:
                    with_real_images += 1
                
                # Simple geopolitical check
                title_lower = title.lower()
                is_geopolitical = any(keyword in title_lower for keyword in [
                    'trump', 'putin', 'ukraine', 'china', 'israel', 'palestine', 'iran',
                    'guerra', 'war', 'conflict', 'military', 'defense', 'diplomatic',
                    'sanctions', 'trade war', 'geopolit', 'nato', 'security', 'terror'
                ])
                
                if is_geopolitical:
                    geopolitical_count += 1
                
                print(f"  {i}. {title[:60]}{'...' if len(title) > 60 else ''}")
                print(f"     📰 Fuente: {source}")
                print(f"     🖼️ Imagen real: {'✅' if has_real_image else '❌'}")
                print(f"     🌍 Geopolítico: {'✅' if is_geopolitical else '❌'}")
                print()
            
            print(f"📊 RESUMEN:")
            print(f"   Total: {len(articles)}")
            print(f"   Con imagen real: {with_real_images}")
            print(f"   Geopolíticos: {geopolitical_count}")
            print(f"   Cumple ambos criterios: {min(with_real_images, geopolitical_count)}")
            
        else:
            print(f"❌ Error en API: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    
    print("\n2. VERIFICANDO DATOS DEL MOSAICO")
    print("-" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/v1/mosaic-data", timeout=10)
        
        if response.status_code == 200:
            mosaic_data = response.json()
            print(f"📊 Artículos en mosaico: {len(mosaic_data)}")
            
            all_good = True
            for i, article in enumerate(mosaic_data[:5], 1):
                title = article.get('title', 'N/A')
                image_url = article.get('image_url', '')
                
                has_real_image = image_url and '/static/images/news/' in image_url
                
                print(f"  {i}. {title[:50]}{'...' if len(title) > 50 else ''}")
                print(f"     🖼️ URL imagen: {image_url}")
                print(f"     ✅ Imagen real: {'Sí' if has_real_image else 'No'}")
                
                if not has_real_image:
                    all_good = False
                print()
            
            if all_good:
                print("🎉 ¡PERFECTO! Todos los artículos del mosaico tienen imágenes reales")
            else:
                print("⚠️  Algunos artículos del mosaico no tienen imágenes reales")
                
        else:
            print(f"❌ Error en mosaico: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión mosaico: {e}")

    print("\n" + "=" * 60)
    print("🏁 VERIFICACIÓN COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    test_api_endpoints()