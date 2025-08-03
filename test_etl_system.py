"""
Script de prueba para el sistema ETL de conflictos geopolíticos
Verifica que todos los componentes estén funcionando correctamente
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Añadir el directorio raíz al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_etl_imports():
    """Probar que las importaciones del ETL funcionan"""
    print("🧪 Probando importaciones del ETL...")
    
    try:
        from src.etl.config import get_etl_config, get_api_credentials, validate_configuration
        print("✅ Configuración ETL importada correctamente")
        
        from src.etl.flask_controller import ETLController, create_etl_routes, get_etl_controller
        print("✅ Controlador Flask ETL importado correctamente")
        
        try:
            from src.etl.conflict_data_etl import ConflictDataETL, ETLConfig, create_etl_instance
            print("✅ Motor ETL principal importado correctamente")
            return True, True
        except ImportError as e:
            print(f"⚠️ Motor ETL principal no disponible: {e}")
            return True, False
            
    except ImportError as e:
        print(f"❌ Error importando módulos ETL: {e}")
        return False, False

def test_etl_configuration():
    """Probar la configuración del ETL"""
    print("\n🔧 Probando configuración del ETL...")
    
    try:
        from src.etl.config import get_etl_config, validate_configuration
        
        config = get_etl_config()
        print(f"✅ Configuración cargada: {len(config)} secciones")
        
        warnings = validate_configuration()
        if warnings:
            print("⚠️ Advertencias de configuración:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("✅ Configuración válida - sin advertencias")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando configuración: {e}")
        return False

def test_etl_controller():
    """Probar el controlador ETL"""
    print("\n🎮 Probando controlador ETL...")
    
    try:
        from src.etl.flask_controller import ETLController
        
        controller = ETLController()
        print("✅ Controlador ETL inicializado")
        
        # Probar catálogo de datasets
        catalog = controller.get_datasets_catalog()
        print(f"📊 Datasets disponibles: {len(catalog.get('etl_datasets', {}))}")
        
        # Probar estado del sistema
        status = controller.get_etl_status()
        print(f"⚡ Estado del sistema: {status.get('system_status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando controlador: {e}")
        return False

def test_etl_core():
    """Probar el motor ETL principal"""
    print("\n⚙️ Probando motor ETL principal...")
    
    try:
        from src.etl.conflict_data_etl import create_etl_instance
        
        etl = create_etl_instance(
            sources=['gdelt'],  # Solo GDELT que no requiere API key
            days_back=1,        # Solo 1 día para prueba rápida
            alert_threshold=10
        )
        
        print("✅ Instancia ETL creada")
        
        # Probar configuración
        catalog = etl.get_datasets_catalog()
        print(f"📊 Datasets del motor: {len(catalog.get('primary_sources', {}))}")
        
        # Probar estadísticas
        stats = etl.get_etl_statistics()
        print(f"📈 Estadísticas disponibles: {len(stats)} métricas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando motor ETL: {e}")
        return False

def test_flask_integration():
    """Probar la integración con Flask"""
    print("\n🌐 Probando integración Flask...")
    
    try:
        from flask import Flask
        from src.etl.flask_controller import create_etl_routes, get_etl_controller
        
        app = Flask(__name__)
        etl_controller = get_etl_controller()
        
        # Configurar rutas ETL
        create_etl_routes(app, etl_controller)
        print("✅ Rutas Flask ETL configuradas")
        
        # Verificar rutas creadas
        routes = [rule.rule for rule in app.url_map.iter_rules() if 'etl' in rule.rule]
        print(f"🛣️ Rutas ETL creadas: {len(routes)}")
        for route in routes:
            print(f"  - {route}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando integración Flask: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del sistema ETL de conflictos geopolíticos")
    print("=" * 70)
    
    results = {
        'imports': False,
        'core_available': False,
        'configuration': False,
        'controller': False,
        'etl_core': False,
        'flask_integration': False
    }
    
    # Test 1: Importaciones
    imports_ok, core_available = test_etl_imports()
    results['imports'] = imports_ok
    results['core_available'] = core_available
    
    if not imports_ok:
        print("\n❌ Las importaciones básicas fallaron. Verifique la instalación.")
        return False
    
    # Test 2: Configuración
    results['configuration'] = test_etl_configuration()
    
    # Test 3: Controlador
    results['controller'] = test_etl_controller()
    
    # Test 4: Motor ETL (solo si está disponible)
    if core_available:
        results['etl_core'] = test_etl_core()
    else:
        print("\n⏭️ Saltando pruebas del motor ETL (no disponible)")
    
    # Test 5: Integración Flask
    results['flask_integration'] = test_flask_integration()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 70)
    
    total_tests = len([k for k in results.keys() if k != 'core_available'])
    passed_tests = len([v for k, v in results.items() if v and k != 'core_available'])
    
    for test_name, passed in results.items():
        if test_name == 'core_available':
            continue
        
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"{test_name.replace('_', ' ').title():<25} {status}")
    
    print("-" * 70)
    print(f"Total: {passed_tests}/{total_tests} pruebas pasaron")
    
    if core_available:
        print("🎉 Motor ETL completo disponible")
    else:
        print("⚠️ Motor ETL en modo mock (falta configuración)")
    
    success_rate = (passed_tests / total_tests) * 100
    if success_rate >= 80:
        print(f"🎉 Sistema ETL funcionando correctamente ({success_rate:.1f}%)")
        return True
    else:
        print(f"⚠️ Sistema ETL requiere atención ({success_rate:.1f}%)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
