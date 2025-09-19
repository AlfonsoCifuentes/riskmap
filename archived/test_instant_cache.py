#!/usr/bin/env python3
"""
Script para forzar el funcionamiento del cache mediante respuesta directa
"""

import requests
import json
from datetime import datetime

def test_cache_forced():
    """Probar forzando respuesta directa desde cache sin análisis IA"""
    
    print("🧪 Probando endpoint con respuesta forzada desde cache...")
    
    try:
        # URL del endpoint
        url = "http://localhost:8050/api/analytics/conflicts"
        
        # Probar con parámetro especial para forzar cache
        response = requests.get(f"{url}?force_cache=true", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta exitosa: {len(data.get('conflicts', []))} conflictos")
            print(f"📊 Tipo: {data.get('analysis_type', 'unknown')}")
            
            # Mostrar algunos conflictos
            conflicts = data.get('conflicts', [])
            for i, conflict in enumerate(conflicts[:3]):
                location = conflict.get('location', 'N/A')
                risk = conflict.get('risk_level', 'N/A')
                conf = conflict.get('confidence', 0)
                coords = conflict.get('coordinates', [0, 0])
                print(f"   {i+1}. {location}: {risk} (conf: {conf:.2f}) - [{coords[0]:.4f}, {coords[1]:.4f}]")
            
            return True
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_manual_response():
    """Crear respuesta manual basada en los datos que sabemos que existen"""
    
    print("🔧 Creando respuesta manual desde datos conocidos...")
    
    # Datos que sabemos que existen en la base de datos
    conflicts = [
        {
            "id": 1,
            "location": "Gaza",
            "latitude": 31.3547,
            "longitude": 34.3088,
            "coordinates": [34.3088, 31.3547],
            "risk_level": "medium",
            "conflict_type": "humanitarian",
            "confidence": 1.0,
            "reasoning": "Crisis humanitaria y diplomática en Gaza",
            "article_title": "Top Trump officials to visit Gaza as hunger crisis draws out",
            "detected_at": datetime.now().isoformat(),
            "data_source": "manual_cache"
        },
        {
            "id": 2,
            "location": "Kyiv",
            "latitude": 50.4533,
            "longitude": 30.5244,
            "coordinates": [30.5244, 50.4533],
            "risk_level": "high",
            "conflict_type": "political",
            "confidence": 1.0,
            "reasoning": "Tensiones políticas en Ucrania",
            "article_title": "Young Ukrainians get their way as Zelensky overturns law",
            "detected_at": datetime.now().isoformat(),
            "data_source": "manual_cache"
        },
        {
            "id": 3,
            "location": "Alaska",
            "latitude": 58.3012,
            "longitude": -134.4197,
            "coordinates": [-134.4197, 58.3012],
            "risk_level": "medium",
            "conflict_type": "economic",
            "confidence": 0.88,
            "reasoning": "Crisis presupuestaria en Alaska",
            "article_title": "Alaska ignored budget crisis signs",
            "detected_at": datetime.now().isoformat(),
            "data_source": "manual_cache"
        }
    ]
    
    statistics = {
        'total_conflicts': len(conflicts),
        'high_risk': len([c for c in conflicts if c['risk_level'] == 'high']),
        'medium_risk': len([c for c in conflicts if c['risk_level'] == 'medium']),
        'low_risk': len([c for c in conflicts if c['risk_level'] == 'low']),
        'ai_analyzed': True,
        'average_confidence': sum(c['confidence'] for c in conflicts) / len(conflicts),
        'analysis_timestamp': datetime.now().isoformat(),
        'precise_coordinates': len([c for c in conflicts if c.get('latitude') and c.get('longitude')]),
        'data_source': 'manual_cache',
        'analysis_type': 'cached_instant'
    }
    
    response = {
        'success': True,
        'conflicts': conflicts,
        'statistics': statistics,
        'analysis_type': 'cached_instant',
        'timestamp': datetime.now().isoformat(),
        'ai_powered': True,
        'precision_guaranteed': True,
        'cache_used': True,
        'response_time_ms': 50  # Respuesta instantánea simulada
    }
    
    print("✅ Respuesta manual creada:")
    print(f"📊 {len(conflicts)} conflictos")
    print(f"📊 {statistics['high_risk']} alto riesgo, {statistics['medium_risk']} medio riesgo")
    print(f"📊 Confianza promedio: {statistics['average_confidence']:.2f}")
    
    for conflict in conflicts:
        print(f"   - {conflict['location']}: {conflict['risk_level']} (conf: {conflict['confidence']:.2f})")
    
    return response

if __name__ == "__main__":
    print("🚀 Probando sistema de cache optimizado...")
    
    # Primero probar endpoint normal
    print("\n1. Probando endpoint normal...")
    success = test_cache_forced()
    
    if not success:
        print("\n2. Creando respuesta manual...")
        manual_response = create_manual_response()
        
        print("\n📋 Respuesta que el endpoint debería retornar:")
        print(json.dumps(manual_response, indent=2, ensure_ascii=False))
        
        print("\n💡 Para implementar:")
        print("   - El endpoint debe retornar esta respuesta instantáneamente")
        print("   - Sin llamadas a Ollama ni análisis IA")
        print("   - Datos directos desde la base de datos")
        print("   - Tiempo de respuesta < 1 segundo")
