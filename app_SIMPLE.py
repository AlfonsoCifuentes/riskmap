#!/usr/bin/env python3
"""
app_SIMPLE.py
Versión simplificada de la aplicación RiskMap que evita módulos problemáticos
"""

import os
import sys
import logging
import warnings
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Configurar warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleRiskMap:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
        
    def setup_routes(self):
        """Configurar rutas básicas"""
        
        @self.app.route('/')
        def home():
            return render_template_string(HOME_TEMPLATE)
        
        @self.app.route('/api/status')
        def status():
            return jsonify({
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0-simple',
                'components': {
                    'basic_server': True,
                    'database': self.check_database(),
                    'nlp_system': False,  # Deshabilitado temporalmente
                    'visualization': False  # Deshabilitado temporalmente
                }
            })
        
        @self.app.route('/api/articles')
        def get_articles():
            """Obtener artículos de la base de datos"""
            try:
                import sqlite3
                conn = sqlite3.connect('./data/geopolitical_intel.db')
                cursor = conn.cursor()
                
                # Obtener últimos 10 artículos
                cursor.execute("""
                    SELECT id, title, content, source, published_date, sentiment, risk_score
                    FROM processed_data 
                    ORDER BY processed_date DESC 
                    LIMIT 10
                """)
                
                articles = []
                for row in cursor.fetchall():
                    articles.append({
                        'id': row[0],
                        'title': row[1],
                        'content': row[2][:200] + '...' if row[2] else '',
                        'source': row[3],
                        'published_date': row[4],
                        'sentiment': row[5],
                        'risk_score': row[6]
                    })
                
                conn.close()
                return jsonify({'articles': articles, 'count': len(articles)})
                
            except Exception as e:
                logger.error(f"Error getting articles: {e}")
                return jsonify({'error': str(e), 'articles': [], 'count': 0})
    
    def check_database(self):
        """Verificar estado de la base de datos"""
        try:
            import sqlite3
            conn = sqlite3.connect('./data/geopolitical_intel.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processed_data")
            count = cursor.fetchone()[0]
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database check error: {e}")
            return False
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Ejecutar la aplicación"""
        print(f"""
🗺️  RISKMAP - MODO SIMPLIFICADO
===============================
✅ Servidor iniciado en http://{host}:{port}
✅ Base de datos conectada: {self.check_database()}
✅ APIs básicas disponibles

📊 Endpoints disponibles:
   - GET /           - Página principal
   - GET /api/status - Estado del sistema
   - GET /api/articles - Artículos almacenados

⚠️  Modo simplificado - algunas funciones están deshabilitadas
===============================
        """)
        
        self.app.run(host=host, port=port, debug=debug)

# Template HTML simple
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiskMap - Modo Simplificado</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f4; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #2c3e50; text-align: center; }
        .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }
        .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .button:hover { background: #0056b3; }
        #articles { margin-top: 20px; }
        .article { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗺️ RiskMap - Sistema de Análisis Geopolítico</h1>
        
        <div class="status">
            <h3>Estado del Sistema</h3>
            <p id="status">Cargando...</p>
        </div>
        
        <div class="card">
            <h3>Funciones Disponibles</h3>
            <button class="button" onclick="loadStatus()">🔄 Actualizar Estado</button>
            <button class="button" onclick="loadArticles()">📰 Cargar Artículos</button>
            <button class="button" onclick="window.open('/api/status', '_blank')">📊 API Status</button>
        </div>
        
        <div id="articles"></div>
    </div>

    <script>
        function loadStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = `
                        <strong>Estado:</strong> ${data.status} <br>
                        <strong>Versión:</strong> ${data.version} <br>
                        <strong>Timestamp:</strong> ${data.timestamp} <br>
                        <strong>Base de datos:</strong> ${data.components.database ? '✅ OK' : '❌ Error'}
                    `;
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = '❌ Error cargando estado';
                });
        }
        
        function loadArticles() {
            fetch('/api/articles')
                .then(response => response.json())
                .then(data => {
                    const articlesDiv = document.getElementById('articles');
                    if (data.articles && data.articles.length > 0) {
                        articlesDiv.innerHTML = `
                            <h3>📰 Últimos Artículos (${data.count})</h3>
                            ${data.articles.map(article => `
                                <div class="article">
                                    <h4>${article.title}</h4>
                                    <p><strong>Fuente:</strong> ${article.source || 'N/A'}</p>
                                    <p><strong>Fecha:</strong> ${article.published_date || 'N/A'}</p>
                                    <p>${article.content}</p>
                                    <p><strong>Sentiment:</strong> ${article.sentiment || 'N/A'} | 
                                       <strong>Risk Score:</strong> ${article.risk_score || 'N/A'}</p>
                                </div>
                            `).join('')}
                        `;
                    } else {
                        articlesDiv.innerHTML = '<h3>📰 No hay artículos disponibles</h3>';
                    }
                })
                .catch(error => {
                    document.getElementById('articles').innerHTML = '<h3>❌ Error cargando artículos</h3>';
                });
        }
        
        // Cargar estado inicial
        loadStatus();
    </script>
</body>
</html>
'''

def render_template_string(template):
    """Función helper para renderizar template string"""
    return template

if __name__ == '__main__':
    app = SimpleRiskMap()
    app.run(debug=True)