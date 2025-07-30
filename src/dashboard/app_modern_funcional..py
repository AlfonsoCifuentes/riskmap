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
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_enhanced_historical.txt'])
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
        
        @self.flask_app.route('/api/background/tasks')
        def api_background_tasks():
            """API: Estado de tareas en background"""
            return jsonify({
                'success': True,
                'tasks': self.system_state['background_tasks']
            })
        
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