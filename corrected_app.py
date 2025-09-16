#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versión simplificada de la app para probar el endpoint corregido /api/articles
"""

import sqlite3
import json
import os
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

def get_corrected_articles_from_db(limit=20, exclude_hero_id=None):
    """
    Versión corregida de get_top_articles_from_db que funciona con los datos reales
    """
    try:
        db_path = './data/geopolitical_intel.db'
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return []
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # QUERY CORREGIDA: Usa campos que existen y es permisiva para desarrollo
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
                    WHEN image_url IS NOT NULL AND image_url != '' THEN image_url
                    ELSE 'https://via.placeholder.com/400x200/cccccc/666666?text=Noticia'
                END as image_url,
                ai_importance
            FROM articles 
            WHERE 
                -- Campos básicos requeridos
                title IS NOT NULL AND title != '' AND
                content IS NOT NULL AND content != '' AND
                
                -- Riesgo válido
                risk_score >= 0.0 AND
                
                -- Excluir artículos HERO (solo para mosaic)
                (content NOT LIKE '%HERO ARTICLE%' OR content IS NULL) AND
                (title NOT LIKE '%HERO%' OR title IS NULL)
        """
        
        # Si hay un ID de artículo HERO para excluir
        exclude_filter = ""
        if exclude_hero_id:
            exclude_filter = f" AND id != {exclude_hero_id}"
        
        # Query final
        query = base_query + exclude_filter + """
            ORDER BY 
                CASE WHEN risk_score >= 0.6 THEN 3
                     WHEN risk_score >= 0.4 THEN 2  
                     ELSE 1 END DESC,
                ai_importance DESC,
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
                'summary': row[2] or 'Sin contenido',
                'url': row[3],
                'source': row[4] or 'Fuente desconocida',
                'published_at': row[5],
                'country': row[6] or 'Global',
                'region': row[7] or 'Internacional',
                'risk_level': row[8] or 'unknown',
                'conflict_type': row[9],
                'sentiment_score': row[10] or 0.0,
                'risk_score': row[11] or 0.0,
                'image_url': row[12],  # Incluye placeholder si no hay imagen
                'location': row[6] or row[7] or 'Global',
                'importance_score': row[13] or 0.0  # ai_importance
            }
            articles.append(article)
        
        conn.close()
        print(f"✅ Obtenidos {len(articles)} artículos de la BD")
        return articles
        
    except Exception as e:
        print(f"❌ Error obteniendo artículos: {e}")
        return []

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Endpoint corregido para obtener artículos"""
    try:
        articles = get_corrected_articles_from_db(limit=20)
        print(f"✅ API devolviendo {len(articles)} artículos")
        return jsonify(articles)
    except Exception as e:
        print(f"❌ Error en endpoint: {e}")
        return jsonify([]), 500

@app.route('/api/hero-article', methods=['GET'])
def get_hero_article():
    """Endpoint para artículo hero"""
    try:
        articles = get_corrected_articles_from_db(limit=1)
        if articles:
            print(f"✅ Hero article: {articles[0]['title'][:50]}...")
            return jsonify(articles[0])
        else:
            return jsonify({}), 404
    except Exception as e:
        print(f"❌ Error en hero endpoint: {e}")
        return jsonify({}), 500

@app.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba"""
    return jsonify({
        "status": "ok", 
        "message": "Servidor corregido funcionando",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Iniciando servidor corregido para test de endpoint...")
    print("📍 URL: http://127.0.0.1:5003")
    print("🔗 Endpoints:")
    print("  - /api/articles (mosaico)")
    print("  - /api/hero-article (hero)")
    print("  - /test (prueba)")
    app.run(host='127.0.0.1', port=5003, debug=True)