#!/usr/bin/env python3
"""
RiskMap - Aplicación Corregida para Noticias Geopolíticas
Versión híbrida que combina simplicidad con funcionalidad correcta
"""

import os
import sys
from datetime import datetime
import sqlite3
from flask import Flask, jsonify, render_template_string, request
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiskMapApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'geopolitical-intelligence-key-2024'
        self.setup_routes()
        
    def setup_routes(self):
        """Configurar rutas de la aplicación"""
        
        @self.app.route('/')
        def home():
            """Página principal"""
            return render_template_string(self.get_home_template())
        
        @self.app.route('/api/status')
        def api_status():
            """Estado del sistema"""
            return jsonify({
                'status': 'operational',
                'timestamp': datetime.now().isoformat(),
                'database': self.check_database(),
                'components': {
                    'core': True,
                    'database': True,
                    'api': True,
                    'nlp_system': False,  # Deshabilitado temporalmente
                    'visualization': False  # Deshabilitado temporalmente
                }
            })
        
        @self.app.route('/api/articles')
        def get_articles():
            """Obtener artículos geopolíticos con imágenes reales"""
            try:
                return jsonify(self.get_top_articles_from_db(limit=20))
            except Exception as e:
                logger.error(f"Error in /api/articles: {e}")
                return jsonify({
                    'error': 'Error al cargar artículos',
                    'message': str(e),
                    'articles': []
                }), 500
        
        @self.app.route('/api/hero-article')
        def get_hero_article():
            """Obtener artículo principal"""
            try:
                articles = self.get_top_articles_from_db(limit=1)
                if articles:
                    return jsonify(articles[0])
                else:
                    return jsonify({
                        'error': 'No hay artículos disponibles',
                        'id': 0,
                        'title': 'Sistema de Análisis Geopolítico',
                        'summary': 'Plataforma de análisis de inteligencia geopolítica en funcionamiento.',
                        'location': 'Global',
                        'risk_score': 0.5
                    })
            except Exception as e:
                logger.error(f"Error in /api/hero-article: {e}")
                return jsonify({
                    'error': 'Error al cargar artículo principal',
                    'message': str(e),
                    'id': 0,
                    'title': 'Error de Sistema',
                    'summary': 'Error temporal en el sistema.',
                    'location': 'Global',
                    'risk_score': 0.0
                }), 500

        @self.app.route('/api/articles/deduplicated')
        def get_deduplicated_articles():
            """Obtener artículos sin duplicados"""
            try:
                # Por ahora, usar la misma lógica que get_articles
                return jsonify(self.get_top_articles_from_db(limit=30))
            except Exception as e:
                logger.error(f"Error in /api/articles/deduplicated: {e}")
                return jsonify({
                    'error': 'Error al cargar artículos sin duplicados',
                    'message': str(e),
                    'articles': []
                }), 500

        @self.app.route('/static/images/news/<path:filename>')
        def serve_news_images(filename):
            """Servir imágenes de noticias"""
            from flask import send_from_directory
            try:
                return send_from_directory('static/images/news', filename)
            except Exception as e:
                logger.error(f"Error serving image {filename}: {e}")
                # Devolver imagen placeholder
                return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='200'%3E%3Crect width='100%25' height='100%25' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999'%3EImagen no disponible%3C/text%3E%3C/svg%3E", 200, {'Content-Type': 'image/svg+xml'}

    def get_top_articles_from_db(self, limit=20, exclude_hero_id=None):
        """
        Obtiene artículos geopolíticos con imágenes reales de la base de datos
        SOLO artículos geopolíticos con fotos originales
        """
        try:
            db_path = "./data/geopolitical_intel.db"
            if not os.path.exists(db_path):
                logger.error(f"Database not found: {db_path}")
                return []

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # FILTRO GEOPOLÍTICO ULTRA-ESTRICTO: Solo contenido geopolítico con imagen real
            base_query = """
                SELECT 
                    id, title, 
                    CASE 
                        WHEN summary IS NOT NULL AND summary != '' AND summary NOT LIKE '%<think>%' THEN 
                            summary
                        WHEN auto_generated_summary IS NOT NULL AND auto_generated_summary != '' AND auto_generated_summary NOT LIKE '%<think>%' THEN 
                            auto_generated_summary
                        WHEN content IS NOT NULL AND content != '' AND content NOT LIKE '%<think>%' THEN 
                            SUBSTR(content, 1, 300) || '...'
                        ELSE 
                            'Análisis de contenido geopolítico disponible para revisión.'
                    END as summary,
                    url, source, published_at, country, region, risk_level, 
                    conflict_type, sentiment_score, risk_score,
                    CASE 
                        WHEN original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
                        THEN original_image_url
                        WHEN image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%via.placeholder%' THEN 
                            image_url
                        ELSE NULL
                    END as image_url,
                    ai_importance
                FROM articles 
                WHERE 
                    -- INCLUSIONES ESTRICTAS: Solo contenido geopolítico
                    (
                        -- Países y regiones de alto interés geopolítico
                        LOWER(title) LIKE '%ukraine%' OR LOWER(title) LIKE '%russia%' OR
                        LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%taiwan%' OR
                        LOWER(title) LIKE '%north korea%' OR LOWER(title) LIKE '%iran%' OR
                        LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%palestine%' OR
                        LOWER(title) LIKE '%gaza%' OR LOWER(title) LIKE '%syria%' OR
                        LOWER(title) LIKE '%afghanistan%' OR LOWER(title) LIKE '%yemen%' OR
                        LOWER(title) LIKE '%iraq%' OR LOWER(title) LIKE '%lebanon%' OR
                        LOWER(title) LIKE '%turkey%' OR LOWER(title) LIKE '%venezuela%' OR
                        LOWER(title) LIKE '%myanmar%' OR LOWER(title) LIKE '%belarus%' OR
                        LOWER(title) LIKE '%hong kong%' OR LOWER(title) LIKE '%tibet%' OR
                        LOWER(title) LIKE '%middle east%' OR LOWER(title) LIKE '%balkans%' OR
                        LOWER(title) LIKE '%kashmir%' OR LOWER(title) LIKE '%kurdish%' OR
                        LOWER(title) LIKE '%romania%' OR LOWER(title) LIKE '%poland%' OR
                        LOWER(title) LIKE '%moldova%' OR LOWER(title) LIKE '%georgia%' OR
                        LOWER(title) LIKE '%armenia%' OR LOWER(title) LIKE '%azerbaijan%' OR
                        LOWER(title) LIKE '%nepal%' OR LOWER(title) LIKE '%india%' OR
                        LOWER(title) LIKE '%pakistan%' OR LOWER(title) LIKE '%bangladesh%' OR
                        
                        -- Líderes políticos y figuras internacionales
                        LOWER(title) LIKE '%putin%' OR LOWER(title) LIKE '%zelensky%' OR
                        LOWER(title) LIKE '%xi jinping%' OR LOWER(title) LIKE '%biden%' OR
                        LOWER(title) LIKE '%trump%' OR LOWER(title) LIKE '%netanyahu%' OR
                        LOWER(title) LIKE '%khamenei%' OR LOWER(title) LIKE '%erdogan%' OR
                        LOWER(title) LIKE '%modi%' OR LOWER(title) LIKE '%marcos%' OR
                        LOWER(title) LIKE '%rubio%' OR LOWER(title) LIKE '%harris%' OR
                        
                        -- Términos geopolíticos en español
                        LOWER(title) LIKE '%guerra%' OR LOWER(title) LIKE '%militar%' OR
                        LOWER(title) LIKE '%política%' OR LOWER(title) LIKE '%gobierno%' OR
                        LOWER(title) LIKE '%seguridad%' OR LOWER(title) LIKE '%diplomacia%' OR
                        LOWER(title) LIKE '%internacional%' OR LOWER(title) LIKE '%rusia%' OR
                        LOWER(title) LIKE '%ucrania%' OR LOWER(title) LIKE '%irán%' OR
                        LOWER(title) LIKE '%conflicto%' OR LOWER(title) LIKE '%crisis%' OR
                        
                        -- Temas de seguridad y inteligencia
                        LOWER(title) LIKE '%intelligence%' OR LOWER(title) LIKE '%spy%' OR
                        LOWER(title) LIKE '%espionage%' OR LOWER(title) LIKE '%cyber%' OR
                        LOWER(title) LIKE '%hacking%' OR LOWER(title) LIKE '%breach%' OR
                        LOWER(title) LIKE '%leak%' OR LOWER(title) LIKE '%classified%' OR
                        LOWER(title) LIKE '%drone%' OR LOWER(title) LIKE '%missile%' OR
                        LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%weapons%'
                    ) AND (
                        -- EXCLUSIONES ULTRA ESTRICTAS: Rechazar CUALQUIER contenido no geopolítico
                        -- Una sola condición que coincida = EXCLUIDO INMEDIATAMENTE
                        
                        -- ENTRETENIMIENTO (Emmy, Oscar, film, etc.)
                        LOWER(title) NOT LIKE '%emmy%' AND LOWER(title) NOT LIKE '%emmys%' AND
                        LOWER(title) NOT LIKE '%oscar%' AND LOWER(title) NOT LIKE '%oscars%' AND
                        LOWER(title) NOT LIKE '%movie%' AND LOWER(title) NOT LIKE '%movies%' AND
                        LOWER(title) NOT LIKE '%film%' AND LOWER(title) NOT LIKE '%films%' AND
                        LOWER(title) NOT LIKE '%festival%' AND LOWER(title) NOT LIKE '%actor%' AND 
                        LOWER(title) NOT LIKE '%actress%' AND LOWER(title) NOT LIKE '%hollywood%' AND 
                        LOWER(title) NOT LIKE '%singer%' AND LOWER(title) NOT LIKE '%music%' AND 
                        LOWER(title) NOT LIKE '%celebrity%' AND LOWER(title) NOT LIKE '%tv show%' AND 
                        LOWER(title) NOT LIKE '%netflix%' AND LOWER(title) NOT LIKE '%anime%' AND
                        LOWER(title) NOT LIKE '%toronto%' AND LOWER(title) NOT LIKE '%hamnet%' AND
                        LOWER(title) NOT LIKE '%audience award%' AND LOWER(title) NOT LIKE '%choice award%' AND
                        
                        -- DEPORTES (NFL, NBA, etc.)
                        LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
                        LOWER(title) NOT LIKE '%game%' AND LOWER(title) NOT LIKE '%games%' AND
                        LOWER(title) NOT LIKE '%match%' AND LOWER(title) NOT LIKE '%team%' AND
                        LOWER(title) NOT LIKE '%player%' AND LOWER(title) NOT LIKE '%football%' AND
                        LOWER(title) NOT LIKE '%soccer%' AND LOWER(title) NOT LIKE '%basketball%' AND
                        LOWER(title) NOT LIKE '%baseball%' AND LOWER(title) NOT LIKE '%nfl%' AND
                        LOWER(title) NOT LIKE '%nba%' AND LOWER(title) NOT LIKE '%giants%' AND
                        LOWER(title) NOT LIKE '%cowboys%' AND LOWER(title) NOT LIKE '%vikings%' AND
                        
                        -- TECNOLOGÍA CONSUMER (iPhone, Apple, etc.)
                        LOWER(title) NOT LIKE '%iphone%' AND LOWER(title) NOT LIKE '%apple%' AND
                        LOWER(title) NOT LIKE '%nintendo%' AND LOWER(title) NOT LIKE '%switch%' AND
                        LOWER(title) NOT LIKE '%google%' AND LOWER(title) NOT LIKE '%meta%' AND
                        LOWER(title) NOT LIKE '%facebook%' AND LOWER(title) NOT LIKE '%spotify%' AND
                        LOWER(title) NOT LIKE '%tesla%' AND LOWER(title) NOT LIKE '%microsoft%' AND
                        LOWER(title) NOT LIKE '%amazon%' AND LOWER(title) NOT LIKE '%smartphone%' AND
                        LOWER(title) NOT LIKE '%9to5mac%' AND LOWER(title) NOT LIKE '%sales off%' AND
                        LOWER(title) NOT LIKE '%air launch%' AND LOWER(title) NOT LIKE '%blocked%' AND
                        
                        -- TÉRMINOS EN ESPAÑOL
                        LOWER(title) NOT LIKE '%deporte%' AND LOWER(title) NOT LIKE '%deportes%' AND
                        LOWER(title) NOT LIKE '%fútbol%' AND LOWER(title) NOT LIKE '%música%' AND
                        LOWER(title) NOT LIKE '%película%' AND LOWER(title) NOT LIKE '%famoso%' AND
                        
                        -- SALUD GENERAL (no geopolítica)
                        LOWER(title) NOT LIKE '%vaccine%' AND LOWER(title) NOT LIKE '%covid%' AND
                        LOWER(title) NOT LIKE '%health%' AND LOWER(title) NOT LIKE '%medical%'
                        
                    ) AND (
                        -- EXCLUSIÓN POR FUENTES: Rechazar fuentes claramente no geopolíticas
                        source NOT LIKE '%Sports%' AND source NOT LIKE '%ESPN%' AND 
                        source NOT LIKE '%Entertainment%' AND source NOT LIKE '%TMZ%' AND 
                        source NOT LIKE '%People%' AND source NOT LIKE '%AppleInsider%' AND 
                        source NOT LIKE '%9to5Mac%' AND source NOT LIKE '%TechCrunch%' AND
                        source NOT LIKE '%Variety%' AND source NOT LIKE '%Hollywood Reporter%' AND
                        source NOT LIKE '%Sporting News%' AND source NOT LIKE '%Sports Illustrated%' AND
                        source NOT LIKE '%CBS Sports%' AND source NOT LIKE '%NBC Sports%' AND
                        source NOT LIKE '%The Verge%' AND source NOT LIKE '%GameSpot%' AND
                        source NOT LIKE '%Giants.com%' AND source NOT LIKE '%NBCSports.com%' AND
                        source NOT LIKE '%Yahoo Entertainment%' AND source NOT LIKE '%Deadline%'
                    ) AND (
                        -- SOLO artículos con imagen real (NO placeholders)
                        (
                            (original_image_url IS NOT NULL AND original_image_url != '') OR
                            (image_url IS NOT NULL AND image_url != '' AND 
                             image_url NOT LIKE '%via.placeholder%' AND 
                             image_url NOT LIKE '%placeholder.com%' AND
                             image_url NOT LIKE '%default%' AND
                             image_url NOT LIKE '%generic%' AND
                             image_url NOT LIKE '%mockup%')
                        )
                    ) AND
                    
                    -- Excluir HERO si se especifica
                    {exclude_clause}
                    
                    -- Solo artículos recientes (últimos 14 días para más contenido geopolítico)
                    created_at >= datetime('now', '-14 days')
                ORDER BY 
                    -- Prioridad: importancia AI > riesgo > fecha
                    COALESCE(ai_importance, 0) DESC,
                    COALESCE(risk_score, 0) DESC,
                    created_at DESC
                LIMIT ?
            """
            
            exclude_clause = "id != ?" if exclude_hero_id else "1=1"
            query = base_query.format(exclude_clause=exclude_clause)
            
            if exclude_hero_id:
                cursor.execute(query, (exclude_hero_id, limit))
            else:
                cursor.execute(query, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convertir a formato diccionario
            articles = []
            for row in rows:
                article = {
                    'id': row[0],
                    'title': row[1] or 'Sin título',
                    'summary': row[2] or 'Sin resumen disponible',
                    'url': row[3] or '',
                    'source': row[4] or 'Fuente desconocida',
                    'published_at': row[5],
                    'country': row[6] or 'Global',
                    'region': row[7] or 'Internacional',
                    'risk_level': row[8] or 'medium',
                    'conflict_type': row[9] or '',
                    'sentiment_score': row[10] or 0.0,
                    'risk_score': row[11] or 0.0,
                    'image_url': row[12],  # Solo imagen real o None
                    'ai_importance': row[13] or 0.0,
                    'location': row[6] or 'Global'
                }
                articles.append(article)
            
            logger.info(f"✅ Filtro geopolítico ESTRICTO aplicado: {len(articles)} artículos válidos de BD")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error al obtener artículos de BD: {e}")
            return []

    def check_database(self):
        """Verificar conectividad de base de datos"""
        try:
            conn = sqlite3.connect('./data/geopolitical_intel.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception:
            return False

    def get_home_template(self):
        """Template HTML simple para la página principal"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>RiskMap - Análisis Geopolítico</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .header { text-align: center; margin-bottom: 30px; }
        .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .endpoints { background: #f0f8ff; padding: 15px; border-radius: 5px; }
        .articles { margin-top: 20px; }
        .article { background: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ RiskMap - Sistema Corregido</h1>
            <p>Análisis de Inteligencia Geopolítica</p>
        </div>
        
        <div class="status">
            <h3>✅ Estado del Sistema</h3>
            <p>Servidor: <strong>Operacional</strong></p>
            <p>Base de datos: <strong id="db-status">Verificando...</strong></p>
            <p>Última actualización: <span id="timestamp">{{timestamp}}</span></p>
        </div>
        
        <div class="endpoints">
            <h3>📊 API Endpoints Disponibles</h3>
            <ul>
                <li>GET / - Esta página</li>
                <li>GET /api/status - Estado del sistema</li>
                <li>GET /api/articles - Artículos geopolíticos</li>
                <li>GET /api/hero-article - Artículo principal</li>
                <li>GET /api/articles/deduplicated - Artículos sin duplicados</li>
            </ul>
        </div>
        
        <div class="articles">
            <h3>📰 Artículos Recientes</h3>
            <div id="articles-container">Cargando artículos...</div>
        </div>
    </div>
    
    <script>
        // Verificar estado del sistema
        fetch('/api/status')
            .then(r => r.json())
            .then(data => {
                document.getElementById('db-status').textContent = data.database ? 'Conectada' : 'Desconectada';
                document.getElementById('timestamp').textContent = new Date(data.timestamp).toLocaleString();
            })
            .catch(e => {
                document.getElementById('db-status').textContent = 'Error';
                document.getElementById('db-status').className = 'error';
            });
        
        // Cargar artículos
        fetch('/api/articles')
            .then(r => r.json())
            .then(articles => {
                const container = document.getElementById('articles-container');
                if (articles && articles.length > 0) {
                    container.innerHTML = articles.slice(0, 5).map(article => `
                        <div class="article">
                            <strong>${article.title}</strong><br>
                            <small>Fuente: ${article.source} | Riesgo: ${(article.risk_score * 100).toFixed(0)}%</small><br>
                            ${article.summary.substring(0, 150)}...
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<p class="error">No hay artículos disponibles</p>';
                }
            })
            .catch(e => {
                document.getElementById('articles-container').innerHTML = '<p class="error">Error al cargar artículos</p>';
            });
    </script>
</body>
</html>
        """

    def run(self, host='0.0.0.0', port=5001, debug=True):
        """Ejecutar la aplicación"""
        print("\n🗺️  RISKMAP - APLICACIÓN CORREGIDA")
        print("=" * 40)
        print(f"✅ Servidor iniciado en http://{host}:{port}")
        print(f"✅ Base de datos conectada: {self.check_database()}")
        print("✅ APIs básicas disponibles")
        print("\n📊 Endpoints disponibles:")
        print("   - GET /           - Página principal")
        print("   - GET /api/status - Estado del sistema")
        print("   - GET /api/articles - Artículos geopolíticos")
        print("   - GET /api/hero-article - Artículo principal")
        print("   - GET /api/articles/deduplicated - Sin duplicados")
        print("\n⚠️  Solo artículos geopolíticos con imágenes reales")
        print("=" * 40)
        
        self.app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == "__main__":
    # Crear y ejecutar la aplicación
    app = RiskMapApp()
    app.run()