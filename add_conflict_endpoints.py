#!/usr/bin/env python3
"""
Script para agregar endpoints de análisis de conflictos al dashboard
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def add_conflict_endpoints_to_app():
    """Agregar endpoints de conflictos a app_modern.py"""
    
    app_path = Path(__file__).parent / 'src' / 'dashboard' / 'app_modern.py'
    
    # Código para agregar al final del archivo app_modern.py
    conflict_endpoints = '''

# ==================== CONFLICT ANALYSIS ENDPOINTS ====================

@app.route('/api/conflicts/hotspots')
def get_conflict_hotspots():
    """Get conflict hotspots data"""
    try:
        from conflict_analyzer import ConflictAnalyzer
        
        analyzer = ConflictAnalyzer()
        hotspots = analyzer.get_conflict_hotspots()
        
        # Convert to JSON-serializable format
        hotspots_data = []
        for _, row in hotspots.iterrows():
            hotspots_data.append({
                'country': row['country'],
                'event_count': int(row['event_count']),
                'total_deaths': int(row['total_deaths']),
                'latitude': float(row['avg_lat']) if not pd.isna(row['avg_lat']) else 0,
                'longitude': float(row['avg_lng']) if not pd.isna(row['avg_lng']) else 0,
                'intensity_index': float(row['intensity_index'])
            })
        
        return jsonify({
            'success': True,
            'data': hotspots_data,
            'total': len(hotspots_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting conflict hotspots: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conflicts/timeline')
def get_conflict_timeline():
    """Get conflict timeline data"""
    try:
        from conflict_analyzer import ConflictAnalyzer
        
        country = request.args.get('country')
        analyzer = ConflictAnalyzer()
        timeline = analyzer.get_conflict_timeline(country)
        
        timeline_data = []
        for _, row in timeline.iterrows():
            timeline_data.append({
                'year': int(row['year']),
                'events': int(row['events']),
                'total_deaths': int(row['total_deaths']),
                'civilian_deaths': int(row['civilian_deaths'])
            })
        
        return jsonify({
            'success': True,
            'data': timeline_data,
            'country': country or 'Global'
        })
        
    except Exception as e:
        logger.error(f"Error getting conflict timeline: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conflicts/actors')
def get_conflict_actors():
    """Get conflict actors analysis"""
    try:
        from conflict_analyzer import ConflictAnalyzer
        
        analyzer = ConflictAnalyzer()
        actors = analyzer.get_actor_analysis()
        
        actors_data = []
        for _, row in actors.iterrows():
            actors_data.append({
                'actor': row['actor'],
                'events': int(row['events']),
                'deaths': int(row['deaths']),
                'type': row['type']
            })
        
        return jsonify({
            'success': True,
            'data': actors_data
        })
        
    except Exception as e:
        logger.error(f"Error getting conflict actors: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conflicts/risk-assessment/<country>')
def get_country_risk_assessment(country):
    """Get risk assessment for specific country"""
    try:
        from conflict_analyzer import ConflictAnalyzer
        
        analyzer = ConflictAnalyzer()
        assessment = analyzer.generate_risk_assessment(country)
        
        return jsonify({
            'success': True,
            'data': assessment
        })
        
    except Exception as e:
        logger.error(f"Error getting risk assessment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conflicts/political-terror')
def get_political_terror_trends():
    """Get political terror scale trends"""
    try:
        from conflict_analyzer import ConflictAnalyzer
        
        analyzer = ConflictAnalyzer()
        trends = analyzer.get_political_terror_trends()
        
        # Convert DataFrames to JSON-serializable format
        result = {}
        
        if 'yearly_trends' in trends:
            yearly_data = []
            for _, row in trends['yearly_trends'].iterrows():
                yearly_data.append({
                    'year': int(row['Year']),
                    'pts_amnesty': float(row['PTS_A']),
                    'pts_hrw': float(row['PTS_H']),
                    'pts_state': float(row['PTS_S'])
                })
            result['yearly_trends'] = yearly_data
        
        if 'recent_by_country' in trends:
            country_data = []
            for _, row in trends['recent_by_country'].iterrows():
                country_data.append({
                    'country': row['Country'],
                    'pts_amnesty': float(row['PTS_A']),
                    'pts_hrw': float(row['PTS_H']),
                    'pts_state': float(row['PTS_S'])
                })
            result['recent_by_country'] = country_data[:20]  # Top 20
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error getting political terror trends: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conflicts/dashboard-data')
def get_conflicts_dashboard_data():
    """Get comprehensive conflict data for dashboard"""
    try:
        from conflict_analyzer import ConflictAnalyzer
        
        analyzer = ConflictAnalyzer()
        
        # Get all data
        hotspots = analyzer.get_conflict_hotspots()
        timeline = analyzer.get_conflict_timeline()
        actors = analyzer.get_actor_analysis()
        
        # Prepare summary statistics
        total_events = timeline['events'].sum() if not timeline.empty else 0
        total_deaths = timeline['total_deaths'].sum() if not timeline.empty else 0
        active_countries = len(hotspots) if not hotspots.empty else 0
        
        # Recent trend (last 2 years vs previous 2 years)
        recent_events = timeline[timeline['year'] >= 2022]['events'].sum() if not timeline.empty else 0
        previous_events = timeline[(timeline['year'] >= 2020) & (timeline['year'] < 2022)]['events'].sum() if not timeline.empty else 0
        
        trend = 'stable'
        if recent_events > previous_events * 1.1:
            trend = 'increasing'
        elif recent_events < previous_events * 0.9:
            trend = 'decreasing'
        
        return jsonify({
            'success': True,
            'summary': {
                'total_events': int(total_events),
                'total_deaths': int(total_deaths),
                'active_countries': int(active_countries),
                'trend': trend,
                'recent_events': int(recent_events)
            },
            'hotspots': hotspots.head(10).to_dict('records') if not hotspots.empty else [],
            'timeline': timeline.tail(10).to_dict('records') if not timeline.empty else [],
            'top_actors': actors.head(5).to_dict('records') if not actors.empty else []
        })
        
    except Exception as e:
        logger.error(f"Error getting conflicts dashboard data: {e}")
        return jsonify({'error': str(e)}), 500
'''
    
    # Leer el archivo actual
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Agregar los endpoints antes del if __name__ == '__main__':
    if "# ==================== CONFLICT ANALYSIS ENDPOINTS ====================" not in content:
        # Encontrar la línea if __name__ == '__main__':
        lines = content.split('\n')
        insert_index = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith("if __name__ == '__main__':"):
                insert_index = i
                break
        
        if insert_index > 0:
            # Insertar los endpoints antes del main
            lines.insert(insert_index, conflict_endpoints)
            
            # Escribir el archivo actualizado
            with open(app_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print("✅ Endpoints de conflictos agregados a app_modern.py")
        else:
            print("❌ No se pudo encontrar la línea if __name__ == '__main__':")
    else:
        print("ℹ️  Los endpoints de conflictos ya están presentes en app_modern.py")

if __name__ == "__main__":
    add_conflict_endpoints_to_app()