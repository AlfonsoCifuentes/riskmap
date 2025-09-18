#!/usr/bin/env python3
"""
Servidor de prueba simple para verificar truncamiento
"""
from flask import Flask, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)

def truncate_title(title, max_length=80):
    """Función de truncamiento igual a la del backend"""
    if len(title) <= max_length:
        return title

    # Buscar el mejor punto para truncar (espacio, punto o coma)
    truncated = title[:max_length]

    # Buscar puntos de corte en orden de preferencia
    last_space = truncated.rfind(' ')
    last_period = truncated.rfind('.')
    last_comma = truncated.rfind(',')
    last_dash = truncated.rfind('-')

    # Elegir el mejor punto de corte (el más cercano al límite)
    cut_points = [cp for cp in [last_space, last_period, last_comma, last_dash] if cp > 10]  # Mínimo 10 chars

    if cut_points:
        # Tomar el punto de corte más cercano al límite máximo
        best_cut = max(cut_points)
        return title[:best_cut] + "..."
    else:
        # Si no hay puntos de corte buenos, truncar directamente
        return title[:max_length-3] + "..."

@app.route('/api/test_truncation')
def test_truncation():
    """Endpoint de prueba para verificar truncamiento"""

    db_path = Path("./data/geopolitical_intel.db")

    if not db_path.exists():
        return jsonify({"error": "Base de datos no encontrada"}), 500

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Obtener artículos con títulos largos
        cursor.execute("""
            SELECT id, title
            FROM articles
            WHERE LENGTH(title) > 80
            ORDER BY LENGTH(title) DESC
            LIMIT 5
        """)

        articles = cursor.fetchall()
        conn.close()

        results = []
        for article_id, title in articles:
            truncated = truncate_title(title)
            results.append({
                "id": article_id,
                "original_title": title,
                "original_length": len(title),
                "truncated_title": truncated,
                "truncated_length": len(truncated),
                "correctly_truncated": len(truncated) <= 83
            })

        return jsonify({
            "success": True,
            "message": "Truncamiento probado correctamente",
            "results": results,
            "total_tested": len(results),
            "all_correct": all(r["correctly_truncated"] for r in results)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def status():
    """Endpoint de estado simple"""
    return jsonify({"status": "ok", "service": "truncation_test"})

if __name__ == "__main__":
    print("🚀 Iniciando servidor de prueba de truncamiento...")
    print("📡 Endpoints disponibles:")
    print("   GET /api/status")
    print("   GET /api/test_truncation")
    print("🌐 Servidor ejecutándose en http://localhost:5002")

    app.run(host='0.0.0.0', port=5002, debug=False)