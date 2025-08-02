#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar el esquema de la base de datos con las nuevas columnas
para el sistema de posicionamiento inteligente de imágenes
"""

import sqlite3
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_path():
    """Obtener la ruta de la base de datos desde las variables de entorno"""
    db_path = os.getenv('DATABASE_PATH', 'data/riskmap.db')
    return Path(db_path)

def update_database_schema():
    """
    Actualizar el esquema de la base de datos añadiendo las columnas necesarias
    para el sistema de posicionamiento inteligente
    """
    db_path = get_database_path()
    
    if not db_path.exists():
        logger.error(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    logger.info(f"🔧 Actualizando esquema de base de datos: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Lista de columnas a agregar
            new_columns = [
                ('image_fingerprint', 'TEXT'),
                ('mosaic_position', 'TEXT'),
                ('visual_analysis_json', 'TEXT'),
                ('cv_quality_score', 'REAL'),
                ('image_width', 'INTEGER'),
                ('image_height', 'INTEGER'),
                ('dominant_colors', 'TEXT'),
                ('has_faces', 'BOOLEAN DEFAULT 0'),
                ('positioning_score', 'REAL')
            ]
            
            # Verificar qué columnas ya existen
            cursor.execute("PRAGMA table_info(articles)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Agregar columnas que no existen
            columns_added = 0
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}"
                        cursor.execute(sql)
                        logger.info(f"✅ Columna agregada: {column_name}")
                        columns_added += 1
                    except Exception as e:
                        logger.error(f"❌ Error agregando columna {column_name}: {e}")
                else:
                    logger.info(f"⚠️ Columna ya existe: {column_name}")
            
            # Crear índices para mejorar el rendimiento
            indices_to_create = [
                ("idx_image_fingerprint", "CREATE INDEX IF NOT EXISTS idx_image_fingerprint ON articles(image_fingerprint)"),
                ("idx_mosaic_position", "CREATE INDEX IF NOT EXISTS idx_mosaic_position ON articles(mosaic_position)"),
                ("idx_cv_quality_score", "CREATE INDEX IF NOT EXISTS idx_cv_quality_score ON articles(cv_quality_score)"),
                ("idx_has_faces", "CREATE INDEX IF NOT EXISTS idx_has_faces ON articles(has_faces)")
            ]
            
            indices_created = 0
            for index_name, sql in indices_to_create:
                try:
                    cursor.execute(sql)
                    logger.info(f"✅ Índice creado: {index_name}")
                    indices_created += 1
                except Exception as e:
                    logger.error(f"❌ Error creando índice {index_name}: {e}")
            
            # Confirmar cambios
            conn.commit()
            
            logger.info(f"🎉 Actualización completada:")
            logger.info(f"   📊 Columnas agregadas: {columns_added}")
            logger.info(f"   🗂️ Índices creados: {indices_created}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error actualizando esquema: {e}")
        return False

def verify_schema():
    """Verificar que el esquema esté actualizado correctamente"""
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Obtener información de la tabla
            cursor.execute("PRAGMA table_info(articles)")
            columns = cursor.fetchall()
            
            logger.info("📋 ESQUEMA ACTUAL DE LA TABLA 'articles':")
            logger.info("=" * 60)
            
            for col in columns:
                col_id, name, data_type, not_null, default_value, pk = col
                logger.info(f"   {name:25} | {data_type:15} | {'NOT NULL' if not_null else 'NULL'}")
            
            # Verificar índices
            cursor.execute("PRAGMA index_list(articles)")
            indices = cursor.fetchall()
            
            logger.info(f"\n🗂️ ÍNDICES DISPONIBLES ({len(indices)}):")
            logger.info("-" * 40)
            for idx in indices:
                logger.info(f"   {idx[1]}")
                
            return True
            
    except Exception as e:
        logger.error(f"❌ Error verificando esquema: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ACTUALIZADOR DE ESQUEMA DE BASE DE DATOS")
    print("=" * 60)
    
    # Actualizar esquema
    if update_database_schema():
        print("\n✅ Esquema actualizado exitosamente")
        
        # Verificar esquema
        print("\n🔍 VERIFICANDO ESQUEMA ACTUALIZADO...")
        verify_schema()
    else:
        print("\n❌ Error actualizando esquema")
        exit(1)
    
    print("\n🎯 Proceso completado. El sistema está listo para usar el posicionamiento inteligente.")
