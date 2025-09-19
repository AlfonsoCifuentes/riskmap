#!/usr/bin/env python3
"""
Test script para los módulos de inteligencia externa
Verifica que ACLED, GDELT, GPR y el analizador integrado funcionen correctamente
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

# Añadir el directorio raíz al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_external_feeds():
    """Test de feeds externos"""
    print("🔍 Testing External Intelligence Feeds...")
    
    try:
        from src.intelligence.external_feeds import ExternalIntelligenceFeeds
        
        # Usar base de datos de test
        test_db = "data/geopolitical_test.db"
        feeds = ExternalIntelligenceFeeds(test_db)
        
        print("✅ ExternalIntelligenceFeeds initialized successfully")
        
        # Test de actualización de feeds (sin hacer requests reales)
        print("\n📊 Testing feed statistics...")
        stats = feeds.get_feed_statistics()
        print(f"Feed Statistics: {json.dumps(stats, indent=2)}")
        
        # Test de hotspots
        print("\n🔥 Testing conflict hotspots...")
        hotspots = feeds.get_conflict_hotspots(days_back=7, min_events=1)
        print(f"Found {len(hotspots)} hotspots")
        
        print("✅ External feeds test completed successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing external feeds: {e}")
        return False

def test_integrated_analyzer():
    """Test del analizador integrado"""
    print("\n🔍 Testing Integrated Geopolitical Analyzer...")
    
    try:
        from src.intelligence.integrated_analyzer import IntegratedGeopoliticalAnalyzer
        
        # Usar base de datos de test
        test_db = "data/geopolitical_test.db"
        analyzer = IntegratedGeopoliticalAnalyzer(test_db)
        
        print("✅ IntegratedGeopoliticalAnalyzer initialized successfully")
        
        # Test de GeoJSON optimizado para satélite
        print("\n🛰️ Testing satellite-optimized GeoJSON...")
        geojson = analyzer.generate_comprehensive_geojson(
            timeframe_days=7,
            include_predictions=True
        )
        
        features_count = len(geojson.get('features', []))
        print(f"Generated GeoJSON with {features_count} features")
        
        if features_count > 0:
            # Mostrar una feature de ejemplo
            sample_feature = geojson['features'][0]
            print(f"Sample feature properties: {list(sample_feature.get('properties', {}).keys())}")
        
        print("✅ Integrated analyzer test completed successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing integrated analyzer: {e}")
        return False

def test_database_schema():
    """Test del esquema de base de datos"""
    print("\n🔍 Testing Database Schema...")
    
    try:
        from src.intelligence.external_feeds import ExternalIntelligenceFeeds
        
        test_db = "data/geopolitical_test.db"
        
        # Verificar que las tablas se crean correctamente
        ExternalIntelligenceFeeds(test_db)
        
        # Verificar estructura de tablas
        with sqlite3.connect(test_db) as conn:
            cursor = conn.cursor()
            
            # Listar todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'acled_events', 'gdelt_events', 'gpr_incidents', 
                'external_feeds_updates', 'processed_data'
            ]
            
            print(f"Available tables: {tables}")
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"⚠️ Missing tables: {missing_tables}")
            else:
                print("✅ All expected tables found")
            
            # Verificar estructura de una tabla
            if 'acled_events' in tables:
                cursor.execute("PRAGMA table_info(acled_events)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"ACLED events columns: {columns}")
        
        print("✅ Database schema test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing database schema: {e}")
        return False

def test_system_integration():
    """Test de integración con el sistema principal"""
    print("\n🔍 Testing System Integration...")
    
    try:
        # Verificar que los módulos se pueden importar desde la app principal
        from app_BUENA import RiskMapUnifiedApp
        
        print("✅ RiskMapUnifiedApp import successful")
        
        # Crear instancia (no inicializar completamente)
        config = {
            'auto_initialize': False,
            'enable_background_tasks': False,
            'flask_debug': False
        }
        
        app = RiskMapUnifiedApp(config)
        
        # Verificar que los nuevos atributos están presentes
        assert hasattr(app, 'external_feeds'), "Missing external_feeds attribute"
        assert hasattr(app, 'integrated_analyzer'), "Missing integrated_analyzer attribute"
        
        # Verificar que el estado del sistema incluye campos de inteligencia externa
        assert 'external_intelligence_initialized' in app.system_state
        assert 'last_external_feeds_update' in app.system_state
        assert 'external_feeds_count' in app.system_state['statistics']
        
        print("✅ System integration test completed successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing system integration: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("🚀 Starting External Intelligence Integration Tests")
    print("=" * 60)
    
    # Crear directorio de datos si no existe
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    test_results = {}
    
    # Ejecutar tests
    test_results['external_feeds'] = test_external_feeds()
    test_results['integrated_analyzer'] = test_integrated_analyzer()
    test_results['database_schema'] = test_database_schema()
    test_results['system_integration'] = test_system_integration()
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! External intelligence integration is ready.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print("\n📋 Next Steps:")
    print("1. Start the unified application: python app_BUENA.py")
    print("2. Test the new endpoints:")
    print("   - GET /api/intelligence/feeds/status")
    print("   - GET /api/intelligence/feeds/update")
    print("   - GET /api/intelligence/hotspots")
    print("   - GET /api/analytics/geojson?include_external=true")
    print("3. Monitor the system logs for external feeds updates")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
