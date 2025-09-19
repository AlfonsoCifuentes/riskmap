#!/usr/bin/env python3
"""
Test del endpoint de conflictos - versión simple
"""

import requests
import json
import time
import sys

def test_conflicts_endpoint():
    """Prueba el endpoint de conflictos de manera simple OPTIMIZADA"""
    try:
        print("🧪 Probando endpoint /api/analytics/conflicts OPTIMIZADO...")
        
        # URL del endpoint - OPTIMIZADO: usar cache para datos rápidos
        url = "http://localhost:8050/api/analytics/conflicts"
        params = {"timeframe": "7d", "cache": "true"}  # Usar cache para respuesta rápida
        
        print(f"📡 Enviando GET request a: {url}")
        print(f"📊 Parámetros OPTIMIZADOS: {params}")
        print("⚡ Modo: Cache habilitado para respuesta rápida, datos de análisis previos")
        
        # Hacer request con timeout reducido
        start_time = time.time()
        response = requests.get(url, params=params, timeout=30)  # Timeout reducido a 30s
        end_time = time.time()
        
        print(f"⏱️ Tiempo de respuesta: {end_time - start_time:.2f} segundos")
        print(f"📱 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response exitosa!")
            print(f"🎯 Success: {data.get('success', 'N/A')}")
            
            if 'conflicts' in data:
                conflicts = data['conflicts']
                print(f"⚔️ Conflictos detectados: {len(conflicts)}")
                
                for i, conflict in enumerate(conflicts[:3]):  # Mostrar primeros 3
                    print(f"  {i+1}. {conflict.get('location', 'N/A')} - {conflict.get('risk_level', 'N/A')}")
                    print(f"     Coordenadas: ({conflict.get('latitude', 'N/A')}, {conflict.get('longitude', 'N/A')})")
                    print(f"     Confianza: {conflict.get('confidence', 'N/A')}")
                    
                if 'statistics' in data:
                    stats = data['statistics']
                    print("📊 Estadísticas:")
                    print(f"   Total: {stats.get('total_conflicts', 'N/A')}")
                    print(f"   Alto riesgo: {stats.get('high_risk', 'N/A')}")
                    print(f"   Medio riesgo: {stats.get('medium_risk', 'N/A')}")
                    print(f"   Bajo riesgo: {stats.get('low_risk', 'N/A')}")
                    print(f"   IA habilitada: {stats.get('ai_analyzed', 'N/A')}")
                    print(f"   Análisis optimizado: {stats.get('optimized_analysis', 'N/A')}")
                    print(f"   Timeframe usado: {stats.get('timeframe_used', 'N/A')} días")
                    
            if 'satellite_zones' in data:
                zones = data['satellite_zones']
                print(f"🛰️ Zonas satelitales: {len(zones)}")
                
        else:
            print(f"❌ Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"💥 Error: {error_data.get('error', 'N/A')}")
                print(f"🔍 Detalles: {error_data.get('suggestion', 'N/A')}")
            except (ValueError, KeyError):
                print(f"📝 Response text: {response.text[:500]}")
        
    except requests.Timeout:
        print("⏰ Timeout - el análisis de IA está tomando demasiado tiempo")
        print("🔧 Sugerencia: Verificar que Ollama esté funcionando rápidamente")
    except requests.ConnectionError:
        print("🔌 Error de conexión - el servidor no está disponible")
        print("🔧 Sugerencia: Verificar que el servidor esté ejecutándose en puerto 8050")
    except Exception as e:
        print(f"💥 Error inesperado: {e}")

if __name__ == "__main__":
    test_conflicts_endpoint()
