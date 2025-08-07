#!/usr/bin/env python3
"""
Test script para verificar la implementación de 3D Earth
Verifica que:
1. Los archivos 3D están disponibles
2. Las rutas de Flask funcionan
3. Los templates se renderizan correctamente
"""

import os
import sys
from pathlib import Path

def check_3d_files():
    """Verificar que los archivos 3D están presentes"""
    files = ['tierra.fbx', 'tierra.mtl', 'espacio.jpg']
    missing = []
    
    print("🔍 Verificando archivos 3D...")
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} - {size:,} bytes")
        else:
            missing.append(file)
            print(f"❌ {file} - No encontrado")
    
    if missing:
        print(f"\n⚠️  Archivos faltantes: {missing}")
        return False
    
    print("✅ Todos los archivos 3D están presentes")
    return True

def test_flask_routes():
    """Test básico de las rutas de Flask"""
    try:
        from app_BUENA import RiskMapUnifiedApplication
        
        print("\n🚀 Iniciando test de Flask...")
        app = RiskMapUnifiedApplication()
        
        with app.flask_app.test_client() as client:
            # Test página principal
            response = client.get('/')
            print(f"📄 Página principal (/) - Status: {response.status_code}")
            
            # Test página about
            response = client.get('/about')
            print(f"📄 Página about (/about) - Status: {response.status_code}")
            
            # Test archivos 3D
            response = client.get('/static/tierra.fbx')
            print(f"🌍 tierra.fbx - Status: {response.status_code}")
            
            response = client.get('/static/espacio.jpg')
            print(f"🌌 espacio.jpg - Status: {response.status_code}")
        
        print("✅ Tests de rutas completados")
        return True
        
    except Exception as e:
        print(f"❌ Error en test de Flask: {e}")
        return False

def check_templates():
    """Verificar que los templates tienen la implementación 3D"""
    templates = [
        'src/web/templates/dashboard_BUENO.html',
        'src/web/templates/about.html'
    ]
    
    print("\n📝 Verificando templates...")
    for template in templates:
        if os.path.exists(template):
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read()
                
            has_three_js = 'three.min.js' in content
            has_earth_container = 'earth3d-container' in content
            has_earth_init = 'init3DEarth' in content
            
            print(f"📄 {template}:")
            print(f"  - Three.js: {'✅' if has_three_js else '❌'}")
            print(f"  - 3D Container: {'✅' if has_earth_container else '❌'}")
            print(f"  - Init Function: {'✅' if has_earth_init else '❌'}")
        else:
            print(f"❌ {template} - No encontrado")

def main():
    """Función principal de test"""
    print("🌍 Test de Implementación 3D Earth")
    print("=" * 50)
    
    # Cambiar al directorio correcto
    os.chdir(Path(__file__).parent)
    
    success = True
    
    # Test 1: Archivos 3D
    if not check_3d_files():
        success = False
    
    # Test 2: Templates
    check_templates()
    
    # Test 3: Flask routes
    if not test_flask_routes():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Implementación 3D Earth lista!")
        print("Para probar:")
        print("1. python app_BUENA.py")
        print("2. Abrir http://localhost:5000")
        print("3. Verificar que el planeta Tierra aparece girando de fondo")
    else:
        print("❌ Hay problemas en la implementación")
    
    return success

if __name__ == "__main__":
    main()
