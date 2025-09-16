#!/usr/bin/env python3
"""
Script para probar los nuevos endpoints de imágenes
"""

import requests
import json

def test_image_endpoints():
    """Probar los endpoints de imágenes"""
    base_url = "http://127.0.0.1:8050"
    
    print("🖼️  Probando endpoints de imágenes...")
    
    # 1. Probar estado de imágenes
    print("\n1. Estado de imágenes:")
    try:
        response = requests.get(f"{base_url}/api/images/status", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('statistics', {})
                print(f"   📊 Total artículos: {stats.get('total_articles', 0)}")
                print(f"   🖼️  Con imagen: {stats.get('with_images', 0)}")
                print(f"   ❌ Sin imagen: {stats.get('without_images', 0)}")
                print(f"   📈 Cobertura: {stats.get('coverage_percentage', 0)}%")
            else:
                print(f"   ❌ Error: {data.get('error')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Probar algunos artículos para ver si tienen imágenes reales
    print("\n2. Verificando imágenes reales en artículos:")
    try:
        response = requests.get(f"{base_url}/api/articles?limit=5", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                articles = data.get('articles', [])
                print(f"   📰 Artículos obtenidos: {len(articles)}")
                
                for i, article in enumerate(articles[:3]):
                    title = article.get('title', 'Sin título')[:50]
                    image_url = article.get('image', '')
                    has_real_image = article.get('has_real_image', False)
                    
                    print(f"\n   📰 Artículo {i+1}: {title}...")
                    print(f"      🖼️  Imagen: {image_url}")
                    print(f"      ✅ Imagen real: {'Sí' if has_real_image else 'No (placeholder)'}")
                    
                    # Verificar si la imagen existe
                    if has_real_image:
                        try:
                            img_response = requests.head(image_url, timeout=5)
                            print(f"      🌐 URL disponible: {'Sí' if img_response.status_code == 200 else 'No'}")
                        except:
                            print("      🌐 URL disponible: No se pudo verificar")
                
            else:
                print(f"   ❌ Error: {data.get('error')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Probar artículo héroe
    print("\n3. Verificando imagen del artículo héroe:")
    try:
        response = requests.get(f"{base_url}/api/hero-article", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                article = data.get('article', {})
                title = article.get('title', 'Sin título')[:50]
                image_url = article.get('image', '')
                has_real_image = article.get('has_real_image', False)
                
                print(f"   📰 Título: {title}...")
                print(f"   🖼️  Imagen: {image_url}")
                print(f"   ✅ Imagen real: {'Sí' if has_real_image else 'No (placeholder)'}")
                
                # Verificar si la imagen existe
                if has_real_image:
                    try:
                        img_response = requests.head(image_url, timeout=5)
                        print(f"   🌐 URL disponible: {'Sí' if img_response.status_code == 200 else 'No'}")
                    except:
                        print("   🌐 URL disponible: No se pudo verificar")
                
            else:
                print(f"   ❌ Error: {data.get('error')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_image_endpoints()
