"""
Módulo de orquestación principal para el Sistema de Inteligencia Geopolítica.
Contiene la clase GeopoliticalIntelligenceOrchestrator que coordina todas las operaciones.
"""

import logging
import json
logger = logging.getLogger(__name__)

from src.data_quality.validator import data_validator
from src.monitoring.system_monitor import system_monitor
from src.reporting.report_generator import AdvancedReportGenerator as ReportGenerator
from src.nlp_processing import bulk_process_articles, GeopoliticalTextAnalyzer

# Import advanced NLP components
try:
    from nlp_processing.advanced_analyzer import AdvancedNLPAnalyzer
    from utils.bert_risk_analyzer import BERTRiskAnalyzer
    ADVANCED_NLP_AVAILABLE = True
    logger.info("Advanced NLP components available")
except ImportError as e:
    logger.warning(f"Advanced NLP components not available: {e}")
    ADVANCED_NLP_AVAILABLE = False
from src.data_ingestion.intelligence_sources import IntelligenceSourcesRegistry, IntelligenceCollector
from src.data_ingestion.global_news_collector import GlobalNewsSourcesRegistry, EnhancedNewsAPICollector, GlobalRSSCollector
from src.data_ingestion.news_collector import GeopoliticalNewsCollector
from src.utils.config import config, logger, DatabaseManager
import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

# Add project root to path for consistent module resolution
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class GeopoliticalIntelligenceOrchestrator:
    """Sistema principal de orquestación para inteligencia geopolítica con datos reales."""

    def __init__(self):
        logger.info(
            "[GLOBAL] Inicializando Sistema de Inteligencia Geopolítica...")

        self.is_running = False
        self.last_update = None
        self.stats = {
            'total_articles': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'last_execution_time': None,
            'uptime_start': datetime.now()
        }

        self.max_workers = config.get('processing.max_workers', 4)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        self._validate_real_apis()

        try:
            self.collector = GeopoliticalNewsCollector()
            self.global_sources_registry = GlobalNewsSourcesRegistry()
            self.enhanced_newsapi = EnhancedNewsAPICollector()
            self.global_rss_collector = GlobalRSSCollector()
            self.intelligence_registry = IntelligenceSourcesRegistry()
            self.intelligence_collector = IntelligenceCollector()
            self.analyzer = GeopoliticalTextAnalyzer()
            self.reporter = ReportGenerator()
            logger.info("[OK] Sistema inicializado correctamente")
        except Exception as e:
            logger.error(f"[ERROR] Error inicializando componentes: {e}")
            raise

    def _validate_real_apis(self):
        """Valida que todas las APIs configuradas sean reales y funcionales."""
        logger.info("[KEY] Validando configuración de APIs...")
        # Init status for all integrated APIs
        self.api_status = {
            'newsapi': False,
            'google_translate': False,
            'openai': False,
            'deepseek': False,
            'groq': False,
            'huggingface': False
        }

        try:
            # NewsAPI
            newsapi_key = config.get_newsapi_key()
            if newsapi_key and newsapi_key != "your_newsapi_key_here":
                import requests
                response = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={'q': 'test', 'apiKey': newsapi_key, 'pageSize': 1},
                    timeout=5
                )
                if response.status_code == 200:
                    self.api_status['newsapi'] = True
                    logger.info("[OK] NewsAPI: Configurada y funcional")
                else:
                    logger.warning(
                        "[WARN] NewsAPI: Configurada pero con errores")
            else:
                logger.warning("[WARN] NewsAPI: No configurada")
        except Exception as e:
            logger.warning(f"[WARN] NewsAPI: Error de validación - {e}")

        # Google Translate
        google_key = config.get_google_translate_key()
        if google_key:
            self.api_status['google_translate'] = True
            logger.info("[OK] Google Translate API: Configurada")
        else:
            logger.info("[INFO] Google Translate API: No configurada (opcional)")

        # OpenAI
        openai_key = config.get_openai_key()
        if openai_key:
            self.api_status['openai'] = True
            logger.info("[OK] OpenAI API: Configurada")
        else:
            logger.info("[INFO] OpenAI API: No configurada (opcional para chatbot)")
        
        # DeepSeek
        deepseek_key = config.get_deepseek_key()
        if deepseek_key:
            self.api_status['deepseek'] = True
            logger.info("[OK] DeepSeek API: Configurada")
        else:
            logger.info("[INFO] DeepSeek API: No configurada (opcional)")
        
        # Groq
        groq_key = config.get_groq_key()
        if groq_key:
            self.api_status['groq'] = True
            logger.info("[OK] Groq API: Configurada")
        else:
            logger.info("[INFO] Groq API: No configurada (opcional)")
        
        # HuggingFace
        hf_token = config.get_hf_token()
        if hf_token:
            self.api_status['huggingface'] = True
            logger.info("[OK] HuggingFace API: Configurada")
        else:
            logger.info("[INFO] HuggingFace API: No configurada (opcional)")

        if not self.api_status['newsapi']:
            logger.warning(
                "[WARN] ADVERTENCIA: NewsAPI no configurada - funcionalidad limitada")

        logger.info("[SEARCH] Validación de APIs completada")

    def run_full_pipeline(
            self,
            validate_data=True,
            use_global_collection=True,
            max_articles=1000):
        """Ejecuta el pipeline completo de inteligencia con manejo robusto de errores."""
        start_time = datetime.now()
        self.is_running = True

        try:
            logger.info(
                "[START] Iniciando pipeline completo de inteligencia geopolítica")

            articles_collected = self._collect_data(
                use_global_collection, max_articles)
            if articles_collected == 0:
                logger.warning(
                    "[WARN] No se recolectaron artículos. Finalizando pipeline.")
                return False

            if validate_data:
                self._validate_data()

            processed_count = self._process_data(articles_collected)
            reports_generated = self._generate_reports()
            self._update_system_metrics(articles_collected, processed_count)

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"[SUCCESS] Pipeline completado en {execution_time:.2f} segundos")
            logger.info(
                f"[STATS] Resumen: {articles_collected} recolectados, {processed_count} procesados, {reports_generated} informes")

            self.stats['last_execution_time'] = execution_time
            return True

        except Exception as e:
            logger.error(f"[ERROR] Error crítico en pipeline: {e}")
            logger.error(f"[SEARCH] Traceback: {traceback.format_exc()}")
            return False
        finally:
            self.is_running = False
            self.last_update = datetime.now()

    def _collect_data(self, use_global_collection, max_articles):
        logger.info("[NEWS] Paso 1: Recolectando datos de noticias...")
        articles_collected = 0
        if use_global_collection and self.api_status.get('newsapi', False):
            try:
                articles_collected = self._run_enhanced_collection(
                    max_articles)
                logger.info(
                    f"[OK] Recolección global: {articles_collected} artículos")
            except Exception as e:
                logger.error(f"[ERROR] Error en recolección global: {e}")
                logger.info("[PROCESS] Cambiando a recolección RSS...")
                articles_collected = self._run_rss_collection(max_articles)
        else:
            articles_collected = self._run_rss_collection(max_articles)
        return articles_collected

    def _validate_data(self):
        logger.info("[SEARCH] Paso 2: Validando calidad de datos...")
        try:
            validation_results = data_validator.validate_recent_data()
            logger.info(
                f"[OK] Validación: {validation_results.get('valid_count', 0)} artículos válidos")
        except Exception as e:
            logger.warning(f"[WARN] Error en validación: {e}")

    def _process_data(self, articles_collected):
        logger.info("[DATA] Paso 3: Procesando análisis NLP...")
        try:
            processed_count = self._run_nlp_processing(articles_collected)
            logger.info(
                f"[OK] Procesamiento NLP: {processed_count} artículos analizados")
            return processed_count
        except Exception as e:
            logger.error(f"[ERROR] Error en procesamiento NLP: {e}")
            return 0

    def _generate_reports(self):
        logger.info("[DOCS] Paso 4: Generando informes...")
        try:
            reports_generated = self._run_report_generation()
            logger.info(f"[OK] Informes: {reports_generated} generados")
            return reports_generated
        except Exception as e:
            logger.error(f"[ERROR] Error generando informes: {e}")
            return 0

    def _run_enhanced_collection(self, max_articles: int) -> int:
        """Ejecuta recolección mejorada con NewsAPI y fuentes globales."""
        total_collected = 0
        languages = ['es', 'en', 'ru', 'zh', 'ar']
        for lang in languages:
            try:
                logger.info(
                    f"[WEB] Recolectando noticias en {lang.upper()}...")
                newsapi_articles = self.enhanced_newsapi.collect_by_language(
                    language=lang, max_articles=max_articles // len(languages))
                rss_articles = self.global_rss_collector.collect_by_language(
                    language=lang, max_articles=max_articles // len(languages))
                lang_total = newsapi_articles + rss_articles
                total_collected += lang_total
                logger.info(
                    f"[OK] {lang.upper()}: {lang_total} artículos ({newsapi_articles} API + {rss_articles} RSS)")
            except Exception as e:
                logger.error(f"[ERROR] Error recolectando en {lang}: {e}")
        return total_collected

    def _run_rss_collection(self, max_articles: int) -> int:
        """Ejecuta recolección usando solo fuentes RSS."""
        try:
            return self.global_rss_collector.collect_all_sources(max_articles)
        except Exception as e:
            logger.error(f"[ERROR] Error en recolección RSS: {e}")
            return 0

    def _run_nlp_processing(self, limit: int = 500) -> int:
        """Ejecuta el procesamiento NLP AVANZADO OBLIGATORIO en artículos no procesados."""
        logger.info(f"🧠 Iniciando procesamiento NLP AVANZADO para hasta {limit} art��culos.")
        
        # Initialize advanced NLP analyzers
        if ADVANCED_NLP_AVAILABLE:
            try:
                advanced_nlp_analyzer = AdvancedNLPAnalyzer()
                bert_analyzer = BERTRiskAnalyzer()
                logger.info("✅ Analizadores NLP avanzados inicializados")
            except Exception as e:
                logger.error(f"❌ Error inicializando analizadores avanzados: {e}")
                return 0
        else:
            logger.error("❌ Análisis NLP avanzado no disponible - ABORTANDO")
            return 0
        
        db = DatabaseManager(config)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get articles that need advanced NLP processing
            query = """
                SELECT a.id, a.title, a.content, a.country, a.language
                FROM articles a
                LEFT JOIN processed_data pd ON a.id = pd.article_id
                WHERE pd.advanced_nlp IS NULL OR pd.advanced_nlp = ''
                ORDER BY a.created_at DESC
                LIMIT ?
            """
            articles_to_process = cursor.execute(query, (limit,)).fetchall()

            if not articles_to_process:
                logger.info("✅ No hay artículos nuevos para procesar con NLP avanzado.")
                return 0

            logger.info(f"🔍 Se encontraron {len(articles_to_process)} artículos para análisis NLP AVANZADO.")
            
            processed_count = 0
            
            for article in articles_to_process:
                article_id, title, content, country, language = article
                
                try:
                    logger.info(f"🔬 Procesando artículo {article_id} con NLP avanzado...")
                    
                    # Prepare article data for comprehensive analysis
                    article_data = {
                        'title': title or '',
                        'content': content or '',
                        'description': ''
                    }
                    
                    # Perform comprehensive NLP analysis
                    nlp_results = advanced_nlp_analyzer.analyze_article_comprehensive(article_data)
                    
                    # Perform BERT risk analysis
                    bert_results = bert_analyzer.analyze_risk(
                        title=title or '',
                        content=content or '',
                        country=country
                    )
                    
                    # Combine all analysis results
                    combined_analysis = {
                        'nlp_entities': nlp_results['entities'],
                        'sentiment_analysis': nlp_results['sentiment'],
                        'title_sentiment': nlp_results['title_sentiment'],
                        'nlp_risk_score': nlp_results['risk_score'],
                        'bert_risk_level': bert_results['level'],
                        'bert_risk_score': bert_results['score'],
                        'bert_confidence': bert_results['confidence'],
                        'bert_reasoning': bert_results['reasoning'],
                        'key_factors': bert_results.get('key_factors', []),
                        'geographic_impact': bert_results.get('geographic_impact', 'Unknown'),
                        'escalation_potential': bert_results.get('potential_escalation', 'Unknown'),
                        'key_persons': nlp_results['key_persons'],
                        'key_locations': nlp_results['key_locations'],
                        'conflict_indicators': nlp_results['conflict_indicators'],
                        'total_entities': nlp_results['total_entities'],
                        'ai_powered': bert_results['ai_powered'],
                        'model_used': bert_results['model_used'],
                        'analysis_timestamp': nlp_results['analysis_timestamp'],
                        'processing_source': 'orchestrator_advanced_nlp'
                    }
                    
                    # Update article with BERT risk analysis
                    cursor.execute("""
                        UPDATE articles 
                        SET risk_level = ?, risk_score = ?
                        WHERE id = ?
                    """, (bert_results['level'], bert_results['score'], article_id))
                    
                    # Update or insert processed data
                    cursor.execute("""
                        SELECT id FROM processed_data WHERE article_id = ?
                    """, (article_id,))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing record with advanced NLP data
                        cursor.execute("""
                            UPDATE processed_data 
                            SET 
                                summary = ?,
                                category = ?,
                                keywords = ?,
                                sentiment = ?,
                                entities = ?,
                                advanced_nlp = ?
                            WHERE article_id = ?
                        """, (
                            content[:300] + '...' if len(content) > 300 else content,
                            'geopolitical_analysis',
                            json.dumps(nlp_results['key_persons'] + nlp_results['key_locations']),
                            nlp_results['sentiment']['score'],
                            json.dumps(nlp_results['entities']),
                            json.dumps(combined_analysis),
                            article_id
                        ))
                    else:
                        # Insert new processed data record
                        cursor.execute("""
                            INSERT INTO processed_data (
                                article_id, summary, category, keywords, sentiment, entities, advanced_nlp
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            article_id,
                            content[:300] + '...' if len(content) > 300 else content,
                            'geopolitical_analysis',
                            json.dumps(nlp_results['key_persons'] + nlp_results['key_locations']),
                            nlp_results['sentiment']['score'],
                            json.dumps(nlp_results['entities']),
                            json.dumps(combined_analysis)
                        ))
                    
                    processed_count += 1
                    
                    logger.info(f"✅ Artículo {article_id} procesado con NLP avanzado:")
                    logger.info(f"   🎯 Riesgo BERT: {bert_results['level']} ({bert_results['score']:.3f})")
                    logger.info(f"   😊 Sentimiento: {nlp_results['sentiment']['label']} ({nlp_results['sentiment']['score']:.3f})")
                    logger.info(f"   👥 Entidades: {nlp_results['total_entities']}")
                    
                    # Commit every 10 articles
                    if processed_count % 10 == 0:
                        conn.commit()
                        logger.info(f"💾 Progreso guardado: {processed_count} artículos procesados")
                    
                except Exception as e:
                    logger.error(f"❌ Error procesando artículo {article_id} con NLP avanzado: {e}")
                    continue
            
            # Final commit
            conn.commit()
            
            self.stats['successful_analyses'] += processed_count
            self.stats['failed_analyses'] += len(articles_to_process) - processed_count
            
            logger.info(f"🎉 Procesamiento NLP avanzado completado: {processed_count}/{len(articles_to_process)} artículos")
            return processed_count
            
        except Exception as e:
            logger.error(f"❌ Error crítico durante el procesamiento NLP avanzado: {e}")
            logger.error(traceback.format_exc())
            return 0
        finally:
            conn.close()

    def _run_report_generation(self) -> int:
        """Genera informes automatizados."""
        try:
            reports_generated = 0
            if self.reporter.generate_daily_report():
                reports_generated += 1
                logger.info("[OK] Informe diario generado")
            if self._has_sufficient_data_for_trends():
                if self.reporter.generate_trend_analysis():
                    reports_generated += 1
                    logger.info("[OK] Análisis de tendencias generado")
            return reports_generated
        except Exception as e:
            logger.error(f"[ERROR] Error generando informes: {e}")
            return 0

    def _update_system_metrics(
            self,
            articles_collected: int,
            processed_count: int):
        """Actualiza métricas del sistema."""
        try:
            self.stats['total_articles'] += articles_collected
            self.stats['successful_analyses'] += processed_count
            system_status = system_monitor.get_system_status()
            logger.info(
                f"[DATA] Uptime: {datetime.now() - self.stats['uptime_start']}")
            logger.info(
                f"[DATA] Total procesado: {self.stats['total_articles']} artículos")
            logger.info(
                f"[DATA] Memoria: {system_status.get('memory_usage', 'N/A')}%")
        except Exception as e:
            logger.warning(f"[WARN] Error actualizando métricas: {e}")

    def _has_sufficient_data_for_trends(self) -> bool:
        """Verifica si hay suficientes datos para análisis de tendencias."""
        try:
            db = DatabaseManager(config)
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM articles WHERE published_at > datetime('now', '-7 days')")
            count = cursor.fetchone()[0]
            return count >= 100
        except Exception:
            return False

    def collect_data_only(self):
        """Ejecuta solo la recolección de datos."""
        try:
            logger.info("Ejecutando solo recolección de datos...")
            articles_collected = self.collector.collect_daily_news()
            logger.info(
                f"Recolección de datos completada: {articles_collected} artículos")
            return articles_collected
        except Exception as e:
            logger.error(f"Error en recolección de datos: {e}")
            return 0

    def process_data_only(self):
        """Ejecuta solo el procesamiento NLP."""
        try:
            logger.info("Ejecutando solo procesamiento NLP...")
            # Use the same method as in _run_nlp_processing
            articles_processed = self._run_nlp_processing(limit=500)
            logger.info(
                f"Procesamiento NLP completado: {articles_processed} artículos")
            return articles_processed
        except Exception as e:
            logger.error(f"Error en procesamiento NLP: {e}")
            return 0

    def generate_reports_only(self, report_type='daily'):
        """Ejecuta solo la generación de informes."""
        try:
            logger.info(f"Generando solo informes de tipo {report_type}...")
            if report_type == 'daily':
                reports = self.reporter.generate_daily_report()
            elif report_type == 'weekly':
                reports = self.reporter.generate_weekly_report()
            else:
                raise ValueError(f"Tipo de informe desconocido: {report_type}")
            logger.info(
                f"Generación de informes completada: {list(reports.values())}")
            return reports
        except Exception as e:
            logger.error(f"Error en generación de informes: {e}")
            return {}

    def show_status(self):
        """Muestra el estado actual del sistema."""
        try:
            db = DatabaseManager(config)
            conn = db.get_connection()
            cursor = conn.cursor()

            print("\n" + "=" * 60)
            print("ESTADO DEL SISTEMA DE INTELIGENCIA GEOPOLÍTICA")
            print("=" * 60)

            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            print(f"Total de Artículos en Base de Datos: {total_articles}")

            cursor.execute("SELECT COUNT(*) FROM processed_data")
            processed_articles = cursor.fetchone()[0]
            print(f"Artículos Procesados: {processed_articles}")

            cursor.execute(
                "SELECT COUNT(*) FROM articles WHERE published_at > datetime('now', '-1 day')")
            recent_articles = cursor.fetchone()[0]
            print(f"Artículos (Últimas 24h): {recent_articles}")

            cursor.execute(
                "SELECT language, COUNT(*) as count FROM articles WHERE published_at > datetime('now', '-7 days') GROUP BY language ORDER BY count DESC")
            languages = cursor.fetchall()
            print("\nDistribución por Idioma (Últimos 7 días):")
            for lang, count in languages:
                print(f"  {lang.upper()}: {count} artículos")

            cursor.execute("SELECT p.category, COUNT(*) as count FROM processed_data p JOIN articles a ON p.article_id = a.id WHERE a.published_at > datetime('now', '-7 days') GROUP BY p.category ORDER BY count DESC")
            categories = cursor.fetchall()
            print("\nCategorías de Eventos (Últimos 7 días):")
            for category, count in categories:
                print(f"  {category.replace('_', ' ').title()}: {count} eventos")

            cursor.execute("""
                SELECT json_extract(p.entities, '$.GPE') as countries, COUNT(*) as event_count, AVG(p.sentiment) as avg_sentiment
                FROM processed_data p JOIN articles a ON p.article_id = a.id
                WHERE a.published_at > datetime('now', '-7 days') AND json_extract(p.entities, '$.GPE') IS NOT NULL
                GROUP BY countries HAVING event_count >= 3 ORDER BY avg_sentiment ASC LIMIT 5
            """)
            risk_regions = cursor.fetchall()
            if risk_regions:
                print("\nPrincipales Regiones de Riesgo (Últimos 7 días):")
                import json
                for countries_json, count, sentiment in risk_regions:
                    try:
                        countries = json.loads(
                            countries_json) if countries_json else []
                        region_name = ', '.join(
                            countries[:2]) if countries else 'Desconocida'
                        print(
                            f"  {region_name}: {count} eventos, sentimiento: {sentiment:.2f}")
                    except (json.JSONDecodeError, TypeError):
                        continue

            conn.close()
            print("=" * 60)
        except Exception as e:
            logger.error(f"Error mostrando estado: {e}")
            print(f"Error recuperando estado: {e}")

    def health_check(self):
        """Realiza una comprobación completa de la salud del sistema."""
        try:
            logger.info("Realizando comprobación de salud del sistema...")
            health_status = system_monitor.check_system_health()
            performance = system_monitor.get_performance_metrics(hours=24)
            quality_report = data_validator.get_quality_report(days=7)
            report_file = system_monitor.save_health_report({
                'health_status': health_status,
                'performance_metrics': performance,
                'data_quality': quality_report
            })

            print("\n" + "=" * 60)
            print("RESULTADOS DE LA COMPROBACIÓN DE SALUD DEL SISTEMA")
            print("=" * 60)
            print(
                f"Estado General: {health_status.get('overall_status', 'unknown').upper()}")
            print(
                f"Rendimiento - Artículos/hora: {performance.get('articles_per_hour', 0)}")
            print(
                f"Calidad de Datos - Tasa de validación: {quality_report.get('validation_rate', 0)}%")
            print(f"Informe completo guardado en: {report_file}")
            print("=" * 60)

            return health_status
        except Exception as e:
            logger.error(f"Error durante la comprobación de salud: {e}")
            return {'overall_status': 'error', 'error': str(e)}

    def validate_data_quality(self, days=7):
        """Ejecuta la validación y limpieza de la calidad de los datos."""
        try:
            logger.info(
                f"Ejecutando validación de calidad de datos para los últimos {days} días...")
            quality_report = data_validator.get_quality_report(days=days)

            print("\n" + "=" * 60)
            print("INFORME DE CALIDAD DE DATOS")
            print("=" * 60)
            print(f"Período: Últimos {days} días")
            print(
                f"Total de Artículos: {quality_report.get('total_articles', 0)}")
            print(
                f"Artículos Válidos: {quality_report.get('valid_articles', 0)}")
            print(
                f"Tasa de Validación: {quality_report.get('validation_rate', 0)}%")
            print(
                f"Puntuación Media de Calidad: {quality_report.get('avg_quality_score', 0)}")

            if 'quality_distribution' in quality_report:
                print("\nDistribución de Calidad:")
                for range_name, count in quality_report['quality_distribution'].items(
                ):
                    print(f"  {range_name}: {count} artículos")

            print("=" * 60)

            invalid_articles = quality_report.get('invalid_articles', 0)
            if invalid_articles > 10:
                print(
                    f"\nSe encontraron {invalid_articles} artículos inválidos.")
                response = input(
                    "¿Desea limpiar los artículos con una puntuación de calidad < 30? (y/N): ")
                if response.lower() == 'y':
                    cleaned = data_validator.cleanup_invalid_articles(
                        min_quality_score=30)
                    print(f"Se limpiaron {cleaned} artículos de baja calidad.")

            return quality_report
        except Exception as e:
            logger.error(
                f"Error durante la validación de calidad de datos: {e}")
            return {'error': str(e)}

    def system_maintenance(self):
        """Realiza tareas de mantenimiento del sistema."""
        try:
            logger.info("Iniciando mantenimiento del sistema...")
            cleaned_files = system_monitor.cleanup_old_reports(days=7)
            logger.info(f"Se limpiaron {cleaned_files} archivos antiguos")
            cleaned_articles = data_validator.cleanup_invalid_articles(
                min_quality_score=20)
            logger.info(
                f"Se limpiaron {cleaned_articles} artículos de muy baja calidad")

            try:
                import sqlite3
                conn = sqlite3.connect(
                    config.get(
                        'database', {}).get(
                        'path', 'data/riskmap.db'))
                conn.execute('VACUUM')
                conn.close()
                logger.info("Base de datos optimizada")
            except Exception as e:
                logger.warning(f"No se pudo optimizar la base de datos: {e}")

            print("\nMantenimiento completado:")
            print(f"- Se limpiaron {cleaned_files} archivos antiguos")
            print(
                f"- Se eliminaron {cleaned_articles} artículos de baja calidad")
            print("- Base de datos optimizada")

            return True
        except Exception as e:
            logger.error(f"Error durante el mantenimiento del sistema: {e}")
            return False

    def run_global_collection(
            self,
            languages=None,
            regions=None,
            include_intelligence=True):
        """Ejecuta la recolección de noticias global mejorada con cobertura mundial."""
        try:
            logger.info("Iniciando recolección de noticias global mejorada...")
            total_articles = 0

            if languages is None:
                languages = config.get(
                    'data_sources.global_coverage.priority_languages', [
                        'en', 'es', 'fr', 'de', 'ru', 'zh', 'ar'])

            logger.info("Recolectando de fuentes RSS globales...")
            for language in languages:
                if regions:
                    for region in regions:
                        sources = self.global_sources_registry.get_sources_by_region(
                            language, region)
                        articles_count = self.global_rss_collector.collect_from_sources(
                            sources)
                        total_articles += articles_count
                        logger.info(
                            f"Recolectados {articles_count} artículos de {language}/{region}")
                else:
                    sources = self.global_sources_registry.get_sources_by_language(
                        language)
                    articles_count = self.global_rss_collector.collect_from_sources(
                        sources)
                    total_articles += articles_count
                    logger.info(
                        f"Recolectados {articles_count} artículos para el idioma {language}")

            logger.info("Recolectando de NewsAPI mejorada...")
            for language in languages:
                try:
                    articles_count = self.enhanced_newsapi.collect_multilingual_headlines(
                        language)
                    total_articles += articles_count
                    logger.info(
                        f"Recolectados {articles_count} artículos de NewsAPI para {language}")
                except Exception as e:
                    logger.warning(
                        f"La recolección de NewsAPI falló para {language}: {e}")

            if include_intelligence:
                logger.info("Recolectando de fuentes de inteligencia...")
                try:
                    intel_articles = self.intelligence_collector.collect_all_sources()
                    total_articles += len(intel_articles)
                    logger.info(
                        f"Recolectados {len(intel_articles)} artículos de inteligencia")
                except Exception as e:
                    logger.warning(
                        f"La recolección de inteligencia falló: {e}")

            logger.info(
                f"Recolección global mejorada completada: {total_articles} artículos en total")
            return total_articles
        except Exception as e:
            logger.error(f"Error en la recolección global: {e}")
            return 0

    def run_regional_collection(self, region: str, max_articles_per_source=15):
        """Ejecuta la recolección dirigida para una región específica."""
        try:
            logger.info(f"Iniciando recolección regional para: {region}")
            total_articles = 0

            region_config = config.get(
                'data_sources.global_coverage.regions', {})
            priority_languages = {
                'americas': [
                    'en', 'es', 'pt'], 'europe': [
                    'en', 'de', 'fr', 'es', 'it', 'ru', 'nl'], 'asia_pacific': [
                    'en', 'zh', 'ja', 'ko'], 'middle_east': [
                    'ar', 'en'], 'africa': [
                        'en', 'fr', 'ar']}.get(
                            region, ['en'])

            for language in priority_languages:
                try:
                    sources = self.global_sources_registry.get_sources_by_region(
                        language, region)
                    if sources:
                        articles_count = self.global_rss_collector.collect_from_sources(
                            sources, max_articles_per_source)
                        total_articles += articles_count
                        logger.info(
                            f"Recolección regional {region}/{language}: {articles_count} artículos")
                except Exception as e:
                    logger.warning(
                        f"La recolección regional falló para {region}/{language}: {e}")

            logger.info(
                f"Recolección regional para {region} completada: {total_articles} artículos")
            return total_articles
        except Exception as e:
            logger.error(
                f"Error en la recolección regional para {region}: {e}")
            return 0

    def run_intelligence_only_collection(self):
        """Ejecuta la recolección solo de fuentes de inteligencia y think tanks."""
        try:
            logger.info("Iniciando recolección solo de inteligencia...")
            total_articles = 0

            for region in ['us', 'europe', 'asia']:
                sources = self.intelligence_registry.get_sources_by_category(
                    'think_tanks', region)
                if sources:
                    articles = self.intelligence_collector.collect_from_sources(
                        sources)
                    total_articles += len(articles)
                    logger.info(
                        f"Recolectados {len(articles)} artículos de think tanks de {region}")

            academic_sources = self.intelligence_registry.get_sources_by_category(
                'academic_institutions')
            if academic_sources:
                articles = self.intelligence_collector.collect_from_sources(
                    academic_sources)
                total_articles += len(articles)
                logger.info(
                    f"Recolectados {len(articles)} artículos académicos")

            gov_sources = self.intelligence_registry.get_sources_by_category(
                'government_sources')
            if gov_sources:
                articles = self.intelligence_collector.collect_from_sources(
                    gov_sources)
                total_articles += len(articles)
                logger.info(
                    f"Recolectados {len(articles)} artículos gubernamentales")

            logger.info(
                f"Recolección solo de inteligencia completada: {total_articles} artículos")
            return total_articles
        except Exception as e:
            logger.error(f"Error en la recolección de inteligencia: {e}")
            return 0
    
    def _save_processed_results(self, articles_list, results, conn):
        """Save processed NLP results to database."""
        import json
        cursor = conn.cursor()
        
        for article, result in zip(articles_list, results):
            if result is None:
                continue
                
            try:
                # Extract data from result
                article_id = article['id']
                category = result.get('category', 'unknown')
                sentiment = result.get('sentiment', 0.0)
                entities = json.dumps(result.get('entities', {}))
                summary = result.get('summary', '')
                keywords = json.dumps(result.get('keywords', []))
                
                # Update article risk level
                risk_level = 'low'
                if category in ['military_conflict', 'terrorism', 'natural_disaster']:
                    risk_level = 'high'
                elif category in ['political_tension', 'economic_crisis', 'social_unrest']:
                    risk_level = 'medium'
                
                cursor.execute("""
                    UPDATE articles 
                    SET risk_level = ? 
                    WHERE id = ?
                """, (risk_level, article_id))
                
                # Insert processed data
                cursor.execute("""
                    INSERT INTO processed_data 
                    (article_id, category, sentiment, entities, summary, keywords)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (article_id, category, sentiment, entities, summary, keywords))
                
            except Exception as e:
                logger.error(f"Error saving processed result for article {article.get('id')}: {e}")
                continue
        
        conn.commit()
