#!/usr/bin/env python3
"""
Automatic Fallback Indicator Updater
Updates all HTML templates to include fallback data indicators
"""

import os
import re
from pathlib import Path

def update_template_with_fallback_indicators(template_path):
    """Update a single template with fallback indicators"""
    print(f"Updating {template_path}...")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    backup_path = f"{template_path}.backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Add fallback CSS if not present
    if 'fallback_indicators.css' not in content:
        # Find the CSS section and add fallback CSS
        css_pattern = r'(<!-- CSS -->.*?)(</head>)'
        if re.search(css_pattern, content, re.DOTALL):
            content = re.sub(
                css_pattern,
                r'\1    <!-- Fallback Data Indicators CSS -->\n    <link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/fallback_indicators.css\') }}">\n\2',
                content,
                flags=re.DOTALL
            )
    
    # Add fallback JS if not present
    if 'fallback_manager.js' not in content:
        # Find the end of body and add fallback JS
        body_end_pattern = r'(</body>)'
        if re.search(body_end_pattern, content):
            content = re.sub(
                body_end_pattern,
                r'    <!-- Fallback Data Management System -->\n    <script src="{{ url_for(\'static\', filename=\'js/fallback_manager.js\') }}"></script>\n\1',
                content
            )
    
    # Update error/loading messages with fallback indicators
    updates = [
        # Replace generic "Cargando..." with fallback-aware messages
        (
            r'<div class="stat-number"[^>]*>Cargando\.\.\.</div>',
            '<div class="stat-number"><span class="text-muted">Cargando...</span><div class="fallback-indicator warning"><i class="fas fa-wifi"></i><span>Conectando APIs</span></div></div>'
        ),
        
        # Replace "Error al cargar" messages
        (
            r'<p>Error al cargar ([^<]+)</p>',
            r'<p>Error al cargar \1</p><div class="fallback-indicator error"><i class="fas fa-exclamation-triangle"></i><span>API temporalmente no disponible</span></div>'
        ),
        
        # Replace "No hay datos disponibles" messages
        (
            r'<p>No hay ([^<]+) disponibles</p>',
            r'<p>No hay \1 disponibles</p><div class="fallback-indicator warning"><i class="fas fa-database"></i><span>Datos simulados disponibles</span></div>'
        ),
        
        # Update "Conectando" messages
        (
            r'<small>Conectando con ([^<]+)\.\.\.</small>',
            r'<div class="fallback-indicator warning"><i class="fas fa-wifi"></i><span>Conectando con \1</span></div>'
        ),
        
        # Update "Verificando" messages
        (
            r'<small>Verificando ([^<]+)\.\.\.</small>',
            r'<div class="fallback-indicator warning"><i class="fas fa-search"></i><span>Verificando \1</span></div>'
        ),
        
        # Update "Esperando" messages
        (
            r'<small>Esperando ([^<]+)</small>',
            r'<div class="fallback-indicator warning"><i class="fas fa-clock"></i><span>Esperando \1</span></div>'
        )
    ]
    
    for pattern, replacement in updates:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # Add specific section headers with status indicators
    section_patterns = [
        # Video/Camera sections
        (
            r'(<h[1-6][^>]*>.*?(?:Video|Cámara|Vigilancia).*?</h[1-6]>)',
            r'\1\n<div class="section-status"><div class="data-status simulation"><i class="fas fa-video"></i><span>Sistema de video en demostración</span></div></div>'
        ),
        
        # Satellite sections
        (
            r'(<h[1-6][^>]*>.*?(?:Satelital|Satélite|Imagen).*?</h[1-6]>)',
            r'\1\n<div class="section-status"><div class="data-status simulation"><i class="fas fa-satellite"></i><span>Imágenes satelitales simuladas</span></div></div>'
        ),
        
        # Economic/Financial sections
        (
            r'(<h[1-6][^>]*>.*?(?:Económic|Financier|Mercado|Bolsa).*?</h[1-6]>)',
            r'\1\n<div class="section-status"><div class="data-status simulation"><i class="fas fa-chart-line"></i><span>Datos económicos simulados</span></div></div>'
        ),
        
        # Analytics/Statistics sections
        (
            r'(<h[1-6][^>]*>.*?(?:Analítica|Análisis|Estadística|Métrica).*?</h[1-6]>)',
            r'\1\n<div class="section-status"><div class="data-status fallback-data"><i class="fas fa-brain"></i><span>Análisis basado en datos RSS</span></div></div>'
        )
    ]
    
    for pattern, replacement in section_patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.DOTALL)
    
    # Add page-specific initialization in JavaScript sections
    js_init_pattern = r'(document\.addEventListener\([\'"]DOMContentLoaded[\'"],\s*function\(\)\s*\{)'
    if re.search(js_init_pattern, content):
        # Determine page type from filename
        filename = os.path.basename(template_path)
        page_type = 'generic'
        
        if 'video' in filename.lower():
            page_type = 'video'
        elif 'satellite' in filename.lower():
            page_type = 'satellite'
        elif 'dashboard' in filename.lower():
            page_type = 'dashboard'
        elif 'economic' in filename.lower() or 'financial' in filename.lower():
            page_type = 'economic'
        
        init_code = f"""
    // Initialize fallback indicators for {page_type} page
    if (window.FallbackManager) {{
        window.FallbackManager.initializePageIndicators('{page_type}');
    }}"""
        
        content = re.sub(
            js_init_pattern,
            r'\1' + init_code,
            content
        )
    
    # Write updated content
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated {template_path}")

def main():
    """Update all templates with fallback indicators"""
    templates_dir = Path("src/web/templates")
    
    if not templates_dir.exists():
        print("❌ Templates directory not found")
        return
    
    # Get all HTML templates except base_navigation (already updated)
    templates = [
        f for f in templates_dir.glob("*.html") 
        if f.name not in ['base_navigation.html', 'dashboard_BUENO.html', 'video_surveillance.html']
    ]
    
    print(f"🔄 Updating {len(templates)} templates with fallback indicators...")
    
    for template in templates:
        try:
            update_template_with_fallback_indicators(template)
        except Exception as e:
            print(f"❌ Error updating {template}: {e}")
    
    print("✅ All templates updated with fallback indicators")
    print("\n📋 Summary of changes:")
    print("- Added fallback_indicators.css to all templates")
    print("- Added fallback_manager.js to all templates")
    print("- Updated error/loading messages with visual indicators")
    print("- Added section status indicators")
    print("- Added page-specific JavaScript initialization")
    print("\nNow all simulated data will be clearly marked!")

if __name__ == "__main__":
    main()
