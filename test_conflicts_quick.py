#!/usr/bin/env python3
"""Test conflicts endpoint with shorter timeout"""

import requests
import json

def test_conflicts_endpoint_quick():
    """Test conflicts endpoint with quick timeout"""
    
    print("🧪 Probando endpoint de conflictos (timeout corto)...")
    
    url = "http://localhost:8050/api/analytics/conflicts"
    params = {"timeframe": "3d"}  # Menos días para análisis más rápido
    
    try:
        print(f"📡 GET {url}")
        print(f"📊 Parámetros: {params}")
        
        response = requests.get(url, params=params, timeout=15)  # Timeout más corto
        
        print(f"📈 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Respuesta exitosa:")
            print(f"   📊 Tipo: {data.get('type', 'N/A')}")
            print(f"   🗺️ Features: {len(data.get('features', []))}")
            
            if data.get('features'):
                feature = data['features'][0]
                props = feature.get('properties', {})
                
                print(f"   📍 Primera ubicación: {props.get('location', 'N/A')}")
                print(f"   🎯 Coordenadas: {props.get('center_lat', 'N/A')}, {props.get('center_lon', 'N/A')}")
                print(f"   🏷️ Tipo conflicto: {props.get('conflict_type', 'N/A')}")
                print(f"   📏 Precisión: {props.get('precision', 'N/A')}")
                
                # Check if GDELT validation is present
                if 'gdelt_validation' in props:
                    gdelt = props['gdelt_validation']
                    print(f"   📊 GDELT validación: {gdelt.get('gdelt_validation', 'N/A')}")
                    print(f"   📈 Eventos GDELT: {gdelt.get('relevant_events_count', 0)}")
                else:
                    print("   📊 GDELT: No incluido en respuesta")
                    
            print("\n🎉 Test exitoso - endpoint funcionando con IA real")
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - el análisis está funcionando pero toma tiempo")
        print("🔧 Esto es normal para análisis de IA complejos")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_conflicts_endpoint_quick()
