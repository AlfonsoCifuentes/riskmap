#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enriquecimiento Masivo de Base de Datos
Procesa todos los artículos usando el sistema de fallback inteligente
Ollama + Groq con selección automática de modelos especializados
"""

import os
import sys
import sqlite3
import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('massive_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar servicios
from src.ai.unified_ai_service import unified_ai_service, AIProvider
from src.ai.ollama_service import ollama_service, OllamaModel
from src.enrichment.intelligent_data_enrichment import IntelligentDataEnrichment

class MassiveEnrichmentOrchestrator:
    """
    Orquestador para enriquecimiento masivo con fallback inteligente
    """
    
    def __init__(self, db_path: str = "geopolitical_data.db"):
        self.db_path = db_path
        self.enrichment_service = IntelligentDataEnrichment()
        self.stats = {
            'total_articles': 0,
            'processed': 0,
            'enriched': 0,
            'skipped': 0,
            'errors': 0,
            'groq_used': 0,
            'ollama_used': 0,
            'deepseek_used': 0,
            'gemma_used': 0,
            'qwen_used': 0,
            'llama_used': 0,
            'start_time': None,
            'estimated_completion': None
        }
        self.lock = threading.Lock()
        
    def get_articles_to_enrich(self, force_re_enrich: bool = False) -> List[Dict[str, Any]]:
        """
        Obtener artículos que necesitan enriquecimiento
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if force_re_enrich:
                # Procesar todos los artículos
                query = """
                    SELECT id, title, content, url, published_date, 
                           country, region, conflict_type, summary,
                           groq_enhanced, enhanced_date
                    FROM articles 
                    WHERE content IS NOT NULL 
                    AND length(trim(content)) > 50
                    ORDER BY published_date DESC
                """
            else:
                # Solo artículos no enriquecidos o con enriquecimiento incompleto
                query = """
                    SELECT id, title, content, url, published_date,
                           country, region, conflict_type, summary,
                           groq_enhanced, enhanced_date
                    FROM articles 
                    WHERE content IS NOT NULL 
                    AND length(trim(content)) > 50
                    AND (
                        groq_enhanced = 0 
                        OR groq_enhanced IS NULL
                        OR country IS NULL 
                        OR region IS NULL
                        OR summary IS NULL
                        OR length(trim(summary)) < 20
                    )
                    ORDER BY published_date DESC
                """
            
            cursor.execute(query)
            articles = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            logger.info(f"📊 Encontrados {len(articles)} artículos para enriquecer")
            return articles
            
        except Exception as e:
            logger.error(f"Error obteniendo artículos: {e}")
            return []
    
    def update_article_enrichment(self, article_id: int, enrichment_data: Dict[str, Any], provider_used: str):
        """
        Actualizar artículo con datos de enriquecimiento
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Preparar datos para actualización
            update_fields = []
            update_values = []
            
            field_mapping = {
                'country': enrichment_data.get('country'),
                'region': enrichment_data.get('region'),
                'conflict_type': enrichment_data.get('conflict_type'),
                'summary': enrichment_data.get('summary'),
                'key_persons': json.dumps(enrichment_data.get('key_persons', [])),
                'key_locations': json.dumps(enrichment_data.get('key_locations', [])),
                'geopolitical_relevance': enrichment_data.get('geopolitical_relevance'),
                'risk_assessment': enrichment_data.get('risk_assessment'),
                'groq_enhanced': 1,
                'enhanced_date': datetime.now().isoformat(),
                'ai_provider_used': provider_used
            }
            
            # Solo actualizar campos que tienen valor
            for field, value in field_mapping.items():
                if value is not None and str(value).strip():
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            if update_fields:
                update_values.append(article_id)
                
                query = f"""
                    UPDATE articles 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """
                
                cursor.execute(query, update_values)
                conn.commit()
                
                logger.debug(f"✅ Artículo {article_id} actualizado con {len(update_fields)} campos")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando artículo {article_id}: {e}")
            return False
    
    async def enrich_single_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquecer un artículo individual usando el sistema unificado
        """
        article_id = article['id']
        title = article.get('title', '')
        content = article.get('content', '')
        
        try:
            # Usar el servicio unificado con preferencia por Ollama
            response = await unified_ai_service.analyze_geopolitical_content(
                content=f"TÍTULO: {title}\nCONTENIDO: {content}",
                prefer_local=True  # Priorizar Ollama para evitar rate limits
            )
            
            if response.success:
                # Extraer datos de enriquecimiento
                if response.metadata:
                    enrichment_data = response.metadata
                else:
                    # Si no hay metadata, procesar el contenido de respuesta
                    try:
                        enrichment_data = json.loads(response.content)
                    except:
                        # Crear estructura básica
                        enrichment_data = {
                            'summary': response.content[:300] if response.content else f"Análisis de: {title}",
                            'country': '',
                            'region': '',
                            'conflict_type': 'diplomatic',
                            'geopolitical_relevance': 0.5,
                            'risk_assessment': 'medium',
                            'key_persons': [],
                            'key_locations': []
                        }
                
                # Actualizar base de datos
                success = self.update_article_enrichment(
                    article_id, 
                    enrichment_data, 
                    response.provider
                )
                
                if success:
                    with self.lock:
                        self.stats['enriched'] += 1
                        if 'ollama' in response.provider.lower():
                            self.stats['ollama_used'] += 1
                            if 'deepseek' in response.model.lower():
                                self.stats['deepseek_used'] += 1
                            elif 'gemma' in response.model.lower():
                                self.stats['gemma_used'] += 1
                            elif 'qwen' in response.model.lower():
                                self.stats['qwen_used'] += 1
                            elif 'llama' in response.model.lower():
                                self.stats['llama_used'] += 1
                        else:
                            self.stats['groq_used'] += 1
                
                return {
                    'success': True,
                    'article_id': article_id,
                    'provider': response.provider,
                    'model': response.model,
                    'fields_updated': len([k for k, v in enrichment_data.items() if v])
                }
            else:
                logger.warning(f"❌ Error enriqueciendo artículo {article_id}: {response.error}")
                with self.lock:
                    self.stats['errors'] += 1
                return {
                    'success': False,
                    'article_id': article_id,
                    'error': response.error
                }
                
        except Exception as e:
            logger.error(f"❌ Excepción enriqueciendo artículo {article_id}: {e}")
            with self.lock:
                self.stats['errors'] += 1
            return {
                'success': False,
                'article_id': article_id,
                'error': str(e)
            }
    
    def sync_enrich_article_wrapper(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper síncrono para enriquecimiento (para uso con ThreadPoolExecutor)
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.enrich_single_article(article))
        finally:
            loop.close()
    
    def update_progress(self, processed: int, total: int):
        """
        Actualizar progreso y estimación de tiempo
        """
        with self.lock:
            self.stats['processed'] = processed
            
            if self.stats['start_time']:
                elapsed = time.time() - self.stats['start_time']
                rate = processed / elapsed if elapsed > 0 else 0
                
                if rate > 0:
                    remaining = total - processed
                    eta_seconds = remaining / rate
                    eta = datetime.now() + timedelta(seconds=eta_seconds)
                    self.stats['estimated_completion'] = eta.strftime('%H:%M:%S')
                
                # Log progreso cada 10 artículos
                if processed % 10 == 0:
                    logger.info(f"📈 Progreso: {processed}/{total} ({processed/total*100:.1f}%) - "
                              f"Enriquecidos: {self.stats['enriched']} - "
                              f"Rate: {rate:.2f} art/s - "
                              f"ETA: {self.stats.get('estimated_completion', 'N/A')}")
    
    def print_final_stats(self):
        """
        Imprimir estadísticas finales
        """
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMEN FINAL DEL ENRIQUECIMIENTO MASIVO")
        print(f"{'='*60}")
        print(f"⏱️  Tiempo total: {elapsed/60:.1f} minutos")
        print(f"📰 Total artículos: {self.stats['total_articles']}")
        print(f"✅ Procesados: {self.stats['processed']}")
        print(f"🎯 Enriquecidos exitosamente: {self.stats['enriched']}")
        print(f"⏭️  Saltados: {self.stats['skipped']}")
        print(f"❌ Errores: {self.stats['errors']}")
        print(f"📊 Tasa de éxito: {self.stats['enriched']/max(self.stats['processed'], 1)*100:.1f}%")
        
        print(f"\n🤖 USO DE PROVEEDORES DE IA:")
        print(f"  └─ Ollama (local): {self.stats['ollama_used']}")
        print(f"  └─ Groq (remoto): {self.stats['groq_used']}")
        
        print(f"\n🎯 MODELOS ESPECIALIZADOS USADOS:")
        print(f"  └─ DeepSeek (análisis profundo): {self.stats['deepseek_used']}")
        print(f"  └─ Gemma (resúmenes rápidos): {self.stats['gemma_used']}")
        print(f"  └─ Qwen (multiidioma): {self.stats['qwen_used']}")
        print(f"  └─ Llama (propósito general): {self.stats['llama_used']}")
        
        total_local = sum([
            self.stats['deepseek_used'],
            self.stats['gemma_used'], 
            self.stats['qwen_used'],
            self.stats['llama_used']
        ])
        
        if total_local > 0:
            print(f"\n💡 BENEFICIOS DEL SISTEMA LOCAL:")
            print(f"  └─ {total_local} artículos procesados sin rate limits")
            print(f"  └─ Procesamiento privado y seguro")
            print(f"  └─ Sin costos adicionales de API")
            print(f"  └─ Modelos especializados por tarea")
        
        print(f"\n✅ Enriquecimiento masivo completado")
    
    def run_massive_enrichment(
        self, 
        max_workers: int = 5,
        force_re_enrich: bool = False,
        batch_size: int = 100
    ):
        """
        Ejecutar enriquecimiento masivo con procesamiento paralelo
        """
        logger.info("🚀 Iniciando enriquecimiento masivo de la base de datos...")
        
        # Verificar servicios disponibles
        status = unified_ai_service.get_service_status()
        logger.info(f"🤖 Ollama disponible: {status['ollama']['available']}")
        logger.info(f"☁️ Groq disponible: {status['groq']['available']}")
        
        if not status['ollama']['available'] and not status['groq']['available']:
            logger.error("❌ Ningún servicio de IA disponible")
            return
        
        # Obtener artículos a procesar
        articles = self.get_articles_to_enrich(force_re_enrich)
        
        if not articles:
            logger.info("✅ No hay artículos que requieran enriquecimiento")
            return
        
        self.stats['total_articles'] = len(articles)
        self.stats['start_time'] = time.time()
        
        logger.info(f"📝 Procesando {len(articles)} artículos con {max_workers} workers...")
        
        # Procesar en lotes para evitar sobrecarga
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(articles) + batch_size - 1) // batch_size
            
            logger.info(f"📦 Procesando lote {batch_num}/{total_batches} ({len(batch)} artículos)")
            
            # Procesar lote con ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.sync_enrich_article_wrapper, article): article 
                    for article in batch
                }
                
                for future in as_completed(futures):
                    article = futures[future]
                    result = future.result()
                    
                    self.update_progress(self.stats['processed'] + 1, len(articles))
                    
                    if result['success']:
                        logger.debug(f"✅ [{result['article_id']}] Enriquecido con {result['provider']} "
                                   f"({result['model']}) - {result['fields_updated']} campos")
                    else:
                        logger.warning(f"❌ [{result['article_id']}] Error: {result.get('error', 'Unknown')}")
            
            # Pausa pequeña entre lotes para no sobrecargar
            if i + batch_size < len(articles):
                time.sleep(1)
        
        self.print_final_stats()

def main():
    """
    Función principal
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Enriquecimiento masivo de base de datos')
    parser.add_argument('--db', default='geopolitical_data.db', help='Ruta a la base de datos')
    parser.add_argument('--workers', type=int, default=5, help='Número de workers paralelos')
    parser.add_argument('--force', action='store_true', help='Forzar re-enriquecimiento de todos los artículos')
    parser.add_argument('--batch-size', type=int, default=100, help='Tamaño de lote para procesamiento')
    
    args = parser.parse_args()
    
    # Verificar que la base de datos existe
    if not os.path.exists(args.db):
        logger.error(f"❌ Base de datos no encontrada: {args.db}")
        return
    
    orchestrator = MassiveEnrichmentOrchestrator(args.db)
    
    try:
        orchestrator.run_massive_enrichment(
            max_workers=args.workers,
            force_re_enrich=args.force,
            batch_size=args.batch_size
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Enriquecimiento detenido por el usuario")
        orchestrator.print_final_stats()
    except Exception as e:
        logger.error(f"❌ Error en enriquecimiento masivo: {e}")

if __name__ == "__main__":
    main()
