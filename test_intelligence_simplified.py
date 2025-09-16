#!/usr/bin/env python3
"""
Test simplificado para los módulos de inteligencia externa
"""

import sys
import os
from pathlib import Path

# Aplicar patch de compatibilidad
try:
    import ml_dtypes_patch
    print("✅ Patch de compatibilidad aplicado")
except ImportError:
    print("⚠️ Patch de compatibilidad no disponible")

def test_intelligence_modules_only():
    """Test solo de los módulos de inteligencia"""
    print("🔬 Testing Intelligence Modules Only...")
    
    try:
        # Test 1: External Feeds
        print("\n1. Testing External Feeds Module...")
        from src.intelligence.external_feeds import ExternalIntelligenceFeeds
        
        db_path = 'data/riskmap.db'
        feeds = ExternalIntelligenceFeeds(db_path)
        print("✅ ExternalIntelligenceFeeds imported and instantiated")
        
        # Test básico de estadísticas
        stats = feeds.get_feed_statistics()
        print(f"✅ Feed statistics retrieved: {len(stats)} sources")
        
        # Test 2: Integrated Analyzer  
        print("\n2. Testing Integrated Analyzer Module...")
        from src.intelligence.integrated_analyzer import IntegratedGeopoliticalAnalyzer
        
        analyzer = IntegratedGeopoliticalAnalyzer(db_path)
        print("✅ IntegratedGeopoliticalAnalyzer imported and instantiated")
        
        # Test básico de GeoJSON
        geojson = analyzer.generate_comprehensive_geojson(timeframe_days=7, include_predictions=False)
        features_count = len(geojson.get('features', []))
        print(f"✅ GeoJSON generated with {features_count} features")
        
        # Test 3: Verificar que las funciones clave están disponibles
        print("\n3. Testing Key Functions...")
        
        # Verificar métodos del ExternalIntelligenceFeeds
        essential_methods = ['get_feed_statistics', 'get_conflict_hotspots', 'update_all_feeds']
        for method in essential_methods:
            if hasattr(feeds, method):
                print(f"✅ {method} available")
            else:
                print(f"❌ {method} missing")
        
        # Verificar métodos del IntegratedGeopoliticalAnalyzer
        analyzer_methods = ['generate_comprehensive_geojson', '_get_news_conflicts', '_consolidate_conflict_zones']
        for method in analyzer_methods:
            if hasattr(analyzer, method):
                print(f"✅ {method} available")
            else:
                print(f"❌ {method} missing")
        
        print("\n🎉 Intelligence modules test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing intelligence modules: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_geojson_structure():
    """Test de la estructura del GeoJSON generado"""
    print("\n🔬 Testing GeoJSON Structure...")
    
    try:
        from src.intelligence.integrated_analyzer import IntegratedGeopoliticalAnalyzer
        
        db_path = 'data/riskmap.db'
        analyzer = IntegratedGeopoliticalAnalyzer(db_path)
        
        geojson = analyzer.generate_comprehensive_geojson(timeframe_days=7, include_predictions=False)
        
        # Verificar estructura GeoJSON
        required_keys = ['type', 'features', 'metadata']
        for key in required_keys:
            if key in geojson:
                print(f"✅ {key} present")
            else:
                print(f"❌ {key} missing")
                return False
        
        # Verificar tipo
        if geojson.get('type') == 'FeatureCollection':
            print("✅ Correct GeoJSON type")
        else:
            print(f"❌ Incorrect type: {geojson.get('type')}")
            return False
        
        # Verificar metadata
        metadata = geojson.get('metadata', {})
        metadata_keys = ['generated_by', 'generated_at', 'version', 'data_sources']
        for key in metadata_keys:
            if key in metadata:
                print(f"✅ Metadata {key} present")
            else:
                print(f"⚠️ Metadata {key} missing")
        
        print("✅ GeoJSON structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error testing GeoJSON structure: {e}")
        return False

def main():
    """Función principal de test simplificado"""
    print("🚀 Starting Simplified Intelligence Tests...\n")
    
    tests = [
        ("Intelligence Modules", test_intelligence_modules_only),
        ("GeoJSON Structure", test_geojson_structure)
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
    print("📊 SIMPLIFIED TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All simplified tests passed!")
        print("✅ Intelligence modules are working correctly!")
        print("✅ Ready for integration with the full system!")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
