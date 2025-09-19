#!/usr/bin/env python3
"""
Verificar conflictos en la base de datos
"""

import sqlite3
from datetime import datetime, timedelta

def check_conflicts_db():
    """Verificar conflictos guardados en la base de datos"""
    try:
        conn = sqlite3.connect('geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conflict_zones'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ La tabla conflict_zones no existe")
            return
            
        print("✅ Tabla conflict_zones existe")
        
        # Contar conflictos totales
        cursor.execute('SELECT COUNT(*) FROM conflict_zones')
        total_count = cursor.fetchone()[0]
        print(f"📊 Total de conflictos en DB: {total_count}")
        
        # Contar conflictos recientes (últimos 7 días)
        seven_days_ago = datetime.now() - timedelta(days=7)
        cursor.execute('SELECT COUNT(*) FROM conflict_zones WHERE detected_at >= ?', (seven_days_ago.isoformat(),))
        recent_count = cursor.fetchone()[0]
        print(f"🕐 Conflictos últimos 7 días: {recent_count}")
        
        # Mostrar últimos conflictos
        cursor.execute('''
            SELECT location, latitude, longitude, intensity, confidence, conflict_type, detected_at 
            FROM conflict_zones 
            ORDER BY detected_at DESC 
            LIMIT 5
        ''')
        conflicts = cursor.fetchall()
        
        if conflicts:
            print("\n🎯 Últimos conflictos:")
            for i, c in enumerate(conflicts, 1):
                location, lat, lon, intensity, confidence, c_type, detected = c
                print(f"  {i}. {location}")
                print(f"     Coords: ({lat}, {lon})")
                print(f"     Intensidad: {intensity} | Confianza: {confidence:.2f}")
                print(f"     Tipo: {c_type} | Detectado: {detected}")
                print()
        else:
            print("❌ No hay conflictos en la base de datos")
            
        conn.close()
        return recent_count > 0
        
    except Exception as e:
        print(f"💥 Error verificando base de datos: {e}")
        return False

if __name__ == "__main__":
    check_conflicts_db()
