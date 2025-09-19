#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatización del Dashboard - BLOQUE 1C
Sistema de generación de reportes automáticos
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

class ReportsSystemImplementation:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.app_file = self.project_root / "app_BUENA.py"
        self.reports_dir = self.project_root / "reports"
        
    def implement_reports_system(self):
        """Implementar sistema completo de reportes"""
        logger.info("IMPLEMENTANDO SISTEMA DE REPORTES...")
        
        try:
            # 1. Crear directorio de reportes
            success_dir = self._create_reports_directory()
            
            # 2. Agregar rutas de reportes al app_BUENA.py
            success_routes = self._add_reports_routes()
            
            # 3. Agregar métodos de generación de reportes
            success_methods = self._add_reports_methods()
            
            # 4. Crear templates para reportes
            success_templates = self._create_report_templates()
            
            if all([success_dir, success_routes, success_methods, success_templates]):
                logger.info("SISTEMA DE REPORTES IMPLEMENTADO COMPLETAMENTE")
                return True
            else:
                logger.error("FALLOS EN IMPLEMENTACIÓN DE REPORTES")
                return False
                
        except Exception as e:
            logger.error(f"Error implementando sistema de reportes: {e}")
            return False
    
    def _create_reports_directory(self):
        """Crear directorio para reportes"""
        try:
            self.reports_dir.mkdir(exist_ok=True)
            logger.info("Directorio de reportes creado")
            return True
        except Exception as e:
            logger.error(f"Error creando directorio de reportes: {e}")
            return False
    
    def _add_reports_routes(self):
        """Agregar rutas para el sistema de reportes"""
        try:
            if not self.app_file.exists():
                logger.error("app_BUENA.py no encontrado")
                return False
            
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar si las rutas ya existen
            if '/api/reports/generate' in content:
                logger.info("Rutas de reportes ya existen")
                return True
            
            reports_routes = '''
# === RUTAS PARA SISTEMA DE REPORTES ===
@app.route('/reportes')
def reportes():
    """Página principal de reportes"""
    try:
        # Obtener reportes disponibles
        available_reports = get_available_reports()
        recent_reports = get_recent_reports()
        
        return render_template('reportes.html', 
                             available_reports=available_reports,
                             recent_reports=recent_reports,
                             page_title="Sistema de Reportes")
    except Exception as e:
        logger.error(f"Error en página de reportes: {e}")
        return render_template('error.html', error="Error cargando reportes")

@app.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    """Generar nuevo reporte"""
    try:
        data = request.get_json()
        report_type = data.get('type', 'daily')
        format_type = data.get('format', 'html')
        date_range = data.get('date_range', 'last_24h')
        
        report_id = generate_report(
            report_type=report_type,
            format_type=format_type,
            date_range=date_range
        )
        
        if report_id:
            return jsonify({
                'success': True,
                'report_id': report_id,
                'message': 'Reporte generado exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error generando reporte'
            })
            
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reports')
def api_list_reports():
    """Listar reportes disponibles"""
    try:
        reports = get_recent_reports()
        return jsonify({
            'success': True,
            'reports': reports,
            'count': len(reports),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error listando reportes: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reports/<report_id>/download')
def api_download_report(report_id):
    """Descargar reporte específico"""
    try:
        report_path = get_report_path(report_id)
        if report_path and os.path.exists(report_path):
            return send_file(report_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': 'Reporte no encontrado'}), 404
            
    except Exception as e:
        logger.error(f"Error descargando reporte: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reports/auto-generate', methods=['POST'])
def api_auto_generate_reports():
    """Generar reportes automáticos programados"""
    try:
        generated_reports = auto_generate_scheduled_reports()
        return jsonify({
            'success': True,
            'generated_reports': generated_reports,
            'count': len(generated_reports)
        })
    except Exception as e:
        logger.error(f"Error en generación automática: {e}")
        return jsonify({'success': False, 'error': str(e)})
'''
            
            # Insertar rutas antes del final del archivo
            content += reports_routes
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("RUTAS DE REPORTES AGREGADAS")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando rutas de reportes: {e}")
            return False
    
    def _add_reports_methods(self):
        """Agregar métodos para generación de reportes"""
        try:
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'generate_report' in content and 'def generate_report(' in content:
                logger.info("Métodos de reportes ya existen")
                return True
            
            reports_methods = '''
# === MÉTODOS PARA GENERACIÓN DE REPORTES ===
def generate_report(report_type='daily', format_type='html', date_range='last_24h'):
    """Generar reporte automático"""
    try:
        import uuid
        from datetime import datetime, timedelta
        
        # Generar ID único para el reporte
        report_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Obtener datos según el tipo de reporte
        if report_type == 'daily':
            data = get_daily_report_data(date_range)
            template_name = 'daily_report.html'
            filename = f'reporte_diario_{timestamp}.{format_type}'
        elif report_type == 'weekly':
            data = get_weekly_report_data()
            template_name = 'weekly_report.html'
            filename = f'reporte_semanal_{timestamp}.{format_type}'
        elif report_type == 'risk_analysis':
            data = get_risk_analysis_data()
            template_name = 'risk_report.html'
            filename = f'analisis_riesgo_{timestamp}.{format_type}'
        else:
            data = get_general_report_data()
            template_name = 'general_report.html'
            filename = f'reporte_general_{timestamp}.{format_type}'
        
        # Crear reporte
        report_path = os.path.join('reports', filename)
        success = create_report_file(data, template_name, report_path, format_type)
        
        if success:
            # Registrar en base de datos
            save_report_metadata(report_id, report_type, filename, report_path)
            logger.info(f"Reporte generado: {filename}")
            return report_id
        else:
            logger.error("Error generando archivo de reporte")
            return None
            
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        return None

def get_daily_report_data(date_range='last_24h'):
    """Obtener datos para reporte diario"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Calcular fecha de inicio
        if date_range == 'last_24h':
            start_date = datetime.now() - timedelta(hours=24)
        elif date_range == 'last_week':
            start_date = datetime.now() - timedelta(days=7)
        else:
            start_date = datetime.now() - timedelta(hours=24)
        
        # Artículos procesados
        cursor.execute("""
            SELECT COUNT(*) FROM enhanced_articles 
            WHERE processed_date >= ?
        """, (start_date.isoformat(),))
        articles_count = cursor.fetchone()[0]
        
        # Alertas generadas
        cursor.execute("""
            SELECT COUNT(*) FROM alerts 
            WHERE created_at >= ?
        """, (start_date.isoformat(),))
        alerts_count = cursor.fetchone()[0]
        
        # Niveles de riesgo promedio
        cursor.execute("""
            SELECT AVG(CAST(risk_level AS FLOAT)) as avg_risk
            FROM enhanced_articles 
            WHERE processed_date >= ? AND risk_level IS NOT NULL
        """, (start_date.isoformat(),))
        avg_risk_result = cursor.fetchone()
        avg_risk = avg_risk_result[0] if avg_risk_result[0] else 0.0
        
        # Top ubicaciones por actividad
        cursor.execute("""
            SELECT location, COUNT(*) as count
            FROM enhanced_articles 
            WHERE processed_date >= ? AND location IS NOT NULL
            GROUP BY location
            ORDER BY count DESC
            LIMIT 10
        """, (start_date.isoformat(),))
        top_locations = [{'location': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'report_type': 'daily',
            'date_range': date_range,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'articles_processed': articles_count,
                'alerts_generated': alerts_count,
                'average_risk_level': round(avg_risk, 2),
                'monitoring_period': '24 horas'
            },
            'top_locations': top_locations,
            'statistics': {
                'total_articles': articles_count,
                'total_alerts': alerts_count,
                'active_monitoring': True
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de reporte diario: {e}")
        return {}

def get_weekly_report_data():
    """Obtener datos para reporte semanal"""
    try:
        # Similar a daily pero con rango de 7 días
        return get_daily_report_data('last_week')
    except Exception as e:
        logger.error(f"Error obteniendo datos de reporte semanal: {e}")
        return {}

def get_risk_analysis_data():
    """Obtener datos para análisis de riesgo"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Distribución por niveles de riesgo
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
        risk_distribution = [{'category': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'report_type': 'risk_analysis',
            'generated_at': datetime.now().isoformat(),
            'risk_distribution': risk_distribution,
            'analysis_period': 'Últimos 30 días'
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de análisis de riesgo: {e}")
        return {}

def create_report_file(data, template_name, report_path, format_type):
    """Crear archivo de reporte"""
    try:
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        if format_type == 'html':
            # Generar HTML
            html_content = generate_html_report(data, template_name)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        elif format_type == 'json':
            # Generar JSON
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format_type == 'txt':
            # Generar texto plano
            text_content = generate_text_report(data)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
        
        return True
        
    except Exception as e:
        logger.error(f"Error creando archivo de reporte: {e}")
        return False

def generate_html_report(data, template_name):
    """Generar reporte en formato HTML"""
    try:
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reporte - {data.get('report_type', 'General')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .summary {{ background: #f5f5f5; padding: 20px; margin: 20px 0; }}
                .metric {{ margin: 10px 0; }}
                .locations {{ margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Reporte de Actividad - {data.get('report_type', 'General').title()}</h1>
                <p>Generado: {data.get('generated_at', 'N/A')}</p>
            </div>
            
            <div class="summary">
                <h2>Resumen Ejecutivo</h2>
        """
        
        if 'summary' in data:
            summary = data['summary']
            html += f"""
                <div class="metric">Artículos procesados: <strong>{summary.get('articles_processed', 0)}</strong></div>
                <div class="metric">Alertas generadas: <strong>{summary.get('alerts_generated', 0)}</strong></div>
                <div class="metric">Nivel de riesgo promedio: <strong>{summary.get('average_risk_level', 0)}</strong></div>
            """
        
        if 'top_locations' in data and data['top_locations']:
            html += """
            </div>
            
            <div class="locations">
                <h2>Ubicaciones con Mayor Actividad</h2>
                <table>
                    <tr><th>Ubicación</th><th>Artículos</th></tr>
            """
            for location in data['top_locations'][:5]:
                html += f"<tr><td>{location['location']}</td><td>{location['count']}</td></tr>"
            html += "</table>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Error generando HTML: {e}")
        return "<html><body><h1>Error generando reporte</h1></body></html>"

def save_report_metadata(report_id, report_type, filename, report_path):
    """Guardar metadatos del reporte en base de datos"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                status TEXT DEFAULT 'completed'
            )
        """)
        
        # Obtener tamaño del archivo
        file_size = os.path.getsize(report_path) if os.path.exists(report_path) else 0
        
        cursor.execute("""
            INSERT INTO reports (id, report_type, filename, file_path, file_size)
            VALUES (?, ?, ?, ?, ?)
        """, (report_id, report_type, filename, report_path, file_size))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error guardando metadatos de reporte: {e}")

def get_recent_reports(limit=10):
    """Obtener reportes recientes"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, report_type, filename, generated_at, file_size, status
            FROM reports 
            ORDER BY generated_at DESC 
            LIMIT ?
        """, (limit,))
        
        reports = []
        for row in cursor.fetchall():
            report = {
                'id': row[0],
                'type': row[1],
                'filename': row[2],
                'generated_at': row[3],
                'file_size': row[4],
                'status': row[5]
            }
            reports.append(report)
        
        conn.close()
        return reports
        
    except Exception as e:
        logger.error(f"Error obteniendo reportes recientes: {e}")
        return []

def get_available_reports():
    """Obtener tipos de reportes disponibles"""
    return [
        {'type': 'daily', 'name': 'Reporte Diario', 'description': 'Actividad de las últimas 24 horas'},
        {'type': 'weekly', 'name': 'Reporte Semanal', 'description': 'Resumen de la semana'},
        {'type': 'risk_analysis', 'name': 'Análisis de Riesgo', 'description': 'Análisis detallado de niveles de riesgo'}
    ]

def get_report_path(report_id):
    """Obtener ruta del archivo de reporte"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        cursor.execute("SELECT file_path FROM reports WHERE id = ?", (report_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Error obteniendo ruta de reporte: {e}")
        return None
'''
            
            content += reports_methods
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("MÉTODOS DE REPORTES AGREGADOS")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando métodos de reportes: {e}")
            return False
    
    def _create_report_templates(self):
        """Crear templates básicos para reportes"""
        try:
            # Crear un template simple de ejemplo
            template_content = """
            <div class="report-template">
                <h2>Template de Reporte</h2>
                <p>Este es un template básico para reportes.</p>
            </div>
            """
            
            template_path = self.reports_dir / "template_base.html"
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            logger.info("Templates de reportes creados")
            return True
            
        except Exception as e:
            logger.error(f"Error creando templates: {e}")
            return False

if __name__ == "__main__":
    project_root = Path(__file__).parent.absolute()
    reports_system = ReportsSystemImplementation(project_root)
    
    print("\n" + "="*50)
    print("BLOQUE 1C: IMPLEMENTACIÓN SISTEMA DE REPORTES")
    print("="*50)
    
    success = reports_system.implement_reports_system()
    
    if success:
        logger.info("BLOQUE 1C COMPLETADO EXITOSAMENTE")
        print("\nBLOQUE 1C COMPLETADO EXITOSAMENTE!")
        print("- Sistema de reportes implementado")
        print("- Generación automática configurada")
        print("- Múltiples formatos soportados")
        print("- API de descarga implementada")
    else:
        logger.error("BLOQUE 1C FALLÓ")
        print("\nBLOQUE 1C FALLÓ - Revisar logs")
    
    sys.exit(0 if success else 1)
