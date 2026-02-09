#!/usr/bin/env python3
"""
Script para encontrar TODAS las referencias SQL problemáticas restantes
"""

import re

def scan_file_for_location_issues():
    with open('RISKMAP.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    issues = []
    
    for i, line in enumerate(lines, 1):
        # Patterns que indican queries SQL problemáticas
        if any([
            # SELECT con location pero no location_extracted 
            re.search(r'SELECT.*location[^_].*FROM.*unified_articles', line, re.IGNORECASE),
            # WHERE con location
            re.search(r'WHERE.*location[^_].*[=<>!]', line, re.IGNORECASE),
            # UPDATE con location
            re.search(r'UPDATE.*unified_articles.*location[^_]', line, re.IGNORECASE),
            # INSERT con location
            re.search(r'INSERT.*unified_articles.*location[^_]', line, re.IGNORECASE),
            # COUNT DISTINCT location
            re.search(r'COUNT\s*\(\s*DISTINCT\s+location[^_]', line, re.IGNORECASE),
            # GROUP BY location
            re.search(r'GROUP BY.*location[^_]', line, re.IGNORECASE),
            # ORDER BY location
            re.search(r'ORDER BY.*location[^_]', line, re.IGNORECASE)
        ]):
            # Skip if it's just creating a table structure or using other tables
            if not any(skip in line.lower() for skip in ['acled_events', 'gdelt_events', 'satellite_alerts', 'create table']):
                issues.append((i, line.strip()))
    
    print(f"🔍 ESCANEANDO PARA REFERENCIAS SQL PROBLEMÁTICAS")
    print("=" * 80)
    
    if issues:
        print(f"⚠️  ENCONTRADAS {len(issues)} LÍNEAS PROBLEMÁTICAS:")
        for line_num, line_content in issues:
            print(f"\nLínea {line_num}: {line_content}")
    else:
        print("✅ No se encontraron referencias SQL problemáticas")
    
    # También buscar queries multilinea que podrían tener location
    print(f"\n🔍 BUSCANDO QUERIES MULTILINEA...")
    multiline_queries = re.findall(r'"""[\s\S]*?SELECT[\s\S]*?"""', content, re.IGNORECASE)
    multiline_queries.extend(re.findall(r'\'\'\'[\s\S]*?SELECT[\s\S]*?\'\'\'', content, re.IGNORECASE))
    
    problematic_multiline = []
    for query in multiline_queries:
        if 'location' in query.lower() and 'unified_articles' in query.lower():
            if 'location_extracted' not in query.lower() and 'as location' not in query.lower():
                # Find line number
                query_start = content.find(query)
                line_num = content[:query_start].count('\n') + 1
                problematic_multiline.append((line_num, query[:200] + '...'))
    
    if problematic_multiline:
        print(f"⚠️  ENCONTRADAS {len(problematic_multiline)} QUERIES MULTILINEA PROBLEMÁTICAS:")
        for line_num, query_preview in problematic_multiline:
            print(f"\nLínea ~{line_num}:")
            print(f"Query: {query_preview}")
    else:
        print("✅ No se encontraron queries multilinea problemáticas")
    
    return issues + problematic_multiline

if __name__ == "__main__":
    issues = scan_file_for_location_issues()
    
    if issues:
        print(f"\n📋 RESUMEN: {len(issues)} problemas encontrados que necesitan ser corregidos")
    else:
        print(f"\n✅ PERFECTO: No se encontraron problemas SQL con 'location'")