#!/usr/bin/env python3
"""
DOCUMENTACIÓN CIENTÍFICA DE LA ESTRUCTURA ACTUAL DE LA BASE DE DATOS
===================================================================
"""

import sqlite3
import json

def get_database_structure():
    """Obtener estructura completa de la base de datos"""
    print("🔍 ANALIZANDO ESTRUCTURA ACTUAL DE LA BASE DE DATOS")
    print("=" * 80)
    
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # 1. Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 TABLAS ACTUALES: {len(tables)}")
    for table in tables:
        print(f"   • {table}")
    
    # 2. Estructura detallada de unified_articles (tabla principal)
    print(f"\n🗄️  ESTRUCTURA DE UNIFIED_ARTICLES (TABLA PRINCIPAL)")
    print("=" * 80)
    
    cursor.execute("PRAGMA table_info(unified_articles)")
    columns = cursor.fetchall()
    
    print(f"Columnas totales: {len(columns)}")
    print("\nEstructura completa:")
    for col in columns:
        col_id, name, data_type, not_null, default, pk = col
        nullable = "NOT NULL" if not_null else "NULL"
        primary = " [PK]" if pk else ""
        default_val = f" DEFAULT {default}" if default else ""
        print(f"   {col_id:2d}. {name:<30} {data_type:<10} {nullable:<8}{default_val}{primary}")
    
    # 3. Estadísticas de datos
    print(f"\n📈 ESTADÍSTICAS DE DATOS")
    print("=" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM unified_articles")
    total_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE title IS NOT NULL AND content IS NOT NULL")
    valid_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE risk_level IS NOT NULL")
    risk_analyzed = cursor.fetchone()[0]
    
    print(f"Total de registros: {total_records:,}")
    print(f"Registros válidos: {valid_records:,} ({valid_records/total_records*100:.1f}%)")
    print(f"Con análisis de riesgo: {risk_analyzed:,} ({risk_analyzed/total_records*100:.1f}%)")
    
    # 4. Índices existentes
    print(f"\n🔍 ÍNDICES OPTIMIZADOS")
    print("=" * 80)
    
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name")
    indexes = cursor.fetchall()
    
    for idx_name, idx_sql in indexes:
        print(f"   • {idx_name}")
        if idx_sql:
            print(f"     {idx_sql}")
    
    # 5. Otras tablas importantes
    print(f"\n🗂️  OTRAS TABLAS DEL SISTEMA")
    print("=" * 80)
    
    other_tables = [t for t in tables if t != 'unified_articles' and t != 'sqlite_sequence']
    for table in other_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        status = "ACTIVA" if count > 0 else "VACÍA"
        print(f"   • {table:<25} | {count:>6,} registros | {status}")
    
    conn.close()
    
    return {
        'tables': tables,
        'unified_articles_columns': [col[1] for col in columns],
        'total_records': total_records,
        'indexes': [idx[0] for idx in indexes]
    }

if __name__ == "__main__":
    structure = get_database_structure()
    
    print(f"\n✅ ESTRUCTURA DOCUMENTADA CIENTÍFICAMENTE")
    print("=" * 80)
    print("Esta es la estructura definitiva que debe usar TODO el código del website.")