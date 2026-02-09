#!/usr/bin/env python3
"""
BUSCADOR DE STRING LITERALS PROBLEMÁTICOS - Encuentra comillas mal escapadas en HTML/JS
Creado por: AI Assistant
Fecha: 2024
"""

import re
import os

def find_problematic_string_literals():
    """Busca string literals problemáticos en archivos HTML/JS"""
    
    # Archivo principal a verificar
    html_file = "src/web/templates/dashboard_BUENO.html"
    
    if not os.path.exists(html_file):
        print(f"❌ Archivo no encontrado: {html_file}")
        return
    
    print(f"🔍 VERIFICANDO STRING LITERALS EN: {html_file}")
    print("=" * 60)
    
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    issues_found = []
    
    # Patrones problemáticos a buscar
    patterns = [
        # Template literals con comillas simples anidadas
        (r"`[^`]*'[^`]*'[^`]*`", "Template literal con comillas simples anidadas"),
        
        # Onclick con string literals problemáticos  
        (r"onclick=['\"][^'\"]*openArticleModal\([^)]*'[^']*'[^)]*\)", "Onclick con comillas simples en parámetros"),
        
        # Template literals mal cerrados
        (r"`[^`]*$", "Template literal posiblemente no cerrado"),
        
        # Comillas dobles dentro de atributos con comillas dobles
        (r'onclick="[^"]*"[^"]*"', "Comillas dobles anidadas en onclick"),
        
        # Comillas simples mal escapadas
        (r"'[^']*'[^']*'[^']*'", "Múltiples comillas simples sin escapar"),
    ]
    
    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        for pattern, description in patterns:
            matches = re.finditer(pattern, line_stripped)
            for match in matches:
                issues_found.append({
                    'line': line_num,
                    'content': line_stripped[:100] + "..." if len(line_stripped) > 100 else line_stripped,
                    'issue': description,
                    'match': match.group()[:50] + "..." if len(match.group()) > 50 else match.group()
                })
    
    # Mostrar resultados
    if issues_found:
        print(f"⚠️ ENCONTRADOS {len(issues_found)} POSIBLES PROBLEMAS:")
        print()
        
        for i, issue in enumerate(issues_found, 1):
            print(f"#{i} Línea {issue['line']}: {issue['issue']}")
            print(f"    Match: {issue['match']}")
            print(f"    Contexto: {issue['content']}")
            print()
    else:
        print("✅ No se encontraron patrones problemáticos obvios")
    
    # Verificación específica para template literals en JavaScript
    print("\n🔍 VERIFICACIÓN ESPECÍFICA DE TEMPLATE LITERALS:")
    print("-" * 50)
    
    js_issues = 0
    for line_num, line in enumerate(lines, 1):
        # Buscar template literals con contenido sospechoso
        if '`' in line and 'onclick' in line and 'openArticleModal' in line:
            print(f"Línea {line_num}: Template literal en onclick detectado")
            print(f"    {line.strip()[:120]}...")
            js_issues += 1
    
    if js_issues == 0:
        print("✅ No se encontraron template literals problemáticos en onclick")
    else:
        print(f"⚠️ {js_issues} posibles template literals problemáticos")
    
    return len(issues_found) == 0 and js_issues == 0

def main():
    """Función principal"""
    print("🔍 DETECTOR DE STRING LITERALS PROBLEMÁTICOS")
    print("=" * 60)
    
    if find_problematic_string_literals():
        print("\n🎉 VERIFICACIÓN COMPLETADA - No hay problemas obvios")
    else:
        print("\n⚠️ SE ENCONTRARON POSIBLES PROBLEMAS")
        print("   Revisa las líneas marcadas arriba")

if __name__ == "__main__":
    main()