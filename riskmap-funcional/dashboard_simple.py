"""
Dashboard Simple - Lanzador del Dashboard sin dependencias pesadas
"""

import logging
import sys
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import sqlite3
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDashboardApp:
    """Dashboard simplificado sin dependencias de ML/NLP pesadas"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        template_folder='src/dashboard/templates',
                        static_folder='src/dashboard/static')
        self.app.secret_key = 'riskmap_dashboard_simple'
        CORS(self.app)
        
        self.setup_routes()
        
    def setup_routes(self):
        """Configurar las rutas del dashboard"""
        
        @self.app.route('/')
        def dashboard():
            """Página principal del dashboard"""
            return render_template('modern_dashboard_updated.html')
            
        @self.app.route('/api/articles/mosaic')
        def api_articles_mosaic():
            """API para el mosaico de artículos"""
            try:
                # Mock data para testing
                mock_articles = [
                    {
                        "id": 1,
                        "title": "Tensiones Geopolíticas en Europa Oriental",
                        "summary": "Análisis de las últimas tensiones diplomáticas en la región",
                        "risk_score": 8.5,
                        "importance": 9.2,
                        "published_date": "2025-07-30T20:00:00Z",
                        "source": "Reuters",
                        "url": "https://example.com/article1",
                        "categories": ["geopolitics", "europe"],
                        "sentiment": "negative"
                    },
                    {
                        "id": 2,
                        "title": "Avances en Energías Renovables",
                        "summary": "Nuevas tecnologías solares aumentan eficiencia energética",
                        "risk_score": 2.1,
                        "importance": 7.8,
                        "published_date": "2025-07-30T18:30:00Z",
                        "source": "Energy Today",
                        "url": "https://example.com/article2",
                        "categories": ["energy", "technology"],
                        "sentiment": "positive"
                    },
                    {
                        "id": 3,
                        "title": "Crisis Económica Regional",
                        "summary": "Indicadores económicos muestran desaceleración",
                        "risk_score": 7.2,
                        "importance": 8.1,
                        "published_date": "2025-07-30T16:45:00Z",
                        "source": "Financial Times",
                        "url": "https://example.com/article3",
                        "categories": ["economy", "finance"],
                        "sentiment": "negative"
                    }
                ]
                
                return jsonify({
                    "status": "success",
                    "articles": mock_articles,
                    "total": len(mock_articles)
                })
                
            except Exception as e:
                logger.error(f"Error en API articles/mosaic: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
                
        @self.app.route('/api/articles/importance', methods=['POST'])
        def api_calculate_importance():
            """API para calcular importancia de artículos"""
            try:
                data = request.get_json()
                articles = data.get('articles', [])
                
                # Simulación de cálculo de importancia
                for article in articles:
                    # Combinar risk_score y otros factores
                    risk = article.get('risk_score', 0)
                    recency = 10 - min(10, (datetime.now() - datetime.fromisoformat(
                        article.get('published_date', '').replace('Z', '+00:00')
                    )).days)
                    
                    importance = (risk * 0.7) + (recency * 0.3)
                    article['calculated_importance'] = min(10, max(0, importance))
                
                return jsonify({
                    "status": "success", 
                    "articles": articles
                })
                
            except Exception as e:
                logger.error(f"Error calculando importancia: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
                
        @self.app.route('/api/statistics/summary')
        def api_statistics():
            """API para estadísticas del dashboard"""
            return jsonify({
                "status": "success",
                "data": {
                    "total_articles": 156,
                    "high_risk_articles": 12,
                    "sources_active": 8,
                    "last_update": datetime.now().isoformat(),
                    "processing_status": "active"
                }
            })
            
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            })
            
    def run(self, host='127.0.0.1', port=5000, debug=True):
        """Ejecutar el dashboard"""
        logger.info(f"🚀 Iniciando Dashboard Simple en http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    dashboard = SimpleDashboardApp()
    dashboard.run()
