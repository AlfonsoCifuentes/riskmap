#!/usr/bin/env python3
"""
Test Final del Endpoint de Conflictos - Completamente Automatizado
===============================================================
Prueba el endpoint /api/analytics/conflicts que ahora es:
- Completamente automático (sin opciones para el usuario)
- Multi-nivel y impulsado por criticidad
- Siempre devuelve los conflictos más importantes, precisos y accionables
"""

import requests
import json
import time
from datetime import datetime

def test_conflicts_endpoint_final():
    """Prueba completa del endpoint automatizado de conflictos"""
    
    print("🎯 TESTING ENDPOINT COMPLETAMENTE AUTOMATIZADO")
    print("=" * 60)
    
    url = "http://localhost:8050/api/analytics/conflicts"
    
    try:
        print(f"📡 Llamando al endpoint: {url}")
        print("⚡ Endpoint automático - sin opciones para el usuario")
        print("🔄 Análisis multi-nivel impulsado por criticidad...")
        
        start_time = time.time()
        
        # Sin parámetros - completamente automático
        response = requests.get(url, timeout=300)  # 5 minutos de timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Tiempo de respuesta: {duration:.2f} segundos")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ RESPUESTA EXITOSA")
            print("=" * 40)
            
            # Análisis de la respuesta
            print(f"🎯 Tipo de análisis: {data.get('analysis_type', 'no especificado')}")
            print(f"🤖 IA habilitada: {data.get('ai_powered', False)}")
            print(f"🔒 Precisión garantizada: {data.get('precision_guaranteed', False)}")
            print(f"🚀 Groq mejorado: {data.get('groq_enhanced', False)}")
            print(f"📊 GDELT validado: {data.get('gdelt_validated', False)}")
            print(f"🗺️ Precisión geográfica: {data.get('geographic_precision', 'no especificada')}")
            
            conflicts = data.get('conflicts', [])
            zones = data.get('satellite_zones', [])
            stats = data.get('statistics', {})
            
            print(f"\n🔥 CONFLICTOS DETECTADOS: {len(conflicts)}")
            
            if conflicts:
                print("\n📋 LISTA DE CONFLICTOS:")
                for i, conflict in enumerate(conflicts[:10], 1):  # Mostrar solo los 10 más importantes
                    print(f"\n{i}. {conflict.get('title', 'Sin título')}")
                    print(f"   📍 Ubicación: {conflict.get('location', 'No especificada')}")
                    print(f"   🚨 Riesgo: {conflict.get('risk_level', 'unknown').upper()}")
                    print(f"   🎯 Confianza: {conflict.get('confidence', 0):.1f}%")
                    print(f"   📅 Fecha: {conflict.get('published_date', 'No disponible')}")
                    
                    if conflict.get('latitude') and conflict.get('longitude'):
                        print(f"   🌍 Coordenadas: {conflict['latitude']:.6f}, {conflict['longitude']:.6f}")
                    
                    if conflict.get('area_km2'):
                        print(f"   📏 Área: {conflict['area_km2']:.2f} km²")
                
                if len(conflicts) > 10:
                    print(f"\n... y {len(conflicts) - 10} conflictos más")
            
            print(f"\n🛰️ ZONAS SATELITALES GENERADAS: {len(zones)}")
            
            if zones:
                print("\n🗺️ ZONAS LISTAS PARA SATÉLITE:")
                for i, zone in enumerate(zones[:5], 1):  # Mostrar solo las 5 más importantes
                    print(f"\n{i}. {zone.get('name', 'Zona sin nombre')}")
                    print(f"   🚨 Prioridad: {zone.get('priority', 'unknown').upper()}")
                    print(f"   📏 Área: {zone.get('area_km2', 0):.2f} km²")
                    
                    if zone.get('bounds'):
                        bounds = zone['bounds']
                        print(f"   🗺️ Límites: [{bounds.get('north', 0):.6f}, {bounds.get('south', 0):.6f}]")
                        print(f"              [{bounds.get('east', 0):.6f}, {bounds.get('west', 0):.6f}]")
                    
                    if zone.get('geojson'):
                        print(f"   ✅ GeoJSON: Disponible ({zone['geojson']['type']})")
                
                if len(zones) > 5:
                    print(f"\n... y {len(zones) - 5} zonas más")
            
            print(f"\n📊 ESTADÍSTICAS:")
            print(f"   🔥 Total conflictos: {stats.get('total_conflicts', 0)}")
            print(f"   🚨 Alto riesgo: {stats.get('high_risk', 0)}")
            print(f"   ⚠️ Medio riesgo: {stats.get('medium_risk', 0)}")
            print(f"   ℹ️ Bajo riesgo: {stats.get('low_risk', 0)}")
            print(f"   🎯 Confianza promedio: {stats.get('average_confidence', 0):.1f}%")
            print(f"   🛰️ Zonas satelitales: {stats.get('satellite_zones_generated', 0)}")
            print(f"   📍 Con coordenadas precisas: {stats.get('precise_coordinates', 0)}")
            
            # Validación de calidad
            print(f"\n🔍 VALIDACIÓN DE CALIDAD:")
            
            high_quality = True
            
            if not data.get('ai_powered'):
                print("   ❌ Sin análisis de IA")
                high_quality = False
            else:
                print("   ✅ Análisis de IA activo")
            
            if not data.get('precision_guaranteed'):
                print("   ❌ Sin garantía de precisión")
                high_quality = False
            else:
                print("   ✅ Precisión garantizada")
            
            if len(conflicts) == 0:
                print("   ⚠️ No se detectaron conflictos")
                high_quality = False
            else:
                print(f"   ✅ {len(conflicts)} conflictos detectados")
            
            precise_conflicts = sum(1 for c in conflicts if c.get('latitude') and c.get('longitude'))
            if precise_conflicts < len(conflicts) * 0.8:  # Al menos 80% con coordenadas
                print(f"   ⚠️ Solo {precise_conflicts}/{len(conflicts)} conflictos tienen coordenadas precisas")
            else:
                print(f"   ✅ {precise_conflicts}/{len(conflicts)} conflictos con coordenadas precisas")
            
            if high_quality:
                print("\n🎉 ENDPOINT FUNCIONANDO PERFECTAMENTE")
                print("   Devuelve conflictos importantes, precisos y accionables")
            else:
                print("\n⚠️ ENDPOINT NECESITA AJUSTES")
                print("   No cumple todos los criterios de calidad")
        
        else:
            print(f"\n❌ ERROR HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Error desconocido')}")
                print(f"Detalle técnico: {error_data.get('technical_detail', 'No disponible')}")
                print(f"Sugerencia: {error_data.get('suggestion', 'No disponible')}")
            except:
                print(f"Respuesta sin JSON: {response.text[:500]}")
    
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - El endpoint tardó más de 5 minutos")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR DE CONEXIÓN - ¿Está corriendo el servidor?")
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")

if __name__ == "__main__":
    test_conflicts_endpoint_final()
