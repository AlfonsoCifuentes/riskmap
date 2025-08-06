#!/usr/bin/env python3
"""Script para triggerar análisis de geolocalización y generar zonas de conflicto."""

import requests
import json
import time

def trigger_geolocation_analysis():
    """Triggear análisis de geolocalización via API."""
    try:
        base_url = "http://localhost:8050"
        
        print("🗺️ TRIGGERANDO ANÁLISIS DE GEOLOCALIZACIÓN")
        print("=" * 60)
        
        # 1. Primero verificar si hay artículos para analizar
        print("📊 Verificando artículos disponibles...")
        response = requests.get(f"{base_url}/api/articles")
        if response.status_code == 200:
            articles = response.json()
            total_articles = len(articles.get('articles', []))
            print(f"📰 Artículos disponibles: {total_articles}")
        else:
            print(f"❌ Error obteniendo artículos: {response.status_code}")
            return
        
        # 2. Triggear análisis de conflictos
        print("\n🔍 Triggerando análisis de conflictos...")
        response = requests.get(f"{base_url}/api/analytics/conflicts")
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Respuesta recibida:")
                print(f"   🗂️ Tipo: {type(data)}")
                
                if isinstance(data, dict):
                    if 'conflict_zones' in data:
                        zones = data['conflict_zones']
                        print(f"   📍 Zonas de conflicto: {len(zones)}")
                        for i, zone in enumerate(zones[:3]):  # Mostrar solo las primeras 3
                            location = zone.get('location', 'Sin ubicación')
                            severity = zone.get('severity', 'N/A')
                            print(f"      {i+1}. {location} (Severidad: {severity})")
                    else:
                        print(f"   📄 Estructura: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"   📍 Zonas encontradas: {len(data)}")
                    for i, zone in enumerate(data[:3]):  # Mostrar solo las primeras 3
                        if isinstance(zone, dict):
                            location = zone.get('location', zone.get('name', 'Sin ubicación'))
                            print(f"      {i+1}. {location}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Error decodificando JSON: {e}")
                print(f"📄 Respuesta raw: {response.text[:500]}...")
        else:
            print(f"❌ Error en análisis: {response.status_code}")
            print(f"📄 Respuesta: {response.text[:500]}...")
        
        # 3. Ahora triggear análisis satelital
        print("\n🛰️ Triggerando análisis satelital...")
        response = requests.post(f"{base_url}/api/satellite/trigger-analysis")
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Análisis satelital iniciado:")
            print(f"   🆔 ID: {result.get('analysis_id')}")
            print(f"   📍 Zonas: {result.get('total_zones')}")
            print(f"   📨 Mensaje: {result.get('message')}")
            
            # Monitorear progreso
            analysis_id = result.get('analysis_id')
            if analysis_id:
                print(f"\n📊 Monitoreando progreso...")
                for i in range(3):  # Verificar 3 veces
                    time.sleep(2)
                    progress_response = requests.get(f"{base_url}/api/satellite/analysis-progress/{analysis_id}")
                    if progress_response.status_code == 200:
                        progress = progress_response.json()
                        status = progress.get('status', 'unknown')
                        percent = progress.get('progress', 0)
                        print(f"   📈 Iteración {i+1}: {status} ({percent}%)")
                        
                        if status == 'completed':
                            break
                    else:
                        print(f"   ❌ Error obteniendo progreso: {progress_response.status_code}")
        else:
            print(f"❌ Error triggerando análisis satelital: {response.status_code}")
            print(f"📄 Respuesta: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error en trigger: {e}")

if __name__ == "__main__":
    trigger_geolocation_analysis()
