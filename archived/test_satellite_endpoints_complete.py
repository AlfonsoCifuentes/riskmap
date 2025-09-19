#!/usr/bin/env python3
"""
Script para probar todos los endpoints de análisis satelital y verificar que no devuelvan 'undefined'
"""

import requests
import json
import time

def test_endpoint(url, description):
    """Prueba un endpoint y verifica su respuesta"""
    print(f"\nProbando {description}...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar si hay undefined en la respuesta
            response_str = json.dumps(data)
            if 'undefined' in response_str:
                print("❌ ERROR: Respuesta contiene 'undefined'")
                print(f"Respuesta: {json.dumps(data, indent=2)}")
            else:
                print("✅ OK: Sin valores 'undefined'")
                print(f"Respuesta: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    base_url = "http://localhost:8050"
    
    # Dar tiempo al servidor para arrancar
    print("Esperando que el servidor esté listo...")
    time.sleep(3)
    
    endpoints = [
        ("/api/satellite/statistics", "Estadísticas"),
        ("/api/satellite/critical-alerts", "Alertas Críticas"),
        ("/api/satellite/gallery-images", "Galería de Imágenes"),
        ("/api/satellite/analysis-timeline", "Cronología de Eventos"),
        ("/api/satellite/evolution-predictions", "Predicciones de Evolución")
    ]
    
    print("=" * 60)
    print("PRUEBA DE ENDPOINTS DE ANÁLISIS SATELITAL")
    print("=" * 60)
    
    for endpoint, description in endpoints:
        test_endpoint(f"{base_url}{endpoint}", description)
        time.sleep(1)  # Pausa entre requests
    
    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
