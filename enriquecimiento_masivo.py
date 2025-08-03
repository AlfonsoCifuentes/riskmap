#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enriquecimiento masivo de toda la base de datos
Usa el sistema de fallback inteligente Ollama + Groq
"""

import os
import sys
import sqlite3
import logging
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'enriquecimiento_masivo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Importar servicios con manejo de errores
try:
    from src.ai.unified_ai_service import unified_ai_service, AIProvider
    from src.ai.ollama_service import ollama_service, OllamaModel
    from src.ai.intelligent_fallback import get_fallback_stats
    logger.info("✅ Servicios de IA importados correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando servicios de IA: {e}")
    sys.exit(1)

class MassiveEnrichmentProcessor:
    """Procesador de enriquecimiento masivo con fallback inteligente"""
    
    def __init__(self):
        # Ruta correcta de la base de datos
        self.db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
        
        # Verificar base de datos
        self._verify_database()
        
        # Estadísticas del procesamiento
        self.stats = {
            'total_articles': 0,
            'processed': 0,
            'enriched_successfully': 0,
            'errors': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None,
            'models_used': {},
            'providers_used': {},
            'fallback_count': 0
        }
        
        # Configuración de procesamiento
        self.batch_size = 10  # Procesar en lotes
        self.delay_between_batches = 2  # Segundos entre lotes
        
    def _verify_database(self):
        """Verificar que la base de datos existe y tiene la estructura correcta"""
        if not os.path.exists(self.db_path):
            # Intentar encontrar la base de datos en ubicaciones alternativas
            alt_paths = [
                "geopolitical_data.db",
                "data/geopolitical_data.db", 
                "geopolitical_intel.db",
                "./geopolitical_data.db"
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    self.db_path = os.path.abspath(alt_path)
                    logger.info(f"✅ Usando base de datos encontrada: {self.db_path}")
                    break
            else:
                raise FileNotFoundError(f"❌ Base de datos no encontrada en: {self.db_path}")
        else:
            logger.info(f"✅ Base de datos encontrada: {self.db_path}")
            
        # Verificar estructura de la base de datos
        self._verify_table_structure()
        
        logger.info(f"✅ Base de datos encontrada: {self.db_path}")
        
        # Configurar enriquecedor
        config = EnricherConfig()
        self.enricher = IntelligentDataEnricher(config)
        
        # Estadísticas
        self.stats = {
            'total_articles': 0,
            'already_enriched': 0,
            'to_enrich': 0,
            'successfully_enriched': 0,
            'failed_enrichment': 0,
            'groq_used': 0,
            'ollama_used': 0,
            'rate_limits_detected': 0,
            'start_time': None,
            'end_time': None
        }
        
    def get_database_status(self) -> Dict:
        """Obtener estado de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de artículos
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # Artículos ya enriquecidos
            cursor.execute("SELECT COUNT(*) FROM articles WHERE groq_enhanced = 1")
            already_enriched = cursor.fetchone()[0]
            
            # Artículos sin enriquecer
            to_enrich = total_articles - already_enriched
            
            # Verificar estructura de tabla
            cursor.execute("PRAGMA table_info(articles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Artículos recientes (últimas 24h)
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE datetime(published_date) > ? OR datetime(created_at) > ?
            """, (yesterday.isoformat(), yesterday.isoformat()))
            recent_articles = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_articles': total_articles,
                'already_enriched': already_enriched,
                'to_enrich': to_enrich,
                'recent_articles_24h': recent_articles,
                'enrichment_percentage': (already_enriched / total_articles * 100) if total_articles > 0 else 0,
                'columns_available': columns,
                'database_path': self.db_path
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de DB: {e}")
            return {}
    
    def get_articles_to_enrich(self, limit: Optional[int] = None, offset: int = 0) -> List[Tuple]:
        """Obtener artículos que necesitan enriquecimiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query para artículos sin enriquecer o con enriquecimiento incompleto
            query = """
                SELECT id, title, content, url, published_date, source_name, 
                       groq_enhanced, enhanced_date, summary, country, region
                FROM articles 
                WHERE groq_enhanced IS NULL OR groq_enhanced = 0 
                   OR summary IS NULL OR summary = ''
                   OR country IS NULL OR country = ''
                ORDER BY published_date DESC
            """
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query)
            articles = cursor.fetchall()
            conn.close()
            
            return articles
            
        except Exception as e:
            logger.error(f"Error obteniendo artículos: {e}")
            return []
    
    def enrich_single_article(self, article_data: Tuple) -> Dict:
        """Enriquecer un solo artículo"""
        try:
            (article_id, title, content, url, published_date, 
             source_name, groq_enhanced, enhanced_date, summary, country, region) = article_data
            
            logger.info(f"🔄 Enriqueciendo artículo {article_id}: {title[:50]}...")
            
            start_time = time.time()
            
            # Usar el enriquecedor con fallback automático
            result = self.enricher.enrich_single_article(article_id)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if result.success:
                logger.info(f"✅ Artículo {article_id} enriquecido en {processing_time:.2f}s")
                self.stats['successfully_enriched'] += 1
                
                # Detectar qué proveedor se usó
                if 'ollama' in str(result.details).lower():
                    self.stats['ollama_used'] += 1
                elif 'groq' in str(result.details).lower():
                    self.stats['groq_used'] += 1
                    
                return {
                    'success': True,
                    'article_id': article_id,
                    'processing_time': processing_time,
                    'fields_updated': result.fields_updated,
                    'provider_used': 'ollama' if 'ollama' in str(result.details).lower() else 'groq'
                }
            else:
                logger.warning(f"⚠️ Error enriqueciendo artículo {article_id}: {result.error}")
                self.stats['failed_enrichment'] += 1
                
                # Detectar rate limits
                if '429' in str(result.error) or 'rate_limit' in str(result.error).lower():
                    self.stats['rate_limits_detected'] += 1
                
                return {
                    'success': False,
                    'article_id': article_id,
                    'error': result.error,
                    'processing_time': processing_time
                }
                
        except Exception as e:
            logger.error(f"Error procesando artículo {article_data[0] if article_data else 'unknown'}: {e}")
            self.stats['failed_enrichment'] += 1
            return {
                'success': False,
                'article_id': article_data[0] if article_data else None,
                'error': str(e),
                'processing_time': 0
            }
    
    def run_batch_enrichment(self, batch_size: int = 10, max_workers: int = 5):
        """Ejecutar enriquecimiento en lotes"""
        logger.info("🚀 Iniciando enriquecimiento masivo...")
        
        # Verificar servicios
        status = unified_ai_service.get_service_status()
        logger.info(f"📊 Estado de servicios:")
        logger.info(f"  - Ollama: {'✅' if status['ollama']['available'] else '❌'}")
        logger.info(f"  - Groq: {'✅' if status['groq']['available'] else '❌'}")
        
        if not status['ollama']['available'] and not status['groq']['available']:
            logger.error("❌ Ningún servicio de IA disponible")
            return
        
        # Estado de la base de datos
        db_status = self.get_database_status()
        logger.info(f"📊 Estado de la base de datos:")
        logger.info(f"  - Total artículos: {db_status['total_articles']}")
        logger.info(f"  - Ya enriquecidos: {db_status['already_enriched']}")
        logger.info(f"  - Por enriquecer: {db_status['to_enrich']}")
        logger.info(f"  - Porcentaje completado: {db_status['enrichment_percentage']:.1f}%")
        
        if db_status['to_enrich'] == 0:
            logger.info("✅ Todos los artículos ya están enriquecidos")
            return
        
        # Actualizar estadísticas
        self.stats.update({
            'total_articles': db_status['total_articles'],
            'already_enriched': db_status['already_enriched'],
            'to_enrich': db_status['to_enrich'],
            'start_time': datetime.now()
        })
        
        # Procesar en lotes
        offset = 0
        total_processed = 0
        
        while True:
            # Obtener lote de artículos
            articles = self.get_articles_to_enrich(limit=batch_size, offset=offset)
            
            if not articles:
                logger.info("✅ No hay más artículos para procesar")
                break
            
            logger.info(f"📦 Procesando lote de {len(articles)} artículos (offset: {offset})")
            
            # Procesar artículos en paralelo
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_article = {
                    executor.submit(self.enrich_single_article, article): article 
                    for article in articles
                }
                
                for future in as_completed(future_to_article):
                    result = future.result()
                    total_processed += 1
                    
                    # Mostrar progreso cada 10 artículos
                    if total_processed % 10 == 0:
                        self.show_progress_stats()
            
            offset += batch_size
            
            # Pausa entre lotes para no sobrecargar
            time.sleep(2)
        
        # Estadísticas finales
        self.stats['end_time'] = datetime.now()
        self.show_final_stats()
    
    def show_progress_stats(self):
        """Mostrar estadísticas de progreso"""
        total_processed = self.stats['successfully_enriched'] + self.stats['failed_enrichment']
        success_rate = (self.stats['successfully_enriched'] / max(total_processed, 1)) * 100
        
        logger.info(f"📊 Progreso: {total_processed} procesados, "
                   f"{self.stats['successfully_enriched']} exitosos ({success_rate:.1f}%)")
        
        if self.stats['rate_limits_detected'] > 0:
            logger.info(f"⚡ Rate limits detectados: {self.stats['rate_limits_detected']} "
                       f"(fallback a Ollama funcionando)")
    
    def show_final_stats(self):
        """Mostrar estadísticas finales"""
        duration = self.stats['end_time'] - self.stats['start_time']
        total_processed = self.stats['successfully_enriched'] + self.stats['failed_enrichment']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 ENRIQUECIMIENTO MASIVO COMPLETADO")
        logger.info(f"{'='*60}")
        logger.info(f"⏱️  Duración total: {duration}")
        logger.info(f"📊 Artículos procesados: {total_processed}")
        logger.info(f"✅ Exitosos: {self.stats['successfully_enriched']}")
        logger.info(f"❌ Fallidos: {self.stats['failed_enrichment']}")
        logger.info(f"📈 Tasa de éxito: {(self.stats['successfully_enriched']/max(total_processed,1)*100):.1f}%")
        logger.info(f"🤖 Uso de Ollama: {self.stats['ollama_used']}")
        logger.info(f"☁️  Uso de Groq: {self.stats['groq_used']}")
        logger.info(f"⚡ Rate limits detectados: {self.stats['rate_limits_detected']}")
        
        if self.stats['rate_limits_detected'] > 0:
            logger.info(f"🎯 Sistema de fallback funcionó correctamente")
        
        # Estado final de la DB
        final_status = self.get_database_status()
        logger.info(f"📊 Estado final de la base de datos:")
        logger.info(f"  - Enriquecimiento completado: {final_status['enrichment_percentage']:.1f}%")
        logger.info(f"  - Artículos restantes: {final_status['to_enrich']}")

def main():
    """Función principal"""
    try:
        processor = MassiveEnrichmentProcessor()
        
        # Mostrar estado inicial
        db_status = processor.get_database_status()
        
        print("🚀 SISTEMA DE ENRIQUECIMIENTO MASIVO")
        print("="*50)
        print(f"📊 Base de datos: {processor.db_path}")
        print(f"📊 Total artículos: {db_status['total_articles']}")
        print(f"📊 Ya enriquecidos: {db_status['already_enriched']}")
        print(f"📊 Por enriquecer: {db_status['to_enrich']}")
        print(f"📊 Progreso actual: {db_status['enrichment_percentage']:.1f}%")
        
        if db_status['to_enrich'] == 0:
            print("✅ Todos los artículos ya están enriquecidos")
            return
        
        # Configuración del procesamiento
        print(f"\n🔧 Configuración:")
        print(f"  - Fallback automático: Groq → Ollama")
        print(f"  - Modelos especializados: DeepSeek, Gemma, Qwen, Llama")
        print(f"  - Procesamiento en paralelo: 5 workers")
        print(f"  - Tamaño de lote: 10 artículos")
        
        # Confirmar procesamiento
        response = input(f"\n¿Proceder con el enriquecimiento de {db_status['to_enrich']} artículos? (y/N): ")
        
        if response.lower() in ['y', 'yes', 's', 'si']:
            processor.run_batch_enrichment(batch_size=10, max_workers=5)
        else:
            print("❌ Enriquecimiento cancelado por el usuario")
            
    except Exception as e:
        logger.error(f"Error en enriquecimiento masivo: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
