#!/usr/bin/env python3
"""Test directo del endpoint /api/articles usando requests"""
import requests
import json
import time

def test_articles_endpoint_http():
    print("🔍 TESTING ENDPOINT /api/articles VÍA HTTP...")
    
    # URL del endpoint
    url = "http://localhost:5001/api/articles"
    
    print(f"📡 Probando: {url}")
    
    try:
        # Hacer request al endpoint
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ SUCCESS: {data.get('success', False)}")
            print(f"📰 Total artículos: {data.get('total', 0)}")
            print(f"🖼️  Artículos en respuesta: {len(data.get('articles', []))}")
            
            # Mostrar algunos artículos
            articles = data.get('articles', [])
            if articles:
                print("\n📰 Artículos del mosaico:")
                for i, article in enumerate(articles[:3]):
                    print(f"   {i+1}. {article.get('title', 'Sin título')[:60]}...")
                    print(f"      🖼️  {article.get('image', 'Sin imagen')[:60]}...")
                    print(f"      🎯 Riesgo: {article.get('risk', 'unknown')}")
                    print()
                
                print(f"🎯 ✅ MOSAICO FUNCIONARÁ: {len(articles)} artículos disponibles")
                return True
            else:
                print("❌ No hay artículos en la respuesta")
                return False
                
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está corriendo en puerto 5001?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Esperando que el servidor esté listo...")
    time.sleep(5)
    
    success = test_articles_endpoint_http()
    
    if success:
        print("\n🚀 ¡EL MOSAICO DEBERÍA FUNCIONAR AHORA!")
        print("   El error '❌ No se pudieron cargar artículos' debería estar resuelto")
    else:
        print("\n⚠️  El servidor puede no estar listo aún. Inténtalo de nuevo en unos segundos.")