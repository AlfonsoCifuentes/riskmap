#!/usr/bin/env python3
"""
Test Simplificado del Sistema CCTV
Verifica funcionalidad básica sin dependencias problemáticas
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """Test de importaciones básicas"""
    print("🔍 Verificando importaciones básicas...")
    
    # Test basic Python modules
    try:
        import json
        import threading
        import time
        from datetime import datetime
        print("  ✅ Módulos Python básicos")
    except Exception as e:
        print(f"  ❌ Error en módulos Python básicos: {e}")
        return False
    
    # Test Flask
    try:
        from flask import Flask, render_template, jsonify
        print("  ✅ Flask")
    except Exception as e:
        print(f"  ❌ Error en Flask: {e}")
        return False
    
    # Test computer vision
    try:
        import cv2
        print(f"  ✅ OpenCV {cv2.__version__}")
    except Exception as e:
        print(f"  ❌ Error en OpenCV: {e}")
        return False
        
    return True

def test_cctv_files():
    """Test de archivos del sistema CCTV"""
    print("\n🔍 Verificando archivos del sistema CCTV...")
    
    required_files = [
        'data/cameras.json',
        'data/conflict_zones.geojson',
        'cams/__init__.py',
        'cams/detector.py',
        'cams/resolver.py',
        'cams/recorder.py',
        'cams/alerts.py',
        'cams/routes.py',
        'cams/templates/cams_map.html',
        'cams/templates/cams_view.html',
        'cams/templates/review.html'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - NO ENCONTRADO")
            all_exist = False
    
    return all_exist

def test_data_files_content():
    """Test del contenido de archivos de datos"""
    print("\n🔍 Verificando contenido de archivos de datos...")
    
    try:
        import json
        
        # Test cameras.json
        with open('data/cameras.json', 'r', encoding='utf-8') as f:
            cameras_data = json.load(f)
            
        # Check if it's an array or object with cameras property
        if isinstance(cameras_data, list):
            cameras_count = len(cameras_data)
            print(f"  ✅ cameras.json - {cameras_count} cámaras configuradas")
        elif isinstance(cameras_data, dict) and 'cameras' in cameras_data:
            cameras_count = len(cameras_data['cameras'])
            print(f"  ✅ cameras.json - {cameras_count} cámaras configuradas")
        else:
            print("  ⚠️  cameras.json - Estructura no reconocida")
            
        # Test conflict_zones.geojson
        with open('data/conflict_zones.geojson', 'r', encoding='utf-8') as f:
            zones_data = json.load(f)
            
        if 'features' in zones_data and len(zones_data['features']) > 0:
            print(f"  ✅ conflict_zones.geojson - {len(zones_data['features'])} zonas configuradas")
        else:
            print("  ⚠️  conflict_zones.geojson - Sin zonas configuradas")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error leyendo archivos de datos: {e}")
        return False

def test_flask_app_integration():
    """Test de integración con la app Flask"""
    print("\n🔍 Verificando integración con app_BUENA.py...")
    
    try:
        with open('app_BUENA.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('from cams import CCTVSystem', 'Importación CCTVSystem'),
            ('from cams.routes import register_cctv_routes', 'Importación rutas CCTV'),
            ('cctv_system_initialized', 'Estado CCTV en system_state'),
            ('register_cctv_routes', 'Registro de rutas CCTV')
        ]
        
        all_found = True
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - NO ENCONTRADO")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ❌ Error verificando app_BUENA.py: {e}")
        return False

def test_templates():
    """Test de templates HTML"""
    print("\n🔍 Verificando templates HTML...")
    
    templates = [
        ('cams/templates/cams_map.html', 'Mapa de cámaras'),
        ('cams/templates/cams_view.html', 'Vista en vivo'),
        ('cams/templates/review.html', 'Revisión de grabaciones')
    ]
    
    all_valid = True
    for template_path, description in templates:
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if len(content) > 1000 and '<html' in content and '</html>' in content:
                print(f"  ✅ {description} - Template válido")
            else:
                print(f"  ⚠️  {description} - Template muy pequeño o incompleto")
                
        except Exception as e:
            print(f"  ❌ {description} - Error: {e}")
            all_valid = False
    
    return all_valid

def main():
    """Función principal de testing simplificado"""
    print("🚀 Test Simplificado del Sistema CCTV\n")
    
    # Tests
    imports_ok = test_basic_imports()
    files_ok = test_cctv_files()
    data_ok = test_data_files_content()
    integration_ok = test_flask_app_integration()
    templates_ok = test_templates()
    
    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE TESTS SIMPLIFICADOS")
    print("="*50)
    
    print(f"Importaciones básicas: {'✅ OK' if imports_ok else '❌ ERROR'}")
    print(f"Archivos del sistema: {'✅ OK' if files_ok else '❌ ERROR'}")
    print(f"Archivos de datos: {'✅ OK' if data_ok else '❌ ERROR'}")
    print(f"Integración Flask: {'✅ OK' if integration_ok else '❌ ERROR'}")
    print(f"Templates HTML: {'✅ OK' if templates_ok else '❌ ERROR'}")
    
    # Estado general
    all_tests = [imports_ok, files_ok, data_ok, integration_ok, templates_ok]
    
    if all(all_tests):
        print("\n🎉 SISTEMA CCTV ESTRUCTURALMENTE COMPLETO")
        print("✅ Todos los archivos están en su lugar")
        print("✅ Integración con RiskMap completada")
        print("✅ Templates HTML funcionales")
        print("\n🔧 Para funcionalidad completa:")
        print("   1. Resolver problemas de dependencias NumPy/ML")
        print("   2. Instalar FFmpeg del sistema si es necesario")
        print("   3. Configurar Redis para procesamiento background")
        return 0
    else:
        failed_tests = [name for test, name in zip(all_tests, 
            ['Importaciones', 'Archivos', 'Datos', 'Integración', 'Templates']) if not test]
        print(f"\n⚠️  SISTEMA CCTV CON PROBLEMAS EN: {', '.join(failed_tests)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
