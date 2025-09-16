#!/usr/bin/env python3
"""
Script para solucionar TODOS los errores de schema detectados en los logs
Errores críticos encontrados:
- table processed_data has no column named summary
- no such column: original_language
- no such column: avg_risk_score
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_all_schema_errors():
    """Solucionar todos los errores de schema detectados"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        logger.info("🚨 SOLUCIONANDO ERRORES CRÍTICOS DE SCHEMA")
        logger.info("=" * 60)
        
        # ==========================================
        # 1. Agregar columna 'summary' a processed_data
        # ==========================================
        logger.info("🔧 Agregando columna 'summary' a processed_data...")
        try:
            cursor.execute("ALTER TABLE processed_data ADD COLUMN summary TEXT")
            logger.info("✅ Columna 'summary' agregada a processed_data")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'summary' ya existe en processed_data")
            else:
                logger.error(f"❌ Error agregando summary: {e}")
        
        # ==========================================
        # 2. Agregar columna 'original_language' 
        # ==========================================
        logger.info("🔧 Agregando columna 'original_language'...")
        
        # Intentar agregar a articles primero
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN original_language TEXT")
            logger.info("✅ Columna 'original_language' agregada a articles")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'original_language' ya existe en articles")
            else:
                logger.warning(f"⚠️ Error agregando original_language a articles: {e}")
        
        # Intentar agregar a processed_data también
        try:
            cursor.execute("ALTER TABLE processed_data ADD COLUMN original_language TEXT")
            logger.info("✅ Columna 'original_language' agregada a processed_data")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'original_language' ya existe en processed_data")
            else:
                logger.warning(f"⚠️ Error agregando original_language a processed_data: {e}")
        
        # ==========================================
        # 3. Agregar columna 'avg_risk_score' a conflict_zones
        # ==========================================
        logger.info("🔧 Agregando columna 'avg_risk_score' a conflict_zones...")
        try:
            cursor.execute("ALTER TABLE conflict_zones ADD COLUMN avg_risk_score REAL DEFAULT 0.0")
            logger.info("✅ Columna 'avg_risk_score' agregada a conflict_zones")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'avg_risk_score' ya existe en conflict_zones")
            else:
                logger.error(f"❌ Error agregando avg_risk_score: {e}")
        
        # ==========================================
        # 4. Verificar todas las columnas agregadas
        # ==========================================
        logger.info("🔍 VERIFICANDO TODAS LAS COLUMNAS AGREGADAS...")
        logger.info("=" * 60)
        
        # Verificar processed_data.summary
        cursor.execute("PRAGMA table_info(processed_data)")
        processed_columns = [col[1] for col in cursor.fetchall()]
        if 'summary' in processed_columns:
            logger.info("✅ processed_data.summary confirmado")
        else:
            logger.error("❌ processed_data.summary todavía no existe")
        
        # Verificar original_language en articles
        cursor.execute("PRAGMA table_info(articles)")
        article_columns = [col[1] for col in cursor.fetchall()]
        if 'original_language' in article_columns:
            logger.info("✅ articles.original_language confirmado")
        else:
            logger.error("❌ articles.original_language todavía no existe")
        
        # Verificar original_language en processed_data
        if 'original_language' in processed_columns:
            logger.info("✅ processed_data.original_language confirmado")
        else:
            logger.error("❌ processed_data.original_language todavía no existe")
        
        # Verificar conflict_zones.avg_risk_score
        cursor.execute("PRAGMA table_info(conflict_zones)")
        conflict_columns = [col[1] for col in cursor.fetchall()]
        if 'avg_risk_score' in conflict_columns:
            logger.info("✅ conflict_zones.avg_risk_score confirmado")
        else:
            logger.error("❌ conflict_zones.avg_risk_score todavía no existe")
        
        # ==========================================
        # 5. Commit cambios
        # ==========================================
        conn.commit()
        conn.close()
        
        logger.info("=" * 60)
        logger.info("🎉 TODAS LAS CORRECCIONES DE SCHEMA COMPLETADAS")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"❌ Error crítico durante la corrección de schema: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 INICIANDO CORRECCIÓN MASIVA DE ERRORES DE SCHEMA")
    logger.info("Errores a solucionar:")
    logger.info("  - table processed_data has no column named summary")
    logger.info("  - no such column: original_language") 
    logger.info("  - no such column: avg_risk_score")
    logger.info("")
    
    success = fix_all_schema_errors()
    
    if success:
        logger.info("✅ CORRECCIÓN EXITOSA - Todos los errores de schema han sido solucionados")
        logger.info("🔄 Ahora puedes reiniciar la aplicación sin errores de schema")
    else:
        logger.error("❌ LA CORRECCIÓN FALLÓ")

if __name__ == "__main__":
    main()