#!/usr/bin/env python3
"""
Test rápido para verificar si Flask sirve las imágenes correctamente
"""
import requests
import time
import subprocess
import sys
from pathlib import Path

def test_image_serving():
    """Test si Flask sirve correctamente las imágenes"""
    
    print("🧪 TEST: Servicio de imágenes de Flask")
    print("=" * 50)
    
    # Lista de imágenes a testear
    test_images = [
        'news_951d3aa44203.jpg',
        'news_1f73950908b0.jpg', 
        'news_08ad704b863a.jpg',
        'news_4af66c3ab90d.png'
    ]
    
    base_url = 'http://localhost:5001/static/images/news/'
    
    print("🔍 Verificando archivos en disco:")
    for img in test_images:
        img_path = Path(f"./static/images/news/{img}")
        if img_path.exists():
            size = img_path.stat().st_size
            print(f"   ✅ {img}: {size:,} bytes")
        else:
            print(f"   ❌ {img}: NO EXISTE")
    
    print(f"\n🌐 Testeando URLs en Flask:")
    for img in test_images:
        url = f"{base_url}{img}"
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"   ✅ {url}: {response.status_code} - {len(response.content):,} bytes")
            else:
                print(f"   ❌ {url}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {url}: ERROR - {e}")
    
    print(f"\n📋 RESULTADO:")
    print("Si ves ✅ para las URLs, el problema está solucionado")
    print("Si ves ❌, Flask no está sirviendo las imágenes correctamente")

if __name__ == "__main__":
    test_image_serving()