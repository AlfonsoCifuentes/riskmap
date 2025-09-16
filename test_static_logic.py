#!/usr/bin/env python3
"""
Test directo del sistema de rutas estáticas sin arrancar Flask completo
"""
import os
from pathlib import Path
from flask import Flask, send_from_directory

def test_static_route_logic():
    """Test la lógica de enrutamiento estático sin arrancar el servidor"""
    
    print("🧪 TEST: Lógica de enrutamiento de imágenes")
    print("=" * 55)
    
    # Simular Flask app simple
    app = Flask(__name__)
    
    # Replicar nuestra lógica de static_files
    def static_files_logic(filename):
        """Replicar la lógica de nuestra ruta estática"""
        print(f"   🔍 Procesando: {filename}")
        
        # Check if it's a news image first (in root static folder)
        if filename.startswith('images/news/'):
            print(f"   📰 Es imagen de noticias")
            full_path = f"static/{filename}"  # static/images/news/xxx.jpg
            if os.path.exists(full_path):
                print(f"   ✅ Archivo existe: {full_path}")
                return f"SERVIR desde raíz: {full_path}"
            else:
                print(f"   ❌ No existe: {full_path}")
                
        # Otherwise serve from src/web/static
        src_path = f"src/web/static/{filename}"
        if os.path.exists(src_path):
            print(f"   ✅ Archivo existe en src: {src_path}")
            return f"SERVIR desde src: {src_path}"
        else:
            print(f"   ❌ No existe en src: {src_path}")
            return "404 NOT FOUND"
    
    # Test con imágenes reales
    test_files = [
        'images/news/news_951d3aa44203.jpg',
        'images/news/news_1f73950908b0.jpg',
        'images/news/news_08ad704b863a.jpg',
        'css/main.css',  # Para probar ruta normal
        'js/app.js'      # Para probar ruta normal
    ]
    
    print("📂 Estado de archivos:")
    for filename in test_files:
        print(f"\n🔍 Testeando: {filename}")
        result = static_files_logic(filename)
        print(f"   ➡️  Resultado: {result}")
    
    # Verificar directorio actual
    print(f"\n📍 Directorio actual: {os.getcwd()}")
    print(f"📁 ./static/images/news/ existe: {os.path.exists('./static/images/news/')}")
    
    if os.path.exists('./static/images/news/'):
        files = os.listdir('./static/images/news/')
        print(f"📊 Archivos en directorio: {len(files)}")
        print(f"📝 Primeros 5 archivos:")
        for f in files[:5]:
            print(f"   - {f}")

if __name__ == "__main__":
    test_static_route_logic()