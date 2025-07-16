"""
Sistema de Inteligencia Geopolítica - Orchestrator Principal
Coordina recolección de datos, procesamiento y análisis de inteligencia geopolítica en tiempo real.
Implementa análisis multilingüe (es, en, ru, zh, ar) con datos 100% reales.
"""

import argparse
import logging
import schedule
import time
import traceback
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path for consistent module resolution
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.config import config, logger, DatabaseManager
    from src.data_ingestion.news_collector import GeopoliticalNewsCollector
    from src.data_ingestion.global_news_collector import GlobalNewsSourcesRegistry, EnhancedNewsAPICollector, GlobalRSSCollector
    from src.data_ingestion.enhanced_global_news_collector import EnhancedGlobalNewsCollector
    from src.data_ingestion.intelligence_sources import IntelligenceSourcesRegistry, IntelligenceCollector
    from src.nlp_processing import GeopoliticalTextAnalyzer, bulk_process_articles
    from src.reporting.report_generator import AdvancedReportGenerator as ReportGenerator
    from src.monitoring.system_monitor import system_monitor
    from src.data_quality.validator import data_validator
except ImportError as e:
    print(f"[ERROR] Error importando módulos: {e}")
    print(f"[INFO] Python Path: {sys.path}")
    print("[WARN] Ejecute 'python setup.py' o 'pip install -r requirements.txt' primero para instalar dependencias.")
    sys.exit(1)


class GeopoliticalIntelligenceOrchestrator:
    """Sistema principal de orquestación para inteligencia geopolítica con datos reales."""
    
    def __init__(self):
        logger.info("[GLOBAL] Inicializando Sistema de Inteligencia Geopolítica...")
        
        # Estado del sistema
        self.is_running = False
        self.last_update = None
        self.stats = {
            'total_articles': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'last_execution_time': None,
            'uptime_start': datetime.now()
        }
        
        # Configuración de threading
        self.max_workers = config.get('processing.max_workers', 4)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Validar configuración de APIs reales
        self._validate_real_apis()
        
        # Initialize collectors
        try:
            self.collector = GeopoliticalNewsCollector()
            self.global_sources_registry = GlobalNewsSourcesRegistry()
            self.enhanced_newsapi = EnhancedNewsAPICollector()
            self.global_rss_collector = GlobalRSSCollector()
            
            # Initialize intelligence sources
            self.intelligence_registry = IntelligenceSourcesRegistry()
            self.intelligence_collector = IntelligenceCollector()
            
            # Initialize processing components
            self.analyzer = GeopoliticalTextAnalyzer()
            self.reporter = ReportGenerator()
            
            logger.info("[OK] Sistema inicializado correctamente")
            
        except Exception as e:
            logger.error(f"[ERROR] Error inicializando componentes: {e}")
            raise
    
    def _validate_real_apis(self):
        """Valida que todas las APIs configuradas sean reales y funcionales."""
        logger.info("[KEY] Validando configuración de APIs...")
        
        api_status = {
            'newsapi': False,
            'google_translate': False,
            'openai': False
        }
        
        # Validar NewsAPI
        try:
            newsapi_key = config.get_newsapi_key()
            if newsapi_key and newsapi_key != "your_newsapi_key_here":
                # Test simple connection
                import requests
                response = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={'q': 'test', 'apiKey': newsapi_key, 'pageSize': 1},
                    timeout=5
                )
                if response.status_code == 200:
                    api_status['newsapi'] = True
                    logger.info("[OK] NewsAPI: Configurada y funcional")
                else:
                    logger.warning("[WARN] NewsAPI: Configurada pero con errores")
            else:
                logger.warning("[WARN] NewsAPI: No configurada")
        except Exception as e:
            logger.warning(f"[WARN] NewsAPI: Error de validación - {e}")
        
        # Validar Google Translate
        google_key = config.get_google_translate_key()
        if google_key and google_key != "your_google_translate_key_here":
            api_status['google_translate'] = True
            logger.info("[OK] Google Translate API: Configurada")
        else:
            logger.info("[INFO] Google Translate API: No configurada (opcional)")
        
        # Validar OpenAI
        openai_key = config.get_openai_key()
        if openai_key and openai_key != "your_openai_key_here":
            api_status['openai'] = True
            logger.info("[OK] OpenAI API: Configurada")
        else:
            logger.info("[INFO] OpenAI API: No configurada (opcional para chatbot avanzado)")
        
        # Verificar estado mínimo
        if not api_status['newsapi']:
            logger.warning("[WARN] ADVERTENCIA: NewsAPI no configurada - funcionalidad limitada")
        
        self.api_status = api_status
        logger.info("[SEARCH] Validación de APIs completada")
    
    def _run_nlp_processing(self, limit: int = 500) -> int:
        """
        Ejecuta el procesamiento NLP en artículos no procesados.
        """
        logger.info(f"Iniciando procesamiento NLP para hasta {limit} artículos.")
        db = DatabaseManager(config)
        conn = db.get_connection()
        try:
            # Seleccionar artículos que no han sido procesados (sin entrada en processed_data)
            # y que tampoco tienen clasificación de riesgo (doble seguridad)
            query = """
                SELECT a.id, a.content, a.language
                FROM articles a
                LEFT JOIN processed_data pd ON a.id = pd.article_id
                WHERE pd.article_id IS NULL AND a.risk_level IS NULL
                ORDER BY a.published_at DESC
                LIMIT ?
            """
            articles_to_process = conn.execute(query, (limit,)).fetchall()
            
            if not articles_to_process:
                logger.info("No hay artículos nuevos para procesar.")
                return 0

            logger.info(f"Se encontraron {len(articles_to_process)} artículos para análisis NLP.")
            
            # Convertir a formato de diccionario
            articles_list = [
                {'id': row[0], 'content': row[1], 'language': row[2]}
                for row in articles_to_process
            ]

            # Usar el procesador masivo
            processed_count = bulk_process_articles(articles_list)
            
            self.stats['successful_analyses'] += processed_count
            self.stats['failed_analyses'] += len(articles_to_process) - processed_count
            
            return processed_count
        except Exception as e:
            logger.error(f"Error crítico durante el procesamiento NLP: {e}")
            logger.error(traceback.format_exc())
            return 0
        finally:
            conn.close()

    def run_full_pipeline(self, validate_data=True, use_global_collection=True, max_articles=1000):
        """Ejecuta el pipeline completo de inteligencia con manejo robusto de errores."""
        start_time = datetime.now()
        self.is_running = True
        
        try:
            logger.info("[START] Iniciando pipeline completo de inteligencia geopolítica")
            logger.info(f"[DATA] Configuración: validate_data={validate_data}, global_collection={use_global_collection}")
            
            # Paso 1: Recolección de datos
            logger.info("[NEWS] Paso 1: Recolectando datos de noticias...")
            articles_collected = 0
            
            if use_global_collection and self.api_status.get('newsapi', False):
                try:
                    articles_collected = self._run_enhanced_collection(max_articles)
                    logger.info(f"[OK] Recolección global: {articles_collected} artículos")
                except Exception as e:
                    logger.error(f"[ERROR] Error en recolección global: {e}")
                    logger.info("[PROCESS] Cambiando a recolección RSS...")
                    articles_collected = self._run_rss_collection(max_articles)
            else:
                articles_collected = self._run_rss_collection(max_articles)
            
            if articles_collected == 0:
                logger.warning("[WARN] No se recolectaron artículos. Verificar configuración.")
                return False
            
            # Paso 2: Validación de datos (opcional)
            if validate_data:
                logger.info("[SEARCH] Paso 2: Validando calidad de datos...")
                try:
                    validation_results = data_validator.validate_recent_data()
                    logger.info(f"[OK] Validación: {validation_results.get('valid_count', 0)} artículos válidos")
                except Exception as e:
                    logger.warning(f"[WARN] Error en validación: {e}")
            
            # Paso 3: Procesamiento NLP
            logger.info("[DATA] Paso 3: Procesando análisis NLP...")
            try:
                processed_count = self._run_nlp_processing(articles_collected)
                logger.info(f"[OK] Procesamiento NLP: {processed_count} artículos analizados")
            except Exception as e:
                logger.error(f"[ERROR] Error en procesamiento NLP: {e}")
                processed_count = 0
            
            # Paso 4: Generación de informes
            logger.info("[DOCS] Paso 4: Generando informes...")
            try:
                reports_generated = self._run_report_generation()
                logger.info(f"[OK] Informes: {reports_generated} generados")
            except Exception as e:
                logger.error(f"[ERROR] Error generando informes: {e}")
                reports_generated = 0
            
            # Paso 5: Monitoreo del sistema
            logger.info("[DATA] Paso 5: Actualizando métricas del sistema...")
            try:
                self._update_system_metrics(articles_collected, processed_count)
            except Exception as e:
                logger.warning(f"[WARN] Error actualizando métricas: {e}")
            
            # Resultados finales
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"[SUCCESS] Pipeline completado en {execution_time:.2f} segundos")
            logger.info(f"[STATS] Resumen: {articles_collected} recolectados, {processed_count} procesados, {reports_generated} informes")
            
            self.stats['last_execution_time'] = execution_time
            self.stats['total_articles'] += articles_collected
            self.stats['successful_analyses'] += processed_count
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error crítico en pipeline: {e}")
            logger.error(f"[SEARCH] Traceback: {traceback.format_exc()}")
            return False
        finally:
            self.is_running = False
            self.last_update = datetime.now()
    
    def _run_enhanced_collection(self, max_articles: int) -> int:
        """Ejecuta recolección mejorada con NewsAPI y fuentes globales."""
        total_collected = 0
        
        # Recolección por idiomas obligatorios
        languages = ['es', 'en', 'ru', 'zh', 'ar']
        
        for lang in languages:
            try:
                logger.info(f"[WEB] Recolectando noticias en {lang.upper()}...")
                
                # NewsAPI collection
                newsapi_articles = self.enhanced_newsapi.collect_by_language(
                    language=lang, 
                    max_articles=max_articles // len(languages)
                )
                
                # RSS collection
                rss_articles = self.global_rss_collector.collect_by_language(
                    language=lang,
                    max_articles=max_articles // len(languages)
                )
                
                lang_total = newsapi_articles + rss_articles
                total_collected += lang_total
                
                logger.info(f"[OK] {lang.upper()}: {lang_total} artículos ({newsapi_articles} API + {rss_articles} RSS)")
                
            except Exception as e:
                logger.error(f"[ERROR] Error recolectando en {lang}: {e}")
                continue
        
        return total_collected
    
    def _run_rss_collection(self, max_articles: int) -> int:
        """Ejecuta recolección usando solo fuentes RSS."""
        try:
            return self.global_rss_collector.collect_all_sources(max_articles)
        except Exception as e:
            logger.error(f"[ERROR] Error en recolección RSS: {e}")
            return 0
    
    def _run_report_generation(self) -> int:
        """Genera informes automatizados."""
        try:
            reports_generated = 0
            
            # Informe diario
            if self.reporter.generate_daily_report():
                reports_generated += 1
                logger.info("[OK] Informe diario generado")
            
            # Informe de tendencias (si hay suficientes datos)
            if self._has_sufficient_data_for_trends():
                if self.reporter.generate_trend_analysis():
                    reports_generated += 1
                    logger.info("[OK] Análisis de tendencias generado")
            
            return reports_generated
            
        except Exception as e:
            logger.error(f"[ERROR] Error generando informes: {e}")
            return 0
    
    def _update_system_metrics(self, articles_collected: int, processed_count: int):
        """Actualiza métricas del sistema."""
        try:
            # Actualizar estadísticas internas
            self.stats['total_articles'] += articles_collected
            self.stats['successful_analyses'] += processed_count
            
            # Monitoreo del sistema
            system_status = system_monitor.get_system_status()
            
            # Log métricas importantes
            logger.info(f"[DATA] Uptime: {datetime.now() - self.stats['uptime_start']}")
            logger.info(f"[DATA] Total procesado: {self.stats['total_articles']} artículos")
            logger.info(f"[DATA] Memoria: {system_status.get('memory_usage', 'N/A')}%")
            
        except Exception as e:
            logger.warning(f"[WARN] Error actualizando métricas: {e}")
    
    def _get_unprocessed_articles(self, limit: int = 1000) -> List[Dict]:
        """Obtiene artículos que no han sido procesados."""
        try:
            from utils.config import DatabaseManager
            db = DatabaseManager(config)
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT a.id, a.title, a.content, a.url, a.language, a.published_at
                FROM articles a
                LEFT JOIN processed_data p ON a.id = p.article_id
                WHERE p.article_id IS NULL
                ORDER BY a.published_at DESC
                LIMIT ?
            """, (limit,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'url': row[3],
                    'language': row[4],
                    'published_at': row[5]
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"[ERROR] Error obteniendo artículos: {e}")
            return []
    
    def _save_analysis_result(self, article_id: int, analysis: Dict):
        """Guarda resultado de análisis en la base de datos."""
        try:
            from utils.config import DatabaseManager
            db = DatabaseManager(config)
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO processed_data
                (article_id, category, sentiment, entities, summary, processed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                article_id,
                analysis.get('category', 'neutral'),
                analysis.get('sentiment', 0.0),
                str(analysis.get('entities', {})),
                analysis.get('summary', ''),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"[ERROR] Error guardando análisis: {e}")
    
    def _has_sufficient_data_for_trends(self) -> bool:
        """Verifica si hay suficientes datos para análisis de tendencias."""
        try:
            from utils.config import DatabaseManager
            db = DatabaseManager(config)
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Verificar artículos de últimos 7 días
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE published_at > datetime('now', '-7 days')
            """)
            
            count = cursor.fetchone()[0]
            return count >= 100  # Mínimo 100 artículos para tendencias
            
        except Exception:
            return False
            if validate_data and articles_collected > 0:
                logger.info("Step 1.5: Validating collected data...")
                # This would require integration with the collector to get article data
                # For now, we'll add this as a separate validation step
            
            # Step 2: Process articles with NLP
            logger.info("Step 2: Processing articles with NLP...")
            articles_processed = self.analyzer.process_unprocessed_articles()
            logger.info(f"Processed {articles_processed} articles")
            
            # Step 3: Generate reports (only if we have processed articles)
            if articles_processed > 0:
                logger.info("Step 3: Generating reports...")
                daily_reports = self.reporter.generate_daily_report()
                logger.info(f"Generated daily reports: {list(daily_reports.values())}")
            else:
                logger.info("No new articles to process, skipping report generation")
            
            logger.info("Enhanced full pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in full pipeline: {e}")
            return False
    
    def collect_data_only(self):
        """Run only data collection."""
        try:
            logger.info("Running data collection only...")
            articles_collected = self.collector.collect_daily_news()
            logger.info(f"Data collection completed: {articles_collected} articles")
            return articles_collected
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            return 0
    
    def process_data_only(self):
        """Run only NLP processing."""
        try:
            logger.info("Running NLP processing only...")
            articles_processed = self.analyzer.process_unprocessed_articles()
            logger.info(f"NLP processing completed: {articles_processed} articles")
            return articles_processed
        except Exception as e:
            logger.error(f"Error in NLP processing: {e}")
            return 0
    
    def generate_reports_only(self, report_type='daily'):
        """Run only report generation."""
        try:
            logger.info(f"Generating {report_type} reports only...")
            
            if report_type == 'daily':
                reports = self.reporter.generate_daily_report()
            elif report_type == 'weekly':
                reports = self.reporter.generate_weekly_report()
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            logger.info(f"Report generation completed: {list(reports.values())}")
            return reports
        except Exception as e:
            logger.error(f"Error in report generation: {e}")
            return {}
    
    def run_scheduled_tasks(self):
        """Set up and run scheduled tasks."""
        logger.info("Setting up scheduled tasks...")
        
        # Schedule data collection every 3 hours
        schedule.every(3).hours.do(self.collect_data_only)
        
        # Schedule NLP processing every hour (for new articles)
        schedule.every().hour.do(self.process_data_only)
        
        # Schedule daily reports at 6 AM
        schedule.every().day.at("06:00").do(self.generate_reports_only, report_type='daily')
        
        # Schedule weekly reports on Mondays at 7 AM
        schedule.every().monday.at("07:00").do(self.generate_reports_only, report_type='weekly')
        
        logger.info("Scheduled tasks configured:")
        logger.info("- Data collection: Every 3 hours")
        logger.info("- NLP processing: Every hour")
        logger.info("- Daily reports: Daily at 6:00 AM")
        logger.info("- Weekly reports: Mondays at 7:00 AM")
        logger.info("Starting scheduler...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Error in scheduler: {e}")
    
    def show_status(self):
        """Show current system status."""
        try:
            from utils.config import DatabaseManager
            db = DatabaseManager(config)
            conn = db.get_connection()
            cursor = conn.cursor()
            
            print("\n" + "="*60)
            print("GEOPOLITICAL INTELLIGENCE SYSTEM STATUS")
            print("="*60)
            
            # Total articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            print(f"Total Articles in Database: {total_articles}")
            
            # Processed articles
            cursor.execute("SELECT COUNT(*) FROM processed_data")
            processed_articles = cursor.fetchone()[0]
            print(f"Processed Articles: {processed_articles}")
            
            # Recent articles (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE published_at > datetime('now', '-1 day')
            """)
            recent_articles = cursor.fetchone()[0]
            print(f"Articles (Last 24h): {recent_articles}")
            
            # Articles by language
            cursor.execute("""
                SELECT language, COUNT(*) as count
                FROM articles
                WHERE published_at > datetime('now', '-7 days')
                GROUP BY language
                ORDER BY count DESC
            """)
            languages = cursor.fetchall()
            print(f"\nLanguage Distribution (Last 7 days):")
            for lang, count in languages:
                print(f"  {lang.upper()}: {count} articles")
            
            # Categories
            cursor.execute("""
                SELECT p.category, COUNT(*) as count
                FROM processed_data p
                JOIN articles a ON p.article_id = a.id
                WHERE a.published_at > datetime('now', '-7 days')
                GROUP BY p.category
                ORDER BY count DESC
            """)
            categories = cursor.fetchall()
            print(f"\nEvent Categories (Last 7 days):")
            for category, count in categories:
                print(f"  {category.replace('_', ' ').title()}: {count} events")
            
            # Risk regions
            cursor.execute("""
                SELECT 
                    json_extract(p.entities, '$.GPE') as countries,
                    COUNT(*) as event_count,
                    AVG(p.sentiment) as avg_sentiment
                FROM processed_data p
                JOIN articles a ON p.article_id = a.id
                WHERE a.published_at > datetime('now', '-7 days')
                    AND json_extract(p.entities, '$.GPE') IS NOT NULL
                GROUP BY countries
                HAVING event_count >= 3
                ORDER BY avg_sentiment ASC
                LIMIT 5
            """)
            risk_regions = cursor.fetchall()
            
            if risk_regions:
                print(f"\nTop Risk Regions (Last 7 days):")
                for countries_json, count, sentiment in risk_regions:
                    try:
                        import json
                        countries = json.loads(countries_json) if countries_json else []
                        region_name = ', '.join(countries[:2]) if countries else 'Unknown'
                        print(f"  {region_name}: {count} events, sentiment: {sentiment:.2f}")
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            conn.close()
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error showing status: {e}")
            print(f"Error retrieving status: {e}")
    
    def health_check(self):
        """Perform comprehensive system health check."""
        try:
            logger.info("Performing system health check...")
            
            # Use the system monitor for health checks
            health_status = system_monitor.check_system_health()
            
            # Get performance metrics
            performance = system_monitor.get_performance_metrics(hours=24)
            
            # Get data quality report
            quality_report = data_validator.get_quality_report(days=7)
            
            # Save health report
            report_file = system_monitor.save_health_report({
                'health_status': health_status,
                'performance_metrics': performance,
                'data_quality': quality_report
            })
            
            # Print summary
            print("\n" + "="*60)
            print("SYSTEM HEALTH CHECK RESULTS")
            print("="*60)
            print(f"Overall Status: {health_status.get('overall_status', 'unknown').upper()}")
            print(f"Performance - Articles/hour: {performance.get('articles_per_hour', 0)}")
            print(f"Data Quality - Validation rate: {quality_report.get('validation_rate', 0)}%")
            print(f"Full report saved to: {report_file}")
            print("="*60)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return {'overall_status': 'error', 'error': str(e)}
    
    def validate_data_quality(self, days=7):
        """Run data quality validation and cleanup."""
        try:
            logger.info(f"Running data quality validation for last {days} days...")
            
            # Get quality report
            quality_report = data_validator.get_quality_report(days=days)
            
            print("\n" + "="*60)
            print("DATA QUALITY REPORT")
            print("="*60)
            print(f"Period: Last {days} days")
            print(f"Total Articles: {quality_report.get('total_articles', 0)}")
            print(f"Valid Articles: {quality_report.get('valid_articles', 0)}")
            print(f"Validation Rate: {quality_report.get('validation_rate', 0)}%")
            print(f"Average Quality Score: {quality_report.get('avg_quality_score', 0)}")
            
            if 'quality_distribution' in quality_report:
                print("\nQuality Distribution:")
                for range_name, count in quality_report['quality_distribution'].items():
                    print(f"  {range_name}: {count} articles")
            
            print("="*60)
            
            # Ask for cleanup if many invalid articles
            invalid_articles = quality_report.get('invalid_articles', 0)
            if invalid_articles > 10:
                print(f"\nFound {invalid_articles} invalid articles.")
                response = input("Do you want to clean up articles with quality score < 30? (y/N): ")
                if response.lower() == 'y':
                    cleaned = data_validator.cleanup_invalid_articles(min_quality_score=30)
                    print(f"Cleaned up {cleaned} low-quality articles.")
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Error during data quality validation: {e}")
            return {'error': str(e)}
    
    def system_maintenance(self):
        """Perform system maintenance tasks."""
        try:
            logger.info("Starting system maintenance...")
            
            # Clean up old reports and logs
            cleaned_files = system_monitor.cleanup_old_reports(days=7)
            logger.info(f"Cleaned up {cleaned_files} old files")
            
            # Clean up low-quality articles
            cleaned_articles = data_validator.cleanup_invalid_articles(min_quality_score=20)
            logger.info(f"Cleaned up {cleaned_articles} very low-quality articles")
            
            # Vacuum database
            try:
                import sqlite3
                conn = sqlite3.connect(config.get('database', {}).get('path', 'data/riskmap.db'))
                conn.execute('VACUUM')
                conn.close()
                logger.info("Database optimized")
            except Exception as e:
                logger.warning(f"Could not optimize database: {e}")
            
            print(f"\nMaintenance completed:")
            print(f"- Cleaned {cleaned_files} old files")
            print(f"- Removed {cleaned_articles} low-quality articles")
            print(f"- Database optimized")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during system maintenance: {e}")
            return False
    
    def run_global_collection(self, languages=None, regions=None, include_intelligence=True):
        """Run enhanced global news collection with worldwide coverage."""
        try:
            logger.info("Starting enhanced global news collection...")
            total_articles = 0
            
            # Use configured languages if not specified
            if languages is None:
                languages = config.get('data_sources.global_coverage.priority_languages', ['en', 'es', 'fr', 'de', 'ru', 'zh', 'ar'])
            
            # Collect from global RSS sources
            logger.info("Collecting from global RSS sources...")
            for language in languages:
                if regions:
                    for region in regions:
                        sources = self.global_sources_registry.get_sources_by_region(language, region)
                        articles = self.global_rss_collector.collect_from_sources(sources)
                        total_articles += len(articles)
                        logger.info(f"Collected {len(articles)} articles from {language}/{region}")
                else:
                    sources = self.global_sources_registry.get_sources_by_language(language)
                    articles = self.global_rss_collector.collect_from_sources(sources)
                    total_articles += len(articles)
                    logger.info(f"Collected {len(articles)} articles for language {language}")
            
            # Collect from enhanced NewsAPI
            logger.info("Collecting from enhanced NewsAPI...")
            for language in languages:
                try:
                    articles = self.enhanced_newsapi.collect_multilingual_headlines(language)
                    total_articles += len(articles)
                    logger.info(f"Collected {len(articles)} NewsAPI articles for {language}")
                except Exception as e:
                    logger.warning(f"NewsAPI collection failed for {language}: {e}")
            
            # Collect from intelligence sources
            if include_intelligence:
                logger.info("Collecting from intelligence sources...")
                try:
                    intel_articles = self.intelligence_collector.collect_all_sources()
                    total_articles += len(intel_articles)
                    logger.info(f"Collected {len(intel_articles)} intelligence articles")
                except Exception as e:
                    logger.warning(f"Intelligence collection failed: {e}")
            
            logger.info(f"Enhanced global collection completed: {total_articles} total articles")
            return total_articles
            
        except Exception as e:
            logger.error(f"Error in global collection: {e}")
            return 0
    
    def run_regional_collection(self, region: str, max_articles_per_source=15):
        """Run targeted collection for a specific region."""
        try:
            logger.info(f"Starting regional collection for: {region}")
            total_articles = 0
            
            # Get priority languages for the region
            region_config = config.get('data_sources.global_coverage.regions', {})
            priority_languages = ['en']  # Default fallback
            
            # Determine languages based on region
            if region in ['americas']:
                priority_languages = ['en', 'es', 'pt']
            elif region in ['europe']:
                priority_languages = ['en', 'de', 'fr', 'es', 'it', 'ru', 'nl']
            elif region in ['asia_pacific']:
                priority_languages = ['en', 'zh', 'ja', 'ko']
            elif region in ['middle_east']:
                priority_languages = ['ar', 'en']
            elif region in ['africa']:
                priority_languages = ['en', 'fr', 'ar']
            
            for language in priority_languages:
                try:
                    sources = self.global_sources_registry.get_sources_by_region(language, region)
                    if sources:
                        articles = self.global_rss_collector.collect_from_sources(sources, max_articles_per_source)
                        total_articles += len(articles)
                        logger.info(f"Regional collection {region}/{language}: {len(articles)} articles")
                except Exception as e:
                    logger.warning(f"Regional collection failed for {region}/{language}: {e}")
            
            logger.info(f"Regional collection for {region} completed: {total_articles} articles")
            return total_articles
            
        except Exception as e:
            logger.error(f"Error in regional collection for {region}: {e}")
            return 0
    
    def run_intelligence_only_collection(self):
        """Run collection from intelligence and think tank sources only."""
        try:
            logger.info("Starting intelligence-only collection...")
            
            # Collect from think tanks by region
            total_articles = 0
            
            for region in ['us', 'europe', 'asia']:
                sources = self.intelligence_registry.get_sources_by_category('think_tanks', region)
                if sources:
                    articles = self.intelligence_collector.collect_from_sources(sources)
                    total_articles += len(articles)
                    logger.info(f"Collected {len(articles)} think tank articles from {region}")
            
            # Collect from academic institutions
            academic_sources = self.intelligence_registry.get_sources_by_category('academic_institutions')
            if academic_sources:
                articles = self.intelligence_collector.collect_from_sources(academic_sources)
                total_articles += len(articles)
                logger.info(f"Collected {len(articles)} academic articles")
            
            # Collect from government sources
            gov_sources = self.intelligence_registry.get_sources_by_category('government_sources')
            if gov_sources:
                articles = self.intelligence_collector.collect_from_sources(gov_sources)
                total_articles += len(articles)
                logger.info(f"Collected {len(articles)} government articles")
            
            logger.info(f"Intelligence-only collection completed: {total_articles} articles")
            return total_articles
            
        except Exception as e:
            logger.error(f"Error in intelligence collection: {e}")
            return 0
def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Geopolitical Intelligence System - Automated OSINT Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --full-pipeline              # Run complete pipeline with global collection
  python main.py --full-pipeline --legacy-mode # Run pipeline with legacy collectors
  python main.py --global-collect             # Enhanced global collection (all languages)
  python main.py --global-collect --languages en es fr # Global collection (specific languages)
  python main.py --regional-collect americas  # Regional collection for Americas
  python main.py --intelligence-collect       # Intelligence sources only
  python main.py --collect                    # Legacy data collection
  python main.py --process                    # Process collected articles
  python main.py --report daily               # Generate daily report
  python main.py --report weekly              # Generate weekly report
  python main.py --schedule                   # Run scheduled tasks
  python main.py --status                     # Show system status
  python main.py --health-check               # Perform system health check
  python main.py --validate-data 7            # Validate data quality (last 7 days)
  python main.py --maintenance                # Run system maintenance
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--full-pipeline', action='store_true',
                       help='Run complete pipeline (collect, process, report)')
    group.add_argument('--collect', action='store_true',
                       help='Run data collection only')
    group.add_argument('--global-collect', action='store_true',
                       help='Run enhanced global news collection')
    group.add_argument('--regional-collect', choices=['americas', 'europe', 'asia_pacific', 'middle_east', 'africa'],
                       help='Run targeted regional collection')
    group.add_argument('--intelligence-collect', action='store_true',
                       help='Run intelligence sources collection only')
    group.add_argument('--process', action='store_true',
                       help='Run NLP processing only')
    group.add_argument('--report', choices=['daily', 'weekly'],
                       help='Generate reports (daily or weekly)')
    group.add_argument('--schedule', action='store_true',
                       help='Run scheduled tasks (continuous mode)')
    group.add_argument('--status', action='store_true',
                       help='Show system status')
    group.add_argument('--health-check', action='store_true',
                       help='Perform comprehensive system health check')
    group.add_argument('--validate-data', type=int, metavar='DAYS', nargs='?', const=7,
                       help='Validate data quality for specified days (default: 7)')
    group.add_argument('--maintenance', action='store_true',
                       help='Perform system maintenance tasks')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--languages', nargs='+', 
                       help='Specify languages for collection (e.g., --languages en es fr)')
    parser.add_argument('--include-intelligence', action='store_true', default=True,
                       help='Include intelligence sources in global collection')
    parser.add_argument('--legacy-mode', action='store_true',
                       help='Use legacy collectors instead of enhanced global collectors')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    
    # Initialize orchestrator
    orchestrator = GeopoliticalIntelligenceOrchestrator()
    
    try:
        if args.full_pipeline:
            success = orchestrator.run_full_pipeline(use_global_collection=not args.legacy_mode)
            sys.exit(0 if success else 1)
            
        elif args.collect:
            count = orchestrator.collect_data_only()
            print(f"Collected {count} articles")
            
        elif args.global_collect:
            count = orchestrator.run_global_collection(
                languages=args.languages, 
                include_intelligence=args.include_intelligence
            )
            print(f"Global collection completed: {count} articles")
            
        elif args.regional_collect:
            count = orchestrator.run_regional_collection(args.regional_collect)
            print(f"Regional collection for {args.regional_collect}: {count} articles")
            
        elif args.intelligence_collect:
            count = orchestrator.run_intelligence_only_collection()
            print(f"Intelligence collection completed: {count} articles")
            
        elif args.process:
            count = orchestrator.process_data_only()
            print(f"Processed {count} articles")
            
        elif args.report:
            reports = orchestrator.generate_reports_only(args.report)
            if reports:
                print(f"Generated {args.report} reports:")
                for format_type, file_path in reports.items():
                    print(f"  {format_type.upper()}: {file_path}")
            else:
                print("No reports generated")
                
        elif args.schedule:
            orchestrator.run_scheduled_tasks()
            
        elif args.status:
            orchestrator.show_status()
            
        elif args.health_check:
            health_status = orchestrator.health_check()
            overall_status = health_status.get('overall_status', 'unknown')
            sys.exit(0 if overall_status in ['healthy', 'degraded'] else 1)
            
        elif args.validate_data is not None:
            quality_report = orchestrator.validate_data_quality(days=args.validate_data)
            validation_rate = quality_report.get('validation_rate', 0)
            sys.exit(0 if validation_rate >= 80 else 1)
            
        elif args.maintenance:
            success = orchestrator.system_maintenance()
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
