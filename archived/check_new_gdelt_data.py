#!/usr/bin/env python3
"""
Script para verificar los nuevos datos GDELT ingresados
"""

import sqlite3
import json
from pathlib import Path

def check_gdelt_data():
    """Verificar datos GDELT en la base de datos"""
    db_path = Path(__file__).parent / "data" / "geopolitical_intel.db"
    
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar tabla gdelt_events
        print("🔍 Verificando tabla gdelt_events...")
        cursor.execute("SELECT COUNT(*) FROM gdelt_events")
        total = cursor.fetchone()[0]
        print(f"📊 Total de eventos GDELT: {total}")
        
        if total > 0:
            # Últimos 5 eventos
            print("\n📋 Últimos 5 eventos GDELT:")
            cursor.execute("""
                SELECT global_event_id, event_date, event_type, action_location, 
                       action_latitude, action_longitude, article_title, severity_score
                FROM gdelt_events 
                ORDER BY event_date DESC 
                LIMIT 5
            """)
            
            events = cursor.fetchall()
            for event in events:
                event_id, date, event_type, location, lat, lon, title, severity = event
                coords = f"({lat}, {lon})" if lat and lon else "Sin coordenadas"
                print(f"  📍 {event_id}")
                print(f"     📅 {date} | 🏷️ {event_type} | 📊 Severidad: {severity}")
                print(f"     📍 {location} {coords}")
                print(f"     📰 {title[:80]}...")
                print()
        
        # Verificar eventos con coordenadas
        cursor.execute("""
            SELECT COUNT(*) FROM gdelt_events 
            WHERE action_latitude IS NOT NULL AND action_longitude IS NOT NULL
        """)
        with_coords = cursor.fetchone()[0]
        print(f"📍 Eventos con coordenadas: {with_coords}/{total}")
        
        # Verificar tipos de conflicto
        cursor.execute("""
            SELECT conflict_type, COUNT(*) as count
            FROM gdelt_events 
            GROUP BY conflict_type
            ORDER BY count DESC
        """)
        conflict_types = cursor.fetchall()
        print(f"\n🏷️ Tipos de conflicto:")
        for conflict_type, count in conflict_types:
            print(f"  {conflict_type}: {count}")
        
        # Verificar ubicaciones
        cursor.execute("""
            SELECT action_location, COUNT(*) as count
            FROM gdelt_events 
            WHERE action_location != ''
            GROUP BY action_location
            ORDER BY count DESC
            LIMIT 10
        """)
        locations = cursor.fetchall()
        print(f"\n📍 Top ubicaciones:")
        for location, count in locations:
            print(f"  {location}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")

if __name__ == "__main__":
    check_gdelt_data()
