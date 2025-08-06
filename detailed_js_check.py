#!/usr/bin/env python3
"""
Detectar error específico de sintaxis JavaScript en dashboard
"""
import re
import json

def find_js_syntax_error():
    dashboard_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\dashboard_BUENO.html"
    
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"🔍 Analizando {len(lines)} líneas...")
        
        # Buscar problemas específicos línea por línea
        potential_issues = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Buscar patrones problemáticos
            if ']' in stripped:
                # Verificar contexto alrededor de ]
                context_before = lines[max(0, i-3):i-1] if i > 1 else []
                context_after = lines[i:min(len(lines), i+2)] if i < len(lines) else []
                
                # Buscar si hay coma antes del ]
                if re.search(r',\s*\]', stripped):
                    potential_issues.append({
                        'line': i,
                        'issue': 'Coma antes de ]',
                        'content': stripped,
                        'context_before': [l.strip() for l in context_before[-2:]],
                        'context_after': [l.strip() for l in context_after[:2]]
                    })
                
                # Buscar ] sin contexto apropiado
                if stripped == ']' or stripped == '];':
                    # Verificar línea anterior
                    prev_line = lines[i-2].strip() if i > 1 else ""
                    if prev_line.endswith(','):
                        potential_issues.append({
                            'line': i,
                            'issue': '] después de coma',
                            'content': stripped,
                            'prev_line': prev_line,
                            'context_before': [l.strip() for l in context_before[-2:]],
                            'context_after': [l.strip() for l in context_after[:2]]
                        })
                
                # Buscar arrays/objetos mal formados
                if '}{' in stripped:
                    potential_issues.append({
                        'line': i,
                        'issue': 'Objetos sin coma separadora',
                        'content': stripped
                    })
                
                if '][' in stripped:
                    potential_issues.append({
                        'line': i,
                        'issue': 'Arrays sin coma separadora',
                        'content': stripped
                    })
        
        # Mostrar resultados
        if potential_issues:
            print(f"\n❌ Encontrados {len(potential_issues)} problemas potenciales:")
            for issue in potential_issues:
                print(f"\n📍 Línea {issue['line']}: {issue['issue']}")
                print(f"   Contenido: {issue['content']}")
                if 'prev_line' in issue:
                    print(f"   Línea anterior: {issue['prev_line']}")
                if 'context_before' in issue:
                    print(f"   Contexto antes: {issue['context_before']}")
                if 'context_after' in issue:
                    print(f"   Contexto después: {issue['context_after']}")
        else:
            print("✅ No se encontraron problemas obvios de sintaxis con ]")
        
        # Buscar específicamente alrededor de la línea 4428 mencionada
        target_range = range(4420, 4440)
        print(f"\n🎯 Revisando líneas específicas {min(target_range)}-{max(target_range)}:")
        
        for line_num in target_range:
            if line_num <= len(lines):
                line_content = lines[line_num - 1].strip()
                if line_content:
                    print(f"   {line_num}: {line_content}")
                    if ']' in line_content:
                        print(f"       ⚠️  Contiene ']'")
        
        return potential_issues
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    find_js_syntax_error()
