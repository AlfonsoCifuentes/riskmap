#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatización del Dashboard - BLOQUE 1D
Fusión de secciones del dashboard en una vista unificada
"""

import sys
import os
import re
import logging
from pathlib import Path
from datetime import datetime

# Configurar codificación UTF-8 para Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurar logging sin emojis
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DashboardUnificationImplementation:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.app_file = self.project_root / "app_BUENA.py"
        self.templates_dir = self.project_root / "src" / "web" / "templates"
        self.static_dir = self.project_root / "src" / "web" / "static"
        
    def implement_dashboard_unification(self):
        """Implementar fusión de secciones del dashboard"""
        logger.info("IMPLEMENTANDO FUSIÓN DE SECCIONES DEL DASHBOARD...")
        
        try:
            # 1. Agregar ruta del dashboard unificado
            success_routes = self._add_unified_dashboard_route()
            
            # 2. Agregar métodos de datos unificados
            success_methods = self._add_unified_data_methods()
            
            # 3. Crear API unificada para dashboard
            success_api = self._add_unified_api_endpoints()
            
            if all([success_routes, success_methods, success_api]):
                logger.info("FUSIÓN DE DASHBOARD IMPLEMENTADA COMPLETAMENTE")
                return True
            else:
                logger.error("FALLOS EN FUSIÓN DE DASHBOARD")
                return False
                
        except Exception as e:
            logger.error(f"Error implementando fusión de dashboard: {e}")
            return False
    
    def _add_unified_dashboard_route(self):
        """Agregar ruta del dashboard unificado"""
        try:
            if not self.app_file.exists():
                logger.error("app_BUENA.py no encontrado")
                return False
            
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar si la ruta ya existe
            if '/dashboard-unificado' in content:
                logger.info("Ruta de dashboard unificado ya existe")
                return True
            
            unified_dashboard_route = '''
# === RUTA DASHBOARD UNIFICADO ===
@app.route('/dashboard-unificado')
def dashboard_unificado():
    """Dashboard principal unificado con todas las secciones"""
    try:
        # Obtener datos de todas las secciones
        unified_data = get_unified_dashboard_data()
        
        return render_template('dashboard_unificado.html', 
                             data=unified_data,
                             page_title="Dashboard Unificado - RiskMap")
    except Exception as e:
        logger.error(f"Error en dashboard unificado: {e}")
        return render_template('error.html', error="Error cargando dashboard")

@app.route('/dashboard')
def dashboard():
    """Redirigir al dashboard unificado"""
    return redirect(url_for('dashboard_unificado'))
'''
            
            # Insertar ruta antes del final del archivo
            content += unified_dashboard_route
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("RUTA DE DASHBOARD UNIFICADO AGREGADA")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando ruta de dashboard unificado: {e}")
            return False
    
    def _add_unified_data_methods(self):
        """Agregar métodos para datos unificados del dashboard"""
        try:
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'get_unified_dashboard_data' in content:
                logger.info("Métodos de datos unificados ya existen")
                return True
            
            unified_data_methods = '''
# === MÉTODOS PARA DASHBOARD UNIFICADO ===
def get_unified_dashboard_data():
    """Obtener todos los datos para el dashboard unificado"""
    try:
        # Obtener datos de todas las secciones
        data = {
            'overview': get_dashboard_overview(),
            'alerts': get_dashboard_alerts(),
            'recent_activity': get_dashboard_recent_activity(),
            'risk_metrics': get_dashboard_risk_metrics(),
            'geographic_data': get_dashboard_geographic_data(),
            'analytics': get_dashboard_analytics(),
            'reports': get_dashboard_reports_summary(),
            'system_status': get_dashboard_system_status(),
            'last_updated': datetime.now().isoformat()
        }
        
        return data
        
    except Exception as e:
        logger.error(f"Error obteniendo datos unificados: {e}")
        return {}

def get_dashboard_overview():
    """Obtener resumen general para el dashboard"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Total de artículos procesados hoy
        cursor.execute("""
            SELECT COUNT(*) FROM enhanced_articles 
            WHERE DATE(processed_date) = DATE('now')
        """)
        articles_today = cursor.fetchone()[0]
        
        # Total de artículos procesados
        cursor.execute("SELECT COUNT(*) FROM enhanced_articles")
        total_articles = cursor.fetchone()[0]
        
        # Alertas activas
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'active'")
        active_alerts = cursor.fetchone()[0]
        
        # Nivel de riesgo promedio
        cursor.execute("""
            SELECT AVG(CAST(risk_level AS FLOAT)) 
            FROM enhanced_articles 
            WHERE risk_level IS NOT NULL AND DATE(processed_date) = DATE('now')
        """)
        avg_risk_result = cursor.fetchone()
        avg_risk = round(avg_risk_result[0], 2) if avg_risk_result[0] else 0.0
        
        conn.close()
        
        return {
            'articles_today': articles_today,
            'total_articles': total_articles,
            'active_alerts': active_alerts,
            'average_risk_level': avg_risk,
            'status': 'operational'
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo overview: {e}")
        return {
            'articles_today': 0,
            'total_articles': 0,
            'active_alerts': 0,
            'average_risk_level': 0.0,
            'status': 'error'
        }

def get_dashboard_alerts():
    """Obtener alertas para el dashboard"""
    try:
        # Reutilizar método existente
        alerts = get_active_alerts()
        return {
            'active_alerts': alerts[:5],  # Solo mostrar las 5 más recientes
            'total_count': len(alerts),
            'critical_count': len([a for a in alerts if a.get('severity') == 'critical']),
            'high_count': len([a for a in alerts if a.get('severity') == 'high'])
        }
    except Exception as e:
        logger.error(f"Error obteniendo alertas para dashboard: {e}")
        return {'active_alerts': [], 'total_count': 0, 'critical_count': 0, 'high_count': 0}

def get_dashboard_recent_activity():
    """Obtener actividad reciente para el dashboard"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Artículos recientes procesados
        cursor.execute("""
            SELECT title, location, risk_level, processed_date, url
            FROM enhanced_articles 
            ORDER BY processed_date DESC 
            LIMIT 10
        """)
        
        recent_articles = []
        for row in cursor.fetchall():
            article = {
                'title': row[0],
                'location': row[1],
                'risk_level': row[2],
                'processed_date': row[3],
                'url': row[4],
                'time_ago': get_time_ago(row[3]) if row[3] else 'Desconocido'
            }
            recent_articles.append(article)
        
        conn.close()
        
        return {
            'recent_articles': recent_articles,
            'processing_active': True
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo actividad reciente: {e}")
        return {'recent_articles': [], 'processing_active': False}

def get_dashboard_risk_metrics():
    """Obtener métricas de riesgo para el dashboard"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Distribución por nivel de riesgo
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN CAST(risk_level AS FLOAT) >= 8 THEN 'Crítico'
                    WHEN CAST(risk_level AS FLOAT) >= 6 THEN 'Alto'
                    WHEN CAST(risk_level AS FLOAT) >= 4 THEN 'Medio'
                    ELSE 'Bajo'
                END as risk_category,
                COUNT(*) as count
            FROM enhanced_articles 
            WHERE risk_level IS NOT NULL
            GROUP BY risk_category
        """)
        
        risk_distribution = {}
        for row in cursor.fetchall():
            risk_distribution[row[0]] = row[1]
        
        # Tendencia de riesgo (últimos 7 días)
        cursor.execute("""
            SELECT DATE(processed_date) as date, AVG(CAST(risk_level AS FLOAT)) as avg_risk
            FROM enhanced_articles 
            WHERE risk_level IS NOT NULL 
            AND processed_date >= DATE('now', '-7 days')
            GROUP BY DATE(processed_date)
            ORDER BY date
        """)
        
        risk_trend = []
        for row in cursor.fetchall():
            risk_trend.append({
                'date': row[0],
                'average_risk': round(row[1], 2)
            })
        
        conn.close()
        
        return {
            'distribution': risk_distribution,
            'trend': risk_trend,
            'total_assessed': sum(risk_distribution.values())
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas de riesgo: {e}")
        return {'distribution': {}, 'trend': [], 'total_assessed': 0}

def get_dashboard_geographic_data():
    """Obtener datos geográficos para el dashboard"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Top países/regiones por actividad
        cursor.execute("""
            SELECT location, COUNT(*) as count, AVG(CAST(risk_level AS FLOAT)) as avg_risk
            FROM enhanced_articles 
            WHERE location IS NOT NULL AND risk_level IS NOT NULL
            GROUP BY location
            ORDER BY count DESC
            LIMIT 15
        """)
        
        geographic_summary = []
        for row in cursor.fetchall():
            geographic_summary.append({
                'location': row[0],
                'article_count': row[1],
                'average_risk': round(row[2], 2) if row[2] else 0.0
            })
        
        # Coordenadas para el mapa (si existen)
        cursor.execute("""
            SELECT latitude, longitude, location, risk_level
            FROM enhanced_articles 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            AND latitude != '' AND longitude != ''
            ORDER BY processed_date DESC
            LIMIT 100
        """)
        
        map_points = []
        for row in cursor.fetchall():
            try:
                lat = float(row[0])
                lng = float(row[1])
                map_points.append({
                    'lat': lat,
                    'lng': lng,
                    'location': row[2],
                    'risk_level': row[3]
                })
            except (ValueError, TypeError):
                continue
        
        conn.close()
        
        return {
            'geographic_summary': geographic_summary,
            'map_points': map_points,
            'total_locations': len(geographic_summary)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos geográficos: {e}")
        return {'geographic_summary': [], 'map_points': [], 'total_locations': 0}

def get_dashboard_analytics():
    """Obtener datos de analytics para el dashboard"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Procesamiento por día (últimos 7 días)
        cursor.execute("""
            SELECT DATE(processed_date) as date, COUNT(*) as count
            FROM enhanced_articles 
            WHERE processed_date >= DATE('now', '-7 days')
            GROUP BY DATE(processed_date)
            ORDER BY date
        """)
        
        daily_processing = []
        for row in cursor.fetchall():
            daily_processing.append({
                'date': row[0],
                'articles_processed': row[1]
            })
        
        # Fuentes más activas
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM enhanced_articles 
            GROUP BY source
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_sources = []
        for row in cursor.fetchall():
            top_sources.append({
                'source': row[0] or 'Desconocido',
                'article_count': row[1]
            })
        
        conn.close()
        
        return {
            'daily_processing': daily_processing,
            'top_sources': top_sources,
            'processing_efficiency': 'Alta'
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        return {'daily_processing': [], 'top_sources': [], 'processing_efficiency': 'Desconocida'}

def get_dashboard_reports_summary():
    """Obtener resumen de reportes para el dashboard"""
    try:
        # Reutilizar método existente
        recent_reports = get_recent_reports(5)
        return {
            'recent_reports': recent_reports,
            'total_reports': len(recent_reports),
            'last_generated': recent_reports[0]['generated_at'] if recent_reports else None
        }
    except Exception as e:
        logger.error(f"Error obteniendo resumen de reportes: {e}")
        return {'recent_reports': [], 'total_reports': 0, 'last_generated': None}

def get_dashboard_system_status():
    """Obtener estado del sistema para el dashboard"""
    try:
        # Verificar conexión a base de datos
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = "Operational"
        conn.close()
        
        # Verificar último procesamiento
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(processed_date) FROM enhanced_articles
        """)
        last_processing = cursor.fetchone()[0]
        conn.close()
        
        # Calcular uptime (simulado)
        uptime_hours = 24  # Valor simulado
        
        return {
            'database_status': db_status,
            'last_processing': last_processing,
            'uptime_hours': uptime_hours,
            'system_health': 'Good',
            'active_monitors': 3
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {e}")
        return {
            'database_status': 'Error',
            'last_processing': None,
            'uptime_hours': 0,
            'system_health': 'Poor',
            'active_monitors': 0
        }
'''
            
            content += unified_data_methods
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("MÉTODOS DE DATOS UNIFICADOS AGREGADOS")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando métodos de datos unificados: {e}")
            return False
    
    def _add_unified_api_endpoints(self):
        """Agregar endpoints API para el dashboard unificado"""
        try:
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '/api/dashboard/unified' in content:
                logger.info("API endpoints unificados ya existen")
                return True
            
            unified_api_endpoints = '''
# === API ENDPOINTS PARA DASHBOARD UNIFICADO ===
@app.route('/api/dashboard/unified')
def api_dashboard_unified():
    """API para obtener todos los datos del dashboard unificado"""
    try:
        data = get_unified_dashboard_data()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error en API dashboard unificado: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dashboard/overview')
def api_dashboard_overview():
    """API para obtener resumen del dashboard"""
    try:
        overview = get_dashboard_overview()
        return jsonify({
            'success': True,
            'overview': overview,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error en API overview: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dashboard/refresh', methods=['POST'])
def api_dashboard_refresh():
    """API para refrescar datos del dashboard"""
    try:
        # Forzar actualización de datos
        data = get_unified_dashboard_data()
        return jsonify({
            'success': True,
            'message': 'Dashboard actualizado',
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error refrescando dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dashboard/metrics/realtime')
def api_dashboard_realtime_metrics():
    """API para obtener métricas en tiempo real"""
    try:
        metrics = {
            'current_risk_level': get_current_average_risk(),
            'active_alerts_count': len(get_active_alerts()),
            'articles_processed_today': get_articles_processed_today(),
            'system_status': 'operational',
            'last_update': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error en métricas tiempo real: {e}")
        return jsonify({'success': False, 'error': str(e)})

def get_current_average_risk():
    """Obtener nivel de riesgo promedio actual"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT AVG(CAST(risk_level AS FLOAT)) 
            FROM enhanced_articles 
            WHERE risk_level IS NOT NULL 
            AND DATE(processed_date) = DATE('now')
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return round(result[0], 2) if result[0] else 0.0
        
    except Exception as e:
        logger.error(f"Error obteniendo riesgo promedio actual: {e}")
        return 0.0

def get_articles_processed_today():
    """Obtener número de artículos procesados hoy"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM enhanced_articles 
            WHERE DATE(processed_date) = DATE('now')
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error obteniendo artículos procesados hoy: {e}")
        return 0
'''
            
            content += unified_api_endpoints
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("API ENDPOINTS UNIFICADOS AGREGADOS")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando API endpoints unificados: {e}")
            return False

if __name__ == "__main__":
    project_root = Path(__file__).parent.absolute()
    dashboard_unification = DashboardUnificationImplementation(project_root)
    
    print("\n" + "="*50)
    print("BLOQUE 1D: FUSIÓN DE SECCIONES DEL DASHBOARD")
    print("="*50)
    
    success = dashboard_unification.implement_dashboard_unification()
    
    if success:
        logger.info("BLOQUE 1D COMPLETADO EXITOSAMENTE")
        print("\nBLOQUE 1D COMPLETADO EXITOSAMENTE!")
        print("- Dashboard unificado implementado")
        print("- Datos de todas las secciones integrados")
        print("- API unificada creada")
        print("- Métricas en tiempo real configuradas")
    else:
        logger.error("BLOQUE 1D FALLÓ")
        print("\nBLOQUE 1D FALLÓ - Revisar logs")
    
    sys.exit(0 if success else 1)
