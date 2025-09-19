#!/usr/bin/env python3
"""
Verificar diversidad de coordenadas únicas en ai_detected_conflicts
"""

import sqlite3

def check_unique_coordinates():
    """Verificar qué coordenadas únicas tenemos para conflictos"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        print("🌍 VERIFICANDO DIVERSIDAD DE COORDENADAS DE CONFLICTOS...")
        
        # Obtener coordenadas únicas
        cursor.execute("""
            SELECT DISTINCT location, latitude, longitude, COUNT(*) as count
            FROM ai_detected_conflicts 
            WHERE is_active = 1
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            GROUP BY location, latitude, longitude
            ORDER BY count DESC
        """)
        
        unique_coords = cursor.fetchall()
        print(f"\n📊 TOTAL UBICACIONES ÚNICAS: {len(unique_coords)}")
        
        print("\n🗺️ COORDENADAS ÚNICAS POR UBICACIÓN:")
        for coord in unique_coords:
            location, lat, lon, count = coord
            print(f"   📍 {location}: ({lat:.4f}, {lon:.4f}) - {count} conflictos")
        
        # Verificar rangos geográficos
        cursor.execute("""
            SELECT MIN(latitude), MAX(latitude), MIN(longitude), MAX(longitude)
            FROM ai_detected_conflicts 
            WHERE is_active = 1
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
        """)
        
        ranges = cursor.fetchone()
        if ranges:
            min_lat, max_lat, min_lon, max_lon = ranges
            print(f"\n📏 RANGOS GEOGRÁFICOS:")
            print(f"   🌐 Latitud: {min_lat:.4f} a {max_lat:.4f}")
            print(f"   🌐 Longitud: {min_lon:.4f} a {max_lon:.4f}")
        
        # Verificar diferentes niveles de riesgo
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count,
                   COUNT(DISTINCT location) as unique_locations
            FROM ai_detected_conflicts 
            WHERE is_active = 1
            GROUP BY risk_level
            ORDER BY count DESC
        """)
        
        risk_levels = cursor.fetchall()
        print(f"\n⚠️ CONFLICTOS POR NIVEL DE RIESGO:")
        for risk in risk_levels:
            level, count, unique_locs = risk
            print(f"   🎯 {level}: {count} conflictos en {unique_locs} ubicaciones únicas")
        
        # Verificar artículos fuente únicos
        cursor.execute("""
            SELECT COUNT(DISTINCT article_id) as unique_articles
            FROM ai_detected_conflicts 
            WHERE is_active = 1
        """)
        
        unique_articles = cursor.fetchone()[0]
        print(f"\n📰 ARTÍCULOS FUENTE ÚNICOS: {unique_articles}")
        
        # Verificar fechas de detección
        cursor.execute("""
            SELECT DATE(detected_at) as detection_date, COUNT(*) as count
            FROM ai_detected_conflicts 
            WHERE is_active = 1
            GROUP BY DATE(detected_at)
            ORDER BY detection_date DESC
            LIMIT 10
        """)
        
        recent_detections = cursor.fetchall()
        print(f"\n📅 DETECCIONES RECIENTES:")
        for detection in recent_detections:
            date, count = detection
            print(f"   📆 {date}: {count} conflictos detectados")
        
        # Buscar todas las ubicaciones mencionadas
        cursor.execute("""
            SELECT location, all_locations, latitude, longitude, confidence, risk_level
            FROM ai_detected_conflicts 
            WHERE is_active = 1
            AND all_locations IS NOT NULL
            AND all_locations != ''
            ORDER BY confidence DESC
            LIMIT 20
        """)
        
        detailed_locations = cursor.fetchall()
        print(f"\n🔍 UBICACIONES DETALLADAS (Top 20 por confianza):")
        
        for detail in detailed_locations:
            location, all_locs, lat, lon, conf, risk = detail
            print(f"   📍 {location} | Todas: {all_locs}")
            print(f"      Coords: ({lat:.4f}, {lon:.4f}) | Risk: {risk} | Conf: {conf:.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_unique_coordinates()
