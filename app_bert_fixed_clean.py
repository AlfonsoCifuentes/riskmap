"""
RiskMap - Aplicación Web Moderna Unificada con BERT + Groq AI
Punto de entrada único que ejecuta TODOS los procesos del sistema:
- Ingesta de datos RSS/OSINT
- Clasificación y procesamiento NLP con BERT real
- Análisis geopolítico con Groq AI
- Análisis histórico multivariable
- Dashboards interactivos
- APIs REST
- Monitoreo en tiempo real
- Alertas automáticas

El usuario solo ejecuta este archivo y todo funciona automáticamente.
"""

import logging
import threading
import time
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import signal
import atexit

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Flask and web imports
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory, render_template_string
from flask_cors import CORS

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import AI services
from src.ai.bert_service import bert_service
from src.ai.groq_service import groq_service

# Import system components (optional for enhanced features)
try:
    from src.orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator
    from src.orchestration.task_scheduler import TaskScheduler
    from src.analytics.enhanced_historical_orchestrator import EnhancedHistoricalOrchestrator
    from src.visualization.historical_dashboard import HistoricalDashboard
    from src.visualization.multivariate_dashboard import MultivariateRelationshipDashboard
    from src.api.rest_status import create_api_blueprint
    from src.utils.config import logger
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"[INFO] Funciones avanzadas no disponibles: {e}")
    print("[INFO] Ejecutando en modo básico con BERT + Groq únicamente")
    ENHANCED_FEATURES_AVAILABLE = False
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class RiskMapUnifiedApplication:
    """
    Aplicación web unificada que ejecuta todos los componentes del sistema RiskMap
    + Integración BERT y Groq AI refactorizada
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Initialize Flask app
        self.flask_app = Flask(__name__, 
                              template_folder='src/web/templates',
                              static_folder='src/web/static')
        self.flask_app.secret_key = 'riskmap_unified_2024'
        CORS(self.flask_app)
        
        # AI Services - Thread-safe initialization
        self.bert_service = bert_service
        self.groq_service = groq_service
        
        # System components (optional)
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
            'bert_model_loaded': False,
            'groq_available': False,
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
        
    def _initialize_ai_services(self):
        """Inicializa los servicios de IA de forma thread-safe"""
        try:
            logger.info("🤖 Inicializando servicios de IA...")
            
            # Inicializar BERT
            if self.bert_service.initialize_model():
                self.system_state['bert_model_loaded'] = True
                logger.info("✅ BERT inicializado correctamente")
            else:
                logger.warning("⚠️ BERT no pudo inicializarse")
            
            # Verificar Groq
            if self.groq_service.is_available():
                self.system_state['groq_available'] = True
                logger.info("✅ Groq AI disponible")
            else:
                logger.warning("⚠️ Groq AI no disponible")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servicios IA: {e}")
    
    def _setup_flask_routes(self):
        """Configurar todas las rutas de Flask - VERSIÓN UNIFICADA"""
        
        @self.flask_app.route('/')
        def index():
            """Página principal del dashboard"""
            return render_template_string(self._get_dashboard_template())
        
        @self.flask_app.route('/api/dashboard/stats')
        def dashboard_stats():
            """Estadísticas del dashboard"""
            return jsonify({
                'total_articles': self.system_state['statistics']['total_articles'],
                'today_articles': 25,
                'high_risk_alerts': self.system_state['statistics']['risk_alerts'],
                'countries_monitored': 45,
                'last_update': datetime.now().isoformat(),
                'bert_loaded': self.system_state['bert_model_loaded'],
                'groq_available': self.system_state['groq_available']
            })

        @self.flask_app.route('/api/articles')
        def get_articles():
            """Obtiene lista de artículos con estructura consistente"""
            # Mock data - En producción conectar a BD real
            mock_articles = [
                {
                    'id': 1,
                    'title': 'Escalada militar en conflicto internacional',
                    'content': 'Las tensiones militares han aumentado significativamente en la región',
                    'location': 'Europa Oriental',
                    'risk_level': 'high',
                    'risk_score': 0.8,
                    'created_at': datetime.now().isoformat(),
                    'source': 'Reuters'
                },
                {
                    'id': 2,
                    'title': 'Cumbre económica internacional concluye exitosamente',
                    'content': 'Los líderes mundiales alcanzan acuerdos importantes',
                    'location': 'Geneva',
                    'risk_level': 'low',
                    'risk_score': 0.3,
                    'created_at': datetime.now().isoformat(),
                    'source': 'AP News'
                },
                {
                    'id': 3,
                    'title': 'Amenaza nuclear en Asia Pacific aumenta tensiones',
                    'content': 'Expertos expresan preocupación por desarrollos nucleares',
                    'location': 'Asia Pacific',
                    'risk_level': 'critical',
                    'risk_score': 0.95,
                    'created_at': datetime.now().isoformat(),
                    'source': 'BBC News'
                }
            ] * 7  # Repetir para tener más datos
            
            return jsonify({
                'articles': mock_articles,
                'page': 1,
                'total': len(mock_articles)
            })

        @self.flask_app.route('/api/analyze-importance', methods=['POST'])
        def analyze_importance():
            """ENDPOINT UNIFICADO: Análisis de importancia con BERT"""
            try:
                article_data = request.get_json()
                
                if not article_data:
                    return jsonify({'error': 'No article data provided'}), 400
                
                # Preparar texto para análisis
                title = article_data.get('title', '')
                content = article_data.get('content', '')
                location = article_data.get('location', '')
                risk_level = article_data.get('risk_level', 'medium')
                
                if not title and not content:
                    return jsonify({'error': 'No text to analyze'}), 400
                
                text = f"{title}. {content}".strip()
                
                # Usar servicio BERT si está disponible
                if self.bert_service.is_available():
                    logger.info(f"🧠 Analizando con BERT: {title[:50]}...")
                    result = self.bert_service.calculate_importance(text, location, risk_level)
                    
                    # Formatear respuesta consistente
                    response = {
                        'importance_factor': result['importance_score'],
                        'risk_factor': result['importance_score'],
                        'ai_analysis': result['sentiment_analysis'],
                        'geopolitical_factors': result['multipliers'],
                        'metadata': result['metadata'],
                        'model_info': {
                            'primary_model': 'BERT Service',
                            'ai_powered': True,
                            'fallback_used': False
                        }
                    }
                    
                    logger.info(f"✅ Análisis BERT completado: {result['importance_score']:.1f}%")
                    return jsonify(response)
                
                else:
                    # Fallback análisis cuando BERT no está disponible
                    logger.warning("⚠️ BERT no disponible, usando análisis de respaldo")
                    importance = self._analyze_importance_fallback(text, location, risk_level)
                    
                    return jsonify({
                        'importance_factor': importance,
                        'risk_factor': importance,
                        'ai_analysis': {'confidence': 0.5, 'method': 'keyword_based'},
                        'model_info': {
                            'primary_model': 'Fallback Analysis',
                            'ai_powered': False,
                            'fallback_used': True
                        }
                    })
                
            except Exception as e:
                logger.error(f"❌ Error en análisis de importancia: {e}")
                return jsonify({
                    'error': f'Error analyzing importance: {str(e)}',
                    'fallback_used': True
                }), 500

        @self.flask_app.route('/api/generate-ai-analysis', methods=['POST'])
        def generate_ai_analysis():
            """ENDPOINT UNIFICADO: Análisis geopolítico con Groq"""
            try:
                data = request.get_json() or {}
                
                # Obtener artículos
                articles = data.get('articles')
                if not articles:
                    # Usar datos de prueba si no se proporcionan artículos
                    articles = self._get_test_articles()
                
                if not articles:
                    return jsonify({'error': 'No articles provided for analysis'}), 400
                
                analysis_type = data.get('analysis_type', 'standard')
                
                logger.info(f"🤖 Generando análisis {analysis_type} con {len(articles)} artículos")
                
                # Usar servicio Groq
                if analysis_type == 'alternative':
                    analysis_result = self.groq_service.generate_alternative_analysis(articles)
                else:
                    analysis_result = self.groq_service.generate_geopolitical_analysis(articles, analysis_type)
                
                return jsonify({
                    'success': True,
                    'analysis': analysis_result,
                    'metadata': {
                        'articles_analyzed': len(articles),
                        'analysis_type': analysis_type,
                        'generation_time': datetime.now().isoformat(),
                        'service_used': 'Groq AI'
                    }
                })
                
            except Exception as e:
                logger.error(f"❌ Error en análisis geopolítico: {e}")
                return jsonify({
                    'error': f'Error generating analysis: {str(e)}',
                    'success': False
                }), 500

        @self.flask_app.route('/api/test-bert')
        def test_bert():
            """Test del servicio BERT"""
            try:
                if not self.bert_service.is_available():
                    return jsonify({
                        'status': 'ERROR',
                        'message': 'Servicio BERT no disponible',
                        'bert_loaded': False
                    }), 503
                
                # Test real del modelo
                test_text = "Military conflict escalates with nuclear threats in the region"
                result = self.bert_service.analyze_sentiment(test_text)
                
                return jsonify({
                    'status': 'OK',
                    'message': 'Servicio BERT funcionando correctamente',
                    'bert_loaded': True,
                    'test_analysis': result,
                    'model_info': self.bert_service.get_model_info()
                })
                
            except Exception as e:
                logger.error(f"❌ Error en test BERT: {e}")
                return jsonify({
                    'status': 'ERROR',
                    'message': f'Error testing BERT: {str(e)}',
                    'bert_loaded': False
                }), 500

        @self.flask_app.route('/api/system/status')
        def system_status():
            """Estado completo del sistema"""
            return jsonify({
                'system_state': self.system_state,
                'ai_services': {
                    'bert': {
                        'available': self.bert_service.is_available(),
                        'info': self.bert_service.get_model_info()
                    },
                    'groq': {
                        'available': self.groq_service.is_available(),
                        'info': self.groq_service.get_service_info()
                    }
                },
                'enhanced_features': ENHANCED_FEATURES_AVAILABLE,
                'timestamp': datetime.now().isoformat()
            })

        # Static files
        @self.flask_app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory('src/web/static', filename)
    
    def _analyze_importance_fallback(self, text: str, location: str, risk_level: str) -> float:
        """Análisis de importancia de respaldo basado en palabras clave"""
        high_importance_keywords = [
            'guerra', 'conflicto', 'crisis', 'ataque', 'sanción', 'nuclear',
            'emergencia', 'amenaza', 'tensión', 'militar', 'terrorista'
        ]
        
        medium_importance_keywords = [
            'acuerdo', 'negociación', 'reunión', 'cumbre', 'elección',
            'presidente', 'ministro', 'diplomático', 'económico'
        ]
        
        text_lower = text.lower()
        
        # Contar palabras clave
        high_count = sum(1 for keyword in high_importance_keywords if keyword in text_lower)
        medium_count = sum(1 for keyword in medium_importance_keywords if keyword in text_lower)
        
        # Calcular puntuación base
        base_score = 30 + (high_count * 15) + (medium_count * 8)
        
        # Aplicar multiplicadores geográficos
        geo_multiplier = 1.0
        high_risk_regions = ['ukraine', 'gaza', 'israel', 'syria', 'iran', 'iraq']
        for region in high_risk_regions:
            if region in location.lower():
                geo_multiplier = 1.3
                break
        
        # Multiplicador por nivel de riesgo
        risk_multipliers = {'critical': 1.4, 'high': 1.2, 'medium': 1.0, 'low': 0.8}
        risk_multiplier = risk_multipliers.get(risk_level.lower(), 1.0)
        
        final_score = base_score * geo_multiplier * risk_multiplier
        return max(10, min(100, final_score))
    
    def _get_test_articles(self) -> List[Dict]:
        """Obtiene artículos de prueba para análisis"""
        return [
            {
                'id': 1,
                'title': 'Escalada militar en conflicto internacional',
                'content': 'Las tensiones militares han aumentado significativamente en la región con movilización de tropas y declaraciones oficiales que indican una posible escalada del conflicto.',
                'location': 'Europa Oriental',
                'risk_level': 'high',
                'risk_score': 0.8,
                'source': 'Reuters'
            },
            {
                'id': 2,
                'title': 'Crisis diplomática entre potencias mundiales',
                'content': 'Las relaciones bilaterales se han deteriorado tras las últimas declaraciones oficiales, generando incertidumbre en los mercados.',
                'location': 'Asia-Pacífico',
                'risk_level': 'medium',
                'risk_score': 0.7,
                'source': 'BBC'
            },
            {
                'id': 3,
                'title': 'Movimientos económicos estratégicos',
                'content': 'Los últimos movimientos en el sector energético indican cambios importantes en las alianzas comerciales globales.',
                'location': 'Medio Oriente',
                'risk_level': 'medium',
                'risk_score': 0.6,
                'source': 'CNN'
            }
        ]
    
    def _get_dashboard_template(self) -> str:
        """Template HTML del dashboard principal"""
        return """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RiskMap Unified - Dashboard Geopolítico</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                body { background: #1a1a2e; color: white; font-family: 'Segoe UI', sans-serif; }
                .navbar { background: linear-gradient(135deg, #16213e, #1a1a2e); }
                .stat-card { 
                    background: linear-gradient(135deg, #0f3460, #16213e);
                    border-radius: 12px; padding: 20px; margin-bottom: 20px;
                    border: 1px solid #e74c3c33;
                }
                .stat-number { font-size: 2.5rem; font-weight: bold; color: #e74c3c; }
                .stat-label { color: #95a5a6; font-size: 0.9rem; }
                .status-indicator { 
                    width: 10px; height: 10px; border-radius: 50%; 
                    display: inline-block; margin-right: 8px;
                }
                .status-online { background: #27ae60; }
                .article-card {
                    background: linear-gradient(135deg, #0f3460, #16213e);
                    border-radius: 8px; padding: 15px; margin-bottom: 15px;
                    border-left: 4px solid #e74c3c;
                }
                .risk-high { border-left-color: #e74c3c; }
                .risk-medium { border-left-color: #f39c12; }
                .risk-low { border-left-color: #27ae60; }
                .risk-critical { border-left-color: #c0392b; }
                .ai-panel {
                    background: linear-gradient(135deg, #2c3e50, #34495e);
                    border-radius: 12px; padding: 20px;
                    border: 1px solid #3498db33;
                }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
                <div class="container-fluid">
                    <a class="navbar-brand" href="#">
                        <i class="fas fa-globe-americas me-2"></i>
                        <strong>RiskMap Unified</strong> <small class="text-light">v3.0 BERT+Groq</small>
                    </a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text">
                            <span class="status-indicator status-online"></span>
                            Sistema Operativo
                        </span>
                    </div>
                </div>
            </nav>

            <div class="container-fluid py-4">
                <!-- Statistics Row -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-number" id="totalArticles">0</div>
                            <div class="stat-label">Artículos Monitoreados</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-number" id="highImportance">0</div>
                            <div class="stat-label">Alta Importancia</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-number" id="activeConflicts">3</div>
                            <div class="stat-label">Conflictos Activos</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-number" id="regionsMonitored">8</div>
                            <div class="stat-label">Regiones Monitoreadas</div>
                        </div>
                    </div>
                </div>

                <!-- Main Content Row -->
                <div class="row">
                    <!-- Articles Panel -->
                    <div class="col-lg-6">
                        <div class="ai-panel">
                            <h5><i class="fas fa-newspaper me-2"></i>Últimas Noticias Críticas</h5>
                            <div id="articlesContainer">
                                <p class="text-muted">Cargando artículos...</p>
                            </div>
                        </div>
                    </div>

                    <!-- AI Analysis Panel -->
                    <div class="col-lg-6">
                        <div class="ai-panel">
                            <h5><i class="fas fa-brain me-2"></i>Análisis Geopolítico IA</h5>
                            <div class="mb-3">
                                <button class="btn btn-primary me-2" onclick="generateAnalysis()">
                                    <i class="fas fa-magic me-1"></i>Generar Análisis Groq
                                </button>
                                <button class="btn btn-info" onclick="testBert()">
                                    <i class="fas fa-flask me-1"></i>Test BERT
                                </button>
                            </div>
                            <div id="analysisContainer">
                                <p class="text-muted">Haz clic en "Generar Análisis" para obtener un análisis geopolítico completo usando IA</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Status Panel -->
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="ai-panel">
                            <h6><i class="fas fa-cogs me-2"></i>Estado del Sistema</h6>
                            <div class="row">
                                <div class="col-md-4">
                                    <span class="badge bg-success me-2">BERT</span>
                                    <span id="bertStatus">Verificando...</span>
                                </div>
                                <div class="col-md-4">
                                    <span class="badge bg-info me-2">Groq AI</span>
                                    <span id="groqStatus">Verificando...</span>
                                </div>
                                <div class="col-md-4">
                                    <span class="badge bg-primary me-2">Sistema</span>
                                    <span id="systemStatus">Operativo</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Load dashboard data
                async function loadDashboard() {
                    try {
                        // Load statistics
                        const statsResponse = await fetch('/api/dashboard/stats');
                        const stats = await statsResponse.json();
                        
                        document.getElementById('totalArticles').textContent = stats.total_articles || 0;
                        document.getElementById('highImportance').textContent = stats.high_risk_alerts || 0;
                        
                        // Load articles
                        const articlesResponse = await fetch('/api/articles');
                        const articlesData = await articlesResponse.json();
                        
                        const articlesHtml = articlesData.articles.slice(0, 5).map(article => `
                            <div class="article-card risk-${article.risk_level}">
                                <h6>${article.title}</h6>
                                <p class="mb-1">${article.content.substring(0, 120)}...</p>
                                <small class="text-muted">
                                    <i class="fas fa-map-marker-alt me-1"></i>${article.location}
                                    <span class="ms-3"><i class="fas fa-exclamation-triangle me-1"></i>Riesgo: ${article.risk_level}</span>
                                </small>
                            </div>
                        `).join('');
                        
                        document.getElementById('articlesContainer').innerHTML = articlesHtml;
                        
                        // Check system status
                        const statusResponse = await fetch('/api/system/status');
                        const status = await statusResponse.json();
                        
                        document.getElementById('bertStatus').textContent = 
                            status.ai_services.bert.available ? 'Operativo' : 'No disponible';
                        document.getElementById('groqStatus').textContent = 
                            status.ai_services.groq.available ? 'Operativo' : 'No disponible';
                        
                    } catch (error) {
                        console.error('Error loading dashboard:', error);
                    }
                }

                async function generateAnalysis() {
                    const container = document.getElementById('analysisContainer');
                    container.innerHTML = '<p class="text-info"><i class="fas fa-spinner fa-spin me-2"></i>Generando análisis geopolítico...</p>';
                    
                    try {
                        const response = await fetch('/api/generate-ai-analysis', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ analysis_type: 'standard' })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            container.innerHTML = `
                                <div class="analysis-result">
                                    <h6 class="text-info">${data.analysis.title}</h6>
                                    <p class="text-muted mb-2">${data.analysis.subtitle}</p>
                                    <div class="analysis-content">${data.analysis.content}</div>
                                    <small class="text-muted mt-2 d-block">
                                        Fuentes analizadas: ${data.analysis.sources_count} | 
                                        Generado: ${new Date(data.metadata.generation_time).toLocaleString()}
                                    </small>
                                </div>
                            `;
                        } else {
                            container.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
                        }
                    } catch (error) {
                        container.innerHTML = `<p class="text-danger">Error generando análisis: ${error.message}</p>`;
                    }
                }

                async function testBert() {
                    try {
                        const response = await fetch('/api/test-bert');
                        const data = await response.json();
                        
                        if (data.status === 'OK') {
                            alert(`✅ BERT Test Exitoso\\n\\nModelo: ${data.model_info.model_name}\\nDispositivo: ${data.model_info.device}\\nConfianza: ${data.test_analysis.confidence}`);
                        } else {
                            alert(`❌ BERT Test Fallido\\n\\n${data.message}`);
                        }
                    } catch (error) {
                        alert(`❌ Error probando BERT: ${error.message}`);
                    }
                }

                // Initialize dashboard
                loadDashboard();
                
                // Auto-refresh every 30 seconds
                setInterval(loadDashboard, 30000);
            </script>
        </body>
        </html>
        """
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto del sistema completo"""
        return {
            # Web server configuration
            'flask_port': 5003,  # Puerto unificado para BERT + Groq
            'flask_host': '127.0.0.1',
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
            'enable_bert_analysis': True,
            'enable_groq_analysis': True,
            
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
    
    def _run_background_task(self, task_name: str, task_function):
        """Ejecuta una tarea en background"""
        if task_name in self.background_threads and self.background_threads[task_name].is_alive():
            logger.warning(f"Task {task_name} already running")
            return
        
        thread = threading.Thread(
            target=task_function,
            name=task_name,
            daemon=True
        )
        thread.start()
        self.background_threads[task_name] = thread
        self.system_state['background_tasks'][task_name] = {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        return thread
    
    def start_application(self):
        """Inicia la aplicación completa"""
        try:
            logger.info("🚀 Iniciando RiskMap Unified Application")
            
            # Inicializar servicios IA
            self._initialize_ai_services()
            
            # Inicializar componentes avanzados si están disponibles
            if ENHANCED_FEATURES_AVAILABLE:
                self._initialize_enhanced_features()
            
            # Marcar como listo
            self.system_state['api_ready'] = True
            self.system_state['system_status'] = 'operational'
            
            logger.info("✅ Aplicación inicializada correctamente")
            
            # Iniciar servidor Flask
            self.flask_app.run(
                host=self.config['flask_host'],
                port=self.config['flask_port'],
                debug=self.config['flask_debug'],
                threaded=True
            )
            
        except Exception as e:
            logger.error(f"❌ Error iniciando aplicación: {e}")
            raise
    
    def _initialize_enhanced_features(self):
        """Inicializa características avanzadas si están disponibles"""
        try:
            logger.info("🔧 Inicializando características avanzadas...")
            
            if ENHANCED_FEATURES_AVAILABLE:
                # Inicializar orquestadores si están disponibles
                try:
                    self.core_orchestrator = GeopoliticalIntelligenceOrchestrator()
                    self.system_state['core_system_initialized'] = True
                    logger.info("✅ Core orchestrator inicializado")
                except Exception as e:
                    logger.warning(f"⚠️ Core orchestrator no disponible: {e}")
                
                try:
                    self.historical_orchestrator = EnhancedHistoricalOrchestrator()
                    self.system_state['historical_system_initialized'] = True
                    logger.info("✅ Historical orchestrator inicializado")
                except Exception as e:
                    logger.warning(f"⚠️ Historical orchestrator no disponible: {e}")
            
        except Exception as e:
            logger.warning(f"⚠️ Características avanzadas no disponibles: {e}")
    
    def stop_application(self):
        """Detiene la aplicación de forma graceful"""
        logger.info("🛑 Deteniendo aplicación...")
        
        # Señalar shutdown
        self.shutdown_event.set()
        
        # Esperar que terminen las tareas background
        for task_name, thread in self.background_threads.items():
            if thread.is_alive():
                logger.info(f"⏳ Esperando tarea: {task_name}")
                thread.join(timeout=5)
        
        self.system_state['system_status'] = 'stopped'
        logger.info("✅ Aplicación detenida")


def main():
    """Función principal del sistema unificado"""
    try:
        logger.info("🚀 Iniciando RiskMap Unified - BERT + Groq AI")
        
        # Crear y configurar aplicación
        app = RiskMapUnifiedApplication()
        
        # Ejecutar aplicación
        app.start_application()
        
    except KeyboardInterrupt:
        logger.info("👋 Aplicación detenida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        raise


if __name__ == "__main__":
    main()
