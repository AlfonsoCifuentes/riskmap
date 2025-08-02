#!/usr/bin/env python3
"""
Test de integración para los módulos de inteligencia externa
"""

import sys
import os
import sqlite3
from pathlib import Path
import json
from datetime import datetime, timedelta

# Añadir el patch de compatibilidad ANTES de cualquier import ML
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Importar patch inmediatamente
try:
    import ml_dtypes_patch
    print("🔧 Patch ml_dtypes aplicado correctamente")
except ImportError as e:
    print(f"⚠️ No se pudo cargar patch ml_dtypes: {e}")
    pass

def get_database_path():
    """Obtener ruta de la base de datos"""
    # Usar la BD real que tiene los datos
    return 'data/geopolitical_intel.db'

def test_external_feeds():
    """Test del módulo de feeds externos"""
    print("🔬 Testing External Intelligence Feeds...")
    
    try:
        from src.intelligence.external_feeds import ExternalIntelligenceFeeds
        
        # Crear instancia
        db_path = get_database_path()
        feeds = ExternalIntelligenceFeeds(db_path)
        
        # Test de estadísticas
        stats = feeds.get_feed_statistics()
        print(f"✅ Feed statistics: {stats}")
        
        # Test de hotspots (sin actualizar feeds para evitar hacer requests)
        hotspots = feeds.get_conflict_hotspots(days_back=30)
        print(f"✅ Conflict hotspots found: {len(hotspots)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing external feeds: {e}")
        return False

def test_integrated_analyzer():
    """Test del analizador integrado"""
    print("🔬 Testing Integrated Geopolitical Analyzer...")
    
    try:
        from src.intelligence.integrated_analyzer import IntegratedGeopoliticalAnalyzer
        
        # Crear instancia
        db_path = get_database_path()
        analyzer = IntegratedGeopoliticalAnalyzer(db_path)
        
        # Test de generación de GeoJSON
        geojson = analyzer.generate_comprehensive_geojson(
            timeframe_days=7,
            include_predictions=False  # Sin feeds externos para evitar requests
        )
        
        print(f"✅ Generated GeoJSON with {len(geojson.get('features', []))} features")
        print(f"   Metadata: {geojson.get('metadata', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing integrated analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_integration():
    """Test de integración con el backend"""
    print("🔬 Testing Backend Integration...")
    
    try:
        # Importar la aplicación principal
        from app_BUENA import RiskMapUnifiedApplication
        
        # Crear instancia de la aplicación
        config = {
            'flask_port': 8050,
            'flask_host': '127.0.0.1',
            'flask_debug': False,
            'auto_initialize': False,  # No inicializar automáticamente
            'enable_background_tasks': False
        }
        
        app = RiskMapUnifiedApplication(config)
        
        # Verificar que los módulos de inteligencia están disponibles
        if hasattr(app, 'external_feeds') and hasattr(app, 'integrated_analyzer'):
            print("✅ Intelligence modules are available in the application")
        else:
            print("⚠️ Intelligence modules not yet initialized in application")
        
        # Verificar que las importaciones están disponibles
        from src.intelligence.external_feeds import ExternalIntelligenceFeeds
        from src.intelligence.integrated_analyzer import IntegratedGeopoliticalAnalyzer
        print("✅ Intelligence modules can be imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing backend integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_schema():
    """Test del esquema de base de datos"""
    print("🔬 Testing Database Schema...")
    
    try:
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            print("⚠️ Database doesn't exist yet, creating basic structure...")
            # Crear directorio si no existe
            os.makedirs('data', exist_ok=True)
            
            # Crear base de datos básica
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        content TEXT,
                        location TEXT,
                        latitude REAL,
                        longitude REAL,
                        published_date TEXT,
                        risk_level TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
            print("✅ Basic database created")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar tablas existentes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Database tables: {tables}")
            
            # Verificar estructura de articles
            cursor.execute("PRAGMA table_info(articles)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"✅ Articles table columns: {columns}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database schema: {e}")
        return False

def main():
    """Función principal de test"""
    print("🚀 Starting Intelligence Integration Tests...\n")
    
    tests = [
        ("Database Schema", test_database_schema),
        ("External Feeds", test_external_feeds),
        ("Integrated Analyzer", test_integrated_analyzer),
        ("Backend Integration", test_backend_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        print('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ FAILED: {test_name} - {e}")
            results.append((test_name, False))
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Intelligence integration is working correctly.")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
