#!/usr/bin/env python3
"""
Test directo con requests hacia Flask minimalista
"""
import requests
import time

def test_flask_images():
    """Test las imágenes con requests"""
    
    base_url = "http://localhost:5002/static/images/news/"
    test_images = [
        "news_951d3aa44203.jpg",
        "news_1f73950908b0.jpg", 
        "news_08ad704b863a.jpg"
    ]
    
    print("🧪 TEST: Imágenes con Flask minimalista")
    print("=" * 50)
    
    for img in test_images:
        url = f"{base_url}{img}"
        try:
            print(f"🔍 Testeando: {url}")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {response.status_code} - {len(response.content):,} bytes")
                print(f"   📋 Content-Type: {response.headers.get('content-type', 'N/A')}")
            else:
                print(f"   ❌ {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERROR: {e}")
        
        time.sleep(0.5)
    
    print("\n🌐 Test página HTML:")
    try:
        response = requests.get("http://localhost:5002/test", timeout=5)
        if response.status_code == 200:
            print("   ✅ Página de test carga correctamente")
            print("   📝 Contiene tags <img>:", response.text.count('<img>'))
        else:
            print(f"   ❌ Error en página: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("⏳ Esperando 2 segundos para que Flask arranque...")
    time.sleep(2)
    test_flask_images()