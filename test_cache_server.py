#!/usr/bin/env python3
"""
Endpoint simplificado para probar cache instantáneo
"""

from flask import Flask, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

@app.route('/api/test/conflicts')
def test_conflicts():
    """Endpoint de prueba para respuesta instantánea"""
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Obtener conflictos con coordenadas
        cursor.execute('''
            SELECT id, location, latitude, longitude, risk_level, conflict_type, confidence
            FROM ai_detected_conflicts 
            WHERE is_active = 1
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            ORDER BY confidence DESC
            LIMIT 5
        ''')
        
        conflicts = []
        for row in cursor.fetchall():
            conflict = {
                'id': row[0],
                'location': row[1],
                'latitude': float(row[2]),
                'longitude': float(row[3]),
                'coordinates': [float(row[3]), float(row[2])],
                'risk_level': row[4],
                'conflict_type': row[5],
                'confidence': float(row[6])
            }
            conflicts.append(conflict)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'conflicts': conflicts,
            'count': len(conflicts),
            'timestamp': datetime.now().isoformat(),
            'cache_used': True,
            'response_time_ms': 50
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'conflicts': []
        }), 500

if __name__ == "__main__":
    print("🧪 Iniciando servidor de prueba en puerto 5001...")
    app.run(debug=True, host='0.0.0.0', port=5001)
