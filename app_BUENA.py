"""
RiskMap - Aplicación Web Moderna Unificada
Punto de entrada único que ejecuta TODOS los procesos del sistema:
- Ingesta de datos RSS/OSINT
- Clasificación y procesamiento NLP
- Análisis histórico multivariable
- Dashboards interactivos
- APIs REST
- Monitoreo en tiempo real
- Alertas automáticas

NOTA: Patch de compatibilidad para ml_dtypes aplicado automáticamente
"""

# ===== PATCH DE COMPATIBILIDAD ML_DTYPES =====
import sys
import warnings

def patch_ml_dtypes():
    """Patch para compatibilidad con ml_dtypes"""
    try:
        import ml_dtypes
        import numpy as np
        
        missing_types = [
            'float8_e3m4', 'float8_e4m3', 'float8_e5m2',
            'float8_e8m0fnu', 'float8_e1m5', 'float8_e2m4',
            'float4_e2m1fn', 'int2', 'int4', 'int8',
            'uint2', 'uint4', 'uint8'  # Tipos unsigned int
        ]
        
        for dtype_name in missing_types:
            if not hasattr(ml_dtypes, dtype_name):
                # Usar tipos numpy apropiados directamente
                if 'float' in dtype_name:
                    setattr(ml_dtypes, dtype_name, np.float32)
                elif 'int' in dtype_name or 'uint' in dtype_name:
                    setattr(ml_dtypes, dtype_name, np.int32)
    except Exception:
        pass

# Aplicar patch inmediatamente
patch_ml_dtypes()

# ===== FIN DEL PATCH =====

import logging
import asyncio
import threading
import time
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Optional, Any
import signal
import atexit
import sqlite3
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] python-dotenv not installed. Environment variables from .env files won't be loaded.")
    pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Database configuration
def get_database_path():
    """Obtener la ruta de la base de datos desde variables de entorno"""
    db_path = os.getenv('DATABASE_PATH', './data/geopolitical_intel.db')
    return db_path

# Flask and web framework imports
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from flask_cors import CORS
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

# Import all system components
try:
    # Core orchestration
    from src.orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator
    from src.orchestration.task_scheduler import TaskScheduler
    
    # Enhanced historical analysis
    from src.analytics.enhanced_historical_orchestrator import EnhancedHistoricalOrchestrator
    
    # Dashboards
    from src.visualization.historical_dashboard import HistoricalDashboard
    from src.visualization.multivariate_dashboard import MultivariateRelationshipDashboard
    
    # API components
    from src.api.rest_status import create_api_blueprint
    
    # Utilities
    from src.utils.config import logger

except ImportError as e:
    print(f"[ERROR] Error importando módulos principales: {e}")
    print("[INFO] Verificando instalación de dependencias...")
    sys.exit(1)

# Computer Vision import
try:
    from src.vision.image_analysis import ImageInterestAnalyzer, analyze_article_image
    CV_AVAILABLE = True
    logger.info("✅ Computer Vision module loaded successfully")
except ImportError as e:
    CV_AVAILABLE = False
    logger.warning(f"⚠️ Computer Vision module not available: {e}")
    # Mock classes for when CV is not available
    class ImageInterestAnalyzer:
        def analyze_image_interest_areas(self, image_url, title=""):
            return {'error': 'Computer Vision not available'}
    
    def analyze_article_image(image_url, title=""):
        return {'error': 'Computer Vision not available'}

# External Intelligence Feeds import
try:
    from src.intelligence.external_feeds import ExternalIntelligenceFeeds
    from src.intelligence.integrated_analyzer import IntegratedGeopoliticalAnalyzer
    INTELLIGENCE_AVAILABLE = True
    logger.info("✅ External Intelligence Feeds module loaded successfully")
except ImportError as e:
    INTELLIGENCE_AVAILABLE = False
    logger.warning(f"⚠️ External Intelligence module not available: {e}")
    # Mock classes for when intelligence feeds are not available
    class ExternalIntelligenceFeeds:
        def __init__(self, db_path):
            pass
        def update_all_feeds(self, **kwargs):
            return {'acled': False, 'gdelt': False, 'gpr': False}
        def get_feed_statistics(self):
            return {'error': 'External intelligence not available'}
    
    class IntegratedGeopoliticalAnalyzer:
        def __init__(self, db_path, groq_client=None):
            pass
        def generate_comprehensive_geojson(self, **kwargs):
            return {'error': 'Integrated analyzer not available'}

# Satellite Integration import
try:
    from satellite_integration import (
        SatelliteIntegrationManager, 
        SentinelHubAPI, 
        PlanetAPI,
        SatelliteQueryParams,
        SatelliteImage
    )
    from dataclasses import asdict
    SATELLITE_AVAILABLE = True
    logger.info("✅ Satellite Integration module loaded successfully")
except ImportError as e:
    SATELLITE_AVAILABLE = False
    logger.warning(f"⚠️ Satellite Integration module not available: {e}")
    # Mock classes for when satellite integration is not available

# Automated Satellite Monitor import
try:
    from src.satellite.automated_satellite_monitor import (
        AutomatedSatelliteMonitor,
        ConflictZone,
        SatelliteImage as AutoSatelliteImage
    )
    AUTOMATED_SATELLITE_AVAILABLE = True
    logger.info("✅ Automated Satellite Monitor module loaded successfully")
except ImportError as e:
    AUTOMATED_SATELLITE_AVAILABLE = False
    logger.warning(f"⚠️ Automated Satellite Monitor not available: {e}")
    # Mock class for when automated satellite monitor is not available
    class AutomatedSatelliteMonitor:
        def __init__(self, db_path=None, config=None):
            pass
        def start_monitoring(self):
            logger.warning("Automated satellite monitoring not available")
        def stop_monitoring(self):
            pass
        def update_all_zones(self, priority_only=False):
            return {'processed': 0, 'updated': 0, 'errors': 1, 'skipped': 0}
        def get_monitoring_statistics(self):
            return {'error': 'Automated satellite monitoring not available'}
        def populate_zones_from_geojson_endpoint(self):
            return 0
    
    class ConflictZone:
        def __init__(self, *args, **kwargs):
            pass
    
    class AutoSatelliteImage:
        def __init__(self, *args, **kwargs):
            pass
    
    # Estas clases deberían estar en el bloque anterior de SATELLITE_AVAILABLE
    if not SATELLITE_AVAILABLE:
        class SatelliteIntegrationManager:
            def __init__(self):
                pass
            def search_images_for_geojson(self, geojson_data, **kwargs):
                return {'error': 'Satellite integration not available'}
            def get_satellite_statistics(self):
                return {'error': 'Satellite integration not available'}
        
        class SentinelHubAPI:
            def __init__(self, client_id=None, client_secret=None):
                pass
            def search_images(self, query_params):
                return []
        
        class PlanetAPI:
            def __init__(self, api_key=None):
                pass
            def search_images(self, query_params):
                return []
        
        def asdict(obj):
            return {'error': 'Satellite integration not available'}

class RiskMapUnifiedApplication:
    """
    Aplicación web unificada que ejecuta todos los componentes del sistema RiskMap
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Initialize Flask app
        self.flask_app = Flask(__name__, 
                              template_folder='src/web/templates',
                              static_folder='src/web/static')
        self.flask_app.secret_key = 'riskmap_unified_2024'
        CORS(self.flask_app)
        
        # System components
        self.core_orchestrator = None
        self.historical_orchestrator = None
        self.task_scheduler = None
        self.dash_apps = {}
        
        # Intelligence modules
        self.external_feeds = None
        self.integrated_analyzer = None
        
        # Satellite integration
        self.satellite_manager = None
        self.sentinelhub_api = None
        self.planet_api = None
        
        # Automated satellite monitoring
        self.automated_satellite_monitor = None
        
        # Intelligent data enrichment system
        self.enrichment_system = None
        
        # System state
        self.system_state = {
            'core_system_initialized': False,
            'historical_system_initialized': False,
            'external_intelligence_initialized': False,
            'satellite_system_initialized': False,
            'data_ingestion_running': False,
            'nlp_processing_running': False,
            'historical_analysis_running': False,
            'satellite_monitoring_running': False,
            'enrichment_system_initialized': False,
            'enrichment_running': False,
            'dashboards_ready': False,
            'api_ready': False,
            'last_ingestion': None,
            'last_processing': None,
            'last_analysis': None,
            'last_external_feeds_update': None,
            'last_satellite_search': None,
            'system_status': 'starting',
            'background_tasks': {},
            'alerts': [],
            'statistics': {
                'total_articles': 0,
                'processed_articles': 0,
                'risk_alerts': 0,
                'data_sources': 0,
                'external_feeds_count': 0,
                'satellite_images_found': 0,
                'sentinel_searches': 0,
                'planet_searches': 0,
                'articles_enriched': 0,
                'fields_completed': 0,
                'duplicates_detected': 0,
                'enrichment_errors': 0
            }
        }
        
        # Background threads
        self.background_threads = {}
        self.shutdown_event = threading.Event()
        
        # Setup application
        self._setup_logging()
        self._create_directories()
        self._setup_flask_routes()
        self._setup_signal_handlers()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto del sistema completo"""
        return {
            # Web server configuration
            'flask_port': 8050,
            'flask_host': '127.0.0.1',  # Cambiar a localhost para ser más claro
            'flask_debug': True,  # Activar debug para ver más información
            
            # Auto-initialization
            'auto_initialize': True,
            'auto_start_ingestion': True,
            'auto_start_processing': True,
            'auto_start_analysis': True,
            
            # Intervals (in hours)
            'ingestion_interval_hours': 1,
            'processing_interval_hours': 2,
            'analysis_interval_hours': 6,
            'maintenance_interval_hours': 24,
            
            # Satellite monitoring intervals
            'satellite_check_interval_hours': 4,
            'satellite_priority_interval_hours': 2,
            'satellite_auto_start': True,
            
            # Enrichment system settings
            'enrichment_auto_start': True,
            'enrichment_batch_size': 100,
            'enrichment_processing_interval_hours': 1,
            
            # Data directories
            'data_dir': 'datasets/historical',
            'multivariate_data_dir': 'datasets/multivariate',
            'model_dir': 'models/predictive',
            'output_dir': 'outputs/patterns',
            'relationships_output_dir': 'outputs/relationships',
            
            # Dashboard ports (integrated into Flask)
            'historical_dashboard_integrated': True,
            'multivariate_dashboard_integrated': True,
            
            # Features enabled
            'enable_rss_ingestion': True,
            'enable_nlp_processing': True,
            'enable_historical_analysis': True,
            'enable_real_time_alerts': True,
            'enable_api': True,
            'enable_background_tasks': True,
            
            # Performance
            'parallel_processing': True,
            'max_workers': 4,
            'cache_enabled': True
        }
    
    def _setup_logging(self):
        """Configurar logging del sistema"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'riskmap_unified.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Suppress verbose logs from external libraries
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        logger.info("Logging system initialized")
    
    def _create_directories(self):
        """Crear directorios necesarios"""
        directories = [
            'logs', 'datasets/historical', 'datasets/multivariate',
            'models/predictive', 'outputs/patterns', 'outputs/relationships',
            'src/web/templates', 'src/web/static', 'reports', 'data'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        logger.info("Directory structure created")
    
    def _setup_signal_handlers(self):
        """Configurar manejadores de señales para shutdown graceful"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.shutdown_event.set()
            self.stop_application()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        atexit.register(self.stop_application)
    
    def _setup_flask_routes(self):
        """Configurar todas las rutas de Flask"""
        
        @self.flask_app.route('/')
        def index():
            """Página principal unificada"""
            return render_template('dashboard_BUENO.html', 
                                 system_state=self.system_state,
                                 config=self.config)
        
        @self.flask_app.route('/dashboard')
        def dashboard_redirect():
            """Redirigir al dashboard histórico integrado"""
            return redirect('/dash/historical/')
        
        @self.flask_app.route('/multivariate')
        def multivariate_redirect():
            """Redirigir al dashboard multivariable integrado"""
            return redirect('/dash/multivariate/')
        
        @self.flask_app.route('/api/system/status')
        def api_system_status():
            """API: Estado completo del sistema"""
            try:
                # Get detailed status from all components
                detailed_status = {}
                
                if self.core_orchestrator:
                    try:
                        core_status = self.core_orchestrator.health_check()
                        detailed_status['core_system'] = core_status
                    except Exception as e:
                        detailed_status['core_system'] = {'error': str(e)}
                
                if self.historical_orchestrator:
                    try:
                        historical_status = asyncio.run(
                            self.historical_orchestrator.get_enhanced_system_status()
                        )
                        detailed_status['historical_system'] = historical_status
                    except Exception as e:
                        detailed_status['historical_system'] = {'error': str(e)}
                
                # Add external intelligence status
                if INTELLIGENCE_AVAILABLE and self.external_feeds:
                    try:
                        feeds_stats = self.external_feeds.get_feed_statistics()
                        detailed_status['external_intelligence'] = {
                            'available': True,
                            'statistics': feeds_stats,
                            'last_update': self.system_state.get('last_external_feeds_update')
                        }
                    except Exception as e:
                        detailed_status['external_intelligence'] = {'available': True, 'error': str(e)}
                else:
                    detailed_status['external_intelligence'] = {'available': False}
                
                return jsonify({
                    'success': True,
                    'system_state': self.system_state,
                    'detailed_status': detailed_status,
                    "html": render_template('dashboard_BUENO.html', 
                                            system_state=self.system_state,
                                            config=self.config),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.flask_app.route('/api/system/initialize', methods=['POST'])
        def api_initialize_system():
            """API: Inicializar todo el sistema"""
            try:
                if not self.system_state['core_system_initialized']:
                    self._run_background_task('initialize_system', self._initialize_all_systems)
                    return jsonify({
                        'success': True,
                        'message': 'System initialization started in background'
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'System already initialized'
                    })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.flask_app.route('/api/ingestion/start', methods=['POST'])
        def api_start_ingestion():
            """API: Iniciar ingesta de datos"""
            try:
                if not self.system_state['data_ingestion_running']:
                    self._run_background_task('start_ingestion', self._start_data_ingestion)
                    return jsonify({
                        'success': True,
                        'message': 'Data ingestion started'
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'Data ingestion already running'
                    })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.flask_app.route('/api/processing/start', methods=['POST'])
        def api_start_processing():
            """API: Iniciar procesamiento NLP"""
            try:
                if not self.system_state['nlp_processing_running']:
                    self._run_background_task('start_processing', self._start_nlp_processing)
                    return jsonify({
                        'success': True,
                        'message': 'NLP processing started'
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'NLP processing already running'
                    })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.flask_app.route('/api/analysis/start', methods=['POST'])
        def api_start_analysis():
            """API: Iniciar análisis histórico"""
            try:
                if not self.system_state['historical_analysis_running']:
                    self._run_background_task('start_analysis', self._start_historical_analysis)
                    return jsonify({
                        'success': True,
                        'message': 'Historical analysis started'
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'Historical analysis already running'
                    })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.flask_app.route('/api/statistics')
        def api_statistics():
            """API: Estadísticas del sistema"""
            try:
                # Update statistics from database
                self._update_statistics()
                return jsonify({
                    'success': True,
                    'statistics': self.system_state['statistics'],
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.flask_app.route('/api/alerts')
        def api_alerts():
            """API: Alertas del sistema"""
            return jsonify({
                'success': True,
                'alerts': self.system_state['alerts'][-50:],  # Last 50 alerts
                'count': len(self.system_state['alerts'])
            })
        
        @self.flask_app.route('/api/groq/analysis')
        def api_groq_analysis():
            """API: Análisis geopolítico con Groq"""
            try:
                # Obtener artículos de la base de datos
                articles = self.get_top_articles_from_db(20)
                
                # Generar análisis con Groq
                analysis = self._generate_groq_geopolitical_analysis(articles)
                
                return jsonify({
                    'success': True,
                    'analysis': analysis,
                    'articles_count': len(articles),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error in Groq analysis endpoint: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'fallback_analysis': self._get_structured_fallback_analysis([])
                })
        
        @self.flask_app.route('/api/groq/test')
        def api_groq_test():
            """API: Test de conectividad Groq"""
            try:
                from groq import Groq
                
                groq_api_key = os.getenv('GROQ_API_KEY')
                if not groq_api_key:
                    return jsonify({
                        'success': False,
                        'error': 'GROQ_API_KEY no encontrada en variables de entorno'
                    })
                
                client = Groq(api_key=groq_api_key)
                
                # Test simple
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": "Responde brevemente: ¿Funciona la API de Groq?"
                        }
                    ],
                    model="llama-3.1-8b-instant",
                    max_tokens=50
                )
                
                response_content = chat_completion.choices[0].message.content
                
                return jsonify({
                    'success': True,
                    'message': 'Groq API funcionando correctamente',
                    'test_response': response_content,
                    'api_key_status': f"Configurada: {groq_api_key[:10]}..."
                })
                
            except ImportError:
                return jsonify({
                    'success': False,
                    'error': 'Librería Groq no disponible'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Error probando Groq API: {str(e)}'
                })
        
        @self.flask_app.route('/api/background/tasks')
        def api_background_tasks():
            """API: Estado de tareas en background"""
            return jsonify({
                'success': True,
                'tasks': self.system_state['background_tasks']
            })

        @self.flask_app.route('/api/ai/geopolitical-analysis', methods=['POST'])
        def api_geopolitical_analysis():
            """API: Generar análisis geopolítico con IA"""
            try:
                data = request.get_json()
                articles = data.get('articles', [])
                
                # Generate the geopolitical analysis using AI
                analysis = self._generate_geopolitical_analysis(articles)
                
                return jsonify({
                    'success': True,
                    'analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error generating geopolitical analysis: {e}")
                return jsonify({
                    'success': False, 
                    'error': str(e),
                    'analysis': 'Error al generar el análisis geopolítico. Por favor, inténtelo de nuevo.'
                })
        
        @self.flask_app.route('/api/generate-ai-analysis', methods=['POST'])
        def generate_groq_ai_analysis():
            """
            API: Generar análisis geopolítico estructurado con Groq IA
            """
            try:
                data = request.get_json() or {}
                
                # Obtener artículos desde la base de datos o usar los proporcionados
                articles = data.get('articles')
                if not articles:
                    articles = self.get_top_articles_from_db(limit=20)
                
                if not articles:
                    return jsonify({
                        'error': 'No se encontraron artículos para analizar',
                        'success': False
                    }), 400
                
                # Determinar tipo de análisis
                analysis_type = data.get('analysis_type', 'standard')
                
                if analysis_type == 'structured':
                    analysis_result = self._generate_groq_geopolitical_analysis(articles)
                else:
                    # Usar análisis de texto simple
                    context = self._prepare_articles_context(articles)
                    analysis_text = self._generate_groq_analysis(f"Analiza estos artículos: {context}")
                    analysis_result = {
                        'title': 'Análisis Geopolítico Global',
                        'subtitle': 'Perspectivas actuales sobre eventos internacionales',
                        'content': analysis_text,
                        'sources_count': len(articles)
                    }
                
                # Estructurar respuesta
                response = {
                    'success': True,
                    'analysis': analysis_result,
                    'metadata': {
                        'articles_analyzed': len(articles),
                        'generation_time': datetime.now().isoformat(),
                        'endpoint_version': '1.0',
                        'analysis_type': analysis_type,
                        'ai_model': 'Groq Llama-3.1-8b-instant'
                    }
                }
                
                logger.info(f"✅ Análisis geopolítico Groq generado: {len(articles)} artículos procesados")
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"❌ Error en endpoint de análisis Groq: {e}")
                return jsonify({
                    'error': f'Error generando análisis: {str(e)}',
                    'success': False
                }), 500
        
        @self.flask_app.route('/settings')
        def settings():
            """Página de configuración"""
            return render_template('settings.html',
                                 config=self.config,
                                 system_state=self.system_state)
        
        @self.flask_app.route('/logs')
        def logs():
            """Página de logs del sistema"""
            try:
                log_file = Path('logs/riskmap_unified.log')
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_content = f.read().split('\n')[-1000:]  # Last 1000 lines
                else:
                    log_content = ["No log file found"]
                
                return render_template('logs.html', 
                                     log_content=log_content,
                                     system_state=self.system_state)
            except Exception as e:
                return f"Error reading logs: {e}"
        
        # ========================================
        # MAIN NAVIGATION ROUTES
        # ========================================
        
        @self.flask_app.route('/news-analysis')
        def news_analysis():
            """Página de análisis de noticias (redirigir a dashboard principal)"""
            return redirect('/')
        
        @self.flask_app.route('/conflict-monitoring')
        def conflict_monitoring():
            """Página de monitoreo de conflictos"""
            return render_template('conflict_monitoring.html',
                                 system_state=self.system_state,
                                 config=self.config)
        
        @self.flask_app.route('/trends-analysis')
        def trends_analysis():
            """Página de análisis de tendencias"""
            return render_template('trends_analysis.html',
                                 system_state=self.system_state,
                                 config=self.config)
        
        @self.flask_app.route('/early-warning')
        def early_warning():
            """Página de alertas tempranas"""
            return render_template('early_warning.html',
                                 system_state=self.system_state,
                                 config=self.config)
        
        @self.flask_app.route('/executive-reports')
        def executive_reports():
            """Página de reportes ejecutivos"""
            return render_template('executive_reports.html',
                                 system_state=self.system_state,
                                 config=self.config)
        
        @self.flask_app.route('/satellite-analysis')
        def satellite_analysis():
            """Página de análisis satelital"""
            return render_template('satellite_analysis.html',
                                 system_state=self.system_state,
                                 config=self.config)
        
        @self.flask_app.route('/video-surveillance')
        def video_surveillance():
            """Página de video vigilancia"""
            return render_template('video_surveillance.html',
                                 system_state=self.system_state,
                                 config=self.config)
        
        @self.flask_app.route('/historical-analysis')
        def historical_analysis():
            """Página de análisis histórico"""
            return render_template('historical_analysis.html',
                                 system_state=self.system_state,
                                 config=self.config)
        
        # ========================================
        # API ENDPOINTS
        # ========================================
        
        @self.flask_app.route('/api/articles')
        def get_articles():
            """Obtener artículos organizados inteligentemente para el dashboard usando análisis CV"""
            try:
                # Importar el sistema de mosaico inteligente
                from src.dashboard.smart_mosaic_layout import get_smart_mosaic_articles
                
                # Obtener parámetros de consulta
                limit = request.args.get('limit', 25, type=int)
                use_smart_layout = request.args.get('smart_layout', 'true').lower() == 'true'
                
                if use_smart_layout:
                    # Usar el sistema inteligente de posicionamiento
                    smart_articles = get_smart_mosaic_articles(limit)
                    
                    # Aplanar la estructura para compatibilidad con el frontend
                    dashboard_articles = []
                    
                    # Agregar artículos en orden de prioridad
                    for position in ['hero', 'featured', 'standard', 'thumbnail']:
                        articles_in_position = smart_articles.get(position, [])
                        dashboard_articles.extend(articles_in_position)
                    
                    # Limitar al número solicitado
                    dashboard_articles = dashboard_articles[:limit]
                    
                    return jsonify({
                        'success': True,
                        'articles': dashboard_articles,
                        'total': len(dashboard_articles),
                        'smart_layout': True,
                        'layout_data': smart_articles,
                        'positioning_info': 'Artículos posicionados usando análisis CV inteligente'
                    })
                
                # Fallback al método original si smart_layout=false
                limit = request.args.get('limit', 20, type=int)
                offset = request.args.get('offset', 0, type=int)
                
                # Primero obtener el artículo héroe para excluirlo
                hero_articles = self.get_top_articles_from_db(1)
                hero_id = hero_articles[0]['id'] if hero_articles else None
                
                # Obtener artículos de la base de datos, excluyendo el héroe
                all_articles = self.get_top_articles_from_db(limit + offset + 1)  # +1 para compensar el héroe excluido
                
                # Filtrar el artículo héroe
                articles = [article for article in all_articles if article['id'] != hero_id]
                
                # Aplicar offset si es necesario
                if offset > 0 and len(articles) > offset:
                    articles = articles[offset:offset + limit]
                else:
                    articles = articles[:limit]
                
                # Convertir a formato para el dashboard
                dashboard_articles = []
                for article in articles:
                    # Mapear risk_level a formato esperado por el dashboard
                    risk_mapping = {
                        'high': 'high',
                        'medium': 'medium', 
                        'low': 'low',
                        'unknown': 'low'
                    }
                    
                    risk_level = risk_mapping.get(article.get('risk_level', 'unknown'), 'low')
                    
                    dashboard_article = {
                        'id': article.get('id'),
                        'title': article.get('title', 'Sin título'),
                        'content': article.get('content', 'Sin contenido'),
                        'location': article.get('location', 'Global'),
                        'country': article.get('country', 'Global'),
                        'region': article.get('region', 'Internacional'),
                        'risk': risk_level,
                        'risk_level': risk_level,
                        'risk_score': article.get('risk_score', 0.0),
                        'source': article.get('source', 'Fuente desconocida'),
                        'published_at': article.get('published_at'),
                        'summary': article.get('summary'),
                        'url': article.get('url'),
                        'image': article.get('image_url') or f"https://picsum.photos/400/300?random={article.get('id', 1)}"  # Imagen real o placeholder
                    }
                    dashboard_articles.append(dashboard_article)
                
                return jsonify({
                    'success': True,
                    'articles': dashboard_articles,
                    'total': len(dashboard_articles),
                    'offset': offset,
                    'limit': limit,
                    'smart_layout': False
                })
                
            except Exception as e:
                logger.error(f"Error en endpoint /api/articles: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'articles': []
                }), 500
        
        @self.flask_app.route('/api/hero-article')
        def get_hero_article():
            """Obtener el artículo héroe (más importante) de la base de datos"""
            try:
                # Obtener el artículo con mayor riesgo
                articles = self.get_top_articles_from_db(1)
                
                if not articles:
                    # Artículo de fallback
                    return jsonify({
                        'success': True,
                        'article': {
                            'title': 'Análisis geopolítico en curso',
                            'text': 'El sistema está procesando los últimos desarrollos geopolíticos para proporcionar análisis actualizados.',
                            'location': 'Global',
                            'risk': 'medium',
                            'image': 'https://picsum.photos/1920/800?random=hero'
                        }
                    })
                
                article = articles[0]
                
                # Mapear risk_level a formato esperado
                risk_mapping = {
                    'high': 'high',
                    'medium': 'medium',
                    'low': 'low', 
                    'unknown': 'medium'
                }
                
                hero_article = {
                    'title': article.get('title', 'Desarrollo geopolítico importante'),
                    'text': article.get('summary') or article.get('content', '')[:300] + '...',
                    'location': article.get('location') or article.get('country') or article.get('region') or 'Global',
                    'risk': risk_mapping.get(article.get('risk_level', 'unknown'), 'medium'),
                    'image': article.get('image_url') or f"https://picsum.photos/1920/800?random=hero{article.get('id', 1)}"
                }
                
                return jsonify({
                    'success': True,
                    'article': hero_article
                })
                
            except Exception as e:
                logger.error(f"Error en endpoint /api/hero-article: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'article': {
                        'title': 'Error al cargar artículo principal',
                        'text': 'No se pudo cargar el contenido principal.',
                        'location': 'Sistema',
                        'risk': 'low',
                        'image': 'https://picsum.photos/1920/800?random=error'
                    }
                }), 500
        
        @self.flask_app.route('/api/images/extract', methods=['POST'])
        def api_extract_images():
            """API: Extraer imágenes para artículos sin imagen"""
            try:
                data = request.get_json() or {}
                limit = data.get('limit', 20)
                
                # Obtener artículos sin imagen
                articles_without_images = self.get_articles_without_images(limit)
                
                if not articles_without_images:
                    return jsonify({
                        'success': True,
                        'message': 'No hay artículos sin imagen para procesar',
                        'processed': 0,
                        'errors': 0
                    })
                
                # Ejecutar extracción en background
                self._run_background_task('extract_images', self._extract_images_background, articles_without_images)
                
                return jsonify({
                    'success': True,
                    'message': f'Iniciada extracción de imágenes para {len(articles_without_images)} artículos',
                    'articles_to_process': len(articles_without_images)
                })
                
            except Exception as e:
                logger.error(f"Error en endpoint de extracción de imágenes: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/images/status')
        def api_images_status():
            """API: Estado de las imágenes en la base de datos"""
            try:
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Total de artículos
                    cursor.execute("SELECT COUNT(*) FROM articles")
                    total_articles = cursor.fetchone()[0]
                    
                    # Artículos con imagen
                    cursor.execute("""
                        SELECT COUNT(*) FROM articles 
                        WHERE image_url IS NOT NULL 
                        AND image_url != '' 
                        AND image_url NOT LIKE '%placeholder%' 
                        AND image_url NOT LIKE '%picsum%'
                    """)
                    articles_with_images = cursor.fetchone()[0]
                    
                    # Artículos sin imagen
                    articles_without_images = total_articles - articles_with_images
                    
                    # Porcentaje de cobertura
                    coverage_percentage = (articles_with_images / total_articles * 100) if total_articles > 0 else 0
                
                return jsonify({
                    'success': True,
                    'statistics': {
                        'total_articles': total_articles,
                        'articles_with_images': articles_with_images,
                        'articles_without_images': articles_without_images,
                        'coverage_percentage': round(coverage_percentage, 2)
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo estado de imágenes: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/images/extract-single', methods=['POST'])
        def api_extract_single_image():
            """API: Extraer imagen para un artículo específico"""
            try:
                data = request.get_json()
                article_id = data.get('article_id')
                
                if not article_id:
                    return jsonify({
                        'success': False,
                        'error': 'article_id requerido'
                    }), 400
                
                # Obtener datos del artículo
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, title, url FROM articles WHERE id = ?", (article_id,))
                    article_data = cursor.fetchone()
                
                if not article_data:
                    return jsonify({
                        'success': False,
                        'error': 'Artículo no encontrado'
                    }), 404
                
                article_id, title, url = article_data
                
                if not url:
                    return jsonify({
                        'success': False,
                        'error': 'El artículo no tiene URL'
                    }), 400
                
                # Extraer imagen
                image_path = self.extract_image_from_url(url, article_id, title)
                
                if image_path:
                    # Actualizar base de datos
                    if self.update_article_image(article_id, image_path):
                        return jsonify({
                            'success': True,
                            'message': 'Imagen extraída y guardada exitosamente',
                            'image_path': image_path
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Error actualizando la base de datos'
                        }), 500
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No se pudo extraer imagen del artículo'
                    }), 500
                
            except Exception as e:
                logger.error(f"Error extrayendo imagen individual: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/images/ensure-all', methods=['POST'])
        def api_ensure_all_images():
            """API: Asegurar que TODOS los artículos tengan imágenes de calidad"""
            try:
                data = request.get_json() or {}
                batch_size = data.get('batch_size', 20)
                
                # Ejecutar proceso masivo en background
                self._run_background_task('ensure_all_images', self.ensure_all_articles_have_images, batch_size)
                
                return jsonify({
                    'success': True,
                    'message': 'Iniciado proceso masivo para asegurar que todos los artículos tengan imágenes de calidad',
                    'batch_size': batch_size
                })
                
            except Exception as e:
                logger.error(f"Error en endpoint de proceso masivo: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/images/quality-check', methods=['POST'])
        def api_image_quality_check():
            """API: Verificar y mejorar la calidad de imágenes existentes"""
            try:
                data = request.get_json() or {}
                limit = data.get('limit', 50)
                
                # Obtener artículos con imágenes que podrían necesitar mejora
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, title, url, image_url
                        FROM articles 
                        WHERE image_url IS NOT NULL 
                        AND image_url != ''
                        AND (
                            image_url LIKE '%300x200%'
                            OR image_url LIKE '%400x300%'
                            OR image_url LIKE '%placeholder%'
                            OR image_url LIKE '%via.placeholder%'
                        )
                        AND url IS NOT NULL 
                        AND url != ''
                        ORDER BY id DESC
                        LIMIT ?
                    """, (limit,))
                    articles_to_improve = cursor.fetchall()
                
                if not articles_to_improve:
                    return jsonify({
                        'success': True,
                        'message': 'No se encontraron artículos con imágenes de baja calidad',
                        'articles_to_improve': 0
                    })
                
                # Ejecutar mejora en background
                self._run_background_task('improve_image_quality', self._improve_images_quality, articles_to_improve)
                
                return jsonify({
                    'success': True,
                    'message': f'Iniciada mejora de calidad para {len(articles_to_improve)} imágenes',
                    'articles_to_improve': len(articles_to_improve)
                })
                
            except Exception as e:
                logger.error(f"Error en verificación de calidad: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ========================================
        # ANALYTICS API ENDPOINTS
        # ========================================
        
        @self.flask_app.route('/api/analytics/conflicts')
        def api_analytics_conflicts():
            """API: Obtener datos de conflictos para analytics"""
            try:
                timeframe = request.args.get('timeframe', '7d')
                
                # Convertir timeframe a días
                timeframe_days = {
                    '24h': 1,
                    '7d': 7,
                    '30d': 30,
                    '90d': 90
                }.get(timeframe, 7)
                
                # Calcular fecha límite
                cutoff_date = datetime.now() - timedelta(days=timeframe_days)
                
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Obtener artículos con análisis de riesgo en el período
                    cursor.execute("""
                        SELECT 
                            id, title, key_locations, country, region, risk_level, conflict_type, 
                            published_at, url, sentiment_score
                        FROM articles 
                        WHERE published_at >= ? 
                        AND (
                            risk_level IN ('high', 'medium') 
                            OR sentiment_score < -0.3
                            OR conflict_type IS NOT NULL
                        )
                        AND (key_locations IS NOT NULL OR country IS NOT NULL OR region IS NOT NULL)
                        ORDER BY published_at DESC
                    """, (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
                    
                    conflicts = cursor.fetchall()
                    
                    # Formatear datos de conflictos
                    formatted_conflicts = []
                    for conflict in conflicts:
                        # Create location from available fields: key_locations, country, region
                        key_locations = conflict[2] or ''
                        country = conflict[3] or ''
                        region = conflict[4] or ''
                        
                        # Priority: key_locations > country > region > 'Global'
                        location = key_locations or country or region or 'Global'
                        
                        formatted_conflicts.append({
                            'id': conflict[0],
                            'title': conflict[1],
                            'location': location,
                            'key_locations': key_locations,
                            'country': country,
                            'region': region,
                            'risk_level': conflict[5] or 'unknown',
                            'category': conflict[6] or 'general',
                            'published_date': conflict[7],
                            'url': conflict[8],
                            'sentiment_score': conflict[9] or 0,
                            'latitude': None,  # Not available in current schema
                            'longitude': None,  # Not available in current schema
                        })
                    
                    # Calcular estadísticas
                    statistics = {
                        'total_conflicts': len(formatted_conflicts),
                        'high_risk': len([c for c in formatted_conflicts if c['risk_level'] == 'high']),
                        'medium_risk': len([c for c in formatted_conflicts if c['risk_level'] == 'medium']),
                        'total_sources': cursor.execute("SELECT COUNT(DISTINCT source) FROM articles WHERE source IS NOT NULL").fetchone()[0],
                        'active_sources': cursor.execute("SELECT COUNT(DISTINCT source) FROM articles WHERE published_at >= ? AND source IS NOT NULL", (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0],
                        'reliability_score': 78  # Score simulado
                    }
                
                return jsonify({
                    'success': True,
                    'conflicts': formatted_conflicts,
                    'statistics': statistics,
                    'timeframe': timeframe,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo datos de conflictos: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/analytics/geojson')
        def api_analytics_geojson():
            """API: Generar GeoJSON enriquecido de zonas de conflicto"""
            try:
                timeframe = request.args.get('timeframe', '7d')
                include_external = request.args.get('include_external', 'true').lower() == 'true'
                satellite_optimized = request.args.get('satellite_optimized', 'true').lower() == 'true'
                
                # Si tenemos el analizador integrado disponible, usarlo
                if INTELLIGENCE_AVAILABLE and self.integrated_analyzer:
                    try:
                        # Convertir timeframe a días
                        timeframe_days = {
                            '24h': 1,
                            '7d': 7,
                            '30d': 30,
                            '90d': 90
                        }.get(timeframe, 7)
                        
                        # Generar GeoJSON enriquecido con todas las fuentes
                        comprehensive_geojson = self.integrated_analyzer.generate_comprehensive_geojson(
                            timeframe_days=timeframe_days,
                            include_predictions=include_external
                        )
                        
                        # Si se solicita optimización satelital y está disponible, enriquecer con datos satelitales
                        if satellite_optimized and SATELLITE_AVAILABLE and self.satellite_manager:
                            try:
                                logger.info("🛰️ Enriqueciendo GeoJSON con datos satelitales...")
                                
                                # Configuración de búsqueda satelital
                                satellite_config = {
                                    'days_back': min(timeframe_days, 30),  # Limitar búsqueda satelital
                                    'cloud_cover_max': 20,
                                    'collection': 'sentinel-2-l2a',
                                    'buffer_km': 15
                                }
                                
                                # Buscar imágenes satelitales para las ubicaciones del GeoJSON
                                satellite_results = self.satellite_manager.search_images_for_geojson(
                                    comprehensive_geojson, **satellite_config
                                )
                                
                                # Añadir información satelital a las features
                                if satellite_results:
                                    features_updated = 0
                                    for feature in comprehensive_geojson.get('features', []):
                                        feature_id = str(feature.get('properties', {}).get('id', ''))
                                        if feature_id in satellite_results:
                                            satellite_data = satellite_results[feature_id]
                                            # Añadir información satelital a las propiedades
                                            feature['properties']['satellite_data'] = {
                                                'images_found': len(satellite_data.get('images', [])),
                                                'latest_image_date': satellite_data.get('latest_date'),
                                                'average_cloud_cover': satellite_data.get('avg_cloud_cover'),
                                                'provider': satellite_data.get('provider', 'SentinelHub')
                                            }
                                            features_updated += 1
                                    
                                    # Actualizar metadatos
                                    if 'metadata' not in comprehensive_geojson:
                                        comprehensive_geojson['metadata'] = {}
                                    comprehensive_geojson['metadata']['satellite_enhanced'] = True
                                    comprehensive_geojson['metadata']['satellite_features_updated'] = features_updated
                                    comprehensive_geojson['metadata']['satellite_config'] = satellite_config
                                    
                                    # Actualizar estadísticas del sistema
                                    total_satellite_images = sum(
                                        len(result.get('images', [])) 
                                        for result in satellite_results.values()
                                    )
                                    self.system_state['statistics']['satellite_images_found'] += total_satellite_images
                                    self.system_state['last_satellite_search'] = datetime.now().isoformat()
                                    
                                    logger.info(f"✅ GeoJSON enriquecido con {total_satellite_images} imágenes satelitales para {features_updated} ubicaciones")
                                
                            except Exception as satellite_error:
                                logger.warning(f"Error enriqueciendo con datos satelitales: {satellite_error}")
                                # Continuar sin datos satelitales
                        
                        # Actualizar estadísticas del sistema
                        if comprehensive_geojson.get('metadata'):
                            self.system_state['last_external_feeds_update'] = datetime.now().isoformat()
                            self.system_state['statistics']['external_feeds_count'] = comprehensive_geojson['metadata'].get('external_sources_count', 0)
                        
                        data_sources = ['news_analysis', 'groq_ai']
                        if include_external:
                            data_sources.append('external_feeds')
                        if satellite_optimized and SATELLITE_AVAILABLE:
                            data_sources.append('satellite_imagery')
                        
                        return jsonify({
                            'success': True,
                            'geojson': comprehensive_geojson,
                            'enhanced': True,
                            'data_sources': data_sources,
                            'satellite_optimized': satellite_optimized,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error using integrated analyzer, falling back to basic GeoJSON: {e}")
                        # Fallback al método básico si hay error
                
                # Fallback: método original usando datos de conflictos básicos
                conflicts_response = api_analytics_conflicts()
                conflicts_data = conflicts_response.get_json()
                
                if not conflicts_data.get('success'):
                    return jsonify({
                        'success': False,
                        'error': 'Error obteniendo datos de conflictos'
                    }), 500
                
                conflicts = conflicts_data.get('conflicts', [])
                
                # Generar GeoJSON básico
                features = []
                for conflict in conflicts:
                    if conflict.get('latitude') and conflict.get('longitude'):
                        feature = {
                            "type": "Feature",
                            "properties": {
                                "id": conflict['id'],
                                "name": conflict['location'],
                                "title": conflict['title'],
                                "risk_level": conflict['risk_level'],
                                "conflict_type": conflict['category'],
                                "intensity": abs(conflict.get('sentiment_score', 0)) if conflict.get('sentiment_score') else 0.5,
                                "articles_count": 1,
                                "sentiment_score": conflict.get('sentiment_score', 0),
                                "published_date": conflict['published_date'],
                                "url": conflict['url']
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": [float(conflict['longitude']), float(conflict['latitude'])]
                            }
                        }
                        features.append(feature)
                
                # Si no hay datos reales, usar datos mock
                if not features:
                    features = self._generate_mock_geojson_features()
                
                geojson = {
                    "type": "FeatureCollection",
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "timeframe": timeframe,
                        "total_features": len(features),
                        "data_source": "RiskMap AI Analytics (Basic)"
                    },
                    "features": features
                }
                
                return jsonify({
                    'success': True,
                    'geojson': geojson,
                    'enhanced': False,
                    'data_sources': ['news_analysis'],
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error generando GeoJSON: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'geojson': self._generate_mock_geojson()
                }), 500
        
        @self.flask_app.route('/api/analytics/save-geojson', methods=['POST'])
        def api_save_geojson():
            """API: Guardar GeoJSON internamente para uso del sistema"""
            try:
                data = request.get_json()
                geojson_data = data.get('geojson')
                timestamp = data.get('timestamp')
                
                if not geojson_data:
                    return jsonify({
                        'success': False,
                        'error': 'No GeoJSON data provided'
                    }), 400
                
                # Crear directorio si no existe
                geojson_dir = Path('data/geojson')
                geojson_dir.mkdir(exist_ok=True)
                
                # Guardar archivo con timestamp
                filename = f"conflict_zones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson"
                file_path = geojson_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(geojson_data, f, indent=2, ensure_ascii=False)
                
                # También guardar la versión más reciente
                latest_path = geojson_dir / 'conflict_zones_latest.geojson'
                with open(latest_path, 'w', encoding='utf-8') as f:
                    json.dump(geojson_data, f, indent=2, ensure_ascii=False)
                
                # Guardar metadatos en base de datos
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Crear tabla si no existe
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS geojson_exports (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            filename TEXT NOT NULL,
                            file_path TEXT NOT NULL,
                            timestamp TEXT NOT NULL,
                            features_count INTEGER,
                            export_type TEXT DEFAULT 'auto',
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Insertar registro
                    features_count = len(geojson_data.get('features', []))
                    cursor.execute("""
                        INSERT INTO geojson_exports 
                        (filename, file_path, timestamp, features_count, export_type)
                        VALUES (?, ?, ?, ?, 'auto')
                    """, (filename, str(file_path), timestamp, features_count))
                    
                    conn.commit()
                
                logger.info(f"GeoJSON saved internally: {filename} ({features_count} features)")
                
                return jsonify({
                    'success': True,
                    'message': 'GeoJSON saved internally',
                    'filename': filename,
                    'features_count': features_count,
                    'timestamp': timestamp
                })
                
            except Exception as e:
                logger.error(f"Error saving GeoJSON internally: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
            }), 500
        
        @self.flask_app.route('/api/analytics/trends')
        def api_analytics_trends():
            """API: Obtener tendencias temporales para analytics"""
            try:
                days = int(request.args.get('days', 7))
                
                db_path = get_database_path()
                trends = []
                
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Obtener datos por día para los últimos N días
                    for i in range(days):
                        date = datetime.now() - timedelta(days=i)
                        date_str = date.strftime('%Y-%m-%d')
                        
                        # Contar artículos por nivel de riesgo ese día
                        cursor.execute("""
                            SELECT 
                                risk_level,
                                COUNT(*) as count
                            FROM articles 
                            WHERE DATE(published_date) = ?
                            GROUP BY risk_level
                        """, (date_str,))
                        
                        day_data = {
                            'date': date_str,
                            'high_risk': 0,
                            'medium_risk': 0,
                            'low_risk': 0,
                            'total': 0
                        }
                        
                        for row in cursor.fetchall():
                            risk_level, count = row
                            if risk_level == 'high':
                                day_data['high_risk'] = count
                            elif risk_level == 'medium':
                                day_data['medium_risk'] = count
                            elif risk_level == 'low':
                                day_data['low_risk'] = count
                            day_data['total'] += count
                        
                        trends.insert(0, day_data)  # Insertar al principio para orden cronológico
                
                return jsonify({
                    'success': True,
                    'trends': trends,
                    'days': days,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo tendencias: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ========================================
        # EXTERNAL INTELLIGENCE API ENDPOINTS
        # ========================================
        
        @self.flask_app.route('/api/intelligence/feeds/update')
        def api_update_external_feeds():
            """API: Actualizar feeds externos de inteligencia"""
            try:
                if not INTELLIGENCE_AVAILABLE or not self.external_feeds:
                    return jsonify({
                        'success': False,
                        'error': 'External intelligence feeds not available'
                    }), 503
                
                force_update = request.args.get('force', 'false').lower() == 'true'
                
                # Actualizar todos los feeds
                update_results = self.external_feeds.update_all_feeds(
                    force_update=force_update
                )
                
                # Actualizar timestamp del sistema
                self.system_state['last_external_feeds_update'] = datetime.now().isoformat()
                
                return jsonify({
                    'success': True,
                    'results': update_results,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error actualizando feeds externos: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/intelligence/feeds/status')
        def api_external_feeds_status():
            """API: Obtener estado de feeds externos"""
            try:
                if not INTELLIGENCE_AVAILABLE or not self.external_feeds:
                    return jsonify({
                        'success': False,
                        'error': 'External intelligence feeds not available'
                    }), 503
                
                # Obtener estadísticas de feeds
                stats = self.external_feeds.get_feed_statistics()
                
                return jsonify({
                    'success': True,
                    'statistics': stats,
                    'last_update': self.system_state.get('last_external_feeds_update'),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo estado de feeds: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/intelligence/hotspots')
        def api_intelligence_hotspots():
            """API: Obtener hotspots de inteligencia externa"""
            try:
                if not INTELLIGENCE_AVAILABLE or not self.external_feeds:
                    return jsonify({
                        'success': False,
                        'error': 'External intelligence feeds not available'
                    }), 503
                
                days = int(request.args.get('days', 7))
                min_events = int(request.args.get('min_events', 3))
                
                # Obtener hotspots
                hotspots = self.external_feeds.get_conflict_hotspots(
                    days_back=days,
                    min_events_threshold=min_events
                )
                
                return jsonify({
                    'success': True,
                    'hotspots': hotspots,
                    'parameters': {
                        'days': days,
                        'min_events': min_events
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo hotspots: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/intelligence/comprehensive-analysis')
        def api_comprehensive_analysis():
            """API: Obtener análisis comprensivo combinando todas las fuentes"""
            try:
                if not INTELLIGENCE_AVAILABLE or not self.integrated_analyzer:
                    return jsonify({
                        'success': False,
                        'error': 'Integrated analyzer not available'
                    }), 503
                
                timeframe_days = int(request.args.get('days', 7))
                include_predictions = request.args.get('include_predictions', 'true').lower() == 'true'
                
                # Generar GeoJSON comprensivo (que incluye análisis)
                geojson = self.integrated_analyzer.generate_comprehensive_geojson(
                    timeframe_days=timeframe_days,
                    include_predictions=include_predictions
                )
                
                return jsonify({
                    'success': True,
                    'geojson': geojson,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error en análisis comprensivo: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ========================================
        # SATELLITE API ENDPOINTS
        # ========================================
        
        @self.flask_app.route('/api/satellite/search', methods=['POST'])
        def api_satellite_search():
            """API: Buscar imágenes satelitales para coordenadas específicas"""
            try:
                if not SATELLITE_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'error': 'Satellite integration not available'
                    }), 503
                
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'JSON data required'
                    }), 400
                
                # Inicializar sistema satelital si no está disponible
                if not self.satellite_manager:
                    self._initialize_satellite_system()
                
                # Extraer parámetros de búsqueda
                bbox = data.get('bbox')  # [min_lon, min_lat, max_lon, max_lat]
                start_date = data.get('start_date', '2024-01-01')
                end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
                cloud_cover_max = data.get('cloud_cover_max', 20)
                collection = data.get('collection', 'sentinel-2-l2a')
                
                if not bbox or len(bbox) != 4:
                    return jsonify({
                        'success': False,
                        'error': 'Valid bbox required: [min_lon, min_lat, max_lon, max_lat]'
                    }), 400
                
                # Crear parámetros de consulta
                query_params = SatelliteQueryParams(
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    cloud_cover_max=cloud_cover_max,
                    collection=collection
                )
                
                # Buscar imágenes
                if collection.startswith('sentinel'):
                    images = self.sentinelhub_api.search_images(query_params)
                    provider = 'SentinelHub'
                else:
                    images = self.planet_api.search_images(query_params)
                    provider = 'Planet'
                
                # Actualizar estadísticas
                self.system_state['statistics']['satellite_images_found'] += len(images)
                if provider == 'SentinelHub':
                    self.system_state['statistics']['sentinel_searches'] += 1
                else:
                    self.system_state['statistics']['planet_searches'] += 1
                
                self.system_state['last_satellite_search'] = datetime.now().isoformat()
                
                return jsonify({
                    'success': True,
                    'images': [asdict(img) for img in images],
                    'provider': provider,
                    'query_params': asdict(query_params),
                    'total_found': len(images),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error en búsqueda satelital: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/search-geojson', methods=['POST'])
        def api_satellite_search_geojson():
            """API: Buscar imágenes satelitales para todas las ubicaciones en un GeoJSON"""
            try:
                if not SATELLITE_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'error': 'Satellite integration not available'
                    }), 503
                
                data = request.get_json()
                geojson_data = data.get('geojson')
                
                if not geojson_data:
                    return jsonify({
                        'success': False,
                        'error': 'GeoJSON data required'
                    }), 400
                
                # Inicializar sistema satelital si no está disponible
                if not self.satellite_manager:
                    self._initialize_satellite_system()
                
                # Configuración de búsqueda
                search_config = {
                    'days_back': data.get('days_back', 30),
                    'cloud_cover_max': data.get('cloud_cover_max', 20),
                    'collection': data.get('collection', 'sentinel-2-l2a'),
                    'buffer_km': data.get('buffer_km', 10)
                }
                
                # Buscar imágenes para todas las ubicaciones del GeoJSON
                results = self.satellite_manager.search_images_for_geojson(
                    geojson_data, 
                    **search_config
                )
                
                # Actualizar estadísticas del sistema
                total_images = sum(len(feature_result.get('images', [])) for feature_result in results.values())
                self.system_state['statistics']['satellite_images_found'] += total_images
                self.system_state['last_satellite_search'] = datetime.now().isoformat()
                
                return jsonify({
                    'success': True,
                    'results': results,
                    'search_config': search_config,
                    'total_locations': len(results),
                    'total_images': total_images,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error en búsqueda satelital GeoJSON: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/status')
        def api_satellite_status():
            """API: Estado del sistema satelital"""
            try:
                if not SATELLITE_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'available': False,
                        'error': 'Satellite integration not available'
                    })
                
                # Verificar credenciales
                sentinelhub_configured = bool(
                    os.getenv("SENTINELHUB_CLIENT_ID") and 
                    os.getenv("SENTINELHUB_CLIENT_SECRET")
                )
                planet_configured = bool(os.getenv("PLANET_API_KEY"))
                
                status = {
                    'available': True,
                    'initialized': self.system_state['satellite_system_initialized'],
                    'providers': {
                        'sentinelhub': {
                            'configured': sentinelhub_configured,
                            'available': sentinelhub_configured,
                            'searches_count': self.system_state['statistics']['sentinel_searches']
                        },
                        'planet': {
                            'configured': planet_configured,
                            'available': planet_configured,
                            'searches_count': self.system_state['statistics']['planet_searches']
                        }
                    },
                    'statistics': {
                        'total_images_found': self.system_state['statistics']['satellite_images_found'],
                        'total_searches': (
                            self.system_state['statistics']['sentinel_searches'] + 
                            self.system_state['statistics']['planet_searches']
                        ),
                        'last_search': self.system_state['last_satellite_search']
                    }
                }
                
                return jsonify({
                    'success': True,
                    **status,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo estado satelital: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/configure', methods=['POST'])
        def api_satellite_configure():
            """API: Configurar credenciales satelitales"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'Configuration data required'
                    }), 400
                
                # Configurar SentinelHub
                if 'sentinelhub' in data:
                    sentinel_config = data['sentinelhub']
                    os.environ['SENTINELHUB_CLIENT_ID'] = sentinel_config.get('client_id', '')
                    os.environ['SENTINELHUB_CLIENT_SECRET'] = sentinel_config.get('client_secret', '')
                
                # Configurar Planet
                if 'planet' in data:
                    planet_config = data['planet']
                    os.environ['PLANET_API_KEY'] = planet_config.get('api_key', '')
                
                # Reinicializar sistema satelital
                self._initialize_satellite_system()
                
                return jsonify({
                    'success': True,
                    'message': 'Satellite system configured and reinitialized',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error configurando sistema satelital: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/test-connection')
        def api_satellite_test_connection():
            """API: Probar conexión con APIs satelitales"""
            try:
                if not SATELLITE_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'error': 'Satellite integration not available'
                    })
                
                # Inicializar si es necesario
                if not self.satellite_manager:
                    self._initialize_satellite_system()
                
                results = {}
                
                # Test SentinelHub
                try:
                    if self.sentinelhub_api and self.sentinelhub_api.authenticate():
                        results['sentinelhub'] = {
                            'status': 'connected',
                            'message': 'Authentication successful'
                        }
                    else:
                        results['sentinelhub'] = {
                            'status': 'failed',
                            'message': 'Authentication failed or not configured'
                        }
                except Exception as e:
                    results['sentinelhub'] = {
                        'status': 'error',
                        'message': str(e)
                    }
                
                # Test Planet (simpler test)
                try:
                    if os.getenv("PLANET_API_KEY"):
                        results['planet'] = {
                            'status': 'configured',
                            'message': 'API key configured'
                        }
                    else:
                        results['planet'] = {
                            'status': 'not_configured',
                            'message': 'API key not configured'
                        }
                except Exception as e:
                    results['planet'] = {
                        'status': 'error',
                        'message': str(e)
                    }
                
                return jsonify({
                    'success': True,
                    'connections': results,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error probando conexiones satelitales: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        # ============================================
        # AUTOMATED SATELLITE MONITORING API ENDPOINTS
        # ============================================
        
        @self.flask_app.route('/api/satellite/monitoring/start', methods=['POST'])
        def api_start_satellite_monitoring():
            """API: Iniciar monitoreo satelital automático"""
            try:
                if not AUTOMATED_SATELLITE_AVAILABLE or not self.automated_satellite_monitor:
                    return jsonify({
                        'success': False,
                        'error': 'Automated satellite monitoring not available'
                    }), 503
                
                # Inicializar monitor si no está inicializado
                if not self.automated_satellite_monitor:
                    self._initialize_satellite_system()
                
                # Iniciar monitoreo
                self.automated_satellite_monitor.start_monitoring()
                self.system_state['satellite_monitoring_running'] = True
                
                # Obtener estadísticas iniciales
                stats = self.automated_satellite_monitor.get_monitoring_statistics()
                
                return jsonify({
                    'success': True,
                    'message': 'Automated satellite monitoring started',
                    'statistics': stats,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error starting satellite monitoring: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/monitoring/stop', methods=['POST'])
        def api_stop_satellite_monitoring():
            """API: Detener monitoreo satelital automático"""
            try:
                if not AUTOMATED_SATELLITE_AVAILABLE or not self.automated_satellite_monitor:
                    return jsonify({
                        'success': False,
                        'error': 'Automated satellite monitoring not available'
                    }), 503
                
                # Detener monitoreo
                self.automated_satellite_monitor.stop_monitoring()
                self.system_state['satellite_monitoring_running'] = False
                
                return jsonify({
                    'success': True,
                    'message': 'Automated satellite monitoring stopped',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error stopping satellite monitoring: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/monitoring/status')
        def api_satellite_monitoring_status():
            """API: Obtener estado del monitoreo satelital automático"""
            try:
                if not AUTOMATED_SATELLITE_AVAILABLE or not self.automated_satellite_monitor:
                    return jsonify({
                        'success': False,
                        'error': 'Automated satellite monitoring not available'
                    }), 503
                
                # Obtener estadísticas
                stats = self.automated_satellite_monitor.get_monitoring_statistics()
                
                return jsonify({
                    'success': True,
                    'monitoring_running': self.system_state.get('satellite_monitoring_running', False),
                    'statistics': stats,
                    'configuration': {
                        'check_interval_hours': self.config.get('satellite_check_interval_hours', 4),
                        'priority_interval_hours': self.config.get('satellite_priority_interval_hours', 2),
                        'auto_start': self.config.get('satellite_auto_start', True)
                    },
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting satellite monitoring status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/monitoring/update-zones', methods=['POST'])
        def api_update_satellite_zones():
            """API: Actualizar zonas de conflicto manualmente"""
            try:
                if not AUTOMATED_SATELLITE_AVAILABLE or not self.automated_satellite_monitor:
                    return jsonify({
                        'success': False,
                        'error': 'Automated satellite monitoring not available'
                    }), 503
                
                # Parsear parámetros
                data = request.get_json() or {}
                priority_only = data.get('priority_only', False)
                
                # Ejecutar actualización
                stats = self.automated_satellite_monitor.update_all_zones(priority_only=priority_only)
                
                return jsonify({
                    'success': True,
                    'message': f'Updated satellite images for conflict zones',
                    'priority_only': priority_only,
                    'statistics': stats,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error updating satellite zones: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/monitoring/populate-zones', methods=['POST'])
        def api_populate_satellite_zones():
            """API: Poblar zonas de conflicto desde datos GeoJSON existentes"""
            try:
                if not AUTOMATED_SATELLITE_AVAILABLE or not self.automated_satellite_monitor:
                    return jsonify({
                        'success': False,
                        'error': 'Automated satellite monitoring not available'
                    }), 503
                
                # Poblar zonas desde el sistema existente
                zones_count = self.automated_satellite_monitor.populate_zones_from_geojson_endpoint()
                
                return jsonify({
                    'success': True,
                    'message': f'Populated {zones_count} conflict zones for satellite monitoring',
                    'zones_created': zones_count,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error populating satellite zones: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/monitoring/zones')
        def api_get_satellite_zones():
            """API: Obtener lista de zonas de conflicto para monitoreo satelital"""
            try:
                if not AUTOMATED_SATELLITE_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'error': 'Automated satellite monitoring not available'
                    }), 503
                
                # Obtener zonas de la base de datos
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT 
                            cz.zone_id, cz.name, cz.risk_level, cz.priority, 
                            cz.last_checked, cz.created_at, cz.active,
                            zsi.sensed_date, zsi.cloud_percent, zsi.download_time, zsi.file_size
                        FROM conflict_zones cz
                        LEFT JOIN zone_satellite_images zsi ON cz.zone_id = zsi.zone_id
                        WHERE cz.active = 1
                        ORDER BY cz.priority ASC, cz.last_checked ASC NULLS FIRST
                    """)
                    
                    zones = []
                    for row in cursor.fetchall():
                        zone = {
                            'zone_id': row[0],
                            'name': row[1],
                            'risk_level': row[2],
                            'priority': row[3],
                            'last_checked': row[4],
                            'created_at': row[5],
                            'active': bool(row[6]),
                            'satellite_image': {
                                'sensed_date': row[7],
                                'cloud_percent': row[8],
                                'download_time': row[9],
                                'file_size_mb': round((row[10] or 0) / (1024 * 1024), 2) if row[10] else None
                            } if row[7] else None
                        }
                        zones.append(zone)
                
                return jsonify({
                    'success': True,
                    'zones': zones,
                    'total_zones': len(zones),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting satellite zones: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/satellite/monitoring/cleanup', methods=['POST'])
        def api_cleanup_satellite_images():
            """API: Limpiar imágenes satelitales antiguas"""
            try:
                if not AUTOMATED_SATELLITE_AVAILABLE or not self.automated_satellite_monitor:
                    return jsonify({
                        'success': False,
                        'error': 'Automated satellite monitoring not available'
                    }), 503
                
                # Parsear parámetros
                data = request.get_json() or {}
                days_to_keep = data.get('days_to_keep', 90)
                
                # Ejecutar limpieza
                deleted_count = self.automated_satellite_monitor.cleanup_old_images(days_to_keep)
                
                return jsonify({
                    'success': True,
                    'message': f'Cleaned up {deleted_count} old satellite images',
                    'deleted_count': deleted_count,
                    'days_to_keep': days_to_keep,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error cleaning up satellite images: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        # ========================================
        # INTELLIGENT DATA ENRICHMENT API ENDPOINTS
        # ========================================
        
        @self.flask_app.route('/api/enrichment/start', methods=['POST'])
        def api_start_enrichment():
            """API: Iniciar enriquecimiento automático de datos"""
            try:
                if not self.enrichment_system:
                    self._initialize_enrichment_system()
                
                if not self.enrichment_system.running:
                    self.enrichment_system.start_automatic_enrichment()
                    return jsonify({
                        'success': True,
                        'message': 'Intelligent data enrichment started',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'Enrichment already running',
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error starting enrichment: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/enrichment/stop', methods=['POST'])
        def api_stop_enrichment():
            """API: Detener enriquecimiento automático"""
            try:
                if self.enrichment_system and self.enrichment_system.running:
                    self.enrichment_system.stop_automatic_enrichment()
                    return jsonify({
                        'success': True,
                        'message': 'Enrichment stopped',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'Enrichment was not running',
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error stopping enrichment: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/enrichment/status')
        def api_enrichment_status():
            """API: Estado del sistema de enriquecimiento"""
            try:
                if not self.enrichment_system:
                    return jsonify({
                        'success': True,
                        'available': False,
                        'message': 'Enrichment system not initialized'
                    })
                
                stats = self.enrichment_system.get_enrichment_statistics()
                return jsonify({
                    'success': True,
                    'available': True,
                    'statistics': stats,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting enrichment status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/enrichment/process-batch', methods=['POST'])
        def api_enrichment_process_batch():
            """API: Procesar lote de artículos específicos"""
            try:
                if not self.enrichment_system:
                    self._initialize_enrichment_system()
                
                data = request.get_json() or {}
                article_ids = data.get('article_ids')
                limit = data.get('limit', 50)
                
                # Ejecutar enriquecimiento en background
                self._run_background_task(
                    'enrichment_batch', 
                    self.enrichment_system.enrich_batch_articles,
                    article_ids, limit
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Batch enrichment started for {len(article_ids) if article_ids else limit} articles',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error starting batch enrichment: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/enrichment/detect-duplicates', methods=['POST'])
        def api_enrichment_detect_duplicates():
            """API: Detectar y procesar artículos duplicados"""
            try:
                if not self.enrichment_system:
                    self._initialize_enrichment_system()
                
                # Ejecutar detección en background
                self._run_background_task(
                    'duplicate_detection', 
                    self.enrichment_system.detect_and_merge_duplicates
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Duplicate detection started',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error starting duplicate detection: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/enrichment/enrich-single', methods=['POST'])
        def api_enrichment_enrich_single():
            """API: Enriquecer un artículo específico"""
            try:
                if not self.enrichment_system:
                    self._initialize_enrichment_system()
                
                data = request.get_json()
                article_id = data.get('article_id')
                
                if not article_id:
                    return jsonify({
                        'success': False,
                        'error': 'article_id required'
                    }), 400
                
                # Enriquecer artículo individual
                result = self.enrichment_system.enrich_single_article(article_id)
                
                return jsonify({
                    'success': result.success,
                    'article_id': result.article_id,
                    'fields_updated': result.fields_updated,
                    'processing_time': result.processing_time,
                    'confidence_scores': result.confidence_scores,
                    'error': result.error,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error enriching single article: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/enrichment/field-completion')
        def api_enrichment_field_completion():
            """API: Estadísticas de completitud de campos"""
            try:
                if not self.enrichment_system:
                    return jsonify({
                        'success': False,
                        'error': 'Enrichment system not available'
                    }), 503
                
                stats = self.enrichment_system.get_enrichment_statistics()
                field_completion = stats.get('field_completion', {})
                total_articles = stats.get('total_articles', 0)
                
                # Calcular porcentajes de completitud
                completion_percentages = {}
                for field, count in field_completion.items():
                    completion_percentages[field] = {
                        'completed': count,
                        'total': total_articles,
                        'percentage': (count / total_articles * 100) if total_articles > 0 else 0
                    }
                
                return jsonify({
                    'success': True,
                    'field_completion': completion_percentages,
                    'total_articles': total_articles,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting field completion: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        # ========================================
        # SMART IMAGE POSITIONING API ENDPOINTS
        # ========================================
        
        @self.flask_app.route('/api/smart-positioning/run', methods=['POST'])
        def api_run_smart_positioning():
            """API: Ejecutar sistema completo de posicionamiento inteligente"""
            try:
                from src.intelligence.smart_image_positioning import SmartImagePositioning
                
                # Inicializar sistema
                smart_positioning = SmartImagePositioning()
                
                # Ejecutar en background
                self._run_background_task('smart_positioning', self._run_smart_positioning_full, smart_positioning)
                
                return jsonify({
                    'success': True,
                    'message': 'Sistema de posicionamiento inteligente iniciado en background',
                    'task_id': 'smart_positioning'
                })
                
            except Exception as e:
                logger.error(f"Error iniciando posicionamiento inteligente: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/smart-positioning/status')
        def api_smart_positioning_status():
            """API: Obtener estado del sistema de posicionamiento"""
            try:
                from src.dashboard.smart_mosaic_layout import get_mosaic_layout_stats
                
                # Obtener estadísticas actuales
                stats = get_mosaic_layout_stats()
                
                # Verificar estado de la tarea en background
                task_status = self.system_state['background_tasks'].get('smart_positioning', {})
                
                return jsonify({
                    'success': True,
                    'layout_stats': stats,
                    'task_status': task_status,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo estado de posicionamiento: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/smart-positioning/duplicates')
        def api_check_duplicates():
            """API: Verificar imágenes duplicadas"""
            try:
                from src.intelligence.smart_image_positioning import SmartImagePositioning
                
                smart_positioning = SmartImagePositioning()
                duplicates = smart_positioning.check_duplicate_images()
                
                return jsonify({
                    'success': True,
                    'duplicates': duplicates,
                    'count': len(duplicates),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error verificando duplicados: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/smart-positioning/optimize-quality', methods=['POST'])
        def api_optimize_image_quality():
            """API: Optimizar imágenes de baja calidad"""
            try:
                from src.intelligence.smart_image_positioning import SmartImagePositioning
                
                data = request.get_json() or {}
                quality_threshold = data.get('quality_threshold', 0.5)
                
                smart_positioning = SmartImagePositioning()
                
                # Ejecutar optimización en background
                self._run_background_task('optimize_quality', smart_positioning.optimize_low_quality_images, quality_threshold)
                
                return jsonify({
                    'success': True,
                    'message': 'Optimización de calidad iniciada en background',
                    'quality_threshold': quality_threshold
                })
                
            except Exception as e:
                logger.error(f"Error iniciando optimización de calidad: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/smart-positioning/assign-positions', methods=['POST'])
        def api_assign_mosaic_positions():
            """API: Asignar posiciones del mosaico basadas en análisis CV"""
            try:
                from src.intelligence.smart_image_positioning import SmartImagePositioning
                
                smart_positioning = SmartImagePositioning()
                
                # Ejecutar asignación en background
                self._run_background_task('assign_positions', smart_positioning.assign_mosaic_positions)
                
                return jsonify({
                    'success': True,
                    'message': 'Asignación de posiciones iniciada en background'
                })
                
            except Exception as e:
                logger.error(f"Error asignando posiciones: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/mosaic/layout')
        def api_get_mosaic_layout():
            """API: Obtener layout completo del mosaico organizado inteligentemente"""
            try:
                from src.dashboard.smart_mosaic_layout import get_smart_mosaic_articles, get_mosaic_layout_stats
                
                # Obtener artículos organizados
                mosaic_articles = get_smart_mosaic_articles()
                
                # Obtener estadísticas
                stats = get_mosaic_layout_stats()
                
                return jsonify({
                    'success': True,
                    'layout': mosaic_articles,
                    'statistics': stats,
                    'total_articles': sum(len(articles) for articles in mosaic_articles.values()),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo layout del mosaico: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ========================================
        # COMPUTER VISION API ENDPOINTS
        # ========================================
        
        @self.flask_app.route('/api/vision/analyze-image', methods=['POST'])
        def api_analyze_image():
            """API: Analizar imagen con computer vision"""
            try:
                data = request.get_json()
                image_url = data.get('image_url')
                article_title = data.get('article_title', '')
                article_id = data.get('article_id')
                
                if not image_url:
                    return jsonify({
                        'success': False,
                        'error': 'image_url is required'
                    }), 400
                
                if not CV_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'error': 'Computer Vision module not available'
                    }), 503
                
                # Realizar análisis de computer vision
                analysis = analyze_article_image(image_url, article_title)
                
                # Guardar análisis en base de datos si se proporciona article_id
                if article_id and not analysis.get('error'):
                    try:
                        db_path = get_database_path()
                        with sqlite3.connect(db_path) as conn:
                            cursor = conn.cursor()
                            
                            # Crear tabla para análisis de CV si no existe
                            cursor.execute("""
                                CREATE TABLE IF NOT EXISTS image_analysis (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    article_id INTEGER,
                                    image_url TEXT,
                                    analysis_json TEXT,
                                    quality_score REAL,
                                    positioning_recommendation TEXT,
                                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    FOREIGN KEY (article_id) REFERENCES articles (id)
                                )
                            """)
                            
                            # Insertar análisis
                            cursor.execute("""
                                INSERT OR REPLACE INTO image_analysis 
                                (article_id, image_url, analysis_json, quality_score, positioning_recommendation)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                article_id,
                                image_url,
                                json.dumps(analysis, ensure_ascii=False),
                                analysis.get('quality_score', 0.5),
                                analysis.get('positioning_recommendation', {}).get('position', 'center')
                            ))
                            
                            conn.commit()
                            logger.info(f"✅ Computer vision analysis saved for article {article_id}")
                    
                    except Exception as db_error:
                        logger.error(f"Error saving CV analysis to database: {db_error}")
                        # Continue without failing the request
                
                return jsonify({
                    'success': True,
                    'analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error analyzing image: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/vision/analyze-article-images', methods=['POST'])
        def api_analyze_article_images():
            """API: Analizar imágenes de múltiples artículos"""
            try:
                data = request.get_json() or {}
                limit = data.get('limit', 10)
                
                if not CV_AVAILABLE:
                    return jsonify({
                        'success': False,
                        'error': 'Computer Vision module not available'
                    }), 503
                
                # Obtener artículos con imágenes para analizar
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Obtener artículos que tienen imagen pero no análisis CV
                    cursor.execute("""
                        SELECT a.id, a.title, a.image_url
                        FROM articles a
                        LEFT JOIN image_analysis ia ON a.id = ia.article_id
                        WHERE a.image_url IS NOT NULL 
                        AND a.image_url != ''
                        AND a.image_url NOT LIKE '%placeholder%'
                        AND a.image_url NOT LIKE '%picsum%'
                        AND ia.id IS NULL
                        ORDER BY a.id DESC
                        LIMIT ?
                    """, (limit,))
                    
                    articles_to_analyze = cursor.fetchall()
                
                if not articles_to_analyze:
                    return jsonify({
                        'success': True,
                        'message': 'No hay artículos pendientes de análisis CV',
                        'analyzed': 0
                    })
                
                # Ejecutar análisis en background
                self._run_background_task(
                    'cv_analysis', 
                    self._analyze_articles_images_background, 
                    articles_to_analyze
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Iniciado análisis de computer vision para {len(articles_to_analyze)} artículos',
                    'articles_to_analyze': len(articles_to_analyze)
                })
                
            except Exception as e:
                logger.error(f"Error starting CV analysis: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/vision/get-analysis/<int:article_id>')
        def api_get_image_analysis(article_id):
            """API: Obtener análisis CV de un artículo específico"""
            try:
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT analysis_json, quality_score, positioning_recommendation, created_at
                        FROM image_analysis 
                        WHERE article_id = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (article_id,))
                    
                    result = cursor.fetchone()
                
                if not result:
                    return jsonify({
                        'success': False,
                        'error': 'No analysis found for this article'
                    }), 404
                
                analysis_json, quality_score, positioning, created_at = result
                
                return jsonify({
                    'success': True,
                    'analysis': json.loads(analysis_json),
                    'quality_score': quality_score,
                    'positioning_recommendation': positioning,
                    'created_at': created_at
                })
                
            except Exception as e:
                logger.error(f"Error getting CV analysis: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/vision/mosaic-positioning')
        def api_get_mosaic_positioning():
            """API: Obtener recomendaciones de posicionamiento para el mosaico"""
            try:
                limit = request.args.get('limit', 20, type=int)
                
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Obtener artículos con análisis CV para posicionamiento
                    cursor.execute("""
                        SELECT 
                            a.id, a.title, a.image_url, a.risk_level,
                            ia.quality_score, ia.positioning_recommendation,
                            ia.analysis_json
                        FROM articles a
                        INNER JOIN image_analysis ia ON a.id = ia.article_id
                        WHERE a.image_url IS NOT NULL 
                        AND a.image_url != ''
                        ORDER BY ia.quality_score DESC, a.published_date DESC
                        LIMIT ?
                    """, (limit,))
                    
                    articles = cursor.fetchall()
                
                positioning_data = []
                for article in articles:
                    article_id, title, image_url, risk_level, quality_score, positioning, analysis_json = article
                    
                    try:
                        analysis = json.loads(analysis_json)
                        positioning_data.append({
                            'article_id': article_id,
                            'title': title,
                            'image_url': image_url,
                            'risk_level': risk_level,
                            'quality_score': quality_score,
                            'positioning_recommendation': positioning,
                            'crop_suggestions': analysis.get('crop_suggestions', []),
                            'interest_areas': analysis.get('interest_areas', []),
                            'composition_score': analysis.get('composition_analysis', {}).get('contrast', 50) / 50
                        })
                    except json.JSONDecodeError:
                        continue
                
                return jsonify({
                    'success': True,
                    'articles': positioning_data,
                    'total': len(positioning_data),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting mosaic positioning: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
            """API: Obtener distribución de categorías de conflicto"""
            try:
                timeframe = request.args.get('timeframe', '7d')
                timeframe_days = {
                    '24h': 1,
                    '7d': 7,
                    '30d': 30,
                    '90d': 90
                }.get(timeframe, 7)
                
                cutoff_date = datetime.now() - timedelta(days=timeframe_days)
                
                db_path = get_database_path()
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT 
                            COALESCE(conflict_category, 'General') as category,
                            COUNT(*) as count,
                            AVG(bert_conflict_probability) as avg_probability
                        FROM articles 
                        WHERE published_date >= ?
                        AND (risk_level IN ('high', 'medium') OR bert_conflict_probability > 0.3)
                        GROUP BY conflict_category
                        ORDER BY count DESC
                    """, (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
                    
                    categories = []
                    for row in cursor.fetchall():
                        category, count, avg_prob = row
                        categories.append({
                            'name': category,
                            'count': count,
                            'avg_probability': round(avg_prob or 0, 2)
                        })
                
                return jsonify({
                    'success': True,
                    'categories': categories,
                    'timeframe': timeframe,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo categorías: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Static files
        @self.flask_app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory('src/web/static', filename)
    
    def _is_publisher_location(self, location: str) -> bool:
        """Verificar si una ubicación es la sede de un medio de comunicación"""
        if not location:
            return False
        
        location_lower = location.lower()
        publisher_locations = [
            'nueva york', 'new york', 'londres', 'london', 'washington', 
            'atlanta', 'doha', 'paris', 'madrid', 'barcelona', 'reuters',
            'cnn center', 'bbc', 'headquarters', 'editorial', 'redacción'
        ]
        
        return any(pub_loc in location_lower for pub_loc in publisher_locations)
    
    def _initialize_dash_apps(self):
        """Inicializar y integrar aplicaciones Dash"""
        try:
            logger.info("Initializing integrated Dash applications...")
            
            # Historical Dashboard
            if self.config['historical_dashboard_integrated']:
                self.dash_apps['historical'] = HistoricalDashboard(
                    data_source=self.historical_orchestrator.data_integrator if self.historical_orchestrator else None,
                    port=None
                )
                self._integrate_dash_app(self.dash_apps['historical'].app, '/dash/historical/')
            
            # Multivariate Dashboard
            if self.config['multivariate_dashboard_integrated']:
                self.dash_apps['multivariate'] = MultivariateRelationshipDashboard(
                    data_integrator=self.historical_orchestrator.multivariate_integrator if self.historical_orchestrator else None,
                    relationship_analyzer=self.historical_orchestrator.relationship_analyzer if self.historical_orchestrator else None,
                    port=None
                )
                self._integrate_dash_app(self.dash_apps['multivariate'].app, '/dash/multivariate/')
            
            self.system_state['dashboards_ready'] = True
            logger.info("Dash applications integrated successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Dash apps: {e}")
    
    def _integrate_dash_app(self, dash_app, url_base_pathname):
        """Integrar una aplicación Dash en Flask"""
        try:
            dash_app.config.update({
                'requests_pathname_prefix': url_base_pathname,
                'url_base_pathname': url_base_pathname,
            })
            dash_app.server = self.flask_app
            
            # Register Dash routes with Flask
            for rule in dash_app.server.url_map.iter_rules():
                if rule.endpoint.startswith('dash'):
                    continue
                
                # Create new rule for Dash app
                new_rule = f"{url_base_pathname.rstrip('/')}{rule.rule}"
                self.flask_app.add_url_rule(
                    new_rule,
                    f"dash_{rule.endpoint}",
                    dash_app.server.view_functions[rule.endpoint],
                    methods=rule.methods
                )
            
        except Exception as e:
            logger.error(f"Error integrating Dash app: {e}")
    
    def _setup_api_endpoints(self):
        """Configurar endpoints de API REST"""
        try:
            if self.config['enable_api'] and self.core_orchestrator:
                api_blueprint = create_api_blueprint(self.core_orchestrator)
                self.flask_app.register_blueprint(api_blueprint, url_prefix='/api/v1')
                self.system_state['api_ready'] = True
                logger.info("API endpoints registered successfully")
        except Exception as e:
            logger.error(f"Error setting up API endpoints: {e}")
    
    def _run_background_task(self, task_name: str, task_func, *args, **kwargs):
        """Ejecutar tarea en background thread"""
        try:
            # Mark task as started
            self.system_state['background_tasks'][task_name] = {
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'progress': 0
            }
            
            def run_task():
                try:
                    result = task_func(*args, **kwargs)
                    self.system_state['background_tasks'][task_name] = {
                        'status': 'completed',
                        'started_at': self.system_state['background_tasks'][task_name]['started_at'],
                        'completed_at': datetime.now().isoformat(),
                        'progress': 100,
                        'result': result
                    }
                    logger.info(f"Background task {task_name} completed successfully")
                except Exception as e:
                    self.system_state['background_tasks'][task_name] = {
                        'status': 'failed',
                        'started_at': self.system_state['background_tasks'][task_name]['started_at'],
                        'failed_at': datetime.now().isoformat(),
                        'progress': 0,
                        'error': str(e)
                    }
                    logger.error(f"Background task {task_name} failed: {e}")
            
            thread = threading.Thread(target=run_task, name=f"bg_{task_name}")
            thread.daemon = True
            thread.start()
            self.background_threads[task_name] = thread
            
        except Exception as e:
            logger.error(f"Error starting background task {task_name}: {e}")
    
    def _initialize_satellite_system(self):
        """Inicializar sistema de integración satelital"""
        try:
            if not SATELLITE_AVAILABLE:
                logger.warning("Satellite integration not available")
                return False
            
            logger.info("Initializing satellite integration system...")
            
            # Inicializar APIs satelitales
            self.sentinelhub_api = SentinelHubAPI()
            self.planet_api = PlanetAPI()
            
            # Inicializar manager principal
            self.satellite_manager = SatelliteIntegrationManager()
            
            # Probar conectividad básica
            sentinelhub_ok = False
            planet_ok = False
            
            try:
                # Test SentinelHub si está configurado
                if os.getenv("SENTINELHUB_CLIENT_ID") and os.getenv("SENTINELHUB_CLIENT_SECRET"):
                    sentinelhub_ok = self.sentinelhub_api.authenticate()
                    if sentinelhub_ok:
                        logger.info("✅ SentinelHub API connected successfully")
                    else:
                        logger.warning("⚠️ SentinelHub API authentication failed")
                else:
                    logger.info("ℹ️ SentinelHub credentials not configured")
            except Exception as e:
                logger.warning(f"SentinelHub connection test failed: {e}")
            
            try:
                # Test Planet si está configurado
                if os.getenv("PLANET_API_KEY"):
                    planet_ok = True  # Planet no requiere autenticación previa
                    logger.info("✅ Planet API configured")
                else:
                    logger.info("ℹ️ Planet API key not configured")
            except Exception as e:
                logger.warning(f"Planet API test failed: {e}")
            
            # Inicializar Monitor Satelital Automático
            try:
                if AUTOMATED_SATELLITE_AVAILABLE:
                    logger.info("Initializing Automated Satellite Monitor...")
                    
                    # Configuración específica para el monitor
                    monitor_config = {
                        'images_dir': 'data/satellite_images',
                        'max_cloud_cover': 20,
                        'image_size': (512, 512),
                        'check_interval_hours': self.config.get('satellite_check_interval_hours', 4),
                        'priority_zones_interval_hours': self.config.get('satellite_priority_interval_hours', 2),
                        'max_age_days': 30,
                        'batch_size': 10,
                        'retry_attempts': 3,
                        'timeout_seconds': 120
                    }
                    
                    # Crear el monitor con la misma BD que usa el resto del sistema
                    self.automated_satellite_monitor = AutomatedSatelliteMonitor(
                        db_path=get_database_path(),
                        config=monitor_config
                    )
                    
                    logger.info("✅ Automated Satellite Monitor initialized successfully")
                    
                    # Verificar si tiene credenciales para funcionar
                    if sentinelhub_ok:
                        logger.info("🛰️ Automated monitoring ready with SentinelHub")
                    else:
                        logger.warning("⚠️ Automated monitoring initialized but needs valid credentials")
                        
                else:
                    logger.warning("⚠️ Automated Satellite Monitor not available")
                    self.automated_satellite_monitor = None
                    
            except Exception as e:
                logger.error(f"Error initializing Automated Satellite Monitor: {e}")
                self.automated_satellite_monitor = None
            
            # Marcar como inicializado si al menos una API está disponible
            if sentinelhub_ok or planet_ok:
                self.system_state['satellite_system_initialized'] = True
                logger.info("🛰️ Satellite system initialized successfully")
                return True
            else:
                logger.warning("⚠️ No satellite APIs are properly configured")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing satellite system: {e}")
            return False

    def _initialize_enrichment_system(self):
        """Inicializar sistema de enriquecimiento inteligente de datos"""
        try:
            logger.info("🤖 Initializing intelligent data enrichment system...")
            
            from src.enrichment.intelligent_data_enrichment import (
                create_enrichment_system, EnrichmentConfig
            )
            
            # Configuración del sistema de enriquecimiento
            enrichment_config = EnrichmentConfig(
                batch_size=self.config.get('enrichment_batch_size', 10),
                max_workers=self.config.get('enrichment_max_workers', 4),
                confidence_threshold=self.config.get('enrichment_confidence_threshold', 0.7),
                auto_enrich_interval_hours=self.config.get('auto_enrich_interval_hours', 6)
            )
            
            # Crear sistema de enriquecimiento
            self.enrichment_system = create_enrichment_system(
                db_path=get_database_path(),
                config=enrichment_config
            )
            
            # Configurar triggers automáticos para nuevos artículos
            self.enrichment_system.setup_automatic_enrichment_triggers()
            
            # Iniciar enriquecimiento automático si está configurado
            if self.config.get('auto_start_enrichment', True):
                self.enrichment_system.start_automatic_enrichment()
                self.system_state['enrichment_running'] = True
                logger.info("✅ Automatic enrichment started")
            
            self.system_state['enrichment_system_initialized'] = True
            logger.info("✅ Intelligent data enrichment system initialized successfully")
            
            # Actualizar estadísticas iniciales
            try:
                stats = self.enrichment_system.get_enrichment_statistics()
                self.system_state['statistics']['articles_enriched'] = stats.get('enriched_articles', 0)
                self.system_state['statistics']['fields_completed'] = sum(stats.get('field_completion', {}).values())
            except Exception as e:
                logger.warning(f"Could not get initial enrichment stats: {e}")
            
            return True
            
        except ImportError as e:
            logger.warning(f"⚠️ Enrichment system dependencies not available: {e}")
            self.enrichment_system = None
            return False
        except Exception as e:
            logger.error(f"Error initializing enrichment system: {e}")
            self.enrichment_system = None
            return False
    
    def _initialize_all_systems(self):
        """Inicializar todos los sistemas del RiskMap"""
        try:
            logger.info("Initializing all RiskMap systems...")
            self.system_state['system_status'] = 'initializing'
            
            # 1. Initialize core orchestrator (RSS ingestion, NLP processing)
            logger.info("Initializing core orchestration system...")
            self.core_orchestrator = GeopoliticalIntelligenceOrchestrator()
            
            # Test core system
            health_status = self.core_orchestrator.health_check()
            if health_status.get('overall_status') in ['healthy', 'degraded']:
                self.system_state['core_system_initialized'] = True
                logger.info("Core system initialized successfully")
            else:
                logger.warning("Core system initialization completed with warnings")
                self.system_state['core_system_initialized'] = True  # Continue anyway
            
            # 2. Load existing data from database for immediate display
            logger.info("Loading existing data from database...")
            self._load_existing_data()
            
            # 3. Initialize enhanced historical orchestrator
            logger.info("Initializing enhanced historical analysis system...")
            self.historical_orchestrator = EnhancedHistoricalOrchestrator()
            
            # Initialize historical system
            historical_init = asyncio.run(
                self.historical_orchestrator.initialize_enhanced_system()
            )
            
            if historical_init['status'] in ['success', 'partial_success']:
                self.system_state['historical_system_initialized'] = True
                logger.info("Historical analysis system initialized successfully")
            else:
                logger.warning("Historical system initialization completed with warnings")
                self.system_state['historical_system_initialized'] = True  # Continue anyway
            
            # 4. Initialize external intelligence feeds and integrated analyzer
            logger.info("Initializing external intelligence feeds...")
            if INTELLIGENCE_AVAILABLE:
                try:
                    db_path = get_database_path()
                    self.external_feeds = ExternalIntelligenceFeeds(db_path)
                    
                    # Initialize with Groq client if available
                    groq_client = None
                    if hasattr(self.core_orchestrator, 'groq_client'):
                        groq_client = self.core_orchestrator.groq_client
                    
                    self.integrated_analyzer = IntegratedGeopoliticalAnalyzer(db_path, groq_client)
                    
                    logger.info("External intelligence modules initialized successfully")
                    self.system_state['external_intelligence_initialized'] = True
                except Exception as e:
                    logger.warning(f"External intelligence initialization failed: {e}")
                    self.system_state['external_intelligence_initialized'] = False
            else:
                logger.warning("External intelligence modules not available")
                self.system_state['external_intelligence_initialized'] = False
            
            # 5. Initialize satellite integration system
            logger.info("Initializing satellite integration system...")
            self._initialize_satellite_system()
            
            # 6. Initialize intelligent data enrichment system
            logger.info("Initializing intelligent data enrichment system...")
            self._initialize_enrichment_system()
            
            # 7. Initialize task scheduler
            logger.info("Initializing task scheduler...")
            self.task_scheduler = TaskScheduler(self.core_orchestrator)
            
            # 8. Setup API endpoints
            self._setup_api_endpoints()
            
            # 9. Initialize Dash applications with existing data
            self._initialize_dash_apps()
            
            # 9. Start background processes if enabled (for continuous updates)
            if self.config['enable_background_tasks']:
                self._start_background_processes()
            
            self.system_state['system_status'] = 'initialized'
            logger.info("All systems initialized successfully with existing data loaded")
            
            return {
                'status': 'success',
                'core_system': self.system_state['core_system_initialized'],
                'historical_system': self.system_state['historical_system_initialized'],
                'external_intelligence': self.system_state['external_intelligence_initialized'],
                'satellite_system': self.system_state['satellite_system_initialized'],
                'dashboards': self.system_state['dashboards_ready'],
                'api': self.system_state['api_ready'],
                'existing_data_loaded': True
            }
            
        except Exception as e:
            self.system_state['system_status'] = 'initialization_failed'
            logger.error(f"Error initializing systems: {e}")
            raise
    
    def _start_background_processes(self):
        """Iniciar procesos automáticos en background"""
        try:
            logger.info("Starting background processes...")
            
            # Auto-start data ingestion
            if self.config['auto_start_ingestion']:
                self._run_background_task('auto_ingestion', self._run_continuous_ingestion)
            
            # Auto-start NLP processing
            if self.config['auto_start_processing']:
                self._run_background_task('auto_processing', self._run_continuous_processing)
            
            # Auto-start historical analysis
            if self.config['auto_start_analysis']:
                self._run_background_task('auto_analysis', self._run_continuous_analysis)
            
            # Auto-start external feeds update
            if INTELLIGENCE_AVAILABLE and self.external_feeds:
                self._run_background_task('auto_external_feeds', self._run_continuous_external_feeds_update)
            
            # Auto-start satellite monitoring
            if self.config.get('satellite_auto_start', True) and AUTOMATED_SATELLITE_AVAILABLE and self.automated_satellite_monitor:
                try:
                    logger.info("Starting automated satellite monitoring...")
                    self.automated_satellite_monitor.start_monitoring()
                    self.system_state['satellite_monitoring_running'] = True
                    logger.info("✅ Automated satellite monitoring started")
                except Exception as e:
                    logger.error(f"Error starting satellite monitoring: {e}")
            
            # Auto-start enrichment system
            if self.config.get('enrichment_auto_start', True) and self.enrichment_system:
                try:
                    logger.info("Starting automated enrichment system...")
                    self.enrichment_system.start_automatic_enrichment()
                    self.system_state['enrichment_running'] = True
                    logger.info("✅ Automated enrichment system started")
                except Exception as e:
                    logger.error(f"Error starting enrichment system: {e}")
            
            # Start maintenance cycle
            self._run_background_task('maintenance', self._run_maintenance_cycle)
            
            logger.info("Background processes started")
            
        except Exception as e:
            logger.error(f"Error starting background processes: {e}")
    
    def _start_data_ingestion(self):
        """Iniciar ingesta de datos una vez"""
        try:
            logger.info("Starting data ingestion...")
            self.system_state['data_ingestion_running'] = True
            
            if self.core_orchestrator:
                # Run global collection
                count = self.core_orchestrator.run_global_collection()
                self.system_state['last_ingestion'] = datetime.now().isoformat()
                
                # Add alert
                self.system_state['alerts'].append({
                    'type': 'ingestion_completed',
                    'message': f'Data ingestion completed: {count} articles collected',
                    'timestamp': datetime.now().isoformat(),
                    'count': count
                })
                
                logger.info(f"Data ingestion completed: {count} articles")
                return count
            else:
                raise Exception("Core orchestrator not initialized")
                
        except Exception as e:
            logger.error(f"Error in data ingestion: {e}")
            raise
        finally:
            self.system_state['data_ingestion_running'] = False
    
    def _start_nlp_processing(self):
        """Iniciar procesamiento NLP una vez"""
        try:
            logger.info("Starting NLP processing...")
            self.system_state['nlp_processing_running'] = True
            
            if self.core_orchestrator:
                # Process pending articles
                count = self.core_orchestrator.process_data_only()
                self.system_state['last_processing'] = datetime.now().isoformat()
                
                # Add alert
                self.system_state['alerts'].append({
                    'type': 'processing_completed',
                    'message': f'NLP processing completed: {count} articles processed',
                    'timestamp': datetime.now().isoformat(),
                    'count': count
                })
                
                logger.info(f"NLP processing completed: {count} articles")
                return count
            else:
                raise Exception("Core orchestrator not initialized")
                
        except Exception as e:
            logger.error(f"Error in NLP processing: {e}")
            raise
        finally:
            self.system_state['nlp_processing_running'] = False
    
    def _start_historical_analysis(self):
        """Iniciar análisis histórico una vez"""
        try:
            logger.info("Starting historical analysis...")
            self.system_state['historical_analysis_running'] = True
            
            if self.historical_orchestrator:
                # Run comprehensive analysis
                result = asyncio.run(
                    self.historical_orchestrator.run_comprehensive_multivariate_analysis()
                )
                self.system_state['last_analysis'] = datetime.now().isoformat()
                
                # Add alert
                self.system_state['alerts'].append({
                    'type': 'analysis_completed',
                    'message': f'Historical analysis completed: {result["status"]}',
                    'timestamp': datetime.now().isoformat(),
                    'status': result['status']
                })
                
                logger.info(f"Historical analysis completed: {result['status']}")
                return result
            else:
                raise Exception("Historical orchestrator not initialized")
                
        except Exception as e:
            logger.error(f"Error in historical analysis: {e}")
            raise
        finally:
            self.system_state['historical_analysis_running'] = False
    
    def _run_continuous_ingestion(self):
        """Ejecutar ingesta continua"""
        logger.info(f"Starting continuous data ingestion (interval: {self.config['ingestion_interval_hours']} hours)")
        
        while not self.shutdown_event.is_set():
            try:
                if not self.system_state['data_ingestion_running']:
                    self._start_data_ingestion()
                
                # Wait for next cycle
                self.shutdown_event.wait(self.config['ingestion_interval_hours'] * 3600)
                
            except Exception as e:
                logger.error(f"Error in continuous ingestion: {e}")
                self.shutdown_event.wait(3600)  # Wait 1 hour before retry
    
    def _run_continuous_processing(self):
        """Ejecutar procesamiento continuo"""
        logger.info(f"Starting continuous NLP processing (interval: {self.config['processing_interval_hours']} hours)")
        
        while not self.shutdown_event.is_set():
            try:
                if not self.system_state['nlp_processing_running']:
                    self._start_nlp_processing()
                
                # Wait for next cycle
                self.shutdown_event.wait(self.config['processing_interval_hours'] * 3600)
                
            except Exception as e:
                logger.error(f"Error in continuous processing: {e}")
                self.shutdown_event.wait(3600)  # Wait 1 hour before retry
    
    def _run_continuous_analysis(self):
        """Ejecutar análisis continuo"""
        logger.info(f"Starting continuous historical analysis (interval: {self.config['analysis_interval_hours']} hours)")
        
        while not self.shutdown_event.is_set():
            try:
                if not self.system_state['historical_analysis_running']:
                    self._start_historical_analysis()
                
                # Wait for next cycle
                self.shutdown_event.wait(self.config['analysis_interval_hours'] * 3600)
                
            except Exception as e:
                logger.error(f"Error in continuous analysis: {e}")
                self.shutdown_event.wait(3600)  # Wait 1 hour before retry
    
    def _run_continuous_external_feeds_update(self):
        """Ejecutar actualización continua de feeds externos"""
        logger.info("Starting continuous external feeds update (interval: 6 hours)")
        
        while not self.shutdown_event.is_set():
            try:
                if INTELLIGENCE_AVAILABLE and self.external_feeds:
                    logger.info("Updating external intelligence feeds...")
                    
                    # Update all feeds
                    update_results = self.external_feeds.update_all_feeds()
                    
                    # Update system state
                    self.system_state['last_external_feeds_update'] = datetime.now().isoformat()
                    
                    # Count successful updates
                    successful_updates = sum(1 for result in update_results.values() if result)
                    total_feeds = len(update_results)
                    
                    # Add alert
                    self.system_state['alerts'].append({
                        'type': 'external_feeds_updated',
                        'message': f'External feeds updated: {successful_updates}/{total_feeds} successful',
                        'timestamp': datetime.now().isoformat(),
                        'results': update_results
                    })
                    
                    logger.info(f"External feeds update completed: {successful_updates}/{total_feeds} successful")
                else:
                    logger.warning("External feeds not available for update")
                
                # Wait 6 hours before next update
                self.shutdown_event.wait(6 * 3600)
                
            except Exception as e:
                logger.error(f"Error in continuous external feeds update: {e}")
                self.shutdown_event.wait(3600)  # Wait 1 hour before retry
    
    def _run_maintenance_cycle(self):
        """Ejecutar ciclo de mantenimiento"""
        logger.info(f"Starting maintenance cycle (interval: {self.config['maintenance_interval_hours']} hours)")
        
        while not self.shutdown_event.is_set():
            try:
                logger.info("Running system maintenance...")
                
                # Update statistics
                self._update_statistics()
                
                # Clean old logs
                self._clean_old_logs()
                
                # System health check
                if self.core_orchestrator:
                    health_status = self.core_orchestrator.health_check()
                    if health_status.get('overall_status') not in ['healthy', 'degraded']:
                        self.system_state['alerts'].append({
                            'type': 'system_health_warning',
                            'message': 'System health check failed',
                            'timestamp': datetime.now().isoformat(),
                            'details': health_status
                        })
                
                logger.info("Maintenance cycle completed")
                
                # Wait for next cycle
                self.shutdown_event.wait(self.config['maintenance_interval_hours'] * 3600)
                
            except Exception as e:
                logger.error(f"Error in maintenance cycle: {e}")
                self.shutdown_event.wait(3600)  # Wait 1 hour before retry
    
    def _load_existing_data(self):
        """Cargar datos existentes de la base de datos para mostrar resultados inmediatamente"""
        try:
            logger.info("Loading existing data from database for immediate display...")
            
            if self.core_orchestrator:
                # Get database connection and load existing articles
                try:
                    # Import database utilities
                    import sqlite3
                    from pathlib import Path
                    
                    # Check if database exists
                    db_path = Path(get_database_path())
                    if not db_path.exists():
                        logger.warning("Database not found, will be created on first ingestion")
                        return
                    
                    # Connect to database
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    
                    # Get article statistics
                    cursor.execute("SELECT COUNT(*) FROM articles")
                    total_articles = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM processed_data WHERE processed = 1")
                    processed_articles = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM processed_data WHERE risk_level > 0.7")
                    risk_alerts = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
                    data_sources = cursor.fetchone()[0]
                    
                    # Update statistics
                    self.system_state['statistics'].update({
                        'total_articles': total_articles,
                        'processed_articles': processed_articles,
                        'risk_alerts': risk_alerts,
                        'data_sources': data_sources
                    })
                    
                    # Get recent articles for display
                    cursor.execute("""
                        SELECT title, source, published_date, risk_level 
                        FROM articles a 
                        LEFT JOIN processed_data p ON a.id = p.article_id 
                        ORDER BY published_date DESC 
                        LIMIT 10
                    """)
                    recent_articles = cursor.fetchall()
                    
                    conn.close()
                    
                    # Add alert about loaded data
                    self.system_state['alerts'].append({
                        'type': 'data_loaded',
                        'message': f'Loaded existing data: {total_articles} articles, {processed_articles} processed',
                        'timestamp': datetime.now().isoformat(),
                        'details': {
                            'total_articles': total_articles,
                            'processed_articles': processed_articles,
                            'risk_alerts': risk_alerts,
                            'data_sources': data_sources
                        }
                    })
                    
                    logger.info(f"Existing data loaded successfully: {total_articles} articles, {processed_articles} processed")
                    
                except Exception as db_error:
                    logger.warning(f"Could not load existing data from database: {db_error}")
                    # Continue without existing data
                    
            else:
                logger.warning("Core orchestrator not available for loading existing data")
                
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
            # Continue without existing data - not critical for startup
    
    def _update_statistics(self):
        """Actualizar estadísticas del sistema"""
        try:
            if self.core_orchestrator:
                # Update statistics from database
                try:
                    import sqlite3
                    from pathlib import Path
                    
                    db_path = Path(get_database_path())
                    if db_path.exists():
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        
                        # Get updated statistics
                        cursor.execute("SELECT COUNT(*) FROM articles")
                        total_articles = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT COUNT(*) FROM processed_data WHERE processed = 1")
                        processed_articles = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT COUNT(*) FROM processed_data WHERE risk_level > 0.7")
                        risk_alerts = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
                        data_sources = cursor.fetchone()[0]
                        
                        # Update statistics
                        self.system_state['statistics'].update({
                            'total_articles': total_articles,
                            'processed_articles': processed_articles,
                            'risk_alerts': risk_alerts,
                            'data_sources': data_sources
                        })
                        
                        conn.close()
                        
                except Exception as db_error:
                    logger.warning(f"Could not update statistics from database: {db_error}")
            
            # Update timestamp
            self.system_state['statistics']['last_updated'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def _generate_geopolitical_analysis(self, articles):
        """Generar análisis geopolítico periodístico usando IA"""
        try:
            # Preparar el contexto de los artículos
            context = self._prepare_articles_context(articles)
            
            # Crear el prompt para el periodista de IA
            prompt = f"""Eres un periodista veterano especializado en geopolítica que escribe para un prestigioso periódico online. Tu trabajo es analizar la actualidad mundial y escribir un artículo de análisis profundo que conecte los eventos actuales con economía, recursos energéticos, políticas internacionales, conflictos y tendencias globales.

CONTEXTO DE NOTICIAS ACTUALES:
{context}

INSTRUCCIONES PARA EL ARTÍCULO:
1. Escribe como un periodista profesional con años de experiencia en geopolítica
2. Estructura tu análisis en un artículo bien organizado con párrafos coherentes
3. Incluye nombres específicos de países, líderes, organizaciones internacionales, empresas relevantes
4. Establece conexiones entre economía, energía, política y conflictos
5. Mantén un tono profesional y objetivo, pero con un ligero sesgo hacia:
   - La importancia de abordar el cambio climático responsablemente
   - La preferencia por soluciones diplomáticas y pacíficas
   - El análisis crítico pero equilibrado de las decisiones geopolíticas
6. Proporciona un análisis rico en detalles y nombres concretos
7. Evita ser activista, mantén la credibilidad periodística

ESTRUCTURA SUGERIDA:
- Una introducción que capture la atención del lector
- Desarrollo del análisis por regiones o temas clave
- Conexiones entre eventos aparentemente separados
- Perspectivas sobre impactos económicos y energéticos
- Conclusiones con proyecciones realistas

Escribe un artículo de análisis geopolítico de aproximadamente 800-1200 palabras:"""

            # Intentar usar un servicio de IA (puedes integrar Groq, OpenAI, etc.)
            analysis = self._call_ai_service(prompt)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating geopolitical analysis: {e}")
            return self._get_fallback_analysis()
    
    def _prepare_articles_context(self, articles):
        """Preparar contexto de artículos para el análisis"""
        if not articles or len(articles) == 0:
            return "No hay artículos recientes disponibles para el análisis."
        
        context_parts = []
        for i, article in enumerate(articles[:10]):  # Solo los primeros 10 artículos
            title = article.get('title', 'Sin título')
            content = article.get('content', article.get('summary', 'Sin contenido'))
            country = article.get('country', article.get('location', 'Global'))
            risk_level = article.get('risk_level', 'unknown')
            
            # Truncar contenido si es muy largo
            if len(content) > 200:
                content = content[:200] + "..."
            
            context_parts.append(f"""
Artículo {i+1}:
- Título: {title}
- Ubicación: {country}
- Nivel de riesgo: {risk_level}
- Resumen: {content}
""")
        
        return "\n".join(context_parts)
    
    def _call_ai_service(self, prompt):
        """Llamar al servicio de IA para generar el análisis"""
        try:
            # Intentar usar Groq AI primero
            return self._generate_groq_analysis(prompt)
            
        except Exception as e:
            logger.error(f"Error calling AI service: {e}")
            return self._get_fallback_analysis()
    
    def _generate_groq_analysis(self, prompt):
        """
        Genera un análisis geopolítico usando Groq API
        
        Args:
            prompt (str): Prompt para generar el análisis
            
        Returns:
            str: Análisis geopolítico generado
        """
        try:
            from groq import Groq
            
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                logger.warning("GROQ_API_KEY no encontrada. Usando análisis de respaldo.")
                return self._get_fallback_analysis()
            
            client = Groq(api_key=groq_api_key)
            
            # Prompt optimizado para análisis periodístico
            optimized_prompt = f"""
            Eres un periodista experto en geopolítica con 25 años de experiencia, escribiendo para un periódico de renombre mundial. Tu estilo es incisivo, humano y riguroso. No temes nombrar líderes, países o conflictos, y ofreces predicciones fundamentadas pero humildes.

            {prompt}

            INSTRUCCIONES CLAVE:
            1. **Estilo Periodístico Humano**: Escribe con una voz personal y experta, no como una IA. Usa un lenguaje rico y evocador.
            2. **Nombres Propios**: Menciona líderes (Putin, Xi Jinping, Biden, Zelensky), países y regiones relevantes.
            3. **Análisis Profundo**: Conecta los puntos entre diferentes conflictos y tendencias. No te limites a resumir.
            4. **Opinión Fundamentada**: Expresa tu opinión y proyecciones, pero siempre desde la humildad y el rigor analítico.
            5. **Formato**: Genera solo el contenido del artículo en texto plano, bien estructurado con párrafos.

            Escribe un análisis geopolítico profundo de 800-1200 palabras:
            """

            logger.info("🤖 Generando análisis con Groq AI...")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analista geopolítico de élite con estilo periodístico profesional."
                    },
                    {
                        "role": "user",
                        "content": optimized_prompt
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.75,
                max_tokens=2000
            )
            
            response_content = chat_completion.choices[0].message.content
            logger.info("✅ Análisis Groq generado exitosamente.")
            
            return response_content
            
        except ImportError:
            logger.error("Librería Groq no instalada. Ejecuta: pip install groq")
            return self._get_fallback_analysis()
        except Exception as e:
            logger.error(f"Error en la llamada a la API de Groq: {e}")
            return self._get_fallback_analysis()
    
    def _generate_groq_geopolitical_analysis(self, articles):
        """
        Genera un análisis geopolítico usando Groq API con artículos como contexto
        
        Args:
            articles (list): Lista de artículos para analizar
            
        Returns:
            dict: Análisis geopolítico estructurado
        """
        try:
            from groq import Groq
            
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                logger.warning("GROQ_API_KEY no encontrada. Usando análisis de respaldo.")
                return self._get_structured_fallback_analysis(articles)
            
            client = Groq(api_key=groq_api_key)
            
            # Preparar contexto de artículos
            articles_context = "\n\n".join([
                f"ARTÍCULO {i+1}:\nTítulo: {article.get('title', 'N/A')}\nContenido: {article.get('content', 'N/A')[:500]}...\nUbicación: {article.get('location', 'N/A')}"
                for i, article in enumerate(articles[:20])
            ])
            
            prompt = f"""
            Eres un periodista experto en geopolítica con 25 años de experiencia, escribiendo para un periódico de renombre mundial. Tu estilo es incisivo, humano y riguroso. No temes nombrar líderes, países o conflictos, y ofreces predicciones fundamentadas pero humildes.

            Analiza los siguientes {len(articles)} artículos de noticias y genera un análisis geopolítico en formato JSON.

            ARTÍCULOS DE CONTEXTO:
            {articles_context}

            INSTRUCCIONES CLAVE:
            1.  **Estilo Periodístico Humano**: Escribe con una voz personal y experta, no como una IA. Usa un lenguaje rico y evocador.
            2.  **Nombres Propios**: Menciona líderes (Putin, Xi Jinping, Biden, Zelensky), países y regiones relevantes.
            3.  **Análisis Profundo**: Conecta los puntos entre diferentes conflictos y tendencias. No te limites a resumir.
            4.  **Opinión Fundamentada**: Expresa tu opinión y proyecciones, pero siempre desde la humildad y el rigor analítico.
            5.  **Formato JSON Específico**:
                *   El `content` debe ser una cadena de texto HTML.
                *   Usa párrafos `<p>` para el cuerpo del texto.
                *   **No uses** `<h1>`, `<h2>`, etc., dentro del `content`. El título y subtítulo van en sus propios campos.
                *   Puedes usar `<strong>` para enfatizar conceptos clave.

            RESPONDE ÚNICAMENTE CON UN OBJETO JSON VÁLIDO con la siguiente estructura:
            {{
              "title": "Un titular principal, impactante y profesional",
              "subtitle": "Un subtítulo que resuma la esencia del análisis",
              "content": "El cuerpo completo del artículo en HTML, usando solo <p> y <strong>.",
              "sources_count": {len(articles)}
            }}
            """

            logger.info("🤖 Generando análisis estructurado con Groq AI...")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analista geopolítico de élite. Tu única salida es un objeto JSON válido que sigue estrictamente la estructura solicitada."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.75,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            response_content = chat_completion.choices[0].message.content
            logger.info("✅ Análisis Groq estructurado generado exitosamente.")
            
            try:
                analysis_data = json.loads(response_content)
                # Validar campos requeridos
                if 'title' in analysis_data and 'subtitle' in analysis_data and 'content' in analysis_data:
                    return analysis_data
                else:
                    logger.error("JSON de Groq incompleto. Faltan campos requeridos.")
                    return self._get_structured_fallback_analysis(articles)
            except json.JSONDecodeError:
                logger.error(f"Error al decodificar JSON de Groq. Contenido: {response_content[:500]}...")
                return self._get_structured_fallback_analysis(articles)
                
        except ImportError:
            logger.error("Librería Groq no instalada. Ejecuta: pip install groq")
            return self._get_structured_fallback_analysis(articles)
        except Exception as e:
            logger.error(f"Error en la llamada a la API de Groq: {e}")
            return self._get_structured_fallback_analysis(articles)
    
    def _get_structured_fallback_analysis(self, articles):
        """
        Genera análisis de respaldo estructurado cuando Groq no está disponible
        
        Args:
            articles (list): Lista de artículos para el contexto
            
        Returns:
            dict: Análisis geopolítico de respaldo estructurado
        """
        current_date = datetime.now().strftime("%d de %B de %Y")
        
        return {
            "title": "El Tablero Geopolítico se Reconfigura en Tiempo Real",
            "subtitle": "Tensiones globales y nuevas alianzas redefinen el orden mundial mientras la incertidumbre marca el rumbo internacional",
            "content": """
                <p>El panorama geopolítico mundial atraviesa uno de sus momentos más complejos de las últimas décadas. Las tensiones que se extienden desde Europa Oriental hasta el Pacífico están redibujando las alianzas internacionales y poniendo a prueba el orden establecido tras la Guerra Fría.</p>
                
                <p>En Europa, el conflicto en Ucrania ha consolidado la posición de la OTAN como un actor determinante en la seguridad continental. La respuesta occidental, liderada por Estados Unidos y respaldada firmemente por Reino Unido y Polonia, ha demostrado una cohesión que pocos predecían. Sin embargo, las fisuras emergen cuando se analiza la dependencia energética europea, particularmente de Alemania, que se ve obligada a reconsiderar décadas de política energética.</p>

                <p>El presidente <strong>Volodymyr Zelensky</strong> ha logrado mantener el apoyo internacional, aunque las elecciones en Estados Unidos podrían alterar significativamente este respaldo. La fatiga bélica en algunos sectores de la opinión pública occidental es palpable, y líderes como <strong>Viktor Orbán</strong> en Hungría han sido voces discordantes dentro de la alianza europea.</p>

                <p>En el frente asiático, las tensiones en el estrecho de Taiwán han escalado a niveles que recuerdan los momentos más álgidos de la Guerra Fría. <strong>Xi Jinping</strong> ha intensificado la retórica sobre la reunificación, mientras que la administración estadounidense, junto con Japón y Australia, han reforzado su presencia militar en la región. Corea del Norte, bajo <strong>Kim Jong-un</strong>, ha aprovechado estas tensiones para acelerar su programa nuclear.</p>

                <p>La crisis energética global ha puesto de manifiesto la vulnerabilidad de las cadenas de suministro internacionales. Los países del Golfo, liderados por Arabia Saudí y Emiratos Árabes Unidos, han recuperado protagonismo geopolítico, navegando hábilmente entre las presiones occidentales y sus relaciones con Rusia y China. <strong>Mohammed bin Salman</strong> ha demostrado una diplomacia pragmática que desafía las expectativas tradicionales.</p>

                <p>En América Latina, el escenario es igualmente complejo. Brasil, bajo <strong>Luiz Inácio Lula da Silva</strong>, busca posicionarse como mediador en los conflictos globales, mientras que países como Colombia y Chile redefinen sus alianzas regionales. La influencia china en la región crece silenciosamente, ofreciendo alternativas de inversión que compiten directamente con los tradicionales socios occidentales.</p>

                <p>África emerge como el continente donde se libra una nueva guerra fría silenciosa. Rusia, a través de grupos mercenarios, y China, mediante su iniciativa de la Franja y la Ruta, compiten por la influencia en un continente que alberga recursos cruciales para la transición energética mundial. Francia ve erosionada su influencia tradicional en el Sahel, mientras que nuevos actores como Turquía e India buscan su espacio.</p>

                <p>El multilateralismo atraviesa una crisis profunda. Las Naciones Unidas muestran signos evidentes de obsolescencia institucional, con un Consejo de Seguridad paralizado por los vetos cruzados entre las potencias. Organizaciones como el G7 y el G20 luchan por mantener relevancia en un mundo cada vez más fragmentado en bloques regionales.</p>

                <p>La tecnología se ha convertido en el nuevo campo de batalla geopolítico. La competencia entre Estados Unidos y China por el dominio de la inteligencia artificial, los semiconductores y las tecnologías 5G está redefiniendo las cadenas de valor globales. Europa intenta mantener su autonomía estratégica, pero se encuentra atrapada entre las dos superpotencias tecnológicas.</p>

                <p>Mirando hacia el futuro, tres escenarios parecen posibles: una bipolarización renovada entre bloques liderados por Washington y Beijing, una multipolaridad caótica donde las potencias medias ganen protagonismo, o una fragmentación regional que privilegie las alianzas geográficas sobre las ideológicas. La próxima década será crucial para determinar cuál de estas tendencias prevalece.</p>

                <p>Como observadores de este complejo tablero, debemos resistir la tentación de las predicciones categóricas. La historia nos enseña que los momentos de mayor incertidumbre son también los de mayor oportunidad para el cambio. Lo que sí parece claro es que el orden mundial tal como lo conocemos está siendo desafiado desde múltiples frentes, y las decisiones que tomen los líderes mundiales en los próximos meses definirán el rumbo de las próximas décadas.</p>
            """,
            "sources_count": len(articles),
            "analysis_date": datetime.now().isoformat()
        }
    
    def get_top_articles_from_db(self, limit=20):
        """
        Obtiene los artículos más importantes de la base de datos real
        
        Args:
            limit (int): Número máximo de artículos a obtener
            
        Returns:
            list: Lista de artículos desde la base de datos
        """
        try:
            import sqlite3
            
            # Ruta de la base de datos
            db_path = r"data\geopolitical_intel.db"
            
            if not os.path.exists(db_path):
                logger.warning(f"Base de datos no encontrada en: {db_path}")
                return self._get_mock_articles(limit)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Consulta para obtener artículos con mayor riesgo primero, priorizando los que tienen imagen
            query = """
                SELECT id, title, content, url, source, published_at, 
                       country, region, risk_level, conflict_type, 
                       sentiment_score, summary, risk_score, image_url
                FROM articles 
                ORDER BY 
                    CASE 
                        WHEN image_url IS NOT NULL AND image_url != '' 
                             AND image_url NOT LIKE '%placeholder%' 
                             AND image_url NOT LIKE '%picsum%' THEN 0
                        ELSE 1
                    END ASC,
                    CASE 
                        WHEN risk_score IS NOT NULL THEN risk_score 
                        WHEN risk_level = 'high' THEN 0.8
                        WHEN risk_level = 'medium' THEN 0.5
                        WHEN risk_level = 'low' THEN 0.2
                        ELSE 0.1
                    END DESC,
                    published_at DESC
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                article = {
                    'id': row[0],
                    'title': row[1] or 'Sin título',
                    'content': row[2] or 'Sin contenido',
                    'url': row[3],
                    'source': row[4] or 'Fuente desconocida',
                    'published_at': row[5],
                    'country': row[6] or 'Global',
                    'region': row[7] or 'Internacional',
                    'risk_level': row[8] or 'unknown',
                    'conflict_type': row[9],
                    'sentiment_score': row[10] or 0.0,
                    'summary': row[11],
                    'risk_score': row[12] or 0.0,
                    'image_url': row[13],  # Imagen real de la base de datos
                    'location': row[6] or row[7] or 'Global'
                }
                articles.append(article)
            
            conn.close()
            
            logger.info(f"✅ Obtenidos {len(articles)} artículos de la base de datos")
            return articles if articles else self._get_mock_articles(limit)
            
        except Exception as e:
            logger.error(f"Error obteniendo artículos de la base de datos: {e}")
            return self._get_mock_articles(limit)
    
    def _get_mock_articles(self, limit=20):
        """
        Obtiene artículos mock para pruebas cuando la BD no está disponible
        
        Args:
            limit (int): Número máximo de artículos mock
            
        Returns:
            list: Lista de artículos mock
        """
        try:
            mock_articles = [
                {
                    'id': 1,
                    'title': 'Escalada militar en conflicto internacional',
                    'content': 'Las tensiones militares han aumentado significativamente en la región con movilización de tropas y declaraciones oficiales que indican una posible escalada del conflicto.',
                    'location': 'Europa Oriental',
                    'risk_score': 0.8,
                    'source': 'Reuters',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 2,
                    'title': 'Crisis diplomática entre potencias mundiales',
                    'content': 'Las relaciones bilaterales se han deteriorado tras las últimas declaraciones oficiales, generando incertidumbre en los mercados internacionales.',
                    'location': 'Asia-Pacífico',
                    'risk_score': 0.7,
                    'source': 'BBC',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 3,
                    'title': 'Movimientos económicos estratégicos',
                    'content': 'Los últimos movimientos en el sector energético indican cambios importantes en las alianzas comerciales globales.',
                    'location': 'Medio Oriente',
                    'risk_score': 0.6,
                    'source': 'CNN',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 4,
                    'title': 'Amenaza nuclear en Asia Pacific aumenta tensiones',
                    'content': 'Expertos en seguridad expresan preocupación por el desarrollo de armas nucleares en la región, escalando las tensiones internacionales.',
                    'location': 'Asia Pacific',
                    'risk_score': 0.95,
                    'source': 'BBC News',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 5,
                    'title': 'Cumbre económica internacional concluye exitosamente',
                    'content': 'Los líderes mundiales alcanzan acuerdos comerciales importantes para la estabilidad económica global.',
                    'location': 'Geneva',
                    'risk_score': 0.3,
                    'source': 'AP News',
                    'created_at': datetime.now().isoformat()
                }
            ]
            
            # Simular más artículos para análisis robusto
            for i in range(6, limit + 1):
                mock_articles.append({
                    'id': i,
                    'title': f'Desarrollo geopolítico importante #{i}',
                    'content': f'Análisis de eventos significativos en diferentes regiones que impactan la estabilidad global y regional. Evento {i} con implicaciones importantes para el equilibrio de poder mundial.',
                    'location': f'Región {i % 6 + 1}',
                    'risk_score': 0.4 + (i % 6) * 0.1,
                    'source': f'Agencia Internacional {i}',
                    'created_at': datetime.now().isoformat()
                })
            
            return mock_articles[:limit]
            
        except Exception as e:
            logger.error(f"Error generando artículos mock: {e}")
            return []
    
    def _get_sample_analysis(self):
        """Obtener un análisis de ejemplo bien estructurado"""
        return """
**Tensiones Crecientes en el Tablero Geopolítico Global**

El panorama geopolítico actual refleja una complejidad sin precedentes, donde las tradicionales alianzas se ven desafiadas por nuevas realidades económicas y energéticas. Los eventos de las últimas semanas revelan patrones que exigen una lectura profunda de las dinámicas de poder en transformación.

**El Nuevo Orden Energético y sus Implicaciones**

La transición energética global está redefiniendo las relaciones internacionales de manera fundamental. Mientras Estados Unidos bajo la administración Biden mantiene su compromiso con las energías renovables, países como China y Rusia aprovechan las tensiones geopolíticas para reposicionar sus sectores energéticos tradicionales. Esta dicotomía entre la sostenibilidad ambiental y la seguridad energética inmediata está creando fricciones que van más allá de las ideologías políticas.

La reciente volatilidad en los precios del petróleo no es solo resultado de factores de oferta y demanda, sino reflejo de una nueva realidad donde la energía se ha convertido en el arma geopolítica más poderosa del siglo XXI. Las sanciones energéticas, antes consideradas de último recurso, ahora forman parte del arsenal diplomático regular.

**Conflictos Regionales con Repercusiones Globales**

Los focos de tensión en Ucrania, Oriente Medio y el Mar de China Meridional no pueden entenderse como eventos aislados. Cada uno de estos conflictos está interconectado a través de cadenas de suministro globales, rutas comerciales estratégicas y alianzas militares que trascienden las fronteras regionales.

La situación en Gaza continúa generando ondas sísmicas que afectan no solo la estabilidad regional, sino también las relaciones comerciales entre Europa y Asia. Las rutas marítimas del Mediterráneo Oriental, vitales para el comercio global, permanecen bajo constante tensión, impactando directamente en los costos de transporte y la seguridad alimentaria global.

**La Diplomacia del Cambio Climático**

Paradójicamente, mientras el mundo enfrenta crisis de seguridad inmediatas, el cambio climático emerge como el desafío que podría determinar el futuro de las relaciones internacionales. Las recientes conferencias climáticas han demostrado que la cooperación ambiental puede servir como puente incluso entre naciones en conflicto.

Los compromisos de descarbonización anunciados por la Unión Europea contrastan con las políticas energéticas más pragmáticas de países en desarrollo, creando una nueva forma de división Norte-Sur que requiere soluciones innovadoras de financiamiento y transferencia tecnológica.

**Perspectivas y Desafíos Inmediatos**

Los próximos meses serán cruciales para determinar si la comunidad internacional puede navegar estas aguas turbulentas sin precipitar un conflicto de mayor escala. La estabilidad económica global depende en gran medida de la capacidad de los líderes mundiales para separar los intereses geopolíticos de corto plazo de los desafíos existenciales de largo plazo.

La interdependencia económica, que una vez se consideró garantía de paz, ahora se percibe como una vulnerabilidad estratégica. Esta paradoja define el momento actual: la necesidad de cooperación nunca ha sido mayor, pero la confianza mutua nunca ha estado más erosionada.

El análisis de estos eventos sugiere que estamos presenciando no solo crisis temporales, sino una transformación fundamental del orden internacional establecido después de la Segunda Guerra Mundial. Las instituciones multilaterales enfrentan su prueba más severa, y su capacidad de adaptación determinará la estabilidad global en las próximas décadas.
"""
    
    def _get_fallback_analysis(self):
        """Análisis de respaldo en caso de error"""
        return """
**Análisis Geopolítico - Estado Actual del Sistema Global**

En el complejo tablero geopolítico actual, observamos una convergencia de factores que están redefiniendo las relaciones internacionales. Los eventos recientes reflejan tensiones profundas en múltiples frentes que requieren un análisis cuidadoso.

**Dinámicas Energéticas y Económicas**

La seguridad energética continúa siendo un factor determinante en las decisiones políticas globales. Las fluctuaciones en los mercados de commodities y las interrupciones en las cadenas de suministro están forzando a los países a reconsiderar sus estrategias de independencia energética.

**Tensiones Regionales**

Los conflictos actuales demuestran la interconexión entre la estabilidad regional y la prosperidad global. Las decisiones tomadas en centros de poder tradicionales continúan teniendo repercusiones que se extienden mucho más allá de sus fronteras inmediatas.

**El Factor Climático**

La urgencia del cambio climático añade una dimensión crítica a todas las consideraciones geopolíticas. La necesidad de transición hacia energías sostenibles debe equilibrarse cuidadosamente con las realidades políticas y económicas inmediatas.

**Perspectivas Futuras**

La estabilidad internacional dependerá de la capacidad de los líderes mundiales para encontrar soluciones que atiendan tanto las preocupaciones de seguridad inmediatas como los desafíos de sostenibilidad a largo plazo. La diplomacia preventiva y el multilateralismo efectivo serán clave para navegar este período de incertidumbre.

*Este análisis se basa en información pública disponible y refleja una perspectiva equilibrada sobre los desarrollos geopolíticos actuales.*
"""
    
    def _run_smart_positioning_full(self, smart_positioning):
        """
        Ejecutar sistema completo de posicionamiento inteligente en background
        """
        try:
            logger.info("🚀 Iniciando sistema completo de posicionamiento inteligente...")
            
            # Paso 1: Actualizar fingerprints
            logger.info("📋 Actualizando fingerprints de imágenes...")
            fingerprint_results = smart_positioning.update_all_image_fingerprints()
            logger.info(f"✅ Fingerprints: {fingerprint_results}")
            
            # Paso 2: Detectar y resolver duplicados
            logger.info("📋 Detectando imágenes duplicadas...")
            duplicates = smart_positioning.check_duplicate_images()
            
            if duplicates:
                logger.info(f"🔍 Encontrados {len(duplicates)} pares similares")
                resolution_results = smart_positioning.resolve_duplicate_images(duplicates)
                logger.info(f"✅ Duplicados resueltos: {resolution_results}")
            
            # Paso 3: Optimizar calidad
            logger.info("📋 Optimizando imágenes de baja calidad...")
            optimization_results = smart_positioning.optimize_low_quality_images()
            logger.info(f"✅ Optimización: {optimization_results}")
            
            # Paso 4: Asignar posiciones
            logger.info("📋 Asignando posiciones del mosaico...")
            position_results = smart_positioning.assign_mosaic_positions()
            logger.info(f"✅ Posiciones: {position_results}")
            
            # Actualizar estadísticas del sistema
            self.system_state['smart_positioning_last_run'] = datetime.now().isoformat()
            self.system_state['smart_positioning_results'] = {
                'fingerprints': fingerprint_results,
                'duplicates_found': len(duplicates),
                'optimization': optimization_results,
                'positions': position_results
            }
            
            logger.info("🎉 Sistema de posicionamiento inteligente completado")
            
        except Exception as e:
            logger.error(f"Error en posicionamiento inteligente: {e}")
            raise
    
    def ensure_smart_positioning_tables(self):
        """
        Asegurar que existen las tablas y columnas necesarias para el posicionamiento inteligente
        """
        try:
            db_path = get_database_path()
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar y añadir columnas necesarias
                cursor.execute("PRAGMA table_info(articles)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'mosaic_position' not in columns:
                    cursor.execute("ALTER TABLE articles ADD COLUMN mosaic_position TEXT DEFAULT 'standard'")
                    logger.info("✅ Columna mosaic_position añadida")
                
                if 'image_fingerprint' not in columns:
                    cursor.execute("ALTER TABLE articles ADD COLUMN image_fingerprint TEXT")
                    logger.info("✅ Columna image_fingerprint añadida")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error configurando tablas de posicionamiento: {e}")
    
    def get_smart_positioning_statistics(self):
        """
        Obtener estadísticas del sistema de posicionamiento inteligente
        """
        try:
            from src.dashboard.smart_mosaic_layout import get_mosaic_layout_stats
            return get_mosaic_layout_stats()
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de posicionamiento: {e}")
            return {}
    
    def _clean_old_logs(self):
        """Limpiar logs antiguos"""
        try:
            log_dir = Path('logs')
            if log_dir.exists():
                # Keep logs for last 30 days
                cutoff_date = datetime.now() - timedelta(days=30)
                
                for log_file in log_dir.glob('*.log'):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file}")
                        
        except Exception as e:
            logger.error(f"Error cleaning old logs: {e}")
    
    def _create_templates(self):
        """Crear templates HTML necesarios"""
        templates_dir = Path('src/web/templates')
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Template principal unificado
        unified_template = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiskMap - Sistema Unificado de Análisis Geopolítico</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .status-running { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-error { background-color: #dc3545; }
        .status-inactive { background-color: #6c757d; }
        .card-feature { transition: transform 0.2s; cursor: pointer; }
        .card-feature:hover { transform: translateY(-5px); }
        .stats-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🗺️ RiskMap</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard">Dashboard Histórico</a>
                <a class="nav-link" href="/multivariate">Análisis Multivariable</a>
                <a class="nav-link" href="/logs">Logs</a>
                <a class="nav-link" href="/settings">Configuración</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h1>🗺️ RiskMap - Sistema Unificado de Análisis Geopolítico</h1>
                <p class="lead">Plataforma integral de inteligencia geopolítica con ingesta automática, procesamiento NLP y análisis histórico multivariable.</p>
            </div>
        </div>

        <!-- Estado del Sistema -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>🔧 Estado del Sistema</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-2">
                                <div class="d-flex align-items-center">
                                    <span id="system-status-indicator" class="status-indicator status-inactive"></span>
                                    <span>Sistema: <span id="system-status">{{ system_state.system_status }}</span></span>
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="d-flex align-items-center">
                                    <span id="ingestion-indicator" class="status-indicator {% if system_state.data_ingestion_running %}status-running{% else %}status-inactive{% endif %}"></span>
                                    <span>Ingesta RSS</span>
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="d-flex align-items-center">
                                    <span id="processing-indicator" class="status-indicator {% if system_state.nlp_processing_running %}status-running{% else %}status-inactive{% endif %}"></span>
                                    <span>Procesamiento NLP</span>
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="d-flex align-items-center">
                                    <span id="analysis-indicator" class="status-indicator {% if system_state.historical_analysis_running %}status-running{% else %}status-inactive{% endif %}"></span>
                                    <span>Análisis Histórico</span>
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="d-flex align-items-center">
                                    <span id="dashboard-indicator" class="status-indicator {% if system_state.dashboards_ready %}status-running{% else %}status-inactive{% endif %}"></span>
                                    <span>Dashboards</span>
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="d-flex align-items-center">
                                    <span id="api-indicator" class="status-indicator {% if system_state.api_ready %}status-running{% else %}status-inactive{% endif %}"></span>
                                    <span>API REST</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Estadísticas -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stats-card">
                    <div class="card-body text-center">
                        <h3 id="total-articles">{{ system_state.statistics.total_articles }}</h3>
                        <p>Artículos Totales</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card">
                    <div class="card-body text-center">
                        <h3 id="processed-articles">{{ system_state.statistics.processed_articles }}</h3>
                        <p>Artículos Procesados</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card">
                    <div class="card-body text-center">
                        <h3 id="risk-alerts">{{ system_state.statistics.risk_alerts }}</h3>
                        <p>Alertas de Riesgo</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card">
                    <div class="card-body text-center">
                        <h3 id="data-sources">{{ system_state.statistics.data_sources }}</h3>
                        <p>Fuentes de Datos</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Controles del Sistema -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>⚡ Controles del Sistema</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-2">
                                <button id="btn-initialize" class="btn btn-primary w-100" onclick="initializeSystem()">
                                    🚀 Inicializar Todo
                                </button>
                            </div>
                            <div class="col-md-2">
                                <button id="btn-start-ingestion" class="btn btn-info w-100" onclick="startIngestion()">
                                    📡 Iniciar Ingesta
                                </button>
                            </div>
                            <div class="col-md-2">
                                <button id="btn-start-processing" class="btn btn-success w-100" onclick="startProcessing()">
                                    🧠 Iniciar NLP
                                </button>
                            </div>
                            <div class="col-md-2">
                                <button id="btn-start-analysis" class="btn btn-warning w-100" onclick="startAnalysis()">
                                    📊 Iniciar Análisis
                                </button>
                            </div>
                            <div class="col-md-2">
                                <button id="btn-refresh" class="btn btn-secondary w-100" onclick="refreshStatus()">
                                    🔄 Actualizar
                                </button>
                            </div>
                            <div class="col-md-2">
                                <button id="btn-view-logs" class="btn btn-dark w-100" onclick="window.open('/logs', '_blank')">
                                    📋 Ver Logs
                                </button>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-md-3">
                                <button id="btn-test-groq" class="btn btn-outline-primary w-100" onclick="testGroq()">
                                    🤖 Test Groq API
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button id="btn-groq-analysis" class="btn btn-outline-success w-100" onclick="generateGroqAnalysis()">
                                    📝 Análisis Groq
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button id="btn-view-analysis" class="btn btn-outline-info w-100" onclick="viewLastAnalysis()">
                                    👁️ Ver Último Análisis
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button id="btn-export-data" class="btn btn-outline-warning w-100" onclick="exportData()">
                                    💾 Exportar Datos
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Funcionalidades Principales -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card card-feature" onclick="window.open('/dashboard', '_blank')">
                    <div class="card-body text-center">
                        <h5 class="card-title">📊 Dashboard Histórico</h5>
                        <p class="card-text">Análisis temporal, patrones históricos y predicciones basadas en 100+ años de datos.</p>
                        <span class="btn btn-outline-primary">Abrir Dashboard</span>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card card-feature" onclick="window.open('/multivariate', '_blank')">
                    <div class="card-body text-center">
                        <h5 class="card-title">🔗 Análisis Multivariable</h5>
                        <p class="card-text">Relaciones entre variables energéticas, climáticas, políticas, sanitarias y de recursos.</p>
                        <span class="btn btn-outline-success">Abrir Análisis</span>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card card-feature" onclick="window.open('/api/v1/docs', '_blank')">
                    <div class="card-body text-center">
                        <h5 class="card-title">🔌 API REST</h5>
                        <p class="card-text">Acceso programático a todos los datos y análisis del sistema.</p>
                        <span class="btn btn-outline-info">Ver Documentación</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Alertas Recientes -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>🚨 Alertas Recientes</h5>
                    </div>
                    <div class="card-body">
                        <div id="alerts-container">
                            <p class="text-muted">No hay alertas recientes</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // JavaScript functions for system control
        async function initializeSystem() {
            try {
                const response = await axios.post('/api/system/initialize');
                if (response.data.success) {
                    showAlert('success', 'Sistema inicializándose en segundo plano...');
                    refreshStatus();
                } else {
                    showAlert('error', 'Error: ' + response.data.error);
                }
            } catch (error) {
                showAlert('error', 'Error de conexión: ' + error.message);
            }
        }

        async function startIngestion() {
            try {
                const response = await axios.post('/api/ingestion/start');
                if (response.data.success) {
                    showAlert('success', 'Ingesta de datos iniciada...');
                    refreshStatus();
                } else {
                    showAlert('error', 'Error: ' + response.data.error);
                }
            } catch (error) {
                showAlert('error', 'Error de conexión: ' + error.message);
            }
        }

        async function startProcessing() {
            try {
                const response = await axios.post('/api/processing/start');
                if (response.data.success) {
                    showAlert('success', 'Procesamiento NLP iniciado...');
                    refreshStatus();
                } else {
                    showAlert('error', 'Error: ' + response.data.error);
                }
            } catch (error) {
                showAlert('error', 'Error de conexión: ' + error.message);
            }
        }

        async function startAnalysis() {
            try {
                const response = await axios.post('/api/analysis/start');
                if (response.data.success) {
                    showAlert('success', 'Análisis histórico iniciado...');
                    refreshStatus();
                } else {
                    showAlert('error', 'Error: ' + response.data.error);
                }
            } catch (error) {
                showAlert('error', 'Error de conexión: ' + error.message);
            }
        }

        async function testGroq() {
            try {
                showAlert('info', 'Probando conexión con Groq API...');
                const response = await axios.get('/api/groq/test');
                if (response.data.success) {
                    showAlert('success', 'Groq API: ' + response.data.message + ' - Respuesta: ' + response.data.test_response);
                } else {
                    showAlert('error', 'Error Groq: ' + response.data.error);
                }
            } catch (error) {
                showAlert('error', 'Error probando Groq: ' + error.message);
            }
        }

        async function generateGroqAnalysis() {
            try {
                showAlert('info', 'Generando análisis geopolítico con Groq... (esto puede tardar unos segundos)');
                const response = await axios.get('/api/groq/analysis');
                if (response.data.success) {
                    const analysis = response.data.analysis;
                    showAlert('success', 'Análisis generado exitosamente con ' + response.data.articles_count + ' artículos');
                    
                    // Mostrar el análisis en un modal
                    showAnalysisModal(analysis);
                } else {
                    showAlert('error', 'Error generando análisis: ' + response.data.error);
                    if (response.data.fallback_analysis) {
                        showAnalysisModal(response.data.fallback_analysis);
                    }
                }
            } catch (error) {
                showAlert('error', 'Error generando análisis: ' + error.message);
            }
        }

        function showAnalysisModal(analysis) {
            const modalHtml = `
                <div class="modal fade" id="analysisModal" tabindex="-1">
                    <div class="modal-dialog modal-xl">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">📝 ${analysis.title || 'Análisis Geopolítico'}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                ${analysis.subtitle ? '<h6 class="text-muted mb-3">' + analysis.subtitle + '</h6>' : ''}
                                <div class="analysis-content">
                                    ${analysis.content || analysis}
                                </div>
                                ${analysis.sources_count ? '<p class="text-muted mt-3"><small>Basado en ' + analysis.sources_count + ' fuentes</small></p>' : ''}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-primary" onclick="exportAnalysis()">💾 Exportar</button>
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('analysisModal');
            if (existingModal) existingModal.remove();
            
            // Add new modal to body
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
            modal.show();
        }

        function viewLastAnalysis() {
            showAlert('info', 'Funcionalidad en desarrollo - por ahora usa "Análisis Groq"');
        }

        function exportData() {
            showAlert('info', 'Funcionalidad de exportación en desarrollo');
        }

        function exportAnalysis() {
            const content = document.querySelector('.analysis-content').innerHTML;
            const blob = new Blob([content], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'analisis_geopolitico_' + new Date().toISOString().slice(0,10) + '.html';
            a.click();
            URL.revokeObjectURL(url);
        }

        async function refreshStatus() {
            try {
                // Get system status
                const statusResponse = await axios.get('/api/system/status');
                if (statusResponse.data.success) {
                    updateStatusDisplay(statusResponse.data.system_state);
                }
                
                // Get statistics
                const statsResponse = await axios.get('/api/statistics');
                if (statsResponse.data.success) {
                    updateStatistics(statsResponse.data.statistics);
                }
                
                // Get alerts
                const alertsResponse = await axios.get('/api/alerts');
                if (alertsResponse.data.success) {
                    updateAlerts(alertsResponse.data.alerts);
                }
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        }

        function updateStatusDisplay(systemState) {
            // Update status indicators
            document.getElementById('system-status').textContent = systemState.system_status;
            document.getElementById('system-status-indicator').className = 'status-indicator ' + getStatusClass(systemState.system_status);
            
            document.getElementById('ingestion-indicator').className = 'status-indicator ' + (systemState.data_ingestion_running ? 'status-running' : 'status-inactive');
            document.getElementById('processing-indicator').className = 'status-indicator ' + (systemState.nlp_processing_running ? 'status-running' : 'status-inactive');
            document.getElementById('analysis-indicator').className = 'status-indicator ' + (systemState.historical_analysis_running ? 'status-running' : 'status-inactive');
            document.getElementById('dashboard-indicator').className = 'status-indicator ' + (systemState.dashboards_ready ? 'status-running' : 'status-inactive');
            document.getElementById('api-indicator').className = 'status-indicator ' + (systemState.api_ready ? 'status-running' : 'status-inactive');
        }

        function updateStatistics(stats) {
            document.getElementById('total-articles').textContent = stats.total_articles || 0;
            document.getElementById('processed-articles').textContent = stats.processed_articles || 0;
            document.getElementById('risk-alerts').textContent = stats.risk_alerts || 0;
            document.getElementById('data-sources').textContent = stats.data_sources || 0;
        }

        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<p class="text-muted">No hay alertas recientes</p>';
                return;
            }

            let html = '';
            alerts.slice(-5).forEach(alert => {
                const alertClass = alert.type.includes('error') || alert.type.includes('failed') ? 'danger' : 
                                 alert.type.includes('warning') ? 'warning' : 'info';
                html += `
                    <div class="alert alert-${alertClass} alert-sm">
                        <strong>${alert.type}</strong>: ${alert.message}
                        <small class="text-muted d-block">${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        function getStatusClass(status) {
            if (status.includes('running') || status.includes('initialized') || status.includes('ready')) return 'status-running';
            if (status.includes('failed') || status.includes('error')) return 'status-error';
            if (status.includes('initializing') || status.includes('starting')) return 'status-warning';
            return 'status-inactive';
        }

        function showAlert(type, message) {
            const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-danger' : 'alert-info';
            const alertHtml = `
                <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            
            // Insert at top of page
            const container = document.querySelector('.container-fluid');
            container.insertAdjacentHTML('afterbegin', alertHtml);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                const alert = container.querySelector('.alert');
                if (alert) alert.remove();
            }, 5000);
        }

        // Auto-refresh every 10 seconds
        setInterval(refreshStatus, 10000);
        
        // Initial load
        document.addEventListener('DOMContentLoaded', refreshStatus);
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        '''
        
        with open(templates_dir / 'unified_index.html', 'w', encoding='utf-8') as f:
            f.write(unified_template)
        
        # Create other necessary templates
        self._create_additional_templates(templates_dir)
        
        logger.info("HTML templates created successfully")
    
    def _create_additional_templates(self, templates_dir):
        """Crear templates adicionales"""
        # Settings template
        settings_template = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configuración - RiskMap</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🗺️ RiskMap</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Inicio</a>
            </div>
        </div>
    </nav>
    <div class="container mt-4">
        <h1>⚙️ Configuración del Sistema</h1>
        <div class="card">
            <div class="card-body">
                <h5>Configuración Actual</h5>
                <pre>{{ config | tojson(indent=2) }}</pre>
            </div>
        </div>
    </div>
</body>
</html>
        '''
        
        # Logs template
        logs_template = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Logs del Sistema - RiskMap</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .log-content { font-family: monospace; font-size: 12px; background: #f8f9fa; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🗺️ RiskMap</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Inicio</a>
            </div>
        </div>
    </nav>
    <div class="container-fluid mt-4">
        <h1>📋 Logs del Sistema</h1>
        <div class="card">
            <div class="card-body">
                <div class="log-content" style="height: 600px; overflow-y: scroll;">
                    {% for line in log_content %}
                    <div>{{ line }}</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        '''
        
        with open(templates_dir / 'settings.html', 'w', encoding='utf-8') as f:
            f.write(settings_template)
        
        with open(templates_dir / 'logs.html', 'w', encoding='utf-8') as f:
            f.write(logs_template)
    
    def start_application(self):
        """Iniciar la aplicación web unificada"""
        try:
            logger.info("Starting RiskMap Unified Application...")
            
            # Create templates
            self._create_templates()
            
            # Auto-initialize if enabled
            if self.config['auto_initialize']:
                self._run_background_task('auto_initialize', self._initialize_all_systems)
            
            # Print startup information
            print("\n" + "="*80)
            print("🗺️  RISKMAP - SISTEMA UNIFICADO DE ANÁLISIS GEOPOLÍTICO")
            print("="*80)
            print("🚀 INICIANDO TODOS LOS SISTEMAS AUTOMÁTICAMENTE:")
            print("   ✅ Ingesta RSS/OSINT automática")
            print("   ✅ Procesamiento NLP en tiempo real")
            print("   ✅ Análisis histórico multivariable")
            print("   ✅ Dashboards interactivos integrados")
            print("   ✅ API REST completa")
            print("   ✅ Monitoreo y alertas automáticas")
            print("="*80)
            print("🌐 INTERFACES DISPONIBLES:")
            print(f"   📱 Interfaz Principal: http://localhost:{self.config['flask_port']}")
            print(f"   📊 Dashboard Histórico: http://localhost:{self.config['flask_port']}/dashboard")
            print(f"   🔗 Análisis Multivariable: http://localhost:{self.config['flask_port']}/multivariate")
            print(f"   🔌 API REST: http://localhost:{self.config['flask_port']}/api/v1/docs")
            print(f"   📋 Logs del Sistema: http://localhost:{self.config['flask_port']}/logs")
            print("="*80)
            print("⚡ PROCESOS AUTOMÁTICOS:")
            print(f"   🔄 Ingesta de datos cada {self.config['ingestion_interval_hours']} horas")
            print(f"   🧠 Procesamiento NLP cada {self.config['processing_interval_hours']} horas")
            print(f"   📊 Análisis histórico cada {self.config['analysis_interval_hours']} horas")
            print("="*80)
            print("✨ NO NECESITAS EJECUTAR COMANDOS ADICIONALES")
            print("✨ TODO SE EJECUTA AUTOMÁTICAMENTE EN SEGUNDO PLANO")
            print("✨ SOLO NAVEGA POR LA INTERFAZ WEB")
            print("="*80)
            print()
            print("🔥" * 30)
            print(f"🔥🔥🔥  SERVIDOR INICIANDO EN PUERTO {self.config['flask_port']}  🔥🔥🔥")
            print(f"🔥🔥🔥  ACCEDE A: http://localhost:{self.config['flask_port']}  🔥🔥🔥")
            print("🔥" * 30)
            print()
            
            # Start Flask server
            print(f"⏳ Iniciando servidor Flask en puerto {self.config['flask_port']}...")
            self.flask_app.run(
                host=self.config['flask_host'],
                port=self.config['flask_port'],
                debug=self.config['flask_debug'],
                threaded=True,
                use_reloader=False  # Disable reloader to avoid issues with background threads
            )
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            raise
    
    def stop_application(self):
        """Detener la aplicación gracefully"""
        try:
            logger.info("Stopping RiskMap Unified Application...")
            
            # Stop satellite monitoring
            if AUTOMATED_SATELLITE_AVAILABLE and self.automated_satellite_monitor:
                try:
                    logger.info("Stopping automated satellite monitoring...")
                    self.automated_satellite_monitor.stop_monitoring()
                    self.system_state['satellite_monitoring_running'] = False
                    logger.info("✅ Automated satellite monitoring stopped")
                except Exception as e:
                    logger.error(f"Error stopping satellite monitoring: {e}")
            
            # Stop enrichment system
            if self.enrichment_system:
                try:
                    logger.info("Stopping enrichment system...")
                    self.enrichment_system.stop_automatic_enrichment()
                    self.system_state['enrichment_running'] = False
                    logger.info("✅ Enrichment system stopped")
                except Exception as e:
                    logger.error(f"Error stopping enrichment system: {e}")
            
            # Set shutdown event
            self.shutdown_event.set();
            
            # Wait for background threads to finish
            for thread_name, thread in self.background_threads.items():
                if thread.is_alive():
                    logger.info(f"Waiting for background thread {thread_name} to finish...")
                    thread.join(timeout=5)
            
            self.system_state['system_status'] = 'stopped'
            logger.info("Application stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
    
    def extract_image_from_url(self, url, article_id, title):
        """Extraer imagen de la URL del artículo, buscando la mejor resolución disponible"""
        try:
            logger.info(f"Extrayendo imagen para artículo {article_id}: {title[:50]}...")
            
            # Método 1: Buscar imágenes usando BeautifulSoup con prioridad por resolución
            image_candidates = self._scrape_all_article_images(url)
            
            if image_candidates:
                # Procesar candidatos para encontrar la mejor imagen
                best_image = self._select_best_image(image_candidates, article_id)
                if best_image:
                    return best_image
            
            # Método 2: Buscar en redes sociales y meta tags
            social_image = self._scrape_social_media_images(url)
            if social_image:
                image_path = self._download_and_save_image(social_image, article_id, "social")
                if image_path:
                    return image_path
            
            # Método 3: Imagen de placeholder como último recurso
            logger.warning(f"No se pudo extraer imagen real para artículo {article_id}, generando placeholder personalizado")
            placeholder_path = self._generate_custom_placeholder(article_id, title)
            return placeholder_path
            
        except Exception as e:
            logger.error(f"Error extrayendo imagen del artículo {article_id}: {e}")
            return self._generate_custom_placeholder(article_id, title)
    
    def _scrape_all_article_images(self, url):
        """Buscar todas las imágenes posibles del artículo para seleccionar la mejor"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            image_candidates = []
            
            # Selectores ordenados por prioridad (más específicos primero)
            selectors_priority = [
                ('meta[property="og:image"]', 'og_image', 'content'),
                ('meta[name="twitter:image"]', 'twitter_image', 'content'),
                ('meta[property="og:image:url"]', 'og_image_url', 'content'),
                ('.hero-image img', 'hero', 'src'),
                ('.featured-image img', 'featured', 'src'),
                ('.article-image img', 'article', 'src'),
                ('.post-thumbnail img', 'thumbnail', 'src'),
                ('article img', 'article_content', 'src'),
                ('.main-image img', 'main', 'src'),
                ('figure img', 'figure', 'src'),
                ('.content img', 'content', 'src'),
                ('img[class*="featured"]', 'featured_class', 'src'),
                ('img[class*="main"]', 'main_class', 'src'),
                ('img[class*="hero"]', 'hero_class', 'src')
            ]
            
            for selector, source_type, attr in selectors_priority:
                elements = soup.select(selector)
                for element in elements:
                    image_url = element.get(attr) or element.get('data-src') or element.get('data-lazy-src')
                    
                    if image_url:
                        # Convertir URL relativa a absoluta
                        full_url = urljoin(url, image_url)
                        
                        # Obtener información adicional de la imagen
                        width = element.get('width') or element.get('data-width')
                        height = element.get('height') or element.get('data-height')
                        alt = element.get('alt', '')
                        
                        candidate = {
                            'url': full_url,
                            'source_type': source_type,
                            'width': self._parse_dimension(width),
                            'height': self._parse_dimension(height),
                            'alt': alt,
                            'priority': len(image_candidates)  # Orden de aparición
                        }
                        
                        if self._is_valid_image_url(full_url):
                            image_candidates.append(candidate)
            
            return image_candidates
            
        except Exception as e:
            logger.error(f"Error buscando imágenes en {url}: {e}")
            return []
    
    def _scrape_social_media_images(self, url):
        """Buscar específicamente en meta tags de redes sociales"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar en meta tags específicos
            social_selectors = [
                'meta[property="og:image"]',
                'meta[property="og:image:url"]',
                'meta[property="og:image:secure_url"]',
                'meta[name="twitter:image"]',
                'meta[name="twitter:image:src"]',
                'link[rel="image_src"]'
            ]
            
            for selector in social_selectors:
                element = soup.select_one(selector)
                if element:
                    image_url = element.get('content') or element.get('href')
                    if image_url:
                        full_url = urljoin(url, image_url)
                        if self._is_valid_image_url(full_url):
                            return full_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando imágenes sociales en {url}: {e}")
            return None
    
    def _select_best_image(self, candidates, article_id):
        """Seleccionar la mejor imagen de entre los candidatos"""
        if not candidates:
            return None
        
        try:
            # Filtrar candidatos válidos
            valid_candidates = []
            
            for candidate in candidates:
                # Verificar que la imagen sea accesible y obtener sus dimensiones reales
                image_info = self._get_image_info(candidate['url'])
                if image_info:
                    candidate.update(image_info)
                    valid_candidates.append(candidate)
            
            if not valid_candidates:
                return None
            
            # Criterios de selección (en orden de prioridad):
            # 1. Resolución mínima aceptable (al menos 300x200)
            # 2. Aspecto ratio razonable (no muy estrecho o muy alto)
            # 3. Tamaño de archivo razonable
            # 4. Tipo de fuente (og:image tiene prioridad)
            
            scored_candidates = []
            
            for candidate in valid_candidates:
                score = 0
                width = candidate.get('real_width', 0)
                height = candidate.get('real_height', 0)
                file_size = candidate.get('file_size', 0)
                
                # Puntuación por resolución
                if width >= 800 and height >= 600:
                    score += 100
                elif width >= 600 and height >= 400:
                    score += 80
                elif width >= 400 and height >= 300:
                    score += 60
                elif width >= 300 and height >= 200:
                    score += 40
                else:
                    score += 10
                
                # Puntuación por aspecto ratio (preferir 16:9, 4:3, etc.)
                if width > 0 and height > 0:
                    ratio = width / height
                    if 1.2 <= ratio <= 2.0:  # Aspecto ratio razonable
                        score += 20
                    elif 1.0 <= ratio <= 2.5:
                        score += 10
                
                # Puntuación por tipo de fuente
                source_scores = {
                    'og_image': 30,
                    'twitter_image': 25,
                    'hero': 20,
                    'featured': 18,
                    'article': 15,
                    'thumbnail': 10
                }
                score += source_scores.get(candidate['source_type'], 5)
                
                # Penalizar imágenes muy pequeñas en tamaño
                if file_size > 50000:  # Mayor a 50KB
                    score += 10
                elif file_size > 20000:  # Mayor a 20KB
                    score += 5
                
                scored_candidates.append((score, candidate))
            
            # Seleccionar la imagen con mayor puntuación
            if scored_candidates:
                best_score, best_candidate = max(scored_candidates, key=lambda x: x[0])
                logger.info(f"Seleccionada imagen con puntuación {best_score}: {best_candidate['url']}")
                
                # Descargar la mejor imagen
                image_path = self._download_and_save_image(
                    best_candidate['url'], 
                    article_id, 
                    best_candidate['source_type']
                )
                return image_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error seleccionando mejor imagen: {e}")
            return None
    
    def _get_image_info(self, image_url):
        """Obtener información de una imagen (dimensiones, tamaño, etc.)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Hacer una petición HEAD primero para verificar el tipo
            head_response = requests.head(image_url, headers=headers, timeout=10)
            
            if not head_response.headers.get('Content-Type', '').startswith('image/'):
                return None
            
            # Obtener tamaño del archivo
            file_size = int(head_response.headers.get('Content-Length', 0))
            
            # Si es muy pequeña, descartar
            if file_size > 0 and file_size < 5000:  # Menos de 5KB
                return None
            
            # Para obtener dimensiones, necesitamos descargar al menos parte de la imagen
            response = requests.get(image_url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()
            
            # Leer solo los primeros bytes para obtener dimensiones
            image_data = b''
            for chunk in response.iter_content(chunk_size=8192):
                image_data += chunk
                if len(image_data) > 50000:  # Máximo 50KB para análisis
                    break
            
            # Usar PIL para obtener dimensiones
            try:
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(image_data))
                width, height = image.size
                
                return {
                    'real_width': width,
                    'real_height': height,
                    'file_size': file_size or len(image_data),
                    'format': image.format
                }
            except Exception:
                return {'file_size': file_size}
            
        except Exception as e:
            logger.debug(f"Error obteniendo info de imagen {image_url}: {e}")
            return None
    
    def _parse_dimension(self, value):
        """Parsear dimensión desde atributo HTML"""
        if not value:
            return 0
        try:
            # Remover 'px' y otros sufijos
            value = str(value).replace('px', '').replace('%', '')
            return int(float(value))
        except:
            return 0
    
    def _generate_custom_placeholder(self, article_id, title):
        """Generar un placeholder personalizado LOCAL para el artículo"""
        try:
            # Crear directorio de placeholders si no existe
            placeholder_dir = Path("static/images/placeholders")
            placeholder_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar filename único para el placeholder
            safe_title = "".join(c for c in title[:20] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"placeholder_{article_id}_{safe_title.replace(' ', '_')}.png"
            placeholder_path = placeholder_dir / filename
            
            # Si ya existe, retornar la ruta
            if placeholder_path.exists():
                return f"/static/images/placeholders/{filename}"
            
            # Crear imagen placeholder local usando PIL
            from PIL import Image, ImageDraw, ImageFont
            
            # Crear imagen de 800x600 con color azul corporativo
            img = Image.new('RGB', (800, 600), color=(37, 99, 235))  # Azul corporativo
            draw = ImageDraw.Draw(img)
            
            # Intentar usar una fuente más grande si está disponible
            try:
                font = ImageFont.truetype("arial.ttf", 40)
                small_font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Texto principal
            main_text = f"Artículo #{article_id}"
            text_width = draw.textlength(main_text, font=font)
            x = (800 - text_width) // 2
            y = 250
            draw.text((x, y), main_text, fill=(255, 255, 255), font=font)
            
            # Título truncado
            title_text = title[:60] + "..." if len(title) > 60 else title
            title_width = draw.textlength(title_text, font=small_font)
            x_title = (800 - title_width) // 2
            y_title = 320
            draw.text((x_title, y_title), title_text, fill=(255, 255, 255), font=small_font)
            
            # Guardar imagen
            img.save(placeholder_path, 'PNG')
            
            logger.info(f"Placeholder local generado: {placeholder_path}")
            return f"/static/images/placeholders/{filename}"
            
        except Exception as e:
            logger.error(f"Error generando placeholder local: {e}")
            # Como último recurso, retornar None para que no se use imagen
            return None
    
    def _scrape_article_image(self, url):
        """Buscar imagen principal del artículo usando web scraping"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Selectores comunes para imágenes de artículos
            image_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                'article img',
                '.article-image img',
                '.post-thumbnail img',
                '.featured-image img',
                '.hero-image img',
                '.main-image img',
                'figure img',
                '.content img'
            ]
            
            for selector in image_selectors:
                elements = soup.select(selector)
                for element in elements:
                    if selector.startswith('meta'):
                        image_url = element.get('content')
                    else:
                        image_url = element.get('src') or element.get('data-src')
                    
                    if image_url:
                        # Convertir URL relativa a absoluta
                        image_url = urljoin(url, image_url)
                        
                        # Verificar que la imagen sea válida
                        if self._is_valid_image_url(image_url):
                            logger.info(f"Imagen encontrada: {image_url}")
                            return image_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error en scraping de imagen para {url}: {e}")
            return None
    
    def _is_valid_image_url(self, url):
        """Verificar si la URL de imagen es válida"""
        try:
            # Verificar extensión
            parsed = urlparse(url)
            path = parsed.path.lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            
            if any(path.endswith(ext) for ext in valid_extensions):
                return True
            
            # Verificar content-type si no hay extensión clara
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.head(url, headers=headers, timeout=5)
                content_type = response.headers.get('Content-Type', '')
                if content_type.startswith('image/'):
                    return True
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando URL de imagen: {e}")
            return False
    
    def _download_and_save_image(self, image_url, article_id, source_type):
        """Descargar y guardar imagen"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Verificar que es una imagen
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL no es una imagen: {content_type}")
                return None
            
            # Crear directorio de imágenes si no existe
            images_dir = Path("static/images/articles")
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # Determinar extensión
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                ext = '.jpg'
            
            # Generar nombre de archivo único
            filename = f"article_{article_id}_{source_type}_{int(time.time())}{ext}"
            file_path = images_dir / filename
            
            # Guardar imagen
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Verificar que la imagen se guardó correctamente
            if file_path.exists() and file_path.stat().st_size > 1000:  # Al menos 1KB
                relative_path = f"static/images/articles/{filename}"
                logger.info(f"Imagen guardada: {relative_path}")
                return relative_path
            else:
                if file_path.exists():
                    file_path.unlink()
                return None
                
        except Exception as e:
            logger.error(f"Error descargando imagen {image_url}: {e}")
            return None
    
    def update_article_image(self, article_id, image_path):
        """Actualizar la imagen del artículo en la base de datos"""
        try:
            db_path = get_database_path()
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE articles 
                    SET image_url = ? 
                    WHERE id = ?
                """, (image_path, article_id))
                
                conn.commit()
                logger.info(f"Imagen actualizada en BD para artículo {article_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error actualizando imagen en BD para artículo {article_id}: {e}")
            return False
    
    def get_articles_without_images(self, limit=50):
        """Obtener artículos que no tienen imagen o tienen imágenes de baja calidad"""
        try:
            db_path = get_database_path()
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, url, source, image_url
                    FROM articles 
                    WHERE (
                        image_url IS NULL 
                        OR image_url = '' 
                        OR image_url LIKE '%placeholder%' 
                        OR image_url LIKE '%picsum%'
                        OR image_url LIKE '%via.placeholder%'
                        OR image_url LIKE '%300x200%'
                        OR image_url LIKE '%400x300%'
                    )
                    AND url IS NOT NULL 
                    AND url != ''
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
                articles = cursor.fetchall()
                logger.info(f"Encontrados {len(articles)} artículos que necesitan imágenes de mejor calidad")
                return articles
        except Exception as e:
            logger.error(f"Error obteniendo artículos sin imagen: {e}")
            return []
    
    def get_articles_with_low_quality_images(self):
        """Obtener artículos con imágenes de baja calidad"""
        try:
            db_path = get_database_path()
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar artículos con URLs de imagen que podrían ser de baja calidad
                cursor.execute("""
                    SELECT id, title, url, image_url
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != '' 
                    AND image_url NOT LIKE '%placeholder%'
                    AND image_url NOT LIKE '%via.placeholder%'
                    AND image_url NOT LIKE '%example.com%'
                    AND image_url NOT LIKE '%picsum%'
                    AND (image_url LIKE '%150x%' 
                         OR image_url LIKE '%100x%' 
                         OR image_url LIKE '%small%'
                         OR image_url LIKE '%thumb%'
                         OR image_url LIKE '%icon%'
                         OR image_url LIKE '%64x%'
                         OR image_url LIKE '%48x%'
                         OR LENGTH(image_url) < 30)
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                
                articles = cursor.fetchall()
                logger.info(f"Encontrados {len(articles)} artículos con posibles imágenes de baja calidad")
                return articles
                
        except Exception as e:
            logger.error(f"Error obteniendo artículos con imágenes de baja calidad: {e}")
            return []
    
    def ensure_all_articles_have_images(self, batch_size=20):
        """Asegurar que TODOS los artículos tengan imágenes de calidad"""
        try:
            logger.info("Iniciando proceso para asegurar que todos los artículos tengan imágenes")
            
            # Obtener todos los artículos que necesitan imágenes
            articles_needing_images = self.get_articles_without_images(1000)  # Procesar muchos
            
            if not articles_needing_images:
                logger.info("✅ Todos los artículos ya tienen imágenes de calidad")
                return {"status": "completed", "message": "Todos los artículos tienen imágenes"}
            
            total_articles = len(articles_needing_images)
            processed = 0
            errors = 0
            
            logger.info(f"📝 Procesando {total_articles} artículos que necesitan imágenes...")
            
            # Procesar en lotes para no sobrecargar
            for i in range(0, total_articles, batch_size):
                batch = articles_needing_images[i:i+batch_size]
                
                logger.info(f"📦 Procesando lote {i//batch_size + 1}/{(total_articles + batch_size - 1)//batch_size}")
                
                for article_id, title, url, source, current_image in batch:
                    try:
                        logger.info(f"🔍 Procesando {article_id}: {title[:50]}...")
                        
                        # Extraer imagen de mejor calidad
                        new_image_path = self.extract_image_from_url(url, article_id, title)
                        
                        if new_image_path and new_image_path != current_image:
                            # Actualizar en la base de datos
                            if self.update_article_image(article_id, new_image_path):
                                processed += 1
                                logger.info(f"✅ Actualizada imagen para: {title[:50]}...")
                            else:
                                errors += 1
                                logger.error(f"❌ Error actualizando BD para: {title[:50]}...")
                        elif new_image_path:
                            processed += 1  # Ya tenía una imagen válida
                        else:
                            errors += 1
                            logger.warning(f"⚠️ No se pudo obtener imagen para: {title[:50]}...")
                        
                        # Pausa para no sobrecargar los servidores
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"❌ Error procesando artículo {article_id}: {e}")
                        errors += 1
                
                # Pausa entre lotes
                logger.info(f"⏳ Pausa entre lotes... ({processed + errors}/{total_articles} procesados)")
                time.sleep(5)
            
            result = {
                "status": "completed",
                "total_articles": total_articles,
                "processed": processed,
                "errors": errors,
                "success_rate": (processed / total_articles * 100) if total_articles > 0 else 0
            }
            
            logger.info(f"🎉 Proceso completado: {processed}/{total_articles} artículos con imágenes")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en proceso masivo de imágenes: {e}")
            return {"status": "error", "error": str(e)}
    
    def _extract_images_background(self, articles_without_images):
        """Función para extraer imágenes en segundo plano"""
        try:
            processed = 0
            errors = 0
            
            logger.info(f"Iniciando extracción de imágenes para {len(articles_without_images)} artículos")
            
            for article_id, title, url, source in articles_without_images:
                try:
                    logger.info(f"Procesando artículo {article_id}: {title[:50]}...")
                    
                    image_path = self.extract_image_from_url(url, article_id, title)
                    
                    if image_path:
                        if self.update_article_image(article_id, image_path):
                            processed += 1
                            logger.info(f"✅ Imagen extraída para: {title[:50]}...")
                        else:
                            errors += 1
                            logger.error(f"❌ Error actualizando BD para: {title[:50]}...")
                    else:
                        errors += 1
                        logger.warning(f"❌ No se pudo extraer imagen para: {title[:50]}...")
                    
                    # Pausa para no sobrecargar los servidores
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error procesando artículo {article_id}: {e}")
                    errors += 1
            
            # Actualizar estado de la tarea
            task_result = {
                'processed': processed,
                'errors': errors,
                'total': len(articles_without_images),
                'success_rate': (processed / len(articles_without_images) * 100) if len(articles_without_images) > 0 else 0
            }
            
            logger.info(f"Extracción de imágenes completada: {processed} exitosos, {errors} errores")
            
            # Agregar alerta del sistema
            self.system_state['alerts'].append({
                'type': 'image_extraction_completed',
                'message': f'Extracción de imágenes completada: {processed}/{len(articles_without_images)} exitosos',
                'timestamp': datetime.now().isoformat(),
                'details': task_result
            })
            
            return task_result
            
        except Exception as e:
            logger.error(f"Error en extracción de imágenes en background: {e}")
            return {'error': str(e)}
    
    def _improve_images_quality(self, articles_to_improve):
        """Mejorar la calidad de imágenes existentes"""
        try:
            processed = 0
            errors = 0
            improved = 0
            
            logger.info(f"Iniciando mejora de calidad para {len(articles_to_improve)} imágenes")
            
            for article_id, title, url, current_image in articles_to_improve:
                try:
                    logger.info(f"🔍 Mejorando imagen para artículo {article_id}: {title[:50]}...")
                    
                    # Buscar imagen de mejor calidad
                    new_image_path = self.extract_image_from_url(url, article_id, title)
                    
                    if new_image_path and new_image_path != current_image:
                        # Actualizar en la base de datos
                        if self.update_article_image(article_id, new_image_path):
                            improved += 1
                            processed += 1
                            logger.info(f"✅ Imagen mejorada para: {title[:50]}...")
                        else:
                            errors += 1
                            logger.error(f"❌ Error actualizando imagen para: {title[:50]}...")
                    else:
                        processed += 1
                        logger.info(f"ℹ️ Imagen actual ya es de buena calidad: {title[:50]}...")
                    
                    # Pausa para no sobrecargar
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error mejorando imagen para artículo {article_id}: {e}")
                    errors += 1
            
            result = {
                'processed': processed,
                'improved': improved,
                'errors': errors,
                'total': len(articles_to_improve),
                'improvement_rate': (improved / len(articles_to_improve) * 100) if len(articles_to_improve) > 0 else 0
            }
            
            logger.info(f"Mejora de calidad completada: {improved} imágenes mejoradas de {len(articles_to_improve)}")
            
            # Agregar alerta del sistema
            self.system_state['alerts'].append({
                'type': 'image_quality_improved',
                'message': f'Mejora de calidad completada: {improved}/{len(articles_to_improve)} imágenes mejoradas',
                'timestamp': datetime.now().isoformat(),
                'details': result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error mejorando calidad de imágenes: {e}")
            return {'error': str(e)}
    
    def _generate_mock_geojson_features(self):
        """Generar features mock para GeoJSON"""
        return [
            {
                "type": "Feature",
                "properties": {
                    "id": 1,
                    "name": "Europa Oriental",
                    "title": "Tensiones geopolíticas en Europa Oriental",
                    "risk_level": "high",
                    "conflict_type": "territorial",
                    "intensity": 0.8,
                    "articles_count": 25,
                    "sentiment_score": -0.6,
                    "published_date": "2024-01-01T12:00:00Z"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [30.0, 50.0]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "id": 2,
                    "name": "Medio Oriente",
                    "title": "Conflictos políticos en Medio Oriente",
                    "risk_level": "medium",
                    "conflict_type": "political",
                    "intensity": 0.6,
                    "articles_count": 18,
                    "sentiment_score": -0.4,
                    "published_date": "2024-01-01T10:00:00Z"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [45.0, 30.0]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "id": 3,
                    "name": "Mar del Sur de China",
                    "title": "Disputas territoriales en el Mar del Sur de China",
                    "risk_level": "high",
                    "conflict_type": "territorial",
                    "intensity": 0.9,
                    "articles_count": 32,
                    "sentiment_score": -0.7,
                    "published_date": "2024-01-01T08:00:00Z"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [115.0, 15.0]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "id": 4,
                    "name": "África Occidental",
                    "title": "Inestabilidad en África Occidental",
                    "risk_level": "medium",
                    "conflict_type": "economic",
                    "intensity": 0.5,
                    "articles_count": 12,
                    "sentiment_score": -0.3,
                    "published_date": "2024-01-01T14:00:00Z"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [-10.0, 10.0]
                }
            }
        ]
    
    def _generate_mock_geojson(self):
        """Generar GeoJSON mock completo"""
        return {
            "type": "FeatureCollection",
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "timeframe": "mock",
                "total_features": 4,
                "data_source": "RiskMap AI Analytics (Mock Data)"
            },
            "features": self._generate_mock_geojson_features()
        }
    
    def _analyze_articles_images_background(self, articles_to_analyze):
        """Analizar imágenes de artículos en background usando computer vision"""
        try:
            if not CV_AVAILABLE:
                logger.warning("Computer vision no disponible para análisis de imágenes")
                return {'error': 'Computer vision not available'}
            
            analyzer = ImageInterestAnalyzer()
            processed = 0
            errors = 0
            
            logger.info(f"🔍 Iniciando análisis CV de {len(articles_to_analyze)} imágenes...")
            
            for article_id, title, image_url in articles_to_analyze:
                try:
                    logger.info(f"🔍 Analizando imagen del artículo {article_id}: {title[:50]}...")
                    
                    # Realizar análisis de computer vision
                    analysis = analyzer.analyze_image_interest_areas(image_url, title)
                    
                    if not analysis.get('error'):
                        # Guardar análisis en base de datos
                        db_path = get_database_path()
                        with sqlite3.connect(db_path) as conn:
                            cursor = conn.cursor()
                            
                            # Crear tabla si no existe
                            cursor.execute("""
                                CREATE TABLE IF NOT EXISTS image_analysis (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    article_id INTEGER,
                                    image_url TEXT,
                                    analysis_json TEXT,
                                    quality_score REAL,
                                    positioning_recommendation TEXT,
                                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    FOREIGN KEY (article_id) REFERENCES articles (id)
                                )
                            """)
                            
                            # Insertar análisis
                            cursor.execute("""
                                INSERT OR REPLACE INTO image_analysis 
                                (article_id, image_url, analysis_json, quality_score, positioning_recommendation)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                article_id,
                                image_url,
                                json.dumps(analysis, ensure_ascii=False),
                                analysis.get('quality_score', 0.5),
                                analysis.get('positioning_recommendation', {}).get('position', 'center')
                            ))
                            
                            conn.commit()
                        
                        processed += 1
                        logger.info(f"✅ Análisis CV completado para artículo {article_id} - Calidad: {analysis.get('quality_score', 0):.2f}")
                    else:
                        errors += 1
                        logger.warning(f"⚠️ Error en análisis CV para artículo {article_id}: {analysis.get('error')}")
                    
                    # Pausa para no sobrecargar
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error analizando imagen del artículo {article_id}: {e}")
                    errors += 1
            
            result = {
                'processed': processed,
                'errors': errors,
                'total': len(articles_to_analyze),
                'success_rate': (processed / len(articles_to_analyze) * 100) if len(articles_to_analyze) > 0 else 0
            }
            
            logger.info(f"✅ Análisis CV completado: {processed} exitosos, {errors} errores de {len(articles_to_analyze)} total")
            
            # Agregar alerta del sistema
            self.system_state['alerts'].append({
                'type': 'cv_analysis_completed',
                'message': f'Análisis de computer vision completado: {processed}/{len(articles_to_analyze)} imágenes analizadas',
                'timestamp': datetime.now().isoformat(),
                'details': result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis CV en background: {e}")
            return {'error': str(e)}

def main():
    """Función principal"""
    try:
        # Create and start the unified application
        app = RiskMapUnifiedApplication()
        app.start_application()
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando la aplicación: {e}")
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()