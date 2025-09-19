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
    from src.utils.ai_risk_analyzer import AIRiskAnalyzer
    
    # Importar procesadores opcionales
    try:
        from src.nlp.advanced_nlp_processor import AdvancedNLPProcessor
        nlp_available = True
    except ImportError:
        nlp_available = False
        logger.warning("⚠️ AdvancedNLPProcessor no disponible")
    
    try:
        from src.cv.computer_vision_processor import ComputerVisionProcessor
        cv_available = True
    except ImportError:
        cv_available = False
        logger.warning("⚠️ ComputerVisionProcessor no disponible")
    
    try:
        from src.ai.intelligent_fallback import get_fallback_stats
    except ImportError:
        def get_fallback_stats():
            return {'total_groq_requests': 0, 'groq_rate_limits': 0, 'groq_success_rate': 100}
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
        
        # Inicializar procesadores
        self.risk_analyzer = AIRiskAnalyzer()
        
        # Inicializar procesadores opcionales
        self.nlp_processor = None
        self.cv_processor = None
        
        if nlp_available:
            try:
                self.nlp_processor = AdvancedNLPProcessor()
                logger.info("✅ AdvancedNLPProcessor inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando NLP processor: {e}")
        
        if cv_available:
            try:
                self.cv_processor = ComputerVisionProcessor()
                logger.info("✅ ComputerVisionProcessor inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando CV processor: {e}")
        
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
            'fallback_count': 0,
            'nlp_processed': 0,
            'cv_processed': 0,
            'ai_processed': 0
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
    
    def _verify_table_structure(self):
        """Verificar que las tablas tienen la estructura necesaria"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar tabla articles
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
            if not cursor.fetchone():
                logger.error("❌ Tabla 'articles' no encontrada")
                raise ValueError("Tabla 'articles' no encontrada")
            
            # Verificar columnas necesarias
            cursor.execute("PRAGMA table_info(articles)")
            columns = [col[1] for col in cursor.fetchall()]
            
            required_columns = ['id', 'title', 'content']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                logger.error(f"❌ Columnas faltantes: {missing_columns}")
                raise ValueError(f"Columnas faltantes: {missing_columns}")
            
            logger.info(f"✅ Estructura de base de datos verificada. Columnas: {len(columns)}")
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error verificando estructura de BD: {e}")
            raise e
    
    def get_articles_to_enrich(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtener artículos que necesitan enriquecimiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query para encontrar artículos sin enriquecer o con datos incompletos
            query = """
                SELECT id, title, content, url, published_at,
                       summary, country, region, risk_level, 
                       sentiment_score, conflict_probability
                FROM articles 
                WHERE (summary IS NULL OR summary = '' OR summary = 'N/A')
                   OR (country IS NULL OR country = '' OR country = 'N/A')
                   OR (risk_level IS NULL OR risk_level = '' OR risk_level = 'N/A')
                   OR (conflict_probability IS NULL OR conflict_probability = 0)
                ORDER BY published_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query)
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1] or '',
                    'content': row[2] or '',
                    'url': row[3] or '',
                    'published_at': row[4] or '',
                    'current_summary': row[5],
                    'current_country': row[6],
                    'current_region': row[7],
                    'current_risk_level': row[8],
                    'current_sentiment_score': row[9],
                    'current_conflict_probability': row[10]
                })
            
            conn.close()
            
            logger.info(f"📊 Encontrados {len(articles)} artículos para enriquecer")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo artículos: {e}")
            return []
    
    def get_total_articles_count(self) -> int:
        """Obtener el total de artículos en la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"❌ Error contando artículos: {e}")
            return 0
    
    async def enrich_single_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquecer un solo artículo siguiendo el pipeline completo:
        1. Análisis NLP con BERT (clasificación de riesgo geopolítico)
        2. Análisis Computer Vision (si hay imagen)
        3. Sistema de fallback Groq + Ollama (análisis avanzado)
        """
        article_id = article['id']
        title = article['title']
        content = article['content']
        
        logger.info(f"🔄 Procesando artículo {article_id}: {title[:60]}...")
        
        enrichment_result = {
            'id': article_id,
            'success': False,
            'provider_used': None,
            'model_used': None,
            'processing_time': 0,
            'error': None,
            'data': {},
            'pipeline_results': {
                'nlp': False,
                'cv': False,
                'ai': False
            }
        }
        
        start_time = time.time()
        full_text = f"TÍTULO: {title}\n\nCONTENIDO: {content}"
        
        try:
            # PASO 1: ANÁLISIS NLP CON BERT
            await self._process_nlp_step(article, enrichment_result, full_text)
            
            # PASO 2: ANÁLISIS COMPUTER VISION
            await self._process_cv_step(article, enrichment_result)
            
            # PASO 3: ANÁLISIS CON SISTEMA DE FALLBACK GROQ + OLLAMA
            await self._process_ai_step(article, enrichment_result, full_text)
            
            # Verificar éxito general
            enrichment_result['success'] = any(enrichment_result['pipeline_results'].values())
            enrichment_result['processing_time'] = time.time() - start_time
            
            return enrichment_result
            
        except Exception as e:
            enrichment_result['error'] = str(e)
            enrichment_result['processing_time'] = time.time() - start_time
            logger.error(f"  ❌ Error en pipeline de enriquecimiento para artículo {article_id}: {e}")
            return enrichment_result
    
    async def _process_nlp_step(self, article: Dict[str, Any], result: Dict[str, Any], full_text: str):
        """Paso 1: Análisis NLP con BERT para clasificación de riesgo geopolítico"""
        try:
            logger.info("  🧠 Paso 1: Análisis NLP con BERT...")
            
            if self.nlp_processor:
                # Usar el procesador NLP avanzado
                nlp_result = await self.nlp_processor.process_text(full_text)
                if nlp_result:
                    result['data'].update({
                        'entities_json': json.dumps(nlp_result.get('entities', [])),
                        'sentiment_score': nlp_result.get('sentiment_score', 0.0),
                        'sentiment_label': nlp_result.get('sentiment_label', 'neutral'),
                        'key_persons': ', '.join(nlp_result.get('persons', [])),
                        'key_locations': ', '.join(nlp_result.get('locations', [])),
                    })
                    result['pipeline_results']['nlp'] = True
                    self.stats['nlp_processed'] += 1
                    logger.info("    ✅ Análisis NLP completado")
            else:
                # Usar analizador de riesgo como fallback
                risk_analysis = self.risk_analyzer.analyze_text(full_text)
                if risk_analysis:
                    result['data'].update({
                        'risk_level': risk_analysis.get('risk_level', 'medium'),
                        'conflict_probability': risk_analysis.get('conflict_probability', 0.5),
                        'sentiment_score': risk_analysis.get('sentiment_score', 0.0)
                    })
                    result['pipeline_results']['nlp'] = True
                    self.stats['nlp_processed'] += 1
                    logger.info("    ✅ Análisis de riesgo completado")
                    
        except Exception as e:
            logger.warning(f"    ⚠️ Error en análisis NLP: {e}")
    
    async def _process_cv_step(self, article: Dict[str, Any], result: Dict[str, Any]):
        """Paso 2: Análisis Computer Vision si hay imagen"""
        try:
            # Verificar si el artículo tiene imagen
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT image_url FROM articles WHERE id = ?", (article['id'],))
            image_result = cursor.fetchone()
            conn.close()
            
            image_url = image_result[0] if image_result and image_result[0] else None
            
            if image_url and self.cv_processor:
                logger.info("  👁️ Paso 2: Análisis Computer Vision...")
                cv_result = await self.cv_processor.analyze_image(image_url)
                
                if cv_result:
                    result['data'].update({
                        'visual_risk_score': cv_result.get('risk_score', 0.0),
                        'detected_objects': json.dumps(cv_result.get('objects', [])),
                        'visual_analysis_json': json.dumps(cv_result),
                        'cv_quality_score': cv_result.get('quality_score', 0.0),
                        'has_faces': cv_result.get('has_faces', False)
                    })
                    result['pipeline_results']['cv'] = True
                    self.stats['cv_processed'] += 1
                    logger.info("    ✅ Análisis Computer Vision completado")
            else:
                logger.info("    ℹ️ Sin imagen para análisis CV")
                
        except Exception as e:
            logger.warning(f"    ⚠️ Error en análisis Computer Vision: {e}")
    
    async def _process_ai_step(self, article: Dict[str, Any], result: Dict[str, Any], full_text: str):
        """Paso 3: Análisis con sistema de fallback Groq + Ollama"""
        try:
            logger.info("  🤖 Paso 3: Análisis con fallback Groq + Ollama...")
            
            # 1. Generar resumen
            summary_response = unified_ai_service.generate_summary(
                title=article['title'],
                content=article['content'],
                provider=AIProvider.AUTO
            )
            
            if summary_response.success:
                result['data']['auto_generated_summary'] = summary_response.content
                logger.info(f"    📝 Resumen generado con {summary_response.provider}")
            
            # 2. Análisis geopolítico avanzado
            analysis_response = await unified_ai_service.analyze_geopolitical_content(
                content=full_text,
                prefer_local=True
            )
            
            if analysis_response.success and analysis_response.metadata:
                metadata = analysis_response.metadata
                
                # Actualizar con datos del análisis IA (complementando NLP)
                ai_data = {
                    'summary': analysis_response.content[:500] if not result['data'].get('summary') else result['data']['summary'],
                    'geopolitical_relevance': metadata.get('geopolitical_relevance', 0.5)
                }
                
                # Solo actualizar si no tenemos datos del NLP
                if not result['data'].get('conflict_probability'):
                    ai_data['conflict_probability'] = metadata.get('conflict_probability', 0.5)
                if not result['data'].get('risk_level'):
                    ai_data['risk_level'] = metadata.get('risk_level', 'medium')
                if not result['data'].get('sentiment_score'):
                    ai_data['sentiment_score'] = metadata.get('sentiment_score', 0.0)
                
                # Combinar ubicaciones y personas
                countries = metadata.get('countries', [])
                if countries and not result['data'].get('country'):
                    ai_data['country'] = ', '.join(countries)
                
                result['data'].update(ai_data)
                result['provider_used'] = analysis_response.provider
                result['model_used'] = analysis_response.model
                result['pipeline_results']['ai'] = True
                self.stats['ai_processed'] += 1
                
                logger.info(f"    ✅ Análisis IA completado con {analysis_response.provider}/{analysis_response.model}")
                
                # Actualizar estadísticas de modelos
                provider = analysis_response.provider
                model = analysis_response.model
                self.stats['providers_used'][provider] = self.stats['providers_used'].get(provider, 0) + 1
                self.stats['models_used'][model] = self.stats['models_used'].get(model, 0) + 1
                
                if 'ollama' in provider.lower():
                    self.stats['fallback_count'] += 1
            
        except Exception as e:
            logger.warning(f"    ⚠️ Error en análisis IA: {e}")
    
    def save_enriched_data(self, enrichment_result: Dict[str, Any]) -> bool:
        """Guardar datos enriquecidos en la base de datos"""
        if not enrichment_result['success'] or not enrichment_result['data']:
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar qué columnas existen realmente en la tabla
            cursor.execute("PRAGMA table_info(articles)")
            existing_columns = {col[1] for col in cursor.fetchall()}
            
            # Construir query de actualización dinámicamente solo con columnas existentes
            data = enrichment_result['data']
            set_clauses = []
            values = []
            
            for key, value in data.items():
                if value is not None and key in existing_columns:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if set_clauses:
                # Agregar timestamp de enriquecimiento si la columna existe
                if 'enrichment_date' in existing_columns:
                    set_clauses.append("enrichment_date = ?")
                    values.append(datetime.now().isoformat())
                elif 'analysis_timestamp' in existing_columns:
                    set_clauses.append("analysis_timestamp = ?")
                    values.append(datetime.now().isoformat())
                
                # Agregar metadatos del modelo usado si la columna existe
                if 'enrichment_metadata' in existing_columns:
                    metadata = {
                        'provider': enrichment_result['provider_used'],
                        'model': enrichment_result['model_used'],
                        'processing_time': enrichment_result['processing_time'],
                        'pipeline_results': enrichment_result.get('pipeline_results', {}),
                        'timestamp': datetime.now().isoformat()
                    }
                    set_clauses.append("enrichment_metadata = ?")
                    values.append(json.dumps(metadata))
                
                # Marcar como procesado si la columna existe
                if 'processed' in existing_columns:
                    set_clauses.append("processed = ?")
                    values.append(1)
                
                values.append(enrichment_result['id'])  # Para WHERE clause
                
                query = f"UPDATE articles SET {', '.join(set_clauses)} WHERE id = ?"
                
                cursor.execute(query, values)
                conn.commit()
                
                logger.info(f"  💾 Datos guardados para artículo {enrichment_result['id']} ({len(set_clauses)} campos)")
                
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando datos para artículo {enrichment_result['id']}: {e}")
            return False
    
    def print_progress_stats(self, current: int, total: int):
        """Mostrar estadísticas de progreso"""
        if self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            rate = current / elapsed if elapsed > 0 else 0
            eta = (total - current) / rate if rate > 0 else 0
            
            print(f"\n📊 PROGRESO: {current}/{total} ({current/total*100:.1f}%)")
            print(f"⏱️  Tiempo transcurrido: {elapsed:.1f}s")
            print(f"🚀 Velocidad: {rate:.2f} artículos/segundo")
            print(f"⏰ ETA: {eta:.0f}s restantes")
            print(f"✅ Exitosos: {self.stats['enriched_successfully']}")
            print(f"❌ Errores: {self.stats['errors']}")
            print(f"🔄 Fallbacks a Ollama: {self.stats['fallback_count']}")
            
            # Mostrar modelos más usados
            if self.stats['models_used']:
                most_used = max(self.stats['models_used'], key=self.stats['models_used'].get)
                print(f"🤖 Modelo más usado: {most_used}")
    
    async def process_all_articles(self, limit: Optional[int] = None):
        """Procesar todos los artículos de la base de datos"""
        logger.info("🚀 Iniciando enriquecimiento masivo...")
        
        # Verificar estado de servicios
        try:
            service_status = unified_ai_service.get_service_status()
            logger.info("🏥 Estado de servicios:")
            logger.info(f"  - Ollama: {'✅' if service_status['ollama']['available'] else '❌'}")
            logger.info(f"  - Groq: {'✅' if service_status['groq']['available'] else '❌'}")
            
            if not any([service_status['ollama']['available'], service_status['groq']['available']]):
                logger.error("❌ Ningún servicio de IA disponible")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Error verificando servicios: {e}")
        
        # Obtener artículos a procesar
        articles = self.get_articles_to_enrich(limit)
        if not articles:
            logger.info("✅ No hay artículos para enriquecer")
            return True
        
        self.stats['total_articles'] = len(articles)
        self.stats['start_time'] = time.time()
        
        logger.info(f"📰 Procesando {len(articles)} artículos en lotes de {self.batch_size}")
        
        # Procesar en lotes
        for i in range(0, len(articles), self.batch_size):
            batch = articles[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(articles) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"\n🔄 Procesando lote {batch_num}/{total_batches} ({len(batch)} artículos)")
            
            # Procesar artículos del lote
            for article in batch:
                try:
                    # Enriquecer artículo
                    result = await self.enrich_single_article(article)
                    
                    # Guardar resultados
                    if result['success']:
                        if self.save_enriched_data(result):
                            self.stats['enriched_successfully'] += 1
                        else:
                            self.stats['errors'] += 1
                    else:
                        self.stats['errors'] += 1
                    
                    self.stats['processed'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error crítico procesando artículo {article['id']}: {e}")
                    self.stats['errors'] += 1
                    self.stats['processed'] += 1
            
            # Mostrar progreso
            self.print_progress_stats(self.stats['processed'], self.stats['total_articles'])
            
            # Pausa entre lotes para evitar sobrecarga
            if i + self.batch_size < len(articles):
                logger.info(f"⏸️  Pausa de {self.delay_between_batches}s entre lotes...")
                await asyncio.sleep(self.delay_between_batches)
        
        self.stats['end_time'] = time.time()
        self._print_final_summary()
        return True
    
    def _print_final_summary(self):
        """Mostrar resumen final del procesamiento"""
        total_time = self.stats['end_time'] - self.stats['start_time']
        success_rate = (self.stats['enriched_successfully'] / self.stats['total_articles']) * 100 if self.stats['total_articles'] > 0 else 0
        
        print(f"\n{'='*60}")
        print("🎉 ENRIQUECIMIENTO MASIVO COMPLETADO")
        print(f"{'='*60}")
        print("📊 Estadísticas finales:")
        print(f"  • Total de artículos: {self.stats['total_articles']}")
        print(f"  • Procesados exitosamente: {self.stats['enriched_successfully']}")
        print(f"  • Errores: {self.stats['errors']}")
        print(f"  • Tasa de éxito: {success_rate:.1f}%")
        print(f"  • Tiempo total: {total_time:.1f}s")
        print(f"  • Velocidad promedio: {self.stats['total_articles']/total_time:.2f} artículos/segundo")
        
        print("\n🔧 Pipeline de procesamiento:")
        print(f"  • NLP/BERT procesados: {self.stats['nlp_processed']}")
        print(f"  • Computer Vision procesados: {self.stats['cv_processed']}")  
        print(f"  • IA avanzada procesados: {self.stats['ai_processed']}")
        print(f"  • Fallbacks a Ollama: {self.stats['fallback_count']}")
        
        print("\n🤖 Modelos utilizados:")
        for model, count in self.stats['models_used'].items():
            percentage = (count / self.stats['total_articles']) * 100
            print(f"  • {model}: {count} ({percentage:.1f}%)")
        
        print("\n☁️ Proveedores utilizados:")
        for provider, count in self.stats['providers_used'].items():
            percentage = (count / self.stats['total_articles']) * 100
            print(f"  • {provider}: {count} ({percentage:.1f}%)")
        
        # Obtener estadísticas de fallback
        try:
            fallback_stats = get_fallback_stats()
            print("\n🔄 Estadísticas de fallback:")
            print(f"  • Total requests Groq: {fallback_stats['total_groq_requests']}")
            print(f"  • Rate limits: {fallback_stats['groq_rate_limits']}")
            print(f"  • Tasa éxito Groq: {fallback_stats['groq_success_rate']}%")
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas de fallback: {e}")

def main():
    """Función principal"""
    print("🚀 ENRIQUECIMIENTO MASIVO DE BASE DE DATOS")
    print("Usando sistema de fallback inteligente Ollama + Groq")
    print("=" * 60)
    
    try:
        # Crear procesador
        processor = MassiveEnrichmentProcessor()
        
        # Mostrar información de la base de datos
        total_articles = processor.get_total_articles_count()
        print(f"📊 Total de artículos en BD: {total_articles}")
        
        # Preguntar confirmación
        response = input("\n¿Proceder con el enriquecimiento masivo? (y/N): ")
        if response.lower() not in ['y', 'yes', 's', 'si']:
            print("❌ Operación cancelada")
            return
        
        # Preguntar límite opcional
        limit_response = input("¿Límite de artículos? (Enter para todos): ")
        limit = None
        if limit_response.strip():
            try:
                limit = int(limit_response)
                print(f"📝 Procesando máximo {limit} artículos")
            except ValueError:
                print("⚠️ Límite inválido, procesando todos los artículos")
        
        # Ejecutar procesamiento
        print("\n🔄 Iniciando procesamiento...")
        success = asyncio.run(processor.process_all_articles(limit))
        
        if success:
            print("\n✅ Enriquecimiento masivo completado exitosamente")
        else:
            print("\n❌ Enriquecimiento masivo completado con errores")
            
    except KeyboardInterrupt:
        print("\n⏹️ Procesamiento interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
