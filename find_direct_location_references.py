#!/usr/bin/env python3
"""
Script para encontrar referencias directas a 'location' como columna de BD
"""

import re

def find_direct_location_references():
    with open('RISKMAP.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patterns más específicos para columnna location directa
    patterns = [
        r'WHERE[\s\S]*?location[\s]*[=<>!]',  # WHERE location = algo
        r'WHERE[\s\S]*?location[\s]*IS[\s]*NOT[\s]*NULL',  # WHERE location IS NOT NULL
        r'WHERE[\s\S]*?location[\s]*!=[\s]*[\'"]',  # WHERE location != ''
        r'WHERE[\s\S]*?location[\s]*=[\s]*[\'"\?]',  # WHERE location = valor
        r'AND[\s\S]*?location[\s]*[=<>!]',  # AND location = algo
        r'OR[\s\S]*?location[\s]*[=<>!]',  # OR location = algo
    ]
    
    findings = []
    
    # Dividir en líneas para el análisis
    lines = content.split('\n')
    
    # Buscar en bloques de texto que contengan SQL
    sql_blocks = []
    current_block = []
    in_sql = False
    
    for i, line in enumerate(lines):
        # Detectar inicio de bloque SQL
        if any(keyword in line.upper() for keyword in ['SELECT', 'UPDATE', 'INSERT', 'DELETE']) or '"""' in line or "'''" in line:
            if current_block:
                sql_blocks.append({
                    'start_line': i - len(current_block) + 1,
                    'end_line': i,
                    'content': '\n'.join(current_block)
                })
            current_block = [line]
            in_sql = True
        elif in_sql and ('"""' in line or "'''" in line or line.strip() == '' or 'cursor.execute' in line or line.strip().startswith(')')):
            current_block.append(line)
            sql_blocks.append({
                'start_line': i - len(current_block) + 1,
                'end_line': i,
                'content': '\n'.join(current_block)
            })
            current_block = []
            in_sql = False
        elif in_sql:
            current_block.append(line)
    
    # Analizar bloques SQL
    print(f"🔍 Analizando {len(sql_blocks)} bloques SQL...")
    
    for block in sql_blocks:
        block_content = block['content']
        
        # Skip si ya usa location_extracted
        if 'location_extracted' in block_content:
            continue
            
        # Skip si es solo un alias (as location)
        if 'as location' in block_content.lower():
            continue
            
        # Buscar referencias directas a 'location' como columna
        for pattern in patterns:
            matches = re.findall(pattern, block_content, re.IGNORECASE | re.MULTILINE)
            
            if matches:
                print(f"⚠️  PROBLEMA ENCONTRADO en líneas {block['start_line']}-{block['end_line']}:")
                print(f"Patrón: {pattern}")
                print(f"Matches: {matches}")
                print("Bloque SQL:")
                print("-" * 60)
                print(block_content)
                print("=" * 80)
                
                findings.append({
                    'start_line': block['start_line'],
                    'end_line': block['end_line'],
                    'pattern': pattern,
                    'matches': matches,
                    'content': block_content
                })
    
    if not findings:
        print("✅ No se encontraron referencias directas problemáticas a 'location' como columna")
        
        # Buscar cualquier referencia a location en queries
        print("\n🔍 Buscando cualquier uso de 'location' en SQL...")
        for i, line in enumerate(lines, 1):
            if 'location' in line.lower() and any(kw in line.upper() for kw in ['SELECT', 'WHERE', 'FROM', 'UPDATE']):
                if 'location_extracted' not in line and 'as location' not in line.lower():
                    print(f"Línea {i}: {line.strip()}")
    
    return findings

if __name__ == "__main__":
    find_direct_location_references()