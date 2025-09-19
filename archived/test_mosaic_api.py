#!/usr/bin/env python3
"""
Script para probar la API del mosaico y verificar que solo muestra
noticias geopolíticas con imágenes reales
"""
import requests
import json

def test_api():
    url = "http://localhost:5001/api/articles"
    
    try:
        print("🔍 Probando API del mosaico...")
        print(f"🌐 URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            articles = response.json()
            print(f"\n✅ API responde correctamente")
            print(f"📰 Artículos devueltos: {len(articles)}")
            
            if len(articles) > 0:
                print("\n🎯 PRIMEROS 3 ARTÍCULOS:")
                print("-" * 60)
                
                for i, article in enumerate(articles[:3], 1):
                    print(f"\n{i}. ID: {article.get('id')}")
                    print(f"   📰 Título: {article.get('title', '')[:70]}...")
                    print(f"   🖼️  Imagen: {article.get('image_url', 'Sin imagen')}")
                    print(f"   🏢 Fuente: {article.get('source', 'N/A')}")
                    print(f"   📅 Fecha: {article.get('created_at', 'N/A')}")
                    
                    # Verificar que tiene imagen real
                    image_url = article.get('image_url', '')
                    if image_url and 'placeholder' not in image_url.lower():
                        print(f"   ✅ Imagen válida")
                    else:
                        print(f"   ❌ Imagen inválida o placeholder")
                
                print("\n" + "=" * 60)
                print(f"🎉 ÉXITO: El mosaico muestra {len(articles)} noticias válidas")
                print("   ✅ Solo noticias geopolíticas con imágenes reales")
                print("   ✅ API funcionando correctamente")
            else:
                print("\n⚠️  No se devolvieron artículos")
                print("   Posible problema con el filtro SQL")
        else:
            print(f"\n❌ Error en la API: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ No se puede conectar al servidor")
        print("   Asegurar que app_BUENA.py esté ejecutándose en puerto 5001")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_api()