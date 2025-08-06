#!/usr/bin/env python3
"""
Script para arreglar y ejecutar el sistema de enriquecimiento correctamente
"""

import os
import sys
import sqlite3
import logging
import json
import time
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnrichmentFixer:
    def __init__(self):
        self.db_path = Path('data/geopolitical_intel.db')
        
    def add_missing_columns(self):
        """Agregar columnas faltantes para tracking de enriquecimiento"""
        logger.info("🔧 Adding missing columns...")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Columnas necesarias para tracking
        missing_columns = [
            ('groq_enhanced', 'INTEGER DEFAULT 0'),
            ('nlp_processed', 'INTEGER DEFAULT 0'),
            ('image_processed', 'INTEGER DEFAULT 0'),
            ('enhanced_date', 'TEXT'),
            ('processing_version', 'TEXT DEFAULT "v1.0"')
        ]
        
        for col_name, col_type in missing_columns:
            try:
                cursor.execute(f'ALTER TABLE articles ADD COLUMN {col_name} {col_type}')
                logger.info(f"✅ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    logger.info(f"⚠️ Column {col_name} already exists")
                else:
                    logger.error(f"❌ Error adding {col_name}: {e}")
        
        conn.commit()
        conn.close()
        logger.info("✅ Database schema updated")
    
    def test_nlp_processing(self):
        """Probar el procesamiento NLP en un artículo de muestra"""
        logger.info("🧠 Testing NLP processing...")
        
        try:
            # Importar dependencias NLP
            sys.path.append(str(Path(__file__).parent))
            from src.enrichment.intelligent_data_enrichment import IntelligentDataEnrichment, EnrichmentConfig
            
            # Configurar enriquecedor
            config = EnrichmentConfig()
            enricher = IntelligentDataEnrichment(config)
            
            # Obtener un artículo sin procesar
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content FROM articles 
                WHERE (key_persons IS NULL OR key_persons = '') 
                AND title IS NOT NULL AND content IS NOT NULL
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if not row:
                logger.warning("⚠️ No unprocessed articles found")
                conn.close()
                return
            
            article_id, title, content = row
            logger.info(f"🔍 Testing with article {article_id}: {title[:50]}...")
            
            # Procesar
            result = enricher.enrich_single_article(article_id)
            
            if result.success:
                logger.info(f"✅ NLP processing successful: {result.fields_updated}")
                logger.info(f"📊 Confidence: {result.confidence}")
            else:
                logger.error(f"❌ NLP processing failed: {result.error}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error testing NLP: {e}")
    
    def process_batch_nlp(self, limit=50):
        """Procesar un lote de artículos con NLP"""
        logger.info(f"🚀 Processing {limit} articles with NLP...")
        
        try:
            sys.path.append(str(Path(__file__).parent))
            from src.enrichment.intelligent_data_enrichment import IntelligentDataEnrichment, EnrichmentConfig
            
            config = EnrichmentConfig()
            enricher = IntelligentDataEnrichment(config)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Obtener artículos sin procesar
            cursor.execute("""
                SELECT id, title FROM articles 
                WHERE (nlp_processed IS NULL OR nlp_processed = 0)
                AND title IS NOT NULL AND content IS NOT NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            articles = cursor.fetchall()
            logger.info(f"📋 Found {len(articles)} articles to process")
            
            successful = 0
            failed = 0
            
            for article_id, title in articles:
                try:
                    logger.info(f"🔄 Processing article {article_id}: {title[:40]}...")
                    
                    result = enricher.enrich_single_article(article_id)
                    
                    if result.success:
                        # Marcar como procesado
                        cursor.execute("""
                            UPDATE articles 
                            SET nlp_processed = 1, enhanced_date = ? 
                            WHERE id = ?
                        """, (datetime.now().isoformat(), article_id))
                        
                        successful += 1
                        logger.info(f"✅ Success: {result.fields_updated}")
                    else:
                        failed += 1
                        logger.warning(f"⚠️ Failed: {result.error}")
                    
                    # Pausa para no sobrecargar
                    time.sleep(0.5)
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Error processing {article_id}: {e}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"🏁 Batch complete: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"❌ Error in batch processing: {e}")
    
    def check_image_urls(self):
        """Verificar que las URLs de imágenes sean válidas"""
        logger.info("🖼️ Checking image URLs...")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Contar URLs válidas vs inválidas
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE image_url IS NOT NULL 
            AND image_url != ''
            AND (image_url LIKE 'http%' OR image_url LIKE 'data/%')
        """)
        valid_urls = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE image_url IS NOT NULL 
            AND image_url != ''
        """)
        total_urls = cursor.fetchone()[0]
        
        logger.info(f"📊 Image URLs: {valid_urls}/{total_urls} valid")
        
        # Mostrar ejemplos de URLs problemáticas
        cursor.execute("""
            SELECT id, title, image_url FROM articles 
            WHERE image_url IS NOT NULL 
            AND image_url != ''
            AND image_url NOT LIKE 'http%'
            AND image_url NOT LIKE 'data/%'
            LIMIT 5
        """)
        
        problematic = cursor.fetchall()
        if problematic:
            logger.info("⚠️ Problematic image URLs:")
            for article_id, title, url in problematic:
                logger.info(f"  - ID {article_id}: {url}")
        
        conn.close()
    
    def run_full_fix(self):
        """Ejecutar todas las correcciones"""
        logger.info("🚀 Starting full enrichment system fix...")
        
        # 1. Arreglar esquema de base de datos
        self.add_missing_columns()
        
        # 2. Verificar URLs de imágenes
        self.check_image_urls()
        
        # 3. Probar NLP
        self.test_nlp_processing()
        
        # 4. Procesar lote de prueba
        self.process_batch_nlp(limit=10)
        
        logger.info("✅ Enrichment system fix complete!")

if __name__ == '__main__':
    fixer = EnrichmentFixer()
    fixer.run_full_fix()
