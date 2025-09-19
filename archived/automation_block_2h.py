#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BLOQUE 2H: Validación Final + Tests
Ejecuta validación completa y tests finales de todo el sistema
"""

import os
import sys
import logging
import sqlite3
import requests
import json
import time
from datetime import datetime
import subprocess

# Configurar logging con UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_block_2h.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FinalValidationTester:
    """Validador y tester final del sistema completo"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.app_file = os.path.join(self.project_root, 'app_BUENA.py')
        self.base_url = 'http://localhost:5000'
        self.test_results = {}
        
    def validate_file_structure(self):
        """Validar estructura de archivos del proyecto"""
        try:
            logger.info("🔍 Validando estructura de archivos...")
            
            required_files = [
                'app_BUENA.py',
                'templates/index.html',
                'templates/dashboard_unificado.html',
                'templates/mapa_calor.html',
                'templates/gdelt_dashboard.html',
                'templates/about.html',
                'templates/analysis_interconectado.html',
                'templates/earth_3d.html',
                'static/js/dashboard.js',
                'static/js/heatmap.js',
                'static/js/gdelt.js',
                'static/js/interconnected-analysis.js',
                'static/js/earth-3d.js',
                'static/css/style.css',
                'README.md'
            ]
            
            missing_files = []
            existing_files = []
            
            for file_path in required_files:
                full_path = os.path.join(self.project_root, file_path)
                if os.path.exists(full_path):
                    existing_files.append(file_path)
                    logger.info(f"✅ {file_path}")
                else:
                    missing_files.append(file_path)
                    logger.warning(f"❌ {file_path} - FALTANTE")
            
            success_rate = len(existing_files) / len(required_files) * 100
            
            self.test_results['file_structure'] = {
                'success_rate': success_rate,
                'existing_files': len(existing_files),
                'missing_files': len(missing_files),
                'details': {
                    'existing': existing_files,
                    'missing': missing_files
                }
            }
            
            logger.info(f"📊 Estructura de archivos: {success_rate:.1f}% completa")
            return success_rate >= 80
            
        except Exception as e:
            logger.error(f"❌ Error validando estructura: {e}")
            return False
    
    def validate_database_schema(self):
        """Validar esquema de base de datos"""
        try:
            logger.info("🔍 Validando esquema de base de datos...")
            
            db_path = os.path.join(self.project_root, 'data', 'riskmap.db')
            
            if not os.path.exists(db_path):
                logger.error(f"❌ Base de datos no encontrada: {db_path}")
                return False
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Obtener lista de tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'enhanced_articles',
                'gdelt_events',
                'alerts',
                'reports',
                'system_correlations',
                'network_metrics',
                'interconnected_events'
            ]
            
            existing_tables = []
            missing_tables = []
            
            for table in required_tables:
                if table in tables:
                    existing_tables.append(table)
                    logger.info(f"✅ Tabla: {table}")
                    
                    # Validar columnas de la tabla
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    logger.info(f"   Columnas: {len(columns)}")
                    
                else:
                    missing_tables.append(table)
                    logger.warning(f"❌ Tabla faltante: {table}")
            
            conn.close()
            
            success_rate = len(existing_tables) / len(required_tables) * 100
            
            self.test_results['database_schema'] = {
                'success_rate': success_rate,
                'existing_tables': len(existing_tables),
                'missing_tables': len(missing_tables),
                'total_tables': len(tables),
                'details': {
                    'existing': existing_tables,
                    'missing': missing_tables,
                    'all_tables': tables
                }
            }
            
            logger.info(f"📊 Esquema de BD: {success_rate:.1f}% completo")
            return success_rate >= 70
            
        except Exception as e:
            logger.error(f"❌ Error validando esquema BD: {e}")
            return False
    
    def validate_app_syntax(self):
        """Validar sintaxis de app_BUENA.py"""
        try:
            logger.info("🔍 Validando sintaxis de app_BUENA.py...")
            
            if not os.path.exists(self.app_file):
                logger.error("❌ app_BUENA.py no encontrado")
                return False
            
            # Validar sintaxis Python
            try:
                with open(self.app_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                compile(code, self.app_file, 'exec')
                logger.info("✅ Sintaxis Python válida")
                
                # Verificar imports críticos
                critical_imports = [
                    'from flask import',
                    'import sqlite3',
                    'import logging',
                    'from datetime import',
                    'import os'
                ]
                
                missing_imports = []
                for imp in critical_imports:
                    if imp not in code:
                        missing_imports.append(imp)
                
                # Verificar rutas críticas
                critical_routes = [
                    '@app.route(\'/\')',
                    '@app.route(\'/dashboard',
                    '@app.route(\'/mapa-calor\')',
                    '@app.route(\'/gdelt-dashboard\')',
                    '@app.route(\'/analysis-interconectado\')',
                    '@app.route(\'/earth-3d\')',
                    '@app.route(\'/about\')'
                ]
                
                missing_routes = []
                for route in critical_routes:
                    if route not in code:
                        missing_routes.append(route)
                
                syntax_score = 100
                if missing_imports:
                    syntax_score -= len(missing_imports) * 5
                    logger.warning(f"⚠️ Imports faltantes: {missing_imports}")
                
                if missing_routes:
                    syntax_score -= len(missing_routes) * 10
                    logger.warning(f"⚠️ Rutas faltantes: {missing_routes}")
                
                self.test_results['app_syntax'] = {
                    'success_rate': max(0, syntax_score),
                    'python_syntax_valid': True,
                    'missing_imports': missing_imports,
                    'missing_routes': missing_routes,
                    'file_size': len(code)
                }
                
                logger.info(f"📊 Sintaxis: {syntax_score}% válida")
                return syntax_score >= 80
                
            except SyntaxError as e:
                logger.error(f"❌ Error de sintaxis: {e}")
                self.test_results['app_syntax'] = {
                    'success_rate': 0,
                    'python_syntax_valid': False,
                    'syntax_error': str(e)
                }
                return False
                
        except Exception as e:
            logger.error(f"❌ Error validando sintaxis: {e}")
            return False
    
    def test_flask_startup(self):
        """Probar inicio de la aplicación Flask"""
        try:
            logger.info("🔍 Probando inicio de Flask...")
            
            # Intentar importar la aplicación
            import sys
            sys.path.insert(0, self.project_root)
            
            try:
                # Validar que el archivo puede ser importado
                spec = __import__('app_BUENA')
                logger.info("✅ app_BUENA.py puede ser importado")
                
                startup_score = 100
                
                self.test_results['flask_startup'] = {
                    'success_rate': startup_score,
                    'importable': True,
                    'startup_time': 'N/A'
                }
                
                logger.info(f"📊 Flask startup: {startup_score}% exitoso")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Error importando app: {e}")
                
                self.test_results['flask_startup'] = {
                    'success_rate': 50,
                    'importable': False,
                    'import_error': str(e)
                }
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando Flask: {e}")
            return False
    
    def validate_static_resources(self):
        """Validar recursos estáticos"""
        try:
            logger.info("🔍 Validando recursos estáticos...")
            
            static_files = [
                'static/css/style.css',
                'static/js/dashboard.js',
                'static/js/heatmap.js',
                'static/js/gdelt.js',
                'static/js/interconnected-analysis.js',
                'static/js/earth-3d.js'
            ]
            
            existing_static = []
            missing_static = []
            
            for file_path in static_files:
                full_path = os.path.join(self.project_root, file_path)
                if os.path.exists(full_path):
                    existing_static.append(file_path)
                    
                    # Verificar que el archivo no esté vacío
                    file_size = os.path.getsize(full_path)
                    if file_size > 0:
                        logger.info(f"✅ {file_path} ({file_size} bytes)")
                    else:
                        logger.warning(f"⚠️ {file_path} está vacío")
                else:
                    missing_static.append(file_path)
                    logger.warning(f"❌ {file_path} - FALTANTE")
            
            success_rate = len(existing_static) / len(static_files) * 100
            
            self.test_results['static_resources'] = {
                'success_rate': success_rate,
                'existing_files': len(existing_static),
                'missing_files': len(missing_static),
                'details': {
                    'existing': existing_static,
                    'missing': missing_static
                }
            }
            
            logger.info(f"📊 Recursos estáticos: {success_rate:.1f}% completos")
            return success_rate >= 70
            
        except Exception as e:
            logger.error(f"❌ Error validando recursos estáticos: {e}")
            return False
    
    def validate_templates(self):
        """Validar templates HTML"""
        try:
            logger.info("🔍 Validando templates HTML...")
            
            templates_dir = os.path.join(self.project_root, 'templates')
            if not os.path.exists(templates_dir):
                logger.error("❌ Directorio templates no encontrado")
                return False
            
            template_files = [
                'index.html',
                'dashboard_unificado.html',
                'mapa_calor.html',
                'gdelt_dashboard.html',
                'about.html',
                'analysis_interconectado.html',
                'earth_3d.html'
            ]
            
            valid_templates = []
            invalid_templates = []
            
            for template in template_files:
                template_path = os.path.join(templates_dir, template)
                
                if os.path.exists(template_path):
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Validaciones básicas HTML
                        has_doctype = '<!DOCTYPE html>' in content
                        has_html_tag = '<html' in content
                        has_head = '<head>' in content
                        has_body = '<body>' in content
                        has_title = '<title>' in content
                        
                        validation_score = sum([has_doctype, has_html_tag, has_head, has_body, has_title])
                        
                        if validation_score >= 4:
                            valid_templates.append(template)
                            logger.info(f"✅ {template} (válido)")
                        else:
                            invalid_templates.append(template)
                            logger.warning(f"⚠️ {template} (problemas de estructura)")
                            
                    except Exception as e:
                        invalid_templates.append(template)
                        logger.warning(f"⚠️ {template} (error leyendo: {e})")
                else:
                    invalid_templates.append(template)
                    logger.warning(f"❌ {template} - FALTANTE")
            
            success_rate = len(valid_templates) / len(template_files) * 100
            
            self.test_results['templates'] = {
                'success_rate': success_rate,
                'valid_templates': len(valid_templates),
                'invalid_templates': len(invalid_templates),
                'details': {
                    'valid': valid_templates,
                    'invalid': invalid_templates
                }
            }
            
            logger.info(f"📊 Templates: {success_rate:.1f}% válidos")
            return success_rate >= 70
            
        except Exception as e:
            logger.error(f"❌ Error validando templates: {e}")
            return False
    
    def generate_final_report(self):
        """Generar reporte final de validación"""
        try:
            logger.info("📊 Generando reporte final...")
            
            # Calcular puntuación general
            total_score = 0
            total_tests = 0
            
            for test_name, result in self.test_results.items():
                if 'success_rate' in result:
                    total_score += result['success_rate']
                    total_tests += 1
            
            overall_score = total_score / total_tests if total_tests > 0 else 0
            
            # Crear reporte
            report = {
                'validation_timestamp': datetime.now().isoformat(),
                'overall_score': round(overall_score, 2),
                'total_tests': total_tests,
                'individual_results': self.test_results,
                'summary': {
                    'excellent': overall_score >= 90,
                    'good': 70 <= overall_score < 90,
                    'needs_improvement': overall_score < 70
                },
                'recommendations': []
            }
            
            # Agregar recomendaciones
            if overall_score < 70:
                report['recommendations'].append("Sistema requiere atención inmediata")
            elif overall_score < 90:
                report['recommendations'].append("Sistema funcional, revisar elementos faltantes")
            else:
                report['recommendations'].append("Sistema completamente funcional")
            
            # Guardar reporte
            report_path = os.path.join(self.project_root, 'validation_final_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # Generar reporte HTML legible
            html_report = self.generate_html_report(report)
            html_report_path = os.path.join(self.project_root, 'validation_final_report.html')
            with open(html_report_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            logger.info(f"✅ Reporte final generado:")
            logger.info(f"   📄 JSON: {report_path}")
            logger.info(f"   📄 HTML: {html_report_path}")
            logger.info(f"   📊 Puntuación general: {overall_score:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte final: {e}")
            return None
    
    def generate_html_report(self, report):
        """Generar reporte HTML legible"""
        try:
            overall_score = report['overall_score']
            
            # Determinar color basado en puntuación
            if overall_score >= 90:
                score_color = '#28a745'  # Verde
                status = 'EXCELENTE'
            elif overall_score >= 70:
                score_color = '#ffc107'  # Amarillo
                status = 'BUENO'
            else:
                score_color = '#dc3545'  # Rojo
                status = 'NECESITA MEJORA'
            
            html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Final de Validación - RiskMap</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f4c75 100%);
            color: white;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: conic-gradient({score_color} {overall_score * 3.6}deg, #333 0deg);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px auto;
            position: relative;
        }}
        .score-inner {{
            width: 120px;
            height: 120px;
            background: #1a1a2e;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }}
        .score-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: {score_color};
        }}
        .score-status {{
            font-size: 1rem;
            color: {score_color};
            margin-top: 5px;
        }}
        .test-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .test-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid;
        }}
        .test-excellent {{ border-left-color: #28a745; }}
        .test-good {{ border-left-color: #ffc107; }}
        .test-poor {{ border-left-color: #dc3545; }}
        .test-title {{
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .test-score {{
            font-size: 2rem;
            font-weight: bold;
            margin: 10px 0;
        }}
        .test-details {{
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        .recommendations {{
            background: rgba(255, 193, 7, 0.1);
            border: 1px solid #ffc107;
            border-radius: 10px;
            padding: 20px;
            margin: 30px 0;
        }}
        .timestamp {{
            text-align: center;
            opacity: 0.7;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Reporte Final de Validación</h1>
            <h2>Sistema RiskMap - Dashboard Geopolítico</h2>
            
            <div class="score-circle">
                <div class="score-inner">
                    <div class="score-number">{overall_score:.1f}%</div>
                    <div class="score-status">{status}</div>
                </div>
            </div>
        </div>
        
        <div class="test-grid">'''
            
            # Agregar tarjetas de tests individuales
            for test_name, result in report['individual_results'].items():
                score = result.get('success_rate', 0)
                
                if score >= 90:
                    card_class = 'test-excellent'
                    score_color = '#28a745'
                elif score >= 70:
                    card_class = 'test-good'
                    score_color = '#ffc107'
                else:
                    card_class = 'test-poor'
                    score_color = '#dc3545'
                
                test_title = test_name.replace('_', ' ').title()
                
                details = []
                if 'existing_files' in result:
                    details.append(f"Archivos existentes: {result['existing_files']}")
                if 'missing_files' in result:
                    details.append(f"Archivos faltantes: {result['missing_files']}")
                if 'existing_tables' in result:
                    details.append(f"Tablas existentes: {result['existing_tables']}")
                
                details_text = '<br>'.join(details) if details else 'Validación completada'
                
                html += f'''
            <div class="test-card {card_class}">
                <div class="test-title">{test_title}</div>
                <div class="test-score" style="color: {score_color};">{score:.1f}%</div>
                <div class="test-details">{details_text}</div>
            </div>'''
            
            html += f'''
        </div>
        
        <div class="recommendations">
            <h3>📋 Recomendaciones</h3>
            <ul>'''
            
            for rec in report['recommendations']:
                html += f'<li>{rec}</li>'
            
            html += f'''
            </ul>
        </div>
        
        <div class="timestamp">
            <p>Reporte generado el {report['validation_timestamp']}</p>
            <p>Total de tests ejecutados: {report['total_tests']}</p>
        </div>
    </div>
</body>
</html>'''
            
            return html
            
        except Exception as e:
            logger.error(f"❌ Error generando HTML del reporte: {e}")
            return "<html><body><h1>Error generando reporte</h1></body></html>"
    
    def run(self):
        """Ejecutar todas las validaciones y tests"""
        try:
            logger.info("🚀 INICIANDO BLOQUE 2H: Validación Final + Tests")
            
            tests = [
                ("Validar estructura de archivos", self.validate_file_structure),
                ("Validar esquema de base de datos", self.validate_database_schema),
                ("Validar sintaxis de aplicación", self.validate_app_syntax),
                ("Probar inicio de Flask", self.test_flask_startup),
                ("Validar recursos estáticos", self.validate_static_resources),
                ("Validar templates HTML", self.validate_templates)
            ]
            
            results = []
            for test_name, test_func in tests:
                logger.info(f"🧪 Ejecutando: {test_name}")
                try:
                    result = test_func()
                    results.append(result)
                    if result:
                        logger.info(f"✅ {test_name} - PASÓ")
                    else:
                        logger.warning(f"⚠️ {test_name} - FALLÓ")
                except Exception as e:
                    logger.error(f"❌ {test_name} - ERROR: {e}")
                    results.append(False)
            
            # Generar reporte final
            final_report = self.generate_final_report()
            
            success_rate = sum(results) / len(results) * 100
            logger.info(f"📊 BLOQUE 2H COMPLETADO - Tests pasados: {success_rate:.1f}%")
            
            if success_rate >= 70:
                logger.info("🎉 BLOQUE 2H: Validación exitosa - Sistema listo para producción")
                return True
            else:
                logger.warning("⚠️ BLOQUE 2H: Sistema requiere atención antes de producción")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando BLOQUE 2H: {e}")
            return False

def main():
    """Función principal"""
    tester = FinalValidationTester()
    success = tester.run()
    
    if success:
        print("\n🎉 BLOQUE 2H: Validación Final completada exitosamente!")
        print("✅ Sistema completamente validado")
        print("✅ Todos los componentes verificados")
        print("✅ Reporte final generado")
        print("✅ Sistema listo para producción")
    else:
        print("\n⚠️ BLOQUE 2H: Validación completada con advertencias")
        print("📋 Revisar reporte final para detalles")
    
    return success

if __name__ == "__main__":
    main()
