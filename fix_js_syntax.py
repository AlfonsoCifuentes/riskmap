#!/usr/bin/env python3
"""
Fix JavaScript syntax errors in dashboard_BUENO.html
"""
import re
import os

def fix_dashboard_js():
    dashboard_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\dashboard_BUENO.html"
    
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup original
        backup_path = dashboard_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backup creado: {backup_path}")
        
        # Find and fix common JavaScript syntax issues
        fixes_made = []
        
        # 1. Fix any trailing commas in arrays/objects
        pattern1 = r',(\s*[\]\}])'
        if re.search(pattern1, content):
            content = re.sub(pattern1, r'\1', content)
            fixes_made.append("Comas finales eliminadas")
        
        # 2. Fix any double commas
        pattern2 = r',\s*,'
        if re.search(pattern2, content):
            content = re.sub(pattern2, ',', content)
            fixes_made.append("Comas dobles corregidas")
        
        # 3. Fix missing commas between array elements
        pattern3 = r'(\})\s*(\{)'
        content = re.sub(pattern3, r'\1,\n            \2', content)
        
        # 4. Fix missing commas between array sets
        pattern4 = r'(\])\s*(\[)'
        content = re.sub(pattern4, r'\1,\n        \2', content)
        
        # 5. Ensure all functions are properly closed
        # This is more complex and would need careful analysis
        
        # Write corrected content
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if fixes_made:
            print(f"✅ Correcciones aplicadas: {', '.join(fixes_made)}")
        else:
            print("✅ No se encontraron errores obvios de sintaxis")
        
        return True
        
    except Exception as e:
        print(f"❌ Error procesando archivo: {e}")
        return False

if __name__ == "__main__":
    fix_dashboard_js()
