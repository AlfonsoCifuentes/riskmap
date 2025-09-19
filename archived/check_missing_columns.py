#!/usr/bin/env python3
"""
Script para verificar columnas faltantes en la base de datos
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_table_structure(table_name):
    """Verificar estructura de una tabla específica"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        logger.info(f"🔍 Tabla {table_name}:")
        for col in columns:
            logger.info(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return [col[1] for col in columns]
        
    except Exception as e:
        logger.error(f"❌ Error verificando tabla {table_name}: {e}")
        return []

def main():
    """Función principal"""
    logger.info("🔍 Verificando estructura de tablas críticas...")
    
    # Verificar tablas críticas
    tables = ['articles', 'processed_data', 'conflict_zones', 'satellite_zones']
    
    for table in tables:
        columns = check_table_structure(table)
        logger.info(f"📊 {table} tiene {len(columns)} columnas\n")
    
    # Verificar errores específicos encontrados en los logs
    logger.info("🔍 Verificando errores específicos de los logs:")
    
    conn = sqlite3.connect('./data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # 1. Verificar article_id en processed_data
    cursor.execute("PRAGMA table_info(processed_data)")
    processed_columns = [col[1] for col in cursor.fetchall()]
    
    if 'article_id' in processed_columns:
        logger.info("✅ processed_data.article_id existe")
    else:
        logger.error("❌ processed_data.article_id NO existe")
    
    # 2. Verificar is_translated en articles
    cursor.execute("PRAGMA table_info(articles)")
    article_columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_translated' in article_columns:
        logger.info("✅ articles.is_translated existe")
    else:
        logger.error("❌ articles.is_translated NO existe")
    
    # 3. Verificar conflict_count en conflict_zones
    cursor.execute("PRAGMA table_info(conflict_zones)")
    conflict_columns = [col[1] for col in cursor.fetchall()]
    
    if 'conflict_count' in conflict_columns:
        logger.info("✅ conflict_zones.conflict_count existe")
    else:
        logger.error("❌ conflict_zones.conflict_count NO existe")
    
    # 4. Verificar latitude en conflict_zones
    if 'latitude' in conflict_columns:
        logger.info("✅ conflict_zones.latitude existe")
    else:
        logger.error("❌ conflict_zones.latitude NO existe")
    
    conn.close()

if __name__ == "__main__":
    main()