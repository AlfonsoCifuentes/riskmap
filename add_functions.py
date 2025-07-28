"""
Funciones adicionales para agregar al app_modern.py
"""

# Funciones auxiliares
def get_recent_alerts(cursor):
    """Get recent alerts from database."""
    try:
        cursor.execute("""
            SELECT title, risk_level, country, created_at
            FROM articles 
            WHERE risk_level = 'high'
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'title': row['title'],
                'level': row['risk_level'],
                'location': row['country'] or 'Global',
                'time': row['created_at']
            })
        return alerts
    except Exception as e:
        print(f"Error getting alerts: {e}")
        return []

def get_map_events(cursor):
    """Get events for map visualization."""
    try:
        cursor.execute("""
            SELECT title, location, type, magnitude, published_at
            FROM events 
            WHERE location IS NOT NULL 
            ORDER BY published_at DESC 
            LIMIT 100
        """)
        events = []
        for row in cursor.fetchall():
            try:
                import json
                location = json.loads(row['location']) if row['location'] else None
                if location and len(location) == 2:
                    events.append({
                        'title': row['title'],
                        'lat': float(location[0]),
                        'lng': float(location[1]),
                        'type': row['type'] or 'general',
                        'magnitude': row['magnitude'] or 1,
                        'time': row['published_at']
                    })
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        return events
    except Exception as e:
        print(f"Error getting map events: {e}")
        return []

# Nuevas rutas para cargar datos de la base de datos
ADDITIONAL_ROUTES = '''
@app.route('/api/articles')
def get_articles():
    """Get recent articles from database."""
    try:
        # Trigger ingest if needed
        ensure_ingest()
        
        limit = request.args.get('limit', 20, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, created_at, country, risk_level, source_url
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'title': row['title'],
                'content': row['content'][:200] + '...' if row['content'] else '',
                'created_at': row['created_at'],
                'country': row['country'] or 'Global',
                'risk_level': row['risk_level'] or 'medium',
                'source_url': row['source_url']
            })
        
        conn.close()
        return jsonify(articles)
        
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/events')
def get_events():
    """Get recent events from database."""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, published_at, source, location, type, magnitude
            FROM events 
            ORDER BY published_at DESC 
            LIMIT ?
        """, (limit,))
        
        events = []
        for row in cursor.fetchall():
            # Intentar parsear la ubicación como JSON
            location = None
            if row['location']:
                try:
                    location = json.loads(row['location'])
                except:
                    location = None
            
            events.append({
                'title': row['title'],
                'content': row['content'][:150] + '...' if row['content'] else '',
                'published_at': row['published_at'],
                'source': row['source'],
                'location': location,
                'type': row['type'] or 'general',
                'magnitude': row['magnitude']
            })
        
        conn.close()
        return jsonify(events)
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-analysis')
def get_risk_analysis():
    """Get risk analysis from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Artículo de mayor riesgo
        cursor.execute("""
            SELECT title, content, country, risk_level, created_at
            FROM articles 
            WHERE risk_level = 'high'
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        top_risk_article = cursor.fetchone()
        
        # Distribución por nivel de riesgo
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM articles 
            GROUP BY risk_level
        """)
        
        risk_distribution = {}
        for row in cursor.fetchall():
            risk_distribution[row['risk_level'] or 'unknown'] = row['count']
        
        # Países con más eventos
        cursor.execute("""
            SELECT country, COUNT(*) as count
            FROM articles 
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """)
        
        countries = []
        for row in cursor.fetchall():
            countries.append({
                'country': row['country'],
                'count': row['count'],
                'risk_score': min(row['count'] * 10, 100)  # Calculado basado en cantidad
            })
        
        conn.close()
        
        result = {
            'top_risk_article': {
                'title': top_risk_article['title'] if top_risk_article else 'No hay artículos de alto riesgo',
                'content': top_risk_article['content'][:300] + '...' if top_risk_article and top_risk_article['content'] else '',
                'country': top_risk_article['country'] if top_risk_article else 'Global',
                'risk_level': top_risk_article['risk_level'] if top_risk_article else 'medium',
                'created_at': top_risk_article['created_at'] if top_risk_article else datetime.now().isoformat()
            },
            'risk_distribution': risk_distribution,
            'countries': countries
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting risk analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmap')
def get_heatmap():
    """Get heatmap data from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener eventos con ubicación
        cursor.execute("""
            SELECT location, type, magnitude, title
            FROM events 
            WHERE location IS NOT NULL 
            AND location != ''
            ORDER BY published_at DESC
            LIMIT 1000
        """)
        
        heatmap_data = []
        for row in cursor.fetchall():
            try:
                location = json.loads(row['location'])
                if isinstance(location, list) and len(location) == 2:
                    heatmap_data.append({
                        'lat': float(location[0]),
                        'lng': float(location[1]),
                        'intensity': min(float(row['magnitude'] or 1), 10),
                        'type': row['type'] or 'general',
                        'title': row['title'][:50] + '...'
                    })
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        
        conn.close()
        return jsonify(heatmap_data)
        
    except Exception as e:
        logger.error(f"Error getting heatmap: {e}")
        return jsonify({'error': str(e)}), 500
'''

print("Funciones adicionales preparadas para agregar al app_modern.py")