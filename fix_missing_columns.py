#!/usr/bin/env python3
"""
Script de migración específico para columnas faltantes
Basado en errores detectados en los logs
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_missing_columns():
    """Agregar las columnas específicamente faltantes"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        logger.info("🔧 Agregando columnas faltantes...")
        
        # 1. Agregar article_id a processed_data
        try:
            cursor.execute("ALTER TABLE processed_data ADD COLUMN article_id INTEGER")
            logger.info("✅ Columna 'article_id' agregada a processed_data")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'article_id' ya existe en processed_data")
            else:
                logger.error(f"❌ Error agregando article_id: {e}")
        
        # 2. Agregar is_translated a articles
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN is_translated INTEGER DEFAULT 0")
            logger.info("✅ Columna 'is_translated' agregada a articles")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'is_translated' ya existe en articles")
            else:
                logger.error(f"❌ Error agregando is_translated: {e}")
        
        # 3. Agregar conflict_count a conflict_zones
        try:
            cursor.execute("ALTER TABLE conflict_zones ADD COLUMN conflict_count INTEGER DEFAULT 0")
            logger.info("✅ Columna 'conflict_count' agregada a conflict_zones")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'conflict_count' ya existe en conflict_zones")
            else:
                logger.error(f"❌ Error agregando conflict_count: {e}")
        
        # Commit cambios
        conn.commit()
        
        # Verificar que las columnas se agregaron
        logger.info("🔍 Verificando columnas agregadas...")
        
        # Verificar article_id en processed_data
        cursor.execute("PRAGMA table_info(processed_data)")
        processed_columns = [col[1] for col in cursor.fetchall()]
        if 'article_id' in processed_columns:
            logger.info("✅ processed_data.article_id confirmado")
        else:
            logger.error("❌ processed_data.article_id todavía no existe")
        
        # Verificar is_translated en articles
        cursor.execute("PRAGMA table_info(articles)")
        article_columns = [col[1] for col in cursor.fetchall()]
        if 'is_translated' in article_columns:
            logger.info("✅ articles.is_translated confirmado")
        else:
            logger.error("❌ articles.is_translated todavía no existe")
        
        # Verificar conflict_count en conflict_zones
        cursor.execute("PRAGMA table_info(conflict_zones)")
        conflict_columns = [col[1] for col in cursor.fetchall()]
        if 'conflict_count' in conflict_columns:
            logger.info("✅ conflict_zones.conflict_count confirmado")
        else:
            logger.error("❌ conflict_zones.conflict_count todavía no existe")
        
        conn.close()
        logger.info("🎉 Migración específica completada")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 Iniciando migración de columnas faltantes...")
    
    success = add_missing_columns()
    
    if success:
        logger.info("🎉 Migración exitosa - todas las columnas faltantes han sido agregadas")
    else:
        logger.error("❌ La migración falló")

if __name__ == "__main__":
    main()