#!/usr/bin/env python3
"""
Validador de sintaxis JavaScript en templates HTML
"""

import re
import sys

def validate_js_syntax(file_path):
    """Valida la sintaxis JavaScript en un archivo HTML"""
    print(f"🔍 Validando sintaxis JavaScript en: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraer bloques de JavaScript
    script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    
    errors = []
    line_offset = 0
    
    for i, block in enumerate(script_blocks):
        print(f"\n📝 Validando bloque JavaScript #{i+1}")
        
        # Contar líneas hasta este bloque
        block_start = content.find(block)
        lines_before = content[:block_start].count('\n')
        
        # Validar paréntesis, corchetes y llaves
        paren_count = 0
        bracket_count = 0
        brace_count = 0
        template_literal_count = 0
        in_string = False
        in_template = False
        string_char = None
        
        for line_num, line in enumerate(block.split('\n'), 1):
            actual_line = lines_before + line_num
            
            i = 0
            while i < len(line):
                char = line[i]
                
                # Skip escaped characters
                if i > 0 and line[i-1] == '\\':
                    i += 1
                    continue
                
                # Handle strings
                if char in ['"', "'"] and not in_template:
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                elif char == '`' and not in_string:
                    in_template = not in_template
                    template_literal_count += 1 if in_template else -1
                elif not in_string and not in_template:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                    elif char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                # Check for negative counts (closing without opening)
                if paren_count < 0:
                    errors.append(f"Línea {actual_line}: Paréntesis ')' sin '(' correspondiente")
                    paren_count = 0
                elif bracket_count < 0:
                    errors.append(f"Línea {actual_line}: Corchete ']' sin '[' correspondiente")
                    bracket_count = 0
                elif brace_count < 0:
                    errors.append(f"Línea {actual_line}: Llave '}}' sin '{{' correspondiente")
                    brace_count = 0
                
                i += 1
        
        # Check final counts
        if paren_count > 0:
            errors.append(f"Bloque #{i+1}: {paren_count} paréntesis '(' sin cerrar")
        if bracket_count > 0:
            errors.append(f"Bloque #{i+1}: {bracket_count} corchetes '[' sin cerrar")
        if brace_count > 0:
            errors.append(f"Bloque #{i+1}: {brace_count} llaves '{{' sin cerrar")
        if template_literal_count > 0:
            errors.append(f"Bloque #{i+1}: {template_literal_count} template literals '`' sin cerrar")
        if in_string:
            errors.append(f"Bloque #{i+1}: String sin cerrar")
    
    # Resultados
    if errors:
        print(f"\n❌ Se encontraron {len(errors)} errores de sintaxis:")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print(f"\n✅ No se encontraron errores de sintaxis JavaScript")
        return True

if __name__ == "__main__":
    file_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\conflict_monitoring.html"
    validate_js_syntax(file_path)
