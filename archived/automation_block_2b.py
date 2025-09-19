#!/usr/bin/env python3
"""
BLOQUE 2B: Correcciones Base - Navbar y Footer
==============================================

Tareas:
- Cambiar título del Navbar a "RISKMAP"
- Crear footer común con datos de la aplicación
- Alfonso Cifuentes Alonso
- Enlaces GitHub, LinkedIn y repositorio

Fecha: Agosto 2025
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('automation_block_2b.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class NavbarFooterUpdater:
    """Sistema para actualizar navbar y footer"""
    
    def __init__(self):
        logger.info("🚀 Iniciando actualización de Navbar y Footer - BLOQUE 2B")
    
    def run_all_updates(self):
        """Ejecutar todas las actualizaciones"""
        try:
            logger.info("=" * 60)
            logger.info("📝 BLOQUE 2B: NAVBAR Y FOOTER")
            logger.info("=" * 60)
            
            # 1. Actualizar navbar
            self.update_navbar_title()
            
            # 2. Crear footer común
            self.create_common_footer()
            
            # 3. Actualizar templates para incluir footer
            self.update_templates_with_footer()
            
            # 4. Actualizar app_BUENA.py para servir footer
            self.update_app_footer_routes()
            
            logger.info("✅ BLOQUE 2B COMPLETADO EXITOSAMENTE")
            
        except Exception as e:
            logger.error(f"❌ Error en BLOQUE 2B: {e}")
            raise e
    
    def update_navbar_title(self):
        """Actualizar título del navbar a RISKMAP"""
        try:
            logger.info("🔤 Actualizando título del navbar a RISKMAP...")
            
            # Buscar archivos que contengan el navbar
            files_to_update = [
                'src/web/templates/dashboard.html',
                'src/web/templates/index.html',
                'src/web/templates/base.html',
                'src/web/static/js/dashboard.js'
            ]
            
            for file_path in files_to_update:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Reemplazos comunes para títulos de navbar
                        replacements = [
                            ('Risk Map', 'RISKMAP'),
                            ('RiskMap', 'RISKMAP'),
                            ('Geopolitical Dashboard', 'RISKMAP'),
                            ('Dashboard Geopolítico', 'RISKMAP'),
                            ('class="navbar-brand"', 'class="navbar-brand">RISKMAP</span'),
                            ('<title>Risk Map', '<title>RISKMAP'),
                            ('<title>RiskMap', '<title>RISKMAP'),
                            ('document.title = "Risk Map"', 'document.title = "RISKMAP"'),
                            ('document.title = "RiskMap"', 'document.title = "RISKMAP"')
                        ]
                        
                        for old, new in replacements:
                            content = content.replace(old, new)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Navbar actualizado en: {file_path}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo actualizar {file_path}: {e}")
            
            logger.info("✅ Título del navbar actualizado a RISKMAP")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando navbar: {e}")
    
    def create_common_footer(self):
        """Crear footer común para todos los routes"""
        try:
            logger.info("👣 Creando footer común...")
            
            # Crear directorio de templates si no existe
            templates_dir = Path('src/web/templates')
            templates_dir.mkdir(parents=True, exist_ok=True)
            
            # Footer HTML común
            footer_html = '''
<!-- Footer común para RISKMAP -->
<footer class="bg-dark text-light py-4 mt-5">
    <div class="container">
        <div class="row">
            <div class="col-md-4">
                <h5 class="text-primary">
                    <i class="fas fa-globe-americas me-2"></i>RISKMAP
                </h5>
                <p class="mb-2">Sistema avanzado de análisis geopolítico e inteligencia de riesgos globales.</p>
                <p class="small text-muted">Análisis en tiempo real • IA • Datos satelitales • Computer Vision</p>
            </div>
            
            <div class="col-md-4">
                <h6 class="text-light">
                    <i class="fas fa-user-tie me-2"></i>Desarrollador
                </h6>
                <p class="mb-1">
                    <strong>Alfonso Cifuentes Alonso</strong>
                </p>
                <p class="mb-2">
                    <a href="https://es.linkedin.com/in/alfonso-cifuentes-alonso-13b186b3" 
                       target="_blank" 
                       rel="noopener noreferrer"
                       class="text-info text-decoration-none">
                        <i class="fab fa-linkedin me-1"></i>LinkedIn
                    </a>
                    •
                    <a href="https://github.com/AlfonsoCifuentes" 
                       target="_blank" 
                       rel="noopener noreferrer"
                       class="text-info text-decoration-none">
                        <i class="fab fa-github me-1"></i>GitHub
                    </a>
                </p>
            </div>
            
            <div class="col-md-4">
                <h6 class="text-light">
                    <i class="fas fa-code-branch me-2"></i>Proyecto
                </h6>
                <p class="mb-2">
                    <a href="https://github.com/AlfonsoCifuentes/riskmap" 
                       target="_blank" 
                       rel="noopener noreferrer"
                       class="text-info text-decoration-none">
                        <i class="fab fa-github me-1"></i>Repositorio del Proyecto
                    </a>
                </p>
                <p class="small text-muted">
                    <i class="fas fa-calendar me-1"></i>© 2025 Alfonso Cifuentes Alonso
                </p>
                <p class="small text-muted">
                    <i class="fas fa-code me-1"></i>Código abierto bajo licencia MIT
                </p>
            </div>
        </div>
        
        <hr class="my-3 border-secondary">
        
        <div class="row align-items-center">
            <div class="col-md-6">
                <p class="small text-muted mb-0">
                    <i class="fas fa-shield-alt me-1"></i>
                    Sistema de análisis geopolítico para fines educativos e informativos
                </p>
            </div>
            <div class="col-md-6 text-md-end">
                <p class="small text-muted mb-0">
                    <i class="fas fa-clock me-1"></i>
                    Actualizado en tiempo real • 
                    <span id="footer-timestamp"></span>
                </p>
            </div>
        </div>
    </div>
</footer>

<!-- Script para actualizar timestamp del footer -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    function updateFooterTimestamp() {
        const now = new Date();
        const timestamp = now.toLocaleString('es-ES', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const timestampElement = document.getElementById('footer-timestamp');
        if (timestampElement) {
            timestampElement.textContent = timestamp;
        }
    }
    
    // Actualizar timestamp inmediatamente
    updateFooterTimestamp();
    
    // Actualizar cada 30 segundos
    setInterval(updateFooterTimestamp, 30000);
});
</script>
'''
            
            # Guardar footer como template separado
            footer_file = templates_dir / 'footer.html'
            with open(footer_file, 'w', encoding='utf-8') as f:
                f.write(footer_html)
            
            logger.info(f"✅ Footer creado en: {footer_file}")
            
            # Crear también CSS específico para el footer
            css_dir = Path('src/web/static/css')
            css_dir.mkdir(parents=True, exist_ok=True)
            
            footer_css = '''
/* Estilos específicos para el footer de RISKMAP */
footer {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
    border-top: 3px solid #007bff;
    box-shadow: 0 -2px 10px rgba(0, 123, 255, 0.1);
}

footer h5 {
    color: #007bff !important;
    font-weight: bold;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

footer h6 {
    color: #ffffff !important;
    font-weight: 600;
    border-bottom: 1px solid #444;
    padding-bottom: 5px;
    margin-bottom: 10px;
}

footer a {
    transition: all 0.3s ease;
}

footer a:hover {
    color: #66b3ff !important;
    text-shadow: 0 0 5px rgba(102, 179, 255, 0.5);
}

footer .text-muted {
    color: #adb5bd !important;
}

footer .border-secondary {
    border-color: #495057 !important;
}

/* Responsividad del footer */
@media (max-width: 768px) {
    footer .col-md-4 {
        margin-bottom: 20px;
        text-align: center;
    }
    
    footer .col-md-6 {
        text-align: center !important;
    }
}

/* Animación sutil para iconos */
footer i {
    transition: transform 0.2s ease;
}

footer a:hover i {
    transform: scale(1.1);
}
'''
            
            footer_css_file = css_dir / 'footer.css'
            with open(footer_css_file, 'w', encoding='utf-8') as f:
                f.write(footer_css)
            
            logger.info(f"✅ CSS del footer creado en: {footer_css_file}")
            
        except Exception as e:
            logger.error(f"❌ Error creando footer: {e}")
    
    def update_templates_with_footer(self):
        """Actualizar templates existentes para incluir el footer"""
        try:
            logger.info("🔗 Actualizando templates para incluir footer...")
            
            templates_to_update = [
                'src/web/templates/dashboard.html',
                'src/web/templates/index.html',
                'src/web/templates/base.html'
            ]
            
            for template_path in templates_to_update:
                if os.path.exists(template_path):
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Si no tiene footer incluido, agregarlo antes del cierre del body
                        if '{% include "footer.html" %}' not in content and 'footer.html' not in content:
                            # Buscar el cierre del body
                            if '</body>' in content:
                                content = content.replace('</body>', '''
    <!-- Footer común -->
    {% include "footer.html" %}
</body>''')
                            elif content.strip().endswith('</html>'):
                                # Si termina directamente con </html>, agregar antes
                                content = content.replace('</html>', '''
    <!-- Footer común -->
    {% include "footer.html" %}
</html>''')
                            else:
                                # Agregar al final
                                content += '\n<!-- Footer común -->\n{% include "footer.html" %}\n'
                        
                        # Asegurar que incluye el CSS del footer
                        if 'footer.css' not in content:
                            # Buscar la sección head para agregar CSS
                            if '<head>' in content:
                                head_content = '''<head>
    <!-- CSS del footer -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/footer.css') }}">'''
                                content = content.replace('<head>', head_content)
                            elif '</head>' in content:
                                css_link = '''    <!-- CSS del footer -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/footer.css') }}">
</head>'''
                                content = content.replace('</head>', css_link)
                        
                        with open(template_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Template actualizado: {template_path}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo actualizar {template_path}: {e}")
            
            logger.info("✅ Templates actualizados con footer")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando templates: {e}")
    
    def update_app_footer_routes(self):
        """Actualizar app_BUENA.py para manejar rutas del footer"""
        try:
            logger.info("🔧 Actualizando app_BUENA.py para footer...")
            
            app_file = 'app_BUENA.py'
            if not os.path.exists(app_file):
                logger.warning(f"Archivo {app_file} no encontrado")
                return
            
            with open(app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar si ya tiene las rutas del footer
            if '/static/css/footer.css' not in content:
                # Buscar la sección de rutas estáticas y agregar
                static_route_section = '''        # Static files
        @self.flask_app.route('/static/<path:filename>')
        def serve_static(filename):
            return send_from_directory('src/web/static', filename)'''
                
                if static_route_section in content:
                    # Agregar ruta específica para footer CSS
                    footer_route = '''        
        # Footer CSS específico
        @self.flask_app.route('/static/css/footer.css')
        def serve_footer_css():
            return send_from_directory('src/web/static/css', 'footer.css')'''
                    
                    content = content.replace(static_route_section, static_route_section + footer_route)
            
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✅ app_BUENA.py actualizado para footer")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando app_BUENA.py: {e}")

def main():
    """Función principal para ejecutar BLOQUE 2B"""
    try:
        updater = NavbarFooterUpdater()
        updater.run_all_updates()
        
        print("\n" + "="*60)
        print("🎉 BLOQUE 2B COMPLETADO EXITOSAMENTE")
        print("="*60)
        print("✅ Navbar cambiado a 'RISKMAP'")
        print("✅ Footer común creado con datos de Alfonso Cifuentes")
        print("✅ Enlaces GitHub, LinkedIn y repositorio incluidos")
        print("✅ Templates actualizados con footer")
        print("✅ CSS específico del footer creado")
        print("✅ app_BUENA.py actualizado")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR EN BLOQUE 2B: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
