#!/usr/bin/env python3
"""
Script para encontrar líneas EXACTAS que contienen SELECT y location en unified_articles
"""

import re

def find_exact_select_location_issues():
    with open('RISKMAP.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 BUSCANDO LÍNEAS EXACTAS CON SELECT...location...unified_articles")
    print("=" * 80)
    
    found_issues = []
    in_multiline_query = False
    multiline_buffer = []
    multiline_start_line = None
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
            
        # Check if we're starting or ending a multiline string
        if '"""' in line or "'''" in line:
            if in_multiline_query:
                # Ending multiline
                multiline_buffer.append(line)
                full_query = '\n'.join(multiline_buffer)
                
                # Check if this multiline block is problematic
                if ('select' in full_query.lower() and 
                    'location' in full_query.lower() and 
                    'unified_articles' in full_query.lower() and
                    'location_extracted' not in full_query.lower() and
                    'as location' not in full_query.lower()):
                    
                    found_issues.append({
                        'start_line': multiline_start_line,
                        'end_line': i,
                        'content': full_query
                    })
                
                # Reset
                in_multiline_query = False
                multiline_buffer = []
                multiline_start_line = None
            else:
                # Starting multiline
                in_multiline_query = True
                multiline_buffer = [line]
                multiline_start_line = i
        elif in_multiline_query:
            multiline_buffer.append(line)
        else:
            # Single line check
            if ('select' in line.lower() and 
                'location' in line.lower() and 
                'unified_articles' in line.lower() and
                'location_extracted' not in line.lower() and
                'as location' not in line.lower()):
                
                found_issues.append({
                    'start_line': i,
                    'end_line': i,
                    'content': line
                })
    
    if found_issues:
        print(f"⚠️  ENCONTRADOS {len(found_issues)} PROBLEMAS REALES:")
        for issue in found_issues:
            if issue['start_line'] == issue['end_line']:
                print(f"\nLínea {issue['start_line']}:")
                print(f"  {issue['content']}")
            else:
                print(f"\nLíneas {issue['start_line']}-{issue['end_line']}:")
                print(f"  {issue['content'][:300]}...")
    else:
        print("✅ No se encontraron problemas reales de SELECT...location...unified_articles")
    
    return found_issues

if __name__ == "__main__":
    issues = find_exact_select_location_issues()