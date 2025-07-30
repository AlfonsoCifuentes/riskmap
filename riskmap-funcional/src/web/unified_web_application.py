"""
Unified Web Application
Sistema web unificado que ejecuta automáticamente todos los análisis en segundo plano
y proporciona una interfaz web completa sin necesidad de comandos de consola.
"""

import logging
import asyncio
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Optional, Any
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

# Flask web framework
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_cors import CORS
import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Import our analysis modules
from analytics.enhanced_historical_orchestrator import EnhancedHistoricalOrchestrator
from visualization.multivariate_dashboard import MultivariateRelationshipDashboard
from visualization.historical_dashboard import HistoricalDashboard

logger = logging.getLogger(__name__)

class UnifiedWebApplication:
    """
    Aplicación web unificada que maneja todo el sistema de análisis histórico
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Initialize Flask app
        self.flask_app = Flask(__name__, 
                              template_folder='templates',
                              static_folder='static')
        self.flask_app.secret_key = 'riskmap_secret_key_2024'
        CORS(self.flask_app)
        
        # Initialize Dash apps
        self.dash_apps = {}
        
        # Initialize orchestrator
        self.orchestrator = EnhancedHistoricalOrchestrator(self.config)
        
        # System state
        self.system_state = {
            'initialized': False,
            'data_updated': False,
            'analysis_running': False,
            'last_analysis': None,
            'background_tasks': {},
            'system_status': 'starting'
        }
        
        # Background task manager
        self.background_executor = None
        self.auto_analysis_thread = None
        
        # Setup routes and initialize
        self._setup_flask_routes()
        self._initialize_dash_apps()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto del sistema"""
        return {
            'flask_port': 8050,
            'flask_host': '0.0.0.0',
            'flask_debug': False,
            'auto_initialize': True,
            'auto_update_interval_hours': 6,
            'auto_analysis_interval_hours': 12,
            'enable_background_tasks': True,
            'data_dir': 'datasets/historical',
            'multivariate_data_dir': 'datasets/multivariate',
            'model_dir': 'models/predictive',
            'output_dir': 'outputs/patterns',
            'relationships_output_dir': 'outputs/relationships'
        }
    
    def _setup_flask_routes(self):
        """Configurar rutas de Flask"""
        
        @self.flask_app.route('/')
        def index():
            """Página principal"""
            return render_template('index.html', 
                                 system_state=self.system_state,
                                 config=self.config)
        
        @self.flask_app.route('/dashboard')
        def dashboard():
            """Redirigir al dashboard principal"""
            return redirect('/dash/historical/')
        
        @self.flask_app.route('/multivariate')
        def multivariate():
            """Redirigir al dashboard multivariable"""
            return redirect('/dash/multivariate/')
        
        @self.flask_app.route('/api/system/status')
        def api_system_status():
            """API para obtener estado del sistema"""
            try:
                if self.orchestrator:
                    status = asyncio.run(self.orchestrator.get_enhanced_system_status())
                    return jsonify({
                        'success': True,
                        'system_state': self.system_state,
                        'detailed_status': status
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Orchestrator not initialized'
                    })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.flask_app.route('/api/system/initialize', methods=['POST'])
        def api_initialize_system():
            """API para inicializar el sistema"""
            try:
                if not self.system_state['initialized']:
                    # Ejecutar inicialización en background
                    self._run_background_task('initialize', self._initialize_system_background)
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
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.flask_app.route('/api/data/update', methods=['POST'])
        def api_update_data():
            """API para actualizar datos"""
            try:
                force_update = request.json.get('force_update', False) if request.json else False
                self._run_background_task('update_data', 
                                        lambda: self._update_data_background(force_update))
                return jsonify({
                    'success': True,
                    'message': 'Data update started in background'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.flask_app.route('/api/analysis/run', methods=['POST'])
        def api_run_analysis():
            """API para ejecutar análisis"""
            try:
                params = request.json or {}
                self._run_background_task('run_analysis', 
                                        lambda: self._run_analysis_background(params))
                return jsonify({
                    'success': True,
                    'message': 'Analysis started in background'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.flask_app.route('/api/analysis/results')
        def api_analysis_results():
            """API para obtener resultados del análisis"""
            try:
                if self.system_state['last_analysis']:
                    return jsonify({
                        'success': True,
                        'results': self.system_state['last_analysis']
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'No analysis results available'
                    })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.flask_app.route('/api/background/tasks')
        def api_background_tasks():
            """API para obtener estado de tareas en background"""
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
        
        @self.flask_app.route('/api/settings/update', methods=['POST'])
        def api_update_settings():
            """API para actualizar configuración"""
            try:
                new_config = request.json
                self.config.update(new_config)
                return jsonify({
                    'success': True,
                    'message': 'Settings updated successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
    
    def _initialize_dash_apps(self):
        """Inicializar aplicaciones Dash integradas"""
        try:
            # Historical Dashboard
            self.dash_apps['historical'] = HistoricalDashboard(
                data_source=self.orchestrator.data_integrator,
                port=None  # Will be integrated into Flask
            )
            
            # Multivariate Dashboard  
            self.dash_apps['multivariate'] = MultivariateRelationshipDashboard(
                data_integrator=self.orchestrator.multivariate_integrator,
                relationship_analyzer=self.orchestrator.relationship_analyzer,
                port=None  # Will be integrated into Flask
            )
            
            # Integrate Dash apps into Flask
            self._integrate_dash_apps()
            
            logger.info("Dash applications initialized and integrated")
            
        except Exception as e:
            logger.error(f"Error initializing Dash apps: {e}")
    
    def _integrate_dash_apps(self):
        """Integrar aplicaciones Dash en Flask"""
        try:
            # Historical Dashboard
            historical_dash = self.dash_apps['historical'].app
            historical_dash.config.requests_pathname_prefix = '/dash/historical/'
            historical_dash.server = self.flask_app
            
            # Multivariate Dashboard
            multivariate_dash = self.dash_apps['multivariate'].app
            multivariate_dash.config.requests_pathname_prefix = '/dash/multivariate/'
            multivariate_dash.server = self.flask_app
            
            # Add Dash routes to Flask
            for view_func in historical_dash.server.view_functions:
                if view_func.startswith('dash.historical'):
                    self.flask_app.add_url_rule(
                        f'/dash/historical{view_func[len("dash.historical"):]}',
                        view_func,
                        historical_dash.server.view_functions[view_func]
                    )
            
            for view_func in multivariate_dash.server.view_functions:
                if view_func.startswith('dash.multivariate'):
                    self.flask_app.add_url_rule(
                        f'/dash/multivariate{view_func[len("dash.multivariate"):]}',
                        view_func,
                        multivariate_dash.server.view_functions[view_func]
                    )
            
        except Exception as e:
            logger.error(f"Error integrating Dash apps: {e}")
    
    def _run_background_task(self, task_name: str, task_func):
        """Ejecutar tarea en background"""
        try:
            # Marcar tarea como iniciada
            self.system_state['background_tasks'][task_name] = {
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'progress': 0
            }
            
            # Ejecutar en thread separado
            def run_task():
                try:
                    result = task_func()
                    self.system_state['background_tasks'][task_name] = {
                        'status': 'completed',
                        'started_at': self.system_state['background_tasks'][task_name]['started_at'],
                        'completed_at': datetime.now().isoformat(),
                        'progress': 100,
                        'result': result
                    }
                except Exception as e:
                    self.system_state['background_tasks'][task_name] = {
                        'status': 'failed',
                        'started_at': self.system_state['background_tasks'][task_name]['started_at'],
                        'failed_at': datetime.now().isoformat(),
                        'progress': 0,
                        'error': str(e)
                    }
                    logger.error(f"Background task {task_name} failed: {e}")
            
            thread = threading.Thread(target=run_task)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"Error starting background task {task_name}: {e}")
    
    def _initialize_system_background(self):
        """Inicializar sistema en background"""
        try:
            logger.info("Starting system initialization in background...")
            self.system_state['system_status'] = 'initializing'
            
            # Ejecutar inicialización
            result = asyncio.run(self.orchestrator.initialize_enhanced_system())
            
            if result['status'] in ['success', 'partial_success']:
                self.system_state['initialized'] = True
                self.system_state['system_status'] = 'initialized'
                logger.info("System initialization completed successfully")
            else:
                self.system_state['system_status'] = 'initialization_failed'
                logger.error("System initialization failed")
            
            return result
            
        except Exception as e:
            self.system_state['system_status'] = 'initialization_failed'
            logger.error(f"Error in system initialization: {e}")
            raise
    
    def _update_data_background(self, force_update: bool = False):
        """Actualizar datos en background"""
        try:
            logger.info("Starting data update in background...")
            self.system_state['system_status'] = 'updating_data'
            
            # Actualizar datos multivariables
            result = asyncio.run(self.orchestrator.update_multivariate_data(force_update))
            
            if result['status'] in ['success', 'partial_success']:
                self.system_state['data_updated'] = True
                self.system_state['system_status'] = 'data_updated'
                logger.info("Data update completed successfully")
            else:
                self.system_state['system_status'] = 'data_update_failed'
                logger.error("Data update failed")
            
            return result
            
        except Exception as e:
            self.system_state['system_status'] = 'data_update_failed'
            logger.error(f"Error in data update: {e}")
            raise
    
    def _run_analysis_background(self, params: Dict[str, Any]):
        """Ejecutar análisis en background"""
        try:
            logger.info("Starting analysis in background...")
            self.system_state['analysis_running'] = True
            self.system_state['system_status'] = 'running_analysis'
            
            # Parámetros por defecto
            start_date = None
            end_date = None
            target_variable = params.get('target_variable', 'conflict_risk')
            
            if params.get('start_date'):
                start_date = datetime.fromisoformat(params['start_date'])
            if params.get('end_date'):
                end_date = datetime.fromisoformat(params['end_date'])
            
            # Ejecutar análisis completo
            result = asyncio.run(self.orchestrator.run_comprehensive_multivariate_analysis(
                start_date=start_date,
                end_date=end_date,
                target_variable=target_variable
            ))
            
            if result['status'] in ['success', 'partial_success']:
                self.system_state['last_analysis'] = result
                self.system_state['system_status'] = 'analysis_completed'
                logger.info("Analysis completed successfully")
            else:
                self.system_state['system_status'] = 'analysis_failed'
                logger.error("Analysis failed")
            
            self.system_state['analysis_running'] = False
            return result
            
        except Exception as e:
            self.system_state['analysis_running'] = False
            self.system_state['system_status'] = 'analysis_failed'
            logger.error(f"Error in analysis: {e}")
            raise
    
    def _start_auto_analysis_cycle(self):
        """Iniciar ciclo automático de análisis"""
        if not self.config.get('enable_background_tasks', True):
            return
        
        def auto_cycle():
            while True:
                try:
                    if self.system_state['initialized'] and not self.system_state['analysis_running']:
                        logger.info("Running automatic analysis cycle...")
                        
                        # Actualizar datos
                        self._update_data_background(force_update=False)
                        
                        # Ejecutar análisis
                        self._run_analysis_background({})
                        
                        # Ejecutar análisis en tiempo real
                        try:
                            real_time_result = asyncio.run(self.orchestrator.run_real_time_analysis())
                            logger.info(f"Real-time analysis completed: {real_time_result['status']}")
                        except Exception as e:
                            logger.error(f"Real-time analysis failed: {e}")
                    
                    # Esperar hasta el próximo ciclo
                    time.sleep(self.config['auto_analysis_interval_hours'] * 3600)
                    
                except Exception as e:
                    logger.error(f"Error in auto analysis cycle: {e}")
                    time.sleep(3600)  # Esperar 1 hora antes de reintentar
        
        self.auto_analysis_thread = threading.Thread(target=auto_cycle)
        self.auto_analysis_thread.daemon = True
        self.auto_analysis_thread.start()
        
        logger.info(f"Auto analysis cycle started (interval: {self.config['auto_analysis_interval_hours']} hours)")
    
    def start_application(self):
        """Iniciar la aplicación web completa"""
        try:
            logger.info("Starting Unified Web Application...")
            
            # Auto-inicialización si está habilitada
            if self.config.get('auto_initialize', True):
                self._run_background_task('auto_initialize', self._initialize_system_background)
            
            # Iniciar ciclo automático
            if self.config.get('enable_background_tasks', True):
                self._start_auto_analysis_cycle()
            
            # Iniciar servidor Flask
            logger.info(f"Starting web server on http://{self.config['flask_host']}:{self.config['flask_port']}")
            
            self.flask_app.run(
                host=self.config['flask_host'],
                port=self.config['flask_port'],
                debug=self.config['flask_debug'],
                threaded=True
            )
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            raise
    
    def stop_application(self):
        """Detener la aplicación"""
        try:
            logger.info("Stopping Unified Web Application...")
            
            # Detener threads de background
            if self.auto_analysis_thread and self.auto_analysis_thread.is_alive():
                # Note: daemon threads will stop automatically when main thread stops
                pass
            
            self.system_state['system_status'] = 'stopped'
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")

def create_templates():
    """Crear templates HTML básicos"""
    templates_dir = Path('src/web/templates')
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Template principal
    index_template = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiskMap - Sistema de Análisis Histórico</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-running { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-error { background-color: #dc3545; }
        .status-inactive { background-color: #6c757d; }
        .card-dashboard {
            transition: transform 0.2s;
            cursor: pointer;
        }
        .card-dashboard:hover {
            transform: translateY(-5px);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🗺️ RiskMap</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard">Dashboard Histórico</a>
                <a class="nav-link" href="/multivariate">Análisis Multivariable</a>
                <a class="nav-link" href="/settings">Configuración</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1>Sistema de Análisis Histórico Multivariable</h1>
                <p class="lead">Análisis integral de relaciones entre variables energéticas, climáticas, políticas, sanitarias y de recursos.</p>
            </div>
        </div>

        <!-- Estado del Sistema -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Estado del Sistema</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <div class="d-flex align-items-center">
                                    <span id="system-status-indicator" class="status-indicator status-inactive"></span>
                                    <span>Sistema: <span id="system-status">{{ system_state.system_status }}</span></span>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="d-flex align-items-center">
                                    <span id="init-status-indicator" class="status-indicator {% if system_state.initialized %}status-running{% else %}status-inactive{% endif %}"></span>
                                    <span>Inicializado: {% if system_state.initialized %}Sí{% else %}No{% endif %}</span>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="d-flex align-items-center">
                                    <span id="data-status-indicator" class="status-indicator {% if system_state.data_updated %}status-running{% else %}status-inactive{% endif %}"></span>
                                    <span>Datos: {% if system_state.data_updated %}Actualizados{% else %}Pendientes{% endif %}</span>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="d-flex align-items-center">
                                    <span id="analysis-status-indicator" class="status-indicator {% if system_state.analysis_running %}status-warning{% else %}status-inactive{% endif %}"></span>
                                    <span>Análisis: {% if system_state.analysis_running %}Ejecutando{% else %}Inactivo{% endif %}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Acciones del Sistema -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Acciones del Sistema</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <button id="btn-initialize" class="btn btn-primary w-100" onclick="initializeSystem()">
                                    Inicializar Sistema
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button id="btn-update-data" class="btn btn-info w-100" onclick="updateData()">
                                    Actualizar Datos
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button id="btn-run-analysis" class="btn btn-success w-100" onclick="runAnalysis()">
                                    Ejecutar Análisis
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button id="btn-refresh-status" class="btn btn-secondary w-100" onclick="refreshStatus()">
                                    Actualizar Estado
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Dashboards -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card card-dashboard" onclick="window.open('/dashboard', '_blank')">
                    <div class="card-body text-center">
                        <h5 class="card-title">📊 Dashboard Histórico</h5>
                        <p class="card-text">Análisis temporal, patrones y predicciones basadas en datos históricos.</p>
                        <span class="btn btn-outline-primary">Abrir Dashboard</span>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card card-dashboard" onclick="window.open('/multivariate', '_blank')">
                    <div class="card-body text-center">
                        <h5 class="card-title">🔗 Análisis Multivariable</h5>
                        <p class="card-text">Relaciones entre variables energéticas, climáticas, políticas y de recursos.</p>
                        <span class="btn btn-outline-success">Abrir Análisis</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tareas en Background -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Tareas en Ejecución</h5>
                    </div>
                    <div class="card-body">
                        <div id="background-tasks">
                            <p class="text-muted">No hay tareas en ejecución</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Funciones JavaScript para interactuar con la API
        async function initializeSystem() {
            try {
                const response = await axios.post('/api/system/initialize');
                if (response.data.success) {
                    alert('Inicialización del sistema iniciada en segundo plano');
                    refreshStatus();
                } else {
                    alert('Error: ' + response.data.error);
                }
            } catch (error) {
                alert('Error de conexión: ' + error.message);
            }
        }

        async function updateData() {
            try {
                const response = await axios.post('/api/data/update');
                if (response.data.success) {
                    alert('Actualización de datos iniciada en segundo plano');
                    refreshStatus();
                } else {
                    alert('Error: ' + response.data.error);
                }
            } catch (error) {
                alert('Error de conexión: ' + error.message);
            }
        }

        async function runAnalysis() {
            try {
                const response = await axios.post('/api/analysis/run');
                if (response.data.success) {
                    alert('Análisis iniciado en segundo plano');
                    refreshStatus();
                } else {
                    alert('Error: ' + response.data.error);
                }
            } catch (error) {
                alert('Error de conexión: ' + error.message);
            }
        }

        async function refreshStatus() {
            try {
                const response = await axios.get('/api/system/status');
                if (response.data.success) {
                    updateStatusDisplay(response.data.system_state);
                }
                
                const tasksResponse = await axios.get('/api/background/tasks');
                if (tasksResponse.data.success) {
                    updateBackgroundTasks(tasksResponse.data.tasks);
                }
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        }

        function updateStatusDisplay(systemState) {
            document.getElementById('system-status').textContent = systemState.system_status;
            
            // Actualizar indicadores
            const systemIndicator = document.getElementById('system-status-indicator');
            systemIndicator.className = 'status-indicator ' + getStatusClass(systemState.system_status);
            
            const initIndicator = document.getElementById('init-status-indicator');
            initIndicator.className = 'status-indicator ' + (systemState.initialized ? 'status-running' : 'status-inactive');
            
            const dataIndicator = document.getElementById('data-status-indicator');
            dataIndicator.className = 'status-indicator ' + (systemState.data_updated ? 'status-running' : 'status-inactive');
            
            const analysisIndicator = document.getElementById('analysis-status-indicator');
            analysisIndicator.className = 'status-indicator ' + (systemState.analysis_running ? 'status-warning' : 'status-inactive');
        }

        function getStatusClass(status) {
            if (status.includes('running') || status.includes('completed')) return 'status-running';
            if (status.includes('failed') || status.includes('error')) return 'status-error';
            if (status.includes('initializing') || status.includes('updating')) return 'status-warning';
            return 'status-inactive';
        }

        function updateBackgroundTasks(tasks) {
            const container = document.getElementById('background-tasks');
            if (Object.keys(tasks).length === 0) {
                container.innerHTML = '<p class="text-muted">No hay tareas en ejecución</p>';
                return;
            }

            let html = '';
            for (const [taskName, taskInfo] of Object.entries(tasks)) {
                const statusClass = taskInfo.status === 'completed' ? 'success' : 
                                  taskInfo.status === 'failed' ? 'danger' : 'warning';
                html += `
                    <div class="alert alert-${statusClass} alert-sm">
                        <strong>${taskName}</strong>: ${taskInfo.status}
                        ${taskInfo.progress !== undefined ? ` (${taskInfo.progress}%)` : ''}
                    </div>
                `;
            }
            container.innerHTML = html;
        }

        // Actualizar estado cada 5 segundos
        setInterval(refreshStatus, 5000);
        
        // Actualizar estado al cargar la página
        document.addEventListener('DOMContentLoaded', refreshStatus);
    </script>
</body>
</html>
    '''
    
    with open(templates_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    # Template de configuración
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
                <a class="nav-link" href="/dashboard">Dashboard Histórico</a>
                <a class="nav-link" href="/multivariate">Análisis Multivariable</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h1>Configuración del Sistema</h1>
        
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
    
    with open(templates_dir / 'settings.html', 'w', encoding='utf-8') as f:
        f.write(settings_template)
    
    logger.info("HTML templates created successfully")

# Función principal para ejecutar la aplicación
def main():
    """Función principal para ejecutar la aplicación web unificada"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/unified_web_app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Crear directorios necesarios
    Path('logs').mkdir(exist_ok=True)
    Path('src/web/static').mkdir(parents=True, exist_ok=True)
    
    # Crear templates
    create_templates()
    
    # Configuración de la aplicación
    config = {
        'flask_port': 8050,
        'flask_host': '0.0.0.0',
        'flask_debug': False,
        'auto_initialize': True,
        'auto_update_interval_hours': 6,
        'auto_analysis_interval_hours': 12,
        'enable_background_tasks': True
    }
    
    # Crear y ejecutar aplicación
    try:
        app = UnifiedWebApplication(config)
        
        print("\n" + "="*70)
        print("🚀 INICIANDO SISTEMA WEB UNIFICADO")
        print("="*70)
        print(f"📱 Interfaz Web: http://localhost:{config['flask_port']}")
        print(f"📊 Dashboard Histórico: http://localhost:{config['flask_port']}/dashboard")
        print(f"🔗 Análisis Multivariable: http://localhost:{config['flask_port']}/multivariate")
        print(f"⚙️ Configuración: http://localhost:{config['flask_port']}/settings")
        print("="*70)
        print("✅ El sistema se inicializará automáticamente en segundo plano")
        print("✅ Los análisis se ejecutarán automáticamente cada 12 horas")
        print("✅ Solo navega por la interfaz web - no necesitas comandos")
        print("="*70)
        
        app.start_application()
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando la aplicación: {e}")
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()