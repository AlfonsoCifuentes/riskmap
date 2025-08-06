#!/usr/bin/env python3
"""Test GDELT cross-referencing integration"""

import sys
import os

# Add the src directory to the path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from src.ai.geolocation_analyzer import GeolocationAnalyzer

def test_gdelt_integration():
    """Test GDELT cross-referencing functionality"""
    
    print("🧪 Probando integración GDELT...")
    
    # Inicializar el analizador
    analyzer = GeolocationAnalyzer()
    
    # Test cross-referencing with a location that might have GDELT events
    test_location = "Gaza"
    test_conflict_type = "military"
    
    print(f"🔍 Probando validación GDELT para: {test_location} ({test_conflict_type})")
    
    try:
        gdelt_result = analyzer.cross_reference_with_gdelt(test_location, test_conflict_type)
        
        if gdelt_result:
            print("✅ GDELT cross-referencing funcionando:")
            print(f"   📊 Validación: {gdelt_result.get('gdelt_validation', 'N/A')}")
            print(f"   📈 Eventos relevantes: {gdelt_result.get('relevant_events_count', 0)}")
            
            if gdelt_result.get('top_events'):
                print("   🗞️ Top eventos:")
                for i, event in enumerate(gdelt_result['top_events'][:2], 1):
                    print(f"      {i}. {event.get('title', 'Sin título')[:60]}...")
                    
            if gdelt_result.get('confidence_boost'):
                print(f"   🎯 Boost de confianza: +{gdelt_result['confidence_boost']:.2f}")
            elif gdelt_result.get('confidence_penalty'):
                print(f"   ⚠️ Penalización: {gdelt_result['confidence_penalty']:.2f}")
                
        else:
            print("⚠️ GDELT cross-referencing no disponible")
            
    except Exception as e:
        print(f"❌ Error en test GDELT: {e}")
        
    # Test keywords function
    print("\n🔑 Probando keywords de conflicto:")
    keywords = analyzer._get_conflict_keywords("military")
    print(f"   Military keywords: {keywords[:5]}...")
    
    keywords = analyzer._get_conflict_keywords("terrorist")
    print(f"   Terrorist keywords: {keywords[:5]}...")
    
    print("\n🎉 Test GDELT completado")

if __name__ == "__main__":
    test_gdelt_integration()
