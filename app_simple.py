"""
RiskMap - Aplicación Web Moderna Simplificada
Dashboard moderno con mosaico de noticias
"""

import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Flask and web framework imports
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='src/dashboard/templates',
            static_folder='src/dashboard/static')
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
CORS(app)

# Global variables
orchestrator = None
articles_cache = []

def load_sample_articles():
    """Load sample articles for testing"""
    return [
        {
            "id": 1,
            "title": "Crisis diplomática se intensifica en Europa Oriental",
            "description": "Las tensiones entre países vecinos alcanzan un punto crítico tras nuevas disputas territoriales.",
            "location": "Ucrania",
            "country": "Ucrania",
            "risk_level": "high",
            "published_date": datetime.now().isoformat(),
            "source_url": "https://example.com/news1",
            "image_url": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop"
        },
        {
            "id": 2,
            "title": "Negociaciones comerciales entre potencias mundiales",
            "description": "Se inician conversaciones sobre nuevos acuerdos comerciales que podrían remodelar la economía global.",
            "location": "Estados Unidos",
            "country": "Estados Unidos",
            "risk_level": "medium",
            "published_date": (datetime.now() - timedelta(hours=2)).isoformat(),
            "source_url": "https://example.com/news2",
            "image_url": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=800&h=600&fit=crop"
        },
        {
            "id": 3,
            "title": "Tensiones geopolíticas en el Mar del Sur de China",
            "description": "Nuevos incidentes navales elevan la preocupación por la estabilidad regional.",
            "location": "China",
            "country": "China",
            "risk_level": "high",
            "published_date": (datetime.now() - timedelta(hours=1)).isoformat(),
            "source_url": "https://example.com/news3",
            "image_url": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=800&h=600&fit=crop"
        },
        {
            "id": 4,
            "title": "Cumbre de líderes regionales aborda seguridad",
            "description": "Representantes de múltiples naciones se reúnen para discutir estrategias de seguridad regional.",
            "location": "Medio Oriente",
            "country": "Emiratos Árabes Unidos",
            "risk_level": "medium",
            "published_date": (datetime.now() - timedelta(hours=3)).isoformat(),
            "source_url": "https://example.com/news4",
            "image_url": "https://images.unsplash.com/photo-1541336032412-2048a678540d?w=800&h=600&fit=crop"
        },
        {
            "id": 5,
            "title": "Ejercicios militares conjuntos preocupan a vecinos",
            "description": "Maniobras militares a gran escala generan tensión en la región.",
            "location": "Corea del Norte",
            "country": "Corea del Norte",
            "risk_level": "high",
            "published_date": (datetime.now() - timedelta(hours=4)).isoformat(),
            "source_url": "https://example.com/news5",
            "image_url": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=800&h=600&fit=crop"
        },
        {
            "id": 6,
            "title": "Acuerdo energético estratégico entre naciones",
            "description": "Nuevo tratado de cooperación energética promete estabilizar el mercado regional.",
            "location": "Rusia",
            "country": "Rusia",
            "risk_level": "low",
            "published_date": (datetime.now() - timedelta(hours=6)).isoformat(),
            "source_url": "https://example.com/news6",
            "image_url": "https://images.unsplash.com/photo-1473649085228-583485e6e4d7?w=800&h=600&fit=crop"
        },
        {
            "id": 7,
            "title": "Migración masiva causa tensiones fronterizas",
            "description": "El flujo migratorio sin precedentes pone a prueba las políticas fronterizas europeas.",
            "location": "Europa",
            "country": "Polonia",
            "risk_level": "medium",
            "published_date": (datetime.now() - timedelta(hours=8)).isoformat(),
            "source_url": "https://example.com/news7",
            "image_url": "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=800&h=600&fit=crop"
        },
        {
            "id": 8,
            "title": "Disputa territorial escalada en zona fronteriza",
            "description": "Las tensiones fronterizas alcanzanun nuevo nivel tras incidentes recientes.",
            "location": "India",
            "country": "India",
            "risk_level": "high",
            "published_date": (datetime.now() - timedelta(hours=5)).isoformat(),
            "source_url": "https://example.com/news8",
            "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop"
        },
        {
            "id": 9,
            "title": "Reunión de emergencia en consejo de seguridad",
            "description": "El Consejo de Seguridad convoca una sesión urgente para abordar la crisis actual.",
            "location": "Nueva York",
            "country": "Estados Unidos",
            "risk_level": "medium",
            "published_date": (datetime.now() - timedelta(hours=7)).isoformat(),
            "source_url": "https://example.com/news9",
            "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=600&fit=crop"
        },
        {
            "id": 10,
            "title": "Operaciones de paz se intensifican en región",
            "description": "Las fuerzas de paz aumentan su presencia para mantener la estabilidad regional.",
            "location": "África",
            "country": "Sudáfrica",
            "risk_level": "low",
            "published_date": (datetime.now() - timedelta(hours=9)).isoformat(),
            "source_url": "https://example.com/news10",
            "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"
        }
    ]

@app.route('/')
def home():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    return render_template('modern_dashboard_updated.html')

@app.route('/api/articles')
def get_articles():
    """Get articles for the dashboard"""
    global articles_cache
    
    try:
        limit = request.args.get('limit', 15, type=int)
        
        # Use sample articles for now
        if not articles_cache:
            articles_cache = load_sample_articles()
            
        # Return limited articles
        limited_articles = articles_cache[:limit]
        
        logger.info(f"Returning {len(limited_articles)} articles")
        return jsonify({
            "articles": limited_articles,
            "total": len(articles_cache),
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        return jsonify({
            "error": str(e),
            "articles": [],
            "total": 0,
            "status": "error"
        }), 500

@app.route('/api/calculate-importance', methods=['POST'])
def calculate_importance():
    """Calculate article importance using simple heuristics"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Simple importance calculation
        score = 50  # Base score
        
        # Risk level weight (40% of importance)
        risk_weights = {
            'high': 40,
            'medium': 24,
            'low': 12
        }
        score += risk_weights.get(data.get('risk_level', 'low'), 20)
        
        # Recency weight (30% of importance)
        try:
            pub_date = datetime.fromisoformat(data.get('published_date', datetime.now().isoformat()))
            now = datetime.now()
            hours_old = (now - pub_date).total_seconds() / 3600
            recency_score = max(0, 30 - (hours_old / 24) * 5)  # Decreases over days
            score += recency_score
        except:
            score += 15  # Default recency
            
        # Content keywords weight (20% of importance)
        high_impact_keywords = [
            'guerra', 'conflicto', 'crisis', 'emergencia', 'ataque', 'bomba',
            'muerte', 'muertos', 'víctimas', 'evacuación', 'desastre',
            'terremoto', 'tsunami', 'huracán', 'incendio', 'explosión',
            'militar', 'ejército', 'terrorismo', 'tensión', 'disputa'
        ]
        
        title = (data.get('title', '') + ' ' + data.get('content', '')).lower()
        keyword_matches = sum(1 for keyword in high_impact_keywords if keyword in title)
        score += min(keyword_matches * 3, 20)
        
        # Location importance (10% of importance)
        high_risk_locations = [
            'ucrania', 'gaza', 'israel', 'siria', 'afganistán', 'yemen',
            'somalia', 'sudán', 'myanmar', 'venezuela', 'corea', 'china',
            'rusia', 'irán'
        ]
        location = (data.get('location', '') + ' ' + data.get('country', '')).lower()
        is_high_risk_location = any(loc in location for loc in high_risk_locations)
        score += 10 if is_high_risk_location else 5
        
        # Normalize to 0-100
        final_score = min(max(score, 0), 100)
        
        logger.info(f"Calculated importance score: {final_score} for article: {data.get('title', 'Unknown')[:50]}")
        
        return jsonify({
            "importance_score": final_score,
            "calculation_method": "heuristic",
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error calculating importance: {e}")
        return jsonify({
            "error": str(e),
            "importance_score": 50,  # Fallback score
            "calculation_method": "fallback",
            "status": "error"
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    global articles_cache
    
    try:
        if not articles_cache:
            articles_cache = load_sample_articles()
            
        high_risk_count = len([a for a in articles_cache if a.get('risk_level') == 'high'])
        medium_risk_count = len([a for a in articles_cache if a.get('risk_level') == 'medium'])
        
        return jsonify({
            "total_articles": len(articles_cache),
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "active_alerts": 3,  # Simulated
            "last_update": datetime.now().strftime("%H:%M"),
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO RISKMAP - DASHBOARD MODERNO")
    logger.info("=" * 80)
    
    try:
        # Load sample data
        articles_cache = load_sample_articles()
        logger.info(f"✅ Loaded {len(articles_cache)} sample articles")
        
        # Start Flask app
        logger.info("🌐 Iniciando servidor web...")
        logger.info("📊 Dashboard disponible en: http://localhost:5000/dashboard")
        logger.info("🔗 API endpoints disponibles en: http://localhost:5000/api/")
        
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo aplicación...")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)
