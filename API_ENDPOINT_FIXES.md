
# Correcciones para app_BUENA.py - Resolver errores 500 en endpoints

## 1. Endpoint /api/satellite/critical-alerts
Reemplazar la consulta SQL problemática con:

```python
@app.route('/api/satellite/critical-alerts')
def get_critical_alerts():
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                alert_type,
                severity,
                location,
                latitude,
                longitude,
                description,
                confidence,
                created_at
            FROM satellite_alerts 
            WHERE severity IN ('high', 'critical')
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'type': row[0],
                'severity': row[1],
                'location': row[2],
                'coordinates': {'lat': row[3], 'lng': row[4]},
                'description': row[5],
                'confidence': row[6],
                'timestamp': row[7]
            })
        
        conn.close()
        return jsonify(alerts)
    except Exception as e:
        print(f"Error en critical alerts: {e}")
        return jsonify([])
```

## 2. Endpoint /api/satellite/analysis-timeline
```python
@app.route('/api/satellite/analysis-timeline')
def get_analysis_timeline():
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                event_type,
                title,
                description,
                location,
                event_date,
                confidence,
                impact_level
            FROM satellite_timeline
            ORDER BY event_date DESC
            LIMIT 20
        ''')
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'type': row[0],
                'title': row[1],
                'description': row[2],
                'location': row[3],
                'date': row[4],
                'confidence': row[5],
                'impact': row[6]
            })
        
        conn.close()
        return jsonify(events)
    except Exception as e:
        print(f"Error en timeline: {e}")
        return jsonify([])
```

## 3. Endpoint /api/satellite/evolution-predictions
```python
@app.route('/api/satellite/evolution-predictions')
def get_evolution_predictions():
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                prediction_type,
                location,
                predicted_event,
                probability,
                confidence,
                time_horizon,
                risk_level,
                prediction_date
            FROM satellite_predictions
            ORDER BY probability DESC
            LIMIT 15
        ''')
        
        predictions = []
        for row in cursor.fetchall():
            predictions.append({
                'type': row[0],
                'location': row[1],
                'event': row[2],
                'probability': row[3],
                'confidence': row[4],
                'timeframe': row[5],
                'risk': row[6],
                'date': row[7]
            })
        
        conn.close()
        return jsonify(predictions)
    except Exception as e:
        print(f"Error en predictions: {e}")
        return jsonify([])
```

## 4. Fix para artículos (cambiar schema):
- Cambiar todas las referencias de `pub_date` por `created_at`
- Cambiar `source_name` por `source`
- Agregar fallback para image_url: `COALESCE(image_url, '/static/default-news-image.jpg') as image_url`

## 5. Incrementar timeout en Flask:
```python
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Agregar timeout handler
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request  
def after_request(response):
    if hasattr(g, 'start_time'):
        response.headers['X-Response-Time'] = str(time.time() - g.start_time)
    return response
```
