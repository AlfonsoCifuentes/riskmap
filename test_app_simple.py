#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App básica para probar solo el endpoint /api/articles sin dependencias complejas
"""

import sqlite3
import json
from flask import Flask, jsonify

app = Flask(__name__)

def get_articles_from_db():
    """Obtener artículos directamente de la base de datos"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Query más simple y permisiva
        query = """
        SELECT 
            id, title, summary, url, image_url, 
            risk_score, language, source, 
            published_date, importance_score
        FROM articles 
        WHERE title IS NOT NULL 
        AND title != '' 
        AND summary IS NOT NULL 
        AND summary != ''
        AND image_url IS NOT NULL 
        AND image_url != ''
        AND risk_score >= 0.0
        ORDER BY 
            CASE WHEN risk_score >= 0.6 THEN 3
                 WHEN risk_score >= 0.4 THEN 2  
                 ELSE 1 END DESC,
            importance_score DESC,
            published_date DESC
        LIMIT 20
        """
        
        cursor.execute(query)
        articles = cursor.fetchall()
        
        # Convertir a formato JSON
        results = []
        for article in articles:
            results.append({
                'id': article[0],
                'title': article[1],
                'summary': article[2],
                'url': article[3],
                'image_url': article[4],
                'risk_score': float(article[5]) if article[5] else 0.0,
                'language': article[6],
                'source': article[7],
                'published_date': article[8],
                'importance_score': float(article[9]) if article[9] else 0.0
            })
        
        conn.close()
        return results
        
    except Exception as e:
        print(f"❌ Error en get_articles_from_db: {e}")
        return []

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Endpoint para obtener artículos"""
    try:
        articles = get_articles_from_db()
        print(f"✅ Devolviendo {len(articles)} artículos")
        return jsonify(articles)
    except Exception as e:
        print(f"❌ Error en endpoint: {e}")
        return jsonify([]), 500

@app.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba"""
    return jsonify({"status": "ok", "message": "Servidor funcionando"})

if __name__ == '__main__':
    print("🚀 Iniciando servidor básico para test de endpoint...")
    app.run(host='127.0.0.1', port=5002, debug=True)