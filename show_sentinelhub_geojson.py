#!/usr/bin/env python3
"""
Mostrar exactamente qué GeoJSON se le está pasando a la API de SentinelHub
en la sección de análisis satelital avanzado
"""

import sys
import os
import json
import sqlite3
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def get_database_path():
    """Obtener ruta de la base de datos"""
    return os.path.join(os.path.dirname(__file__), 'data', 'articles.db')

def show_real_geojson_from_db():
    """Mostrar GeoJSON real desde la base de datos"""
    try:
        from src.intelligence.integrated_analyzer import IntegratedGeopoliticalAnalyzer
        
        db_path = get_database_path()
        
        print("🌍 GEOJSON PARA SENTINELHUB - ANÁLISIS SATELITAL AVANZADO")
        print("=" * 70)
        
        # Crear analizador
        analyzer = IntegratedGeopoliticalAnalyzer(db_path)
        
        # Generar GeoJSON como se hace en producción
        print("📊 Generando GeoJSON integrado desde todas las fuentes...")
        
        geojson_data = analyzer.generate_comprehensive_geojson(
            timeframe_days=7,
            include_predictions=True
        )
        
        print(f"\n✅ GeoJSON generado exitosamente")
        print(f"📋 Tipo: {geojson_data.get('type', 'N/A')}")
        print(f"🏷️  Features: {len(geojson_data.get('features', []))}")
        
        # Mostrar metadatos específicos para SentinelHub
        if 'sentinel_hub' in geojson_data:
            sentinel_config = geojson_data['sentinel_hub']
            print(f"\n🛰️  CONFIGURACIÓN SENTINELHUB:")
            print(f"   📡 Colecciones recomendadas: {sentinel_config.get('recommended_collections', [])}")
            print(f"   🎯 Zonas prioritarias: {len(sentinel_config.get('priority_zones', []))}")
            print(f"   ⏰ Frecuencia de monitoreo: {sentinel_config.get('monitoring_frequency', 'N/A')}")
        
        # Mostrar algunas features de ejemplo
        features = geojson_data.get('features', [])
        if features:
            print(f"\n📍 EJEMPLO DE FEATURES (ZONAS DE CONFLICTO):")
            print("-" * 50)
            
            for i, feature in enumerate(features[:3]):  # Mostrar las primeras 3
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [0, 0])
                
                print(f"\n🏢 ZONA {i+1}:")
                print(f"   📌 Ubicación: {props.get('name', 'N/A')}")
                print(f"   🌍 País: {props.get('country', 'N/A')}")
                print(f"   📍 Coordenadas: [{coords[1]:.4f}, {coords[0]:.4f}]")
                print(f"   ⚠️  Risk Score: {props.get('risk_score', 0):.3f}")
                print(f"   🚨 Prioridad Sentinel: {props.get('sentinel_priority', 'N/A')}")
                print(f"   📊 Eventos totales: {props.get('total_events', 0)}")
                print(f"   📦 Fuentes de datos: {props.get('data_sources', [])}")
                print(f"   📏 BoundingBox: {props.get('bbox', 'N/A')}")
                print(f"   🔍 Resolución recomendada: {props.get('recommended_resolution', 'N/A')}")
                print(f"   ☁️  Max cobertura nubes: {props.get('cloud_cover_max', 'N/A')}%")
                print(f"   ⏱️  Frecuencia monitoreo: {props.get('monitoring_frequency', 'N/A')}")
                
                if props.get('ai_enhanced'):
                    print(f"   🤖 AI Risk Assessment: {props.get('ai_risk_assessment', 'N/A')}")
                    print(f"   📈 Probabilidad escalada: {props.get('ai_escalation_probability', 'N/A')}")
        
        # Guardar ejemplo completo en archivo
        output_file = "sentinelhub_geojson_example.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 GeoJSON completo guardado en: {output_file}")
        
        # Mostrar estructura simplificada del primer feature
        if features:
            first_feature = features[0]
            print(f"\n📋 ESTRUCTURA COMPLETA DEL PRIMER FEATURE:")
            print("-" * 50)
            print(json.dumps(first_feature, indent=2, ensure_ascii=False))
        
        return geojson_data
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return None
    except Exception as e:
        print(f"❌ Error generando GeoJSON: {e}")
        return None

def show_zone_analysis_geojson():
    """Mostrar el GeoJSON que se pasa específicamente para análisis de zonas"""
    print(f"\n🎯 GEOJSON PARA ANÁLISIS DE ZONA ESPECÍFICA")
    print("=" * 50)
    
    # Ejemplo de GeoJSON que se pasa a get_satellite_image_for_zone
    example_zone_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [30.5234, 50.4501],  # Esquina SO (lng, lat)
                [30.6234, 50.4501],  # Esquina SE
                [30.6234, 50.5501],  # Esquina NE
                [30.5234, 50.5501],  # Esquina NO
                [30.5234, 50.4501]   # Cierre del polígono
            ]]
        },
        "properties": {
            "id": "conflict_zone_1",
            "location": "Kiev Region",
            "country": "Ukraine",
            "region": "Eastern Europe",
            "risk_score": 0.85,
            "risk_level": "high",
            "total_events": 15,
            "fatalities": 45,
            "data_sources": ["news_analysis", "acled", "gdelt"],
            "actors": ["Government Forces", "Opposition Groups"],
            "event_types": ["Armed Conflict", "Violence against civilians"],
            "latest_event": datetime.now().isoformat(),
            "sentinel_priority": "critical",
            "monitoring_frequency": "daily",
            "bbox": [30.4234, 50.3501, 30.7234, 50.6501],
            "recommended_resolution": "10m",
            "cloud_cover_max": 20,
            "ai_enhanced": True,
            "ai_risk_assessment": "High probability of escalation",
            "ai_escalation_probability": 0.78
        }
    }
    
    print("📍 Este es el tipo de GeoJSON Feature que se pasa a SentinelHub:")
    print(json.dumps(example_zone_geojson, indent=2, ensure_ascii=False))
    
    print(f"\n🔍 PUNTOS CLAVE PARA SENTINELHUB:")
    print(f"   🗺️  Geometría: {example_zone_geojson['geometry']['type']}")
    print(f"   📏 Coordenadas: {len(example_zone_geojson['geometry']['coordinates'][0])} puntos")
    print(f"   📦 BoundingBox: {example_zone_geojson['properties']['bbox']}")
    print(f"   🎯 Centro calculado: lat={sum(coord[1] for coord in example_zone_geojson['geometry']['coordinates'][0]) / len(example_zone_geojson['geometry']['coordinates'][0]):.4f}, lng={sum(coord[0] for coord in example_zone_geojson['geometry']['coordinates'][0]) / len(example_zone_geojson['geometry']['coordinates'][0]):.4f}")
    print(f"   🔍 Resolución: {example_zone_geojson['properties']['recommended_resolution']}")
    print(f"   ☁️  Max nubes: {example_zone_geojson['properties']['cloud_cover_max']}%")

def main():
    """Función principal"""
    print("🛰️  RISKMAP - ANÁLISIS DE GEOJSON PARA SENTINELHUB")
    print("=" * 70)
    print("Este script muestra exactamente qué GeoJSON se le pasa")
    print("a la API de SentinelHub en el análisis satelital avanzado.")
    print("=" * 70)
    
    # Mostrar GeoJSON real generado por el sistema
    geojson_data = show_real_geojson_from_db()
    
    # Mostrar ejemplo específico para análisis de zona
    show_zone_analysis_geojson()
    
    print(f"\n✅ RESUMEN:")
    print(f"   📊 El sistema genera un FeatureCollection GeoJSON integrado")
    print(f"   🎯 Cada Feature representa una zona de conflicto con:")
    print(f"      - Geometría (Point o Polygon)")
    print(f"      - Propiedades de riesgo y metadatos")
    print(f"      - Configuración específica para SentinelHub")
    print(f"   🛰️  SentinelHub recibe:")
    print(f"      - Coordenadas precisas del área de interés")
    print(f"      - BoundingBox calculado automáticamente")
    print(f"      - Parámetros de resolución y cobertura de nubes")
    print(f"      - Prioridad de monitoreo (critical/high/medium/low)")

if __name__ == "__main__":
    main()
