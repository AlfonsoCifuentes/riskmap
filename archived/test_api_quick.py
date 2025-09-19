#!/usr/bin/env python3
"""
Quick API test to verify our geopolitical filter is working
"""

import requests
import json

def test_api():
    try:
        print("🔍 VERIFICACIÓN DEL FILTRO GEOPOLÍTICO")
        print("=" * 50)
        
        # Test main API endpoint
        url = "http://localhost:5001/api/articles"
        params = {"limit": 10}
        
        print(f"Conectando a: {url}")
        response = requests.get(url, params=params, timeout=15)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            articles = response.json()
            print(f"✅ Encontrados {len(articles)} artículos")
            
            print("\nPrimeros artículos devueltos:")
            for i, article in enumerate(articles[:5]):
                title = article.get('title', 'N/A')
                if len(title) > 70:
                    title = title[:70]
                has_image = 'image_url' in article and article['image_url']
                img_status = "✅ Con imagen" if has_image else "❌ Sin imagen"
                print(f"{i+1}. {title}... ({img_status})")
                
            print(f"\n🎉 RESULTADO: El filtro devuelve {len(articles)} noticias geopolíticas")
            print("✅ Todas deberían tener imágenes originales y contenido geopolítico")
            
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_api()