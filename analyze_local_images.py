#!/usr/bin/env python3
"""
Script para analizar específicamente las imágenes locales que no tienen análisis CV
"""

import sys
import os
import sqlite3
import logging
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir el patch de compatibilidad ANTES de cualquier import ML
sys.path.insert(0, os.path.dirname(__file__))

# Importar patch inmediatamente
try:
    import ml_dtypes_patch
    print("🔧 Patch ml_dtypes aplicado correctamente")
except ImportError as e:
    print(f"⚠️ No se pudo cargar patch ml_dtypes: {e}")

def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/local_images_analysis.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_database_path():
    """Obtener ruta de la base de datos desde variables de entorno"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    return database_url

def get_local_images_without_analysis(limit=None):
    """Obtener artículos con imágenes locales sin análisis CV"""
    db_path = get_database_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT id, title, image_url
            FROM articles 
            WHERE image_url IS NOT NULL 
            AND image_url != '' 
            AND image_url NOT LIKE 'http%'
            AND image_url NOT LIKE '%placeholder%'
            AND image_url NOT LIKE '%via.placeholder%'
            AND image_url NOT LIKE '%picsum%'
            AND (visual_analysis_json IS NULL OR visual_analysis_json = '')
            ORDER BY id DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        return cursor.fetchall()

def analyze_single_local_image(article_id, title, image_url, analyzer_func, logger):
    """Analizar una sola imagen local y devolver resultados"""
    try:
        logger.info(f"Analizando imagen local para artículo {article_id}: {title[:50]}...")
        logger.info(f"Ruta imagen: {image_url}")
        
        # Realizar análisis
        analysis_result = analyzer_func(image_url, title)
        
        if analysis_result and 'error' not in analysis_result:
            logger.info(f"✅ Análisis local completado para artículo {article_id}")
            return analysis_result
        else:
            logger.warning(f"⚠️ Análisis local falló para artículo {article_id}: {analysis_result}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error analizando imagen local {article_id}: {e}")
        return None

def save_analysis_to_db(article_id, analysis_result, logger):
    """Guardar resultado del análisis en la base de datos"""
    try:
        db_path = get_database_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Extraer datos del análisis
            visual_risk_score = analysis_result.get('risk_score', 0.0)
            detected_objects = json.dumps(analysis_result.get('detected_objects', []))
            visual_analysis_json = json.dumps(analysis_result)
            
            # Actualizar la base de datos
            cursor.execute("""
                UPDATE articles 
                SET visual_risk_score = ?,
                    detected_objects = ?,
                    visual_analysis_json = ?,
                    visual_analysis_timestamp = ?
                WHERE id = ?
            """, (
                visual_risk_score,
                detected_objects,
                visual_analysis_json,
                datetime.now().isoformat(),
                article_id
            ))
            
            conn.commit()
            logger.info(f"💾 Análisis local guardado en BD para artículo {article_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error guardando análisis local en BD para artículo {article_id}: {e}")
        return False

def analyze_local_images(batch_size=20, max_articles=None):
    """Analizar todas las imágenes locales en lotes"""
    logger = setup_logging()
    
    # Verificar disponibilidad del módulo CV
    try:
        from src.vision.image_analysis import ImageInterestAnalyzer, analyze_article_image
        logger.info("✅ Computer Vision module imported successfully")
    except ImportError as e:
        logger.error(f"❌ Error importing Computer Vision: {e}")
        return
    
    # Obtener artículos con imágenes locales para analizar
    articles = get_local_images_without_analysis(limit=max_articles)
    total_articles = len(articles)
    
    if total_articles == 0:
        logger.info("✅ No hay imágenes locales pendientes de análisis CV")
        return
    
    logger.info(f"🚀 Iniciando análisis CV de {total_articles} imágenes locales en lotes de {batch_size}")
    
    # Procesar en lotes
    processed = 0
    successful = 0
    failed = 0
    
    for i in range(0, total_articles, batch_size):
        batch = articles[i:i + batch_size]
        logger.info(f"📦 Procesando lote {i//batch_size + 1}/{(total_articles-1)//batch_size + 1} ({len(batch)} artículos)")
        
        for article_id, title, image_url in batch:
            processed += 1
            
            # Analizar imagen local
            analysis_result = analyze_single_local_image(
                article_id, title, image_url, analyze_article_image, logger
            )
            
            if analysis_result:
                # Guardar en base de datos
                if save_analysis_to_db(article_id, analysis_result, logger):
                    successful += 1
                else:
                    failed += 1
            else:
                failed += 1
            
            # Mostrar progreso
            if processed % 10 == 0:
                logger.info(f"📊 Progreso: {processed}/{total_articles} ({processed/total_articles*100:.1f}%) - ✅{successful} ❌{failed}")
    
    # Resumen final
    logger.info("🎉 Análisis CV de imágenes locales completado")
    logger.info(f"📊 Total procesados: {processed}")
    logger.info(f"✅ Exitosos: {successful}")
    logger.info(f"❌ Fallidos: {failed}")
    logger.info(f"📈 Tasa de éxito: {successful/processed*100 if processed > 0 else 0:.1f}%")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analizar imágenes locales con Computer Vision')
    parser.add_argument('--batch-size', type=int, default=20, help='Tamaño del lote (default: 20)')
    parser.add_argument('--max-articles', type=int, help='Máximo número de artículos a procesar')
    parser.add_argument('--test', action='store_true', help='Solo probar con 5 artículos')
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Modo de prueba: analizando solo 5 imágenes locales")
        analyze_local_images(batch_size=5, max_articles=5)
    else:
        analyze_local_images(batch_size=args.batch_size, max_articles=args.max_articles)

if __name__ == "__main__":
    main()
