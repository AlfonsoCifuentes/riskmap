#!/usr/bin/env python3
"""
Script de migración de base de datos para RiskMap
Soluciona los errores de schema encontrados en los logs
"""

import sqlite3
import logging
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_database():
    """Ejecuta las migraciones necesarias para solucionar errores de schema"""
    
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        logger.info("🔧 Iniciando migración de base de datos...")
        
        # ==========================================
        # 1. Agregar columna 'advanced_nlp' a processed_data 
        # ==========================================
        try:
            cursor.execute("ALTER TABLE processed_data ADD COLUMN advanced_nlp TEXT")
            logger.info("✅ Columna 'advanced_nlp' agregada a processed_data")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'advanced_nlp' ya existe en processed_data")
            else:
                logger.warning(f"⚠️ Error agregando columna advanced_nlp: {e}")
        
        # ==========================================
        # 2. Agregar columnas faltantes a articles
        # ==========================================
        article_columns = [
            ("is_excluded", "INTEGER DEFAULT 0"),
            ("is_translated", "INTEGER DEFAULT 0"),
        ]
        
        for column_name, column_def in article_columns:
            try:
                cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_def}")
                logger.info(f"✅ Columna '{column_name}' agregada a articles")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info(f"ℹ️ Columna '{column_name}' ya existe en articles")
                else:
                    logger.warning(f"⚠️ Error agregando columna {column_name}: {e}")
        
        # ==========================================
        # 3. Agregar columnas de geolocalización a conflict_zones
        # ==========================================
        conflict_columns = [
            ("latitude", "REAL"),
            ("longitude", "REAL"),
            ("conflict_count", "INTEGER DEFAULT 0"),
        ]
        
        for column_name, column_def in conflict_columns:
            try:
                cursor.execute(f"ALTER TABLE conflict_zones ADD COLUMN {column_name} {column_def}")
                logger.info(f"✅ Columna '{column_name}' agregada a conflict_zones")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info(f"ℹ️ Columna '{column_name}' ya existe en conflict_zones")
                else:
                    logger.warning(f"⚠️ Error agregando columna {column_name}: {e}")
        
        # ==========================================
        # 4. Verificar y crear vista para ambiguedad de 'title'
        # ==========================================
        try:
            cursor.execute("DROP VIEW IF EXISTS articles_view")
            cursor.execute("""
                CREATE VIEW articles_view AS 
                SELECT 
                    a.id,
                    a.title as article_title,
                    a.content,
                    a.url,
                    a.source,
                    a.published_at,
                    a.language,
                    a.created_at,
                    a.risk_level,
                    a.country,
                    a.region,
                    a.summary,
                    a.risk_score,
                    a.sentiment_score,
                    a.sentiment_label,
                    a.is_excluded,
                    pd.advanced_nlp,
                    pd.sentiment as processed_sentiment,
                    pd.risk_score as processed_risk_score
                FROM articles a
                LEFT JOIN processed_data pd ON a.url = pd.url
                WHERE a.is_excluded = 0 OR a.is_excluded IS NULL
            """)
            logger.info("✅ Vista 'articles_view' creada para evitar ambiguedad de columnas")
        except Exception as e:
            logger.warning(f"⚠️ Error creando vista: {e}")
        
        # ==========================================
        # 5. Agregar columna article_id a processed_data
        # ==========================================
        try:
            cursor.execute("ALTER TABLE processed_data ADD COLUMN article_id INTEGER")
            logger.info("✅ Columna 'article_id' agregada a processed_data")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columna 'article_id' ya existe en processed_data")
            else:
                logger.warning(f"⚠️ Error agregando columna article_id: {e}")
        
        # ==========================================
        # 6. Actualizar satellite_zones con coordenadas si no existen
        # ==========================================
        try:
            cursor.execute("ALTER TABLE satellite_zones ADD COLUMN center_lat REAL")
            cursor.execute("ALTER TABLE satellite_zones ADD COLUMN center_lon REAL")
            logger.info("✅ Columnas de coordenadas agregadas a satellite_zones")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️ Columnas de coordenadas ya existen en satellite_zones")
            else:
                logger.warning(f"⚠️ Error agregando columnas de coordenadas: {e}")
        
        # ==========================================
        # 7. Verificar integridad de datos
        # ==========================================
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_data")
        processed_count = cursor.fetchone()[0]
        
        logger.info(f"📊 Estado actual: {articles_count} artículos, {processed_count} procesados")
        
        # Commit cambios
        conn.commit()
        conn.close()
        
        logger.info("🎉 Migración completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        return False

def verify_migration():
    """Verifica que las migraciones se aplicaron correctamente"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        logger.info("🔍 Verificando migración...")
        
        # Verificar columnas críticas
        checks = [
            ("processed_data", "advanced_nlp"),
            ("processed_data", "article_id"),
            ("articles", "is_excluded"),
            ("articles", "is_translated"),
            ("conflict_zones", "latitude"),
            ("conflict_zones", "longitude"),
            ("conflict_zones", "conflict_count"),
            ("satellite_zones", "center_lat"),
            ("satellite_zones", "center_lon")
        ]
        
        all_passed = True
        
        for table, column in checks:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if column in columns:
                    logger.info(f"✅ {table}.{column} existe")
                else:
                    logger.error(f"❌ {table}.{column} NO existe")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ Error verificando {table}.{column}: {e}")
                all_passed = False
        
        conn.close()
        
        if all_passed:
            logger.info("🎉 Todas las verificaciones pasaron")
        else:
            logger.error("❌ Algunas verificaciones fallaron")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Error durante verificación: {e}")
        return False

if __name__ == "__main__":
    print("🛠️ Script de Migración de Base de Datos - RiskMap")
    print("=" * 50)
    
    success = migrate_database()
    if success:
        verify_migration()
        print("\n✅ Migración completada. Puedes ejecutar la aplicación ahora.")
    else:
        print("\n❌ Error en migración. Revisa los logs.")
        sys.exit(1)