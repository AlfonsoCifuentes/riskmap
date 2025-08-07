#!/usr/bin/env python3
"""
Script para completar la creación de zonas de conflicto
"""

import sqlite3
import os

def complete_conflict_zones():
    """Completar la creación de zonas de conflicto"""
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    print("🎯 COMPLETANDO ZONAS DE CONFLICTO")
    print("=" * 40)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe y recrearla correctamente
        cursor.execute("DROP TABLE IF EXISTS conflict_zones")
        
        # Crear tabla para zonas de conflicto
        cursor.execute("""
            CREATE TABLE conflict_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                latitude REAL,
                longitude REAL,
                conflict_count INTEGER DEFAULT 0,
                avg_risk_score REAL DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla conflict_zones creada")
        
        # Generar zonas de conflicto basadas en artículos de alto riesgo
        cursor.execute("""
            INSERT INTO conflict_zones (name, latitude, longitude, conflict_count, avg_risk_score)
            SELECT 
                country as name,
                AVG(latitude) as latitude,
                AVG(longitude) as longitude,
                COUNT(*) as conflict_count,
                AVG(risk_score) as avg_risk_score
            FROM articles 
            WHERE risk_level = 'high' 
              AND latitude IS NOT NULL 
              AND longitude IS NOT NULL
              AND (is_excluded IS NULL OR is_excluded != 1)
              AND country IS NOT NULL
            GROUP BY country
            HAVING COUNT(*) >= 2
            ORDER BY COUNT(*) DESC
        """)
        
        zones_created = cursor.rowcount
        print(f"✅ {zones_created} zonas de conflicto creadas")
        
        # Mostrar las zonas creadas
        cursor.execute("""
            SELECT name, conflict_count, avg_risk_score, latitude, longitude 
            FROM conflict_zones 
            ORDER BY conflict_count DESC 
            LIMIT 10
        """)
        
        print("\\n🔥 TOP 10 ZONAS DE CONFLICTO:")
        for row in cursor.fetchall():
            name, count, avg_score, lat, lng = row
            print(f"   {name}: {count} conflictos (riesgo: {avg_score:.2f}) - [{lat:.2f}, {lng:.2f}]")
        
        # Estadísticas finales completas
        print("\\n📊 ESTADÍSTICAS FINALES:")
        
        cursor.execute("SELECT risk_level, COUNT(*) FROM articles WHERE (is_excluded IS NULL OR is_excluded != 1) GROUP BY risk_level")
        final_distribution = cursor.fetchall()
        print("   ⚖️ Distribución final de risk_level (solo artículos geopolíticos):")
        total_geo = 0
        for level, count in final_distribution:
            print(f"   - {level}: {count} artículos")
            total_geo += count
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND (is_excluded IS NULL OR is_excluded != 1)")
        geocoded_total = cursor.fetchone()[0]
        print(f"   📍 Artículos geopolíticos geocodificados: {geocoded_total}")
        
        cursor.execute("SELECT COUNT(*) FROM conflict_zones")
        zones_total = cursor.fetchone()[0]
        print(f"   🎯 Total zonas de conflicto: {zones_total}")
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_excluded = 1")
        excluded_total = cursor.fetchone()[0]
        print(f"   🚫 Total artículos excluidos (no geopolíticos): {excluded_total}")
        
        print(f"   🌍 Total artículos geopolíticos válidos: {total_geo}")
        
        conn.commit()
        print("\\n✅ ZONAS DE CONFLICTO COMPLETADAS")

if __name__ == "__main__":
    complete_conflict_zones()
