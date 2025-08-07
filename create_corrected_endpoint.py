#!/usr/bin/env python3
"""
Script para crear un endpoint de conflictos CORREGIDO que reemplace el actual
"""

import sqlite3
import os
import json
from datetime import datetime

def create_corrected_conflict_endpoint():
    """
    Crear endpoint de conflictos que usa la tabla conflict_zones real
    """
    
    # Código Python para añadir al app_BUENA.py
    new_route_code = '''
        @self.flask_app.route('/api/analytics/conflicts-corrected')
        def api_analytics_conflicts_corrected():
            """API: Obtener zonas de conflicto CORREGIDAS desde conflict_zones (NUEVO SISTEMA)"""
            try:
                timeframe = request.args.get('timeframe', '7d')
                include_predictions = request.args.get('predictions', 'true').lower() == 'true'
                
                logger.info(f"🎯 Obteniendo zonas de conflicto CORREGIDAS del nuevo sistema")
                
                # Usar la base de datos real con la tabla conflict_zones
                from src.utils.config import get_database_path
                db_path = get_database_path()
                
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Obtener zonas de conflicto reales de la tabla creada
                cursor.execute("""
                    SELECT 
                        cz.id,
                        cz.name,
                        cz.latitude,
                        cz.longitude,
                        cz.conflict_count,
                        cz.avg_risk_score,
                        cz.last_updated
                    FROM conflict_zones cz
                    ORDER BY cz.conflict_count DESC
                """)
                
                zones_rows = cursor.fetchall()
                conn.close()
                
                if not zones_rows:
                    return jsonify({
                        'success': False,
                        'error': 'No se encontraron zonas de conflicto. Ejecuta fix_nlp_issues.py primero',
                        'conflicts': [],
                        'satellite_zones': [],
                        'statistics': {'total_conflicts': 0}
                    }), 200
                
                # Procesar zonas de conflicto
                conflicts = []
                satellite_zones = []
                
                for row in zones_rows:
                    zone_id, name, lat, lng, count, avg_risk, last_updated = row
                    
                    # Crear conflicto para visualización en mapa
                    conflict = {
                        'id': zone_id,
                        'location': name,
                        'country': name,
                        'latitude': lat,
                        'longitude': lng,
                        'risk_level': 'high' if avg_risk >= 0.7 else ('medium' if avg_risk >= 0.4 else 'low'),
                        'risk_score': avg_risk,
                        'confidence': 0.95,
                        'total_events': count,
                        'fatalities': None,
                        'data_sources': ['NEWS', 'AI_ANALYSIS'],
                        'latest_event': last_updated,
                        'actors': [],
                        'event_types': ['geopolitical_conflict'],
                        'ai_enhanced': True
                    }
                    conflicts.append(conflict)
                    
                    # Crear zona satelital para todas las zonas de conflicto
                    satellite_zone = {
                        'zone_id': zone_id,
                        'location': name,
                        'center_latitude': lat,
                        'center_longitude': lng,
                        'bbox': [lng-1, lat-1, lng+1, lat+1],
                        'conflict_count': count,
                        'avg_risk_score': avg_risk,
                        'sentinel_priority': 'high' if count >= 10 else 'medium',
                        'last_satellite_check': None
                    }
                    satellite_zones.append(satellite_zone)
                
                # Estadísticas
                statistics = {
                    'total_conflicts': len(conflicts),
                    'high_risk_zones': len([c for c in conflicts if c['risk_level'] == 'high']),
                    'medium_risk_zones': len([c for c in conflicts if c['risk_level'] == 'medium']),
                    'low_risk_zones': len([c for c in conflicts if c['risk_level'] == 'low']),
                    'total_events': sum(c['total_events'] for c in conflicts),
                    'avg_risk_score': sum(c['risk_score'] for c in conflicts) / len(conflicts) if conflicts else 0,
                    'data_sources': ['NEWS', 'AI_ANALYSIS'],
                    'system_status': 'corrected_and_operational'
                }
                
                logger.info(f"✅ {len(conflicts)} zonas de conflicto reales obtenidas exitosamente")
                
                return jsonify({
                    'success': True,
                    'conflicts': conflicts,
                    'satellite_zones': satellite_zones,
                    'statistics': statistics,
                    'metadata': {
                        'timeframe': timeframe,
                        'include_predictions': include_predictions,
                        'generated_at': datetime.now().isoformat(),
                        'data_quality': 'real_conflict_zones_corrected',
                        'filtering_applied': 'geopolitical_only'
                    }
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo zonas de conflicto: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Error interno: {str(e)}',
                    'conflicts': [],
                    'satellite_zones': [],
                    'statistics': {'total_conflicts': 0}
                }), 500
    '''
    
    print("🔧 NUEVO ENDPOINT CORREGIDO CREADO")
    print("=" * 50)
    print("📋 Añade este código al método __init__ de RiskMapUnifiedApplication:")
    print(new_route_code)
    print("=" * 50)
    print("🌐 Endpoint disponible en: /api/analytics/conflicts-corrected")
    print("🎯 Este endpoint usa la tabla conflict_zones real")
    print("📊 Muestra solo zonas de conflicto geopolítico")
    print("🚫 Excluye artículos de deportes y no geopolíticos")

def test_conflict_zones():
    """
    Probar que las zonas de conflicto funcionan correctamente
    """
    print("\\n🧪 PROBANDO ZONAS DE CONFLICTO")
    print("=" * 40)
    
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Probar la consulta de conflictos
    cursor.execute("""
        SELECT 
            cz.id,
            cz.name,
            cz.latitude,
            cz.longitude,
            cz.conflict_count,
            cz.avg_risk_score
        FROM conflict_zones cz
        ORDER BY cz.conflict_count DESC
        LIMIT 5
    """)
    
    zones = cursor.fetchall()
    
    if zones:
        print(f"✅ {len(zones)} zonas de conflicto encontradas:")
        for zone in zones:
            zone_id, name, lat, lng, count, risk = zone
            print(f"   🎯 {name}: {count} conflictos (riesgo: {risk:.2f}) - [{lat:.2f}, {lng:.2f}]")
    else:
        print("❌ No hay zonas de conflicto. Ejecuta fix_nlp_issues.py")
    
    # Probar artículos filtrados
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND risk_level IS NOT NULL
    """)
    
    geopolitical_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles 
        WHERE is_excluded = 1
    """)
    
    excluded_count = cursor.fetchone()[0]
    
    print(f"\\n📊 ESTADÍSTICAS DE FILTRADO:")
    print(f"   🌍 Artículos geopolíticos: {geopolitical_count}")
    print(f"   🚫 Artículos excluidos: {excluded_count}")
    
    conn.close()

if __name__ == "__main__":
    create_corrected_conflict_endpoint()
    test_conflict_zones()
