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

El usuario solo ejecuta este archivo y todo funciona automáticamente.
"""

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
    print(f"[ERROR] Error importando módulos: {e}")
    print("[INFO] Instalando dependencias...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_enhanced_historical_fixed.txt'])
        print("[INFO] Dependencias instaladas. Reiniciando...")
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as install_error:
        print(f"[ERROR] No se pudieron instalar las dependencias: {install_error}")
        sys.exit(1)

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
        
        # System state
        self.system_state = {
            'core_system_initialized': False,
            'historical_system_initialized': False,
            'data_ingestion_running': False,
            'nlp_processing_running': False,
            'historical_analysis_running': False,
            'dashboards_ready': False,
            'api_ready': False,
            'last_ingestion': None,
            'last_processing': None,
            'last_analysis': None,
            'system_status': 'starting',
            'background_tasks': {},
            'alerts': [],
            'statistics': {
                'total_articles': 0,
                'processed_articles': 0,
                'risk_alerts': 0,
                'data_sources': 0
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
            'flask_host': '0.0.0.0',
            'flask_debug': False,
            
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
            return render_template('unified_index.html', 
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
                
                return jsonify({
                    'success': True,
                    'system_state': self.system_state,
                    'detailed_status': detailed_status,
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
        
        # Static files
        @self.flask_app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory('src/web/static', filename)
    
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
            
            # 4. Initialize task scheduler
            logger.info("Initializing task scheduler...")
            self.task_scheduler = TaskScheduler(self.core_orchestrator)
            
            # 5. Setup API endpoints
            self._setup_api_endpoints()
            
            # 6. Initialize Dash applications with existing data
            self._initialize_dash_apps()
            
            # 7. Start background processes if enabled (for continuous updates)
            if self.config['enable_background_tasks']:
                self._start_background_processes()
            
            self.system_state['system_status'] = 'initialized'
            logger.info("All systems initialized successfully with existing data loaded")
            
            return {
                'status': 'success',
                'core_system': self.system_state['core_system_initialized'],
                'historical_system': self.system_state['historical_system_initialized'],
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
                    db_path = Path('data/riskmap.db')
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
                    
                    db_path = Path('data/riskmap.db')
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
            "content": f"""
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
            db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
            
            if not os.path.exists(db_path):
                logger.warning(f"Base de datos no encontrada en: {db_path}")
                return self._get_mock_articles(limit)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Consulta para obtener artículos con mayor riesgo primero
            query = """
                SELECT id, title, content, url, source, published_at, 
                       country, region, risk_level, conflict_type, 
                       sentiment_score, summary, risk_score
                FROM articles 
                ORDER BY 
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
            
            # Start Flask server
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
            
            # Set shutdown event
            self.shutdown_event.set()
            
            # Wait for background threads to finish
            for thread_name, thread in self.background_threads.items():
                if thread.is_alive():
                    logger.info(f"Waiting for background thread {thread_name} to finish...")
                    thread.join(timeout=5)
            
            self.system_state['system_status'] = 'stopped'
            logger.info("Application stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")

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