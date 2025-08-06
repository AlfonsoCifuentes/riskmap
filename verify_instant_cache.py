#!/usr/bin/env python3
"""
Verificación definitiva del cache instant
"""

import requests
import time
import json

def test_instant_cache():
    """Prueba el endpoint con múltiples requests para verificar cache"""
    try:
        print("🧪 VERIFICACIÓN DEFINITIVA DEL CACHE INSTANT...")
        url = "http://localhost:8050/api/analytics/conflicts"
        params = {"timeframe": "7d", "cache": "true"}
        
        # Hacer 3 requests consecutivos para probar cache
        times = []
        for i in range(3):
            print(f"\n🔄 Request {i+1}/3:")
            start_time = time.time()
            response = requests.get(url, params=params, timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            times.append(response_time)
            
            print(f"⏱️ Tiempo: {response_time:.3f} segundos")
            print(f"📱 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                conflicts = data.get('conflicts', [])
                print(f"⚔️ Conflictos: {len(conflicts)}")
            else:
                print(f"❌ Error: {response.status_code}")
        
        # Analizar tiempos
        avg_time = sum(times) / len(times)
        print(f"\n📊 RESUMEN:")
        print(f"   Promedio: {avg_time:.3f} segundos")
        print(f"   Más rápido: {min(times):.3f} segundos")
        print(f"   Más lento: {max(times):.3f} segundos")
        
        if avg_time < 1.0:
            print("✅ ¡CACHE INSTANT FUNCIONANDO!")
        elif avg_time < 2.0:
            print("⚠️ Cache funcionando pero no instant (< 1s)")
        else:
            print("❌ Cache no optimizado (> 2s)")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_instant_cache()
