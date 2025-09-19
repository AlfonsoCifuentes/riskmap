#!/usr/bin/env python3
"""
Test del Sistema CCTV
Verifica que todos los componentes estén funcionando correctamente
"""

import sys
import os
import importlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_dependencies():
    """Test de dependencias requeridas"""
    print("🔍 Verificando dependencias del sistema CCTV...")
    
    dependencies = {
        'cv2': 'OpenCV',
        'torch': 'PyTorch', 
        'ultralytics': 'YOLO',
        'flask_socketio': 'Flask-SocketIO',
        'yt_dlp': 'yt-dlp',
        'ffmpeg': 'FFmpeg Python',
        'celery': 'Celery',
        'redis': 'Redis',
        'geopandas': 'GeoPandas',
        'shapely': 'Shapely'
    }
    
    results = {}
    for module, name in dependencies.items():
        try:
            importlib.import_module(module)
            print(f"  ✅ {name}")
            results[module] = True
        except ImportError:
            print(f"  ❌ {name} - NO DISPONIBLE")
            results[module] = False
    
    return results

def test_cctv_system():
    """Test del sistema CCTV principal"""
    print("\n🔍 Verificando sistema CCTV...")
    
    try:
        from cams import CCTVSystem
        print("  ✅ Importación del sistema CCTV exitosa")
        
        # Test de inicialización
        config = {
            'data_dir': 'data',
            'static_dir': 'static',
            'gpu_device': 'cpu',
            'fps_analyze': 1
        }
        
        cctv = CCTVSystem(config)
        print("  ✅ Inicialización del sistema exitosa")
        
        # Test de estado del sistema
        status = cctv.get_system_status()
        print(f"  ✅ Estado del sistema: {status.get('status', 'unknown')}")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error en el sistema: {e}")
        return False

def test_cctv_routes():
    """Test de las rutas Flask"""
    print("\n🔍 Verificando rutas del sistema CCTV...")
    
    try:
        from cams.routes import register_cctv_routes
        print("  ✅ Importación de rutas exitosa")
        
        from flask import Flask
        app = Flask(__name__)
        
        # Test de registro de rutas
        register_cctv_routes(app, None)  # Sin SocketIO para el test
        print("  ✅ Registro de rutas exitoso")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Error de importación de rutas: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error en rutas: {e}")
        return False

def test_data_files():
    """Test de archivos de datos"""
    print("\n🔍 Verificando archivos de datos...")
    
    files_to_check = [
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
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - NO ENCONTRADO")
            all_exist = False
    
    return all_exist

def test_integration():
    """Test de integración con la aplicación principal"""
    print("\n🔍 Verificando integración con RiskMap...")
    
    try:
        # Test de importación en app_BUENA.py
        with open('app_BUENA.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            'from cams import CCTVSystem',
            'from cams.routes import register_cctv_routes',
            'cctv_system_initialized',
            'register_cctv_routes'
        ]
        
        all_integrated = True
        for check in checks:
            if check in content:
                print(f"  ✅ {check} encontrado en app_BUENA.py")
            else:
                print(f"  ❌ {check} NO encontrado en app_BUENA.py")
                all_integrated = False
        
        return all_integrated
        
    except Exception as e:
        print(f"  ❌ Error verificando integración: {e}")
        return False

def main():
    """Función principal de testing"""
    print("🚀 Iniciando tests del Sistema CCTV\n")
    
    # Test de dependencias
    deps_ok = test_dependencies()
    
    # Test del sistema principal
    system_ok = test_cctv_system()
    
    # Test de rutas
    routes_ok = test_cctv_routes()
    
    # Test de archivos de datos
    files_ok = test_data_files()
    
    # Test de integración
    integration_ok = test_integration()
    
    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE TESTS")
    print("="*50)
    
    total_deps = len([v for v in deps_ok.values() if v])
    missing_deps = len([v for v in deps_ok.values() if not v])
    
    print(f"Dependencias: {total_deps} instaladas, {missing_deps} faltantes")
    print(f"Sistema CCTV: {'✅ OK' if system_ok else '❌ ERROR'}")
    print(f"Rutas Flask: {'✅ OK' if routes_ok else '❌ ERROR'}")
    print(f"Archivos de datos: {'✅ OK' if files_ok else '❌ ERROR'}")
    print(f"Integración: {'✅ OK' if integration_ok else '❌ ERROR'}")
    
    # Estado general
    if all([system_ok, routes_ok, files_ok, integration_ok]) and missing_deps == 0:
        print("\n🎉 SISTEMA CCTV COMPLETAMENTE OPERATIVO")
        return 0
    elif all([system_ok, routes_ok, files_ok, integration_ok]):
        print(f"\n⚠️  SISTEMA CCTV OPERATIVO CON {missing_deps} DEPENDENCIAS FALTANTES")
        print("Instale las dependencias faltantes con:")
        print("pip install -r requirements_cctv.txt")
        return 1
    else:
        print("\n❌ SISTEMA CCTV CON ERRORES")
        print("Revise los errores anteriores y corrija los problemas")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
