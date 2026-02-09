#!/usr/bin/env python3
"""
Buscar TODAS las queries SQL en RISKMAP.py que contengan 'location' sin '_'
"""

import re

def find_all_location_queries():
    """Encontrar todas las queries que usen 'location' sin '_' """
    
    with open('./RISKMAP.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar todas las queries SQL (patrones comunes)
    sql_patterns = [
        r'SELECT[^;]*?location[^_\s]',
        r'WHERE[^;]*?location[^_\s]',
        r'UPDATE[^;]*?location[^_\s]',
        r'INSERT[^;]*?location[^_\s]',
        r'FROM[^;]*?location[^_\s]',
        r'JOIN[^;]*?location[^_\s]'
    ]
    
    findings = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower()
        
        # Buscar 'location' que no sea 'location_extracted' o similar
        if 'location' in line_lower and 'location_extracted' not in line_lower:
            # Verificar que no sea una variable de Python o algo similar
            if any([
                'select ' in line_lower and ' location' in line_lower,
                'where ' in line_lower and ' location' in line_lower,
                'from ' in line_lower and ' location' in line_lower,
                'join ' in line_lower and ' location' in line_lower,
                ', location' in line_lower,
                'location,' in line_lower,
                'location ' in line_lower and ('=' in line_lower or '!=' in line_lower or 'is ' in line_lower),
                "location'" in line_lower or '"location"' in line_lower
            ]):
                findings.append({
                    'line_number': line_num,
                    'line_content': line.strip(),
                    'issue': 'SQL query using location instead of location_extracted'
                })
    
    return findings

def main():
    print("=== BUSCANDO REFERENCIAS A 'location' EN QUERIES SQL ===")
    
    findings = find_all_location_queries()
    
    if not findings:
        print("✅ No se encontraron queries SQL con 'location' problemático")
        return
    
    print(f"❌ Se encontraron {len(findings)} referencias problemáticas:")
    print()
    
    for finding in findings:
        print(f"LÍNEA {finding['line_number']}: {finding['issue']}")
        print(f"   {finding['line_content']}")
        print()
    
    # Resumen
    print("=== RESUMEN ===")
    print(f"Total de líneas problemáticas: {len(findings)}")
    print("Todas estas líneas deben usar 'location_extracted' en lugar de 'location'")

if __name__ == "__main__":
    main()