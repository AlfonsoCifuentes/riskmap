#!/usr/bin/env python3
"""
Fix para agregar columnas faltantes a la base de datos
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Agregar columnas faltantes a la base de datos"""
    try:
        db_path = r"data\geopolitical_intel.db"
        
        if not os.path.exists(db_path):
            logger.warning(f"Base de datos no encontrada: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Agregar columnas necesarias
        columns_to_add = [
            ("category", "TEXT DEFAULT 'general'"),
            ("is_excluded", "INTEGER DEFAULT 0"), 
            ("excluded_reason", "TEXT"),
            ("has_gdelt_data", "INTEGER DEFAULT 0"),
            ("gdelt_event_count", "INTEGER DEFAULT 0"),
            ("avg_goldstein_scale", "REAL DEFAULT 0.0"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_def}")
                logger.info(f"✅ Columna agregada: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info(f"📋 Columna ya existe: {column_name}")
                else:
                    logger.error(f"❌ Error agregando {column_name}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Esquema de base de datos actualizado")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando esquema: {e}")

if __name__ == "__main__":
    fix_database_schema()
