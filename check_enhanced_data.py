#!/usr/bin/env python3
"""Verificar datos mejorados en la base de datos"""

import sqlite3
import json

def check_enhanced_data():
    """Verificar que los datos mejorados se guardaron correctamente"""
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Verificar conflictos con coordenadas precisas
        cursor.execute("""
            SELECT location, latitude, longitude, area_precision, 
                   area_size_km2, satellite_ready, geojson_feature
            FROM ai_detected_conflicts 
            ORDER BY detected_at DESC 
            LIMIT 5
        """)
        
        conflicts = cursor.fetchall()
        print("📊 Recent AI Conflicts with Enhanced Data:")
        for i, row in enumerate(conflicts, 1):
            location, lat, lon, precision, area, sat_ready, geojson = row
            print(f"  {i}. {location}")
            print(f"     Coordinates: ({lat}, {lon})")
            print(f"     Precision: {precision}")
            print(f"     Area: {area} km²")
            print(f"     Satellite Ready: {'Yes' if sat_ready else 'No'}")
            if geojson:
                try:
                    geojson_data = json.loads(geojson)
                    print(f"     GeoJSON Type: {geojson_data.get('type', 'Unknown')}")
                    print(f"     Geometry: {geojson_data.get('geometry', {}).get('type', 'Unknown')}")
                except (json.JSONDecodeError, TypeError):
                    print("     GeoJSON: Invalid")
            print()
        
        # Verificar zonas satelitales
        cursor.execute("""
            SELECT zone_name, center_latitude, center_longitude, 
                   priority, conflict_count, area_size_km2
            FROM satellite_target_zones
            ORDER BY last_updated DESC
        """)
        
        zones = cursor.fetchall()
        print(f"\n🛰️ Satellite Target Zones ({len(zones)} zones):")
        for i, row in enumerate(zones, 1):
            name, lat, lon, priority, count, area = row
            priority_label = ['High', 'Medium', 'Low'][priority-1] if 1 <= priority <= 3 else 'Unknown'
            print(f"  {i}. {name}")
            print(f"     Center: ({lat}, {lon})")
            print(f"     Priority: {priority_label}")
            print(f"     Conflicts: {count}")
            print(f"     Area: {area} km²")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_enhanced_data()
