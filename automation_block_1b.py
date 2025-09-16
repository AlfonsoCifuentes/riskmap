#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatización del Dashboard - BLOQUE 1B
Implementación del sistema de alertas
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

class AlertsSystemImplementation:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.app_file = self.project_root / "app_BUENA.py"
        self.templates_dir = self.project_root / "src" / "web" / "templates"
        
    def implement_alerts_system(self):
        """Implementar sistema completo de alertas"""
        logger.info("IMPLEMENTANDO SISTEMA DE ALERTAS...")
        
        try:
            # 1. Agregar rutas de alertas al app_BUENA.py
            success_routes = self._add_alerts_routes()
            
            # 2. Agregar métodos de gestión de alertas
            success_methods = self._add_alerts_methods()
            
            if all([success_routes, success_methods]):
                logger.info("SISTEMA DE ALERTAS IMPLEMENTADO COMPLETAMENTE")
                return True
            else:
                logger.error("FALLOS EN IMPLEMENTACIÓN DE ALERTAS")
                return False
                
        except Exception as e:
            logger.error(f"Error implementando sistema de alertas: {e}")
            return False
    
    def _add_alerts_routes(self):
        """Agregar rutas para el sistema de alertas"""
        try:
            if not self.app_file.exists():
                logger.error("app_BUENA.py no encontrado")
                return False
            
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar si las rutas ya existen
            if '/api/alerts' in content:
                logger.info("Rutas de alertas ya existen")
                return True
            
            alerts_routes = '''
# === RUTAS PARA SISTEMA DE ALERTAS ===
@app.route('/alertas')
def alertas():
    """Página principal de alertas"""
    try:
        # Obtener alertas activas
        active_alerts = get_active_alerts()
        alert_stats = get_alert_statistics()
        
        return render_template('alertas.html', 
                             alerts=active_alerts,
                             stats=alert_stats,
                             page_title="Sistema de Alertas")
    except Exception as e:
        logger.error(f"Error en página de alertas: {e}")
        return render_template('error.html', error="Error cargando alertas")

@app.route('/api/alerts')
def api_alerts():
    """API para obtener alertas"""
    try:
        alerts = get_active_alerts()
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error API alertas: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alerts/create', methods=['POST'])
def api_create_alert():
    """Crear nueva alerta"""
    try:
        data = request.get_json()
        alert_id = create_new_alert(
            title=data.get('title'),
            message=data.get('message'),
            severity=data.get('severity', 'medium'),
            category=data.get('category', 'general'),
            location=data.get('location'),
            source=data.get('source', 'manual')
        )
        
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'message': 'Alerta creada exitosamente'
        })
    except Exception as e:
        logger.error(f"Error creando alerta: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def api_acknowledge_alert(alert_id):
    """Marcar alerta como reconocida"""
    try:
        success = acknowledge_alert(alert_id)
        return jsonify({
            'success': success,
            'message': 'Alerta reconocida' if success else 'Error reconociendo alerta'
        })
    except Exception as e:
        logger.error(f"Error reconociendo alerta: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alerts/stats')
def api_alert_stats():
    """Estadísticas de alertas"""
    try:
        stats = get_alert_statistics()
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'success': False, 'error': str(e)})
'''
            
            # Insertar rutas antes del final del archivo
            content += alerts_routes
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("RUTAS DE ALERTAS AGREGADAS")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando rutas de alertas: {e}")
            return False
    
    def _add_alerts_methods(self):
        """Agregar métodos para gestión de alertas"""
        try:
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'get_active_alerts' in content:
                logger.info("Métodos de alertas ya existen")
                return True
            
            alerts_methods = '''
# === MÉTODOS PARA GESTIÓN DE ALERTAS ===
def get_active_alerts():
    """Obtener alertas activas"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                category TEXT DEFAULT 'general',
                location TEXT,
                source TEXT DEFAULT 'system',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged_at TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)
        
        # Obtener alertas activas
        cursor.execute("""
            SELECT id, title, message, severity, category, location, 
                   source, status, created_at, acknowledged_at
            FROM alerts 
            WHERE status = 'active'
            ORDER BY 
                CASE severity 
                    WHEN 'critical' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    WHEN 'low' THEN 4 
                END,
                created_at DESC
        """)
        
        alerts = []
        for row in cursor.fetchall():
            alert = {
                'id': row[0],
                'title': row[1],
                'message': row[2],
                'severity': row[3],
                'category': row[4],
                'location': row[5],
                'source': row[6],
                'status': row[7],
                'created_at': row[8],
                'acknowledged_at': row[9],
                'time_ago': get_time_ago(row[8])
            }
            alerts.append(alert)
        
        conn.close()
        return alerts
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {e}")
        return []

def create_new_alert(title, message, severity='medium', category='general', location=None, source='system'):
    """Crear nueva alerta"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alerts (title, message, severity, category, location, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, message, severity, category, location, source))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Alerta creada: {alert_id} - {title}")
        return alert_id
        
    except Exception as e:
        logger.error(f"Error creando alerta: {e}")
        return None

def acknowledge_alert(alert_id):
    """Marcar alerta como reconocida"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE alerts 
            SET acknowledged_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (alert_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
        
    except Exception as e:
        logger.error(f"Error reconociendo alerta: {e}")
        return False

def get_alert_statistics():
    """Obtener estadísticas de alertas"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Estadísticas por severidad
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM alerts 
            WHERE status = 'active'
            GROUP BY severity
        """)
        severity_stats = dict(cursor.fetchall())
        
        # Total de alertas activas
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'active'")
        total_active = cursor.fetchone()[0]
        
        # Alertas por categoría
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM alerts 
            WHERE status = 'active'
            GROUP BY category
        """)
        category_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_active': total_active,
            'by_severity': severity_stats,
            'by_category': category_stats,
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return {
            'total_active': 0,
            'by_severity': {},
            'by_category': {},
            'last_updated': datetime.now().isoformat()
        }

def get_time_ago(timestamp_str):
    """Calcular tiempo transcurrido"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"Hace {diff.days} días"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"Hace {hours} horas"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"Hace {minutes} minutos"
        else:
            return "Hace un momento"
            
    except Exception:
        return "Tiempo desconocido"

# Crear algunas alertas de ejemplo si no existen
def initialize_sample_alerts():
    """Inicializar alertas de ejemplo"""
    try:
        # Verificar si ya hay alertas
        alerts = get_active_alerts()
        if len(alerts) > 0:
            return
        
        # Crear alertas de ejemplo
        sample_alerts = [
            {
                'title': 'Actividad sísmica detectada',
                'message': 'Movimiento sísmico de magnitud 4.2 detectado en zona de monitoreo',
                'severity': 'high',
                'category': 'geological',
                'location': 'Región Metropolitana',
                'source': 'seismic_monitor'
            },
            {
                'title': 'Incremento en tensiones geopolíticas',
                'message': 'Aumento significativo en actividad de conflictos reportados',
                'severity': 'medium',
                'category': 'geopolitical',
                'location': 'Oriente Medio',
                'source': 'news_analysis'
            },
            {
                'title': 'Patrón climático anómalo',
                'message': 'Detectadas condiciones meteorológicas fuera de parámetros normales',
                'severity': 'low',
                'category': 'climate',
                'location': 'Región Pacífico',
                'source': 'weather_monitor'
            }
        ]
        
        for alert in sample_alerts:
            create_new_alert(**alert)
        
        logger.info("Alertas de ejemplo inicializadas")
        
    except Exception as e:
        logger.error(f"Error inicializando alertas de ejemplo: {e}")
'''
            
            content += alerts_methods
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("MÉTODOS DE ALERTAS AGREGADOS")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando métodos de alertas: {e}")
            return False

if __name__ == "__main__":
    project_root = Path(__file__).parent.absolute()
    alerts_system = AlertsSystemImplementation(project_root)
    
    print("\n" + "="*50)
    print("BLOQUE 1B: IMPLEMENTACIÓN SISTEMA DE ALERTAS")
    print("="*50)
    
    success = alerts_system.implement_alerts_system()
    
    if success:
        logger.info("BLOQUE 1B COMPLETADO EXITOSAMENTE")
        print("\nBLOQUE 1B COMPLETADO EXITOSAMENTE!")
        print("- Sistema de alertas implementado")
        print("- Rutas API creadas")
        print("- Métodos de gestión agregados")
    else:
        logger.error("BLOQUE 1B FALLÓ")
        print("\nBLOQUE 1B FALLÓ - Revisar logs")
    
    sys.exit(0 if success else 1)
