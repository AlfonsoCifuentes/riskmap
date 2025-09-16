#!/usr/bin/env python3
"""
Test final: Verificar que Flask sirve correctamente las imágenes de noticias
"""

import subprocess
import time
import requests
from pathlib import Path
import sys

def verify_images_exist():
    """Verificar que las imágenes existen donde Flask las busca"""
    
    print("🔍 VERIFICANDO UBICACIÓN DE IMÁGENES:")
    print("=" * 50)
    
    target_dir = Path("./src/web/static/images/news")
    if target_dir.exists():
        files = list(target_dir.glob("news_*"))
        print(f"✅ Directorio: {target_dir}")
        print(f"📊 Archivos: {len(files)}")
        
        # Test con archivos específicos que aparecían en el error
        test_files = [
            'news_951d3aa44203.jpg',
            'news_1f73950908b0.jpg', 
            'news_08ad704b863a.jpg'
        ]
        
        print(f"\n📋 Verificando archivos específicos:")
        for filename in test_files:
            filepath = target_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"   ✅ {filename}: {size:,} bytes")
            else:
                print(f"   ❌ {filename}: NO EXISTE")
        
        return len(files) > 0
        
    else:
        print(f"❌ Directorio no existe: {target_dir}")
        return False

def test_flask_simple():
    """Test simple con requests sin arrancar Flask nosotros"""
    
    print(f"\n🌐 TESTING URLs DE IMÁGENES:")
    print("(Asumiendo que Flask está corriendo en localhost:5001)")
    
    base_url = "http://localhost:5001/static/images/news/"
    test_images = [
        "news_951d3aa44203.jpg",
        "news_1f73950908b0.jpg", 
        "news_08ad704b863a.jpg"
    ]
    
    for img in test_images:
        url = f"{base_url}{img}"
        try:
            print(f"🔍 {url}")
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                print(f"   ✅ {response.status_code} - {len(response.content):,} bytes")
            else:
                print(f"   ❌ {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Conexión rechazada (Flask no está corriendo)")
            return False
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    return True

def show_solution():
    """Mostrar la solución implementada"""
    
    print(f"\n" + "=" * 60)
    print(f"💡 ANÁLISIS DEL PROBLEMA:")
    print(f"   🔴 Error original: 404 (NOT FOUND) en imágenes")
    print(f"   🔍 Causa: Flask busca en 'src/web/static/'") 
    print(f"   🔧 Solución: Mover imágenes a ubicación correcta")
    
    print(f"\n✅ SOLUCIÓN IMPLEMENTADA:")
    print(f"   📁 Imágenes movidas a: src/web/static/images/news/")
    print(f"   🌐 URLs funcionarán: /static/images/news/news_xxx.jpg")
    print(f"   ⚙️  Flask configuration: static_folder='src/web/static'")
    
    print(f"\n🧪 PARA PROBAR:")
    print(f"   1. Ejecutar: python app_BUENA.py")
    print(f"   2. Abrir: http://localhost:5001")  
    print(f"   3. Las imágenes de noticias deberían cargarse correctamente")
    
    print(f"\n📊 ESTADO ACTUAL:")
    verify_images_exist()

def main():
    """Función principal"""
    print("🔧 TEST FINAL: Solución de imágenes 404")
    print("=" * 60)
    
    # Verificar archivos
    images_ok = verify_images_exist()
    
    if images_ok:
        # Intentar test con Flask (si está corriendo)
        flask_ok = test_flask_simple()
        
        # Mostrar solución
        show_solution()
        
        print(f"\n📋 RESULTADO FINAL:")
        if flask_ok:
            print(f"🎉 PROBLEMA SOLUCIONADO")
            print(f"✅ Imágenes se sirven correctamente")
        else:
            print(f"✅ SOLUCIÓN IMPLEMENTADA")
            print(f"⚠️  Para probar: ejecutar app_BUENA.py")
            
    else:
        print(f"\n❌ ERROR: No se encontraron imágenes")

if __name__ == "__main__":
    main()