#!/usr/bin/env python3
"""
Servidor simplificado para probar el endpoint deduplicado
"""
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)

@app.route('/api/articles/deduplicated', methods=['GET'])
def api_deduplicated_articles():
    """API: Obtener artículos deduplicados - VERSIÓN SIMPLIFICADA SIN PROCESAMIENTO PESADO"""
    try:
        logger.info("📡 Endpoint /api/articles/deduplicated llamado")

        # Respuesta hardcoded simple para evitar problemas de procesamiento
        response_data = {
            'success': True,
            'hero': {
                'id': 1,
                'title': 'Noticia geopolítica principal',
                'image_url': 'https://via.placeholder.com/400x300?text=Hero+Image',
                'risk_level': 'high',
                'original_url': 'https://example.com/article1'
            },
            'mosaic': [
                {
                    'id': 2,
                    'title': 'Desarrollo en Oriente Medio',
                    'image_url': 'https://via.placeholder.com/300x200?text=News+1',
                    'risk_level': 'medium',
                    'original_url': 'https://example.com/article2'
                },
                {
                    'id': 3,
                    'title': 'Análisis de política internacional',
                    'image_url': 'https://via.placeholder.com/300x200?text=News+2',
                    'risk_level': 'low',
                    'original_url': 'https://example.com/article3'
                },
                {
                    'id': 4,
                    'title': 'Conflicto en Europa del Este',
                    'image_url': 'https://via.placeholder.com/300x200?text=News+3',
                    'risk_level': 'high',
                    'original_url': 'https://example.com/article4'
                }
            ],
            'stats': {
                'total_processed': 4,
                'duplicates_removed': 0,
                'unique_articles': 4
            },
            'timestamp': datetime.now().isoformat(),
            '_version': 'simplified'
        }

        logger.info("✅ Respuesta del endpoint generada correctamente")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"❌ Error en endpoint deduplicado: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mosaic': [],
            'hero': None
        }), 500

@app.route('/')
def index():
    return "<h1>Servidor Simplificado RiskMap</h1><p>Endpoint disponible: <a href='/api/articles/deduplicated'>/api/articles/deduplicated</a></p>"

if __name__ == '__main__':
    print("🚀 Iniciando servidor simplificado en http://localhost:5001")
    app.run(host='127.0.0.1', port=5001, debug=True)