#!/usr/bin/env python3
"""
Script para corregir transparencias CSS y permitir que el 3D Earth sea visible
"""

import re
import os

def fix_transparency_issues():
    """Corregir problemas de transparencia en templates"""
    
    dashboard_file = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\dashboard_BUENO.html"
    
    if not os.path.exists(dashboard_file):
        print(f"❌ Archivo no encontrado: {dashboard_file}")
        return
    
    print(f"🔧 Corrigiendo transparencias en {dashboard_file}")
    
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Patrones de transparencia problemáticos
    fixes = [
        # Reducir opacidades altas para mejor visibilidad del 3D Earth
        (r'background:\s*rgba\(26,\s*32,\s*64,\s*0\.[7-9]\d*\)', 'background: rgba(26, 32, 64, 0.3)'),
        (r'background:\s*rgba\(10,\s*15,\s*44,\s*0\.[5-9]\d*\)', 'background: rgba(10, 15, 44, 0.2)'),
        
        # Asegurar que body y html sean transparentes
        (r'(body\s*\{[^}]*background:\s*)[^;]*;', r'\1transparent;'),
        (r'(html\s*\{[^}]*background:\s*)[^;]*;', r'\1transparent;'),
        
        # Mejorar transparencia de elementos principales
        (r'background:\s*rgba\(([0-9]+),\s*([0-9]+),\s*([0-9]+),\s*0\.[6-9]\d*\)', 
         r'background: rgba(\1, \2, \3, 0.3)'),
    ]
    
    changes_made = 0
    
    for pattern, replacement in fixes:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            matches = len(re.findall(pattern, content))
            print(f"✅ Corregido {matches} instancias de: {pattern[:50]}...")
            content = new_content
            changes_made += matches
    
    # Asegurar elementos específicos sean transparentes
    specific_fixes = [
        # Hero section
        ('.hero-container', 'rgba(10, 15, 44, 0.1)'),
        ('.glass-card', 'rgba(26, 32, 64, 0.25)'),
        ('.nav-item', 'rgba(255, 255, 255, 0.1)'),
        # Main content areas
        ('.main-content', 'rgba(0, 0, 0, 0.1)'),
        ('.dashboard-section', 'rgba(0, 0, 0, 0.05)'),
    ]
    
    for selector, bg_color in specific_fixes:
        pattern = f'({re.escape(selector)}\\s*{{[^}}]*background:\\s*)[^;]*;'
        replacement = f'\\1{bg_color};'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            print(f"✅ Corregido fondo de {selector}")
            content = new_content
            changes_made += 1
    
    if content != original_content:
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"🎉 Archivo actualizado! Total de cambios: {changes_made}")
    else:
        print("ℹ️ No se necesitaron cambios")
    
    return changes_made > 0

if __name__ == "__main__":
    try:
        fixed = fix_transparency_issues()
        if fixed:
            print("\n🌍 Reinicia la aplicación para ver el 3D Earth con mejor visibilidad")
        else:
            print("\n🌍 El archivo ya está optimizado para mostrar el 3D Earth")
    except Exception as e:
        print(f"❌ Error: {e}")
