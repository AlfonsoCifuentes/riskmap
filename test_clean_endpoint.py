#!/usr/bin/env python3
"""
Ultra Simple Mosaic Endpoint
Crear un endpoint completamente limpio que SOLO devuelva campos necesarios
"""

from flask import Flask, jsonify
import sqlite3
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/articles/mosaic-clean', methods=['GET'])
def get_clean_mosaic():
    """Endpoint ultra-limpio que SOLO devuelve campos permitidos"""
    try:
        # Conectar a la BD
        db_path = "./data/geopolitical_intel.db"
        if not os.path.exists(db_path):
            return jsonify({'success': False, 'error': 'Database not found'}), 404
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query ULTRA-SIMPLE: solo campos necesarios
        query = """
            SELECT id, title, 
                   COALESCE(original_image_url, image_url) as image_url, 
                   COALESCE(risk_level, 'medium') as risk_level,
                   COALESCE(url, '') as original_url
            FROM articles 
            WHERE geopolitical_relevance = 1 
              AND title IS NOT NULL 
              AND title != ''
              AND (original_image_url IS NOT NULL OR image_url IS NOT NULL)
              AND (original_image_url NOT LIKE '%placeholder%' OR image_url NOT LIKE '%placeholder%')
            ORDER BY created_at DESC 
            LIMIT 13
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir a formato JSON - SOLO campos permitidos
        articles = []
        hero = None
        
        for i, row in enumerate(rows):
            article = {
                'id': row[0],
                'title': row[1] or 'Sin título',
                'image_url': row[2] or '',
                'risk_level': row[3] or 'medium',
                'original_url': row[4] or ''
            }
            
            if i == 0:
                hero = article
            else:
                articles.append(article)
        
        return jsonify({
            'success': True,
            'hero': hero,
            'mosaic': articles[:12],  # Limitar a 12 artículos
            'stats': {
                'total_processed': len(rows),
                'duplicates_removed': 0,
                'unique_articles': len(articles)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in clean mosaic endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5002, debug=True)