#!/usr/bin/env python3
"""
Script para encontrar referencias SQL específicas a 'location' que podrían causar errores
"""

import re

def find_sql_location_references():
    with open('RISKMAP.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patterns que podrían indicar uso de 'location' en SQL
    patterns = [
        # WHERE clauses con location
        r'WHERE.*?location[^_]',  # location not followed by _
        r'location\s*IS\s*NOT\s*NULL',
        r'location\s*=\s*\?',
        r'location\s*!=\s*\'\'',
        r'location\s*LIKE\s*',
        r'SELECT.*?location[^_].*?FROM',  # SELECT con location (no location_extracted)
        r'ORDER BY.*?location[^_]',
        r'GROUP BY.*?location[^_]',
    ]
    
    findings = []
    
    # Dividir en líneas para el análisis
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Skip comments and non-SQL lines
        if line.strip().startswith('#') or line.strip().startswith('//'):
            continue
            
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Check if it's actually SQL (look for SQL keywords)
                if any(keyword in line.upper() for keyword in ['SELECT', 'WHERE', 'FROM', 'UPDATE', 'INSERT', 'DELETE']):
                    findings.append({
                        'line': i,
                        'content': line.strip(),
                        'pattern': pattern
                    })
    
    print(f"🔍 Encontradas {len(findings)} líneas que podrían usar 'location' en lugar de 'location_extracted':")
    print("=" * 80)
    
    for finding in findings:
        print(f"Línea {finding['line']}: {finding['content']}")
        print(f"Patrón: {finding['pattern']}")
        print("-" * 40)
    
    # También buscar en strings multilinea
    print("\n🔍 Buscando en queries multilinea...")
    
    # Find multiline SQL strings
    sql_blocks = re.findall(r'["\'][\s\S]*?SELECT[\s\S]*?["\']', content, re.IGNORECASE | re.MULTILINE)
    
    for block in sql_blocks:
        if 'location' in block and 'location_extracted' not in block:
            # Find line number
            block_start = content.find(block)
            line_num = content[:block_start].count('\n') + 1
            print(f"Línea ~{line_num}: Query multilinea sospechosa")
            print(f"Query: {block[:200]}...")
            print("-" * 40)

if __name__ == "__main__":
    find_sql_location_references()