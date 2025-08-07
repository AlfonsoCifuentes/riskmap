#!/usr/bin/env python3
"""
Buscar errores específicos de sintaxis JavaScript
"""

def find_unclosed_braces(file_path):
    """Encuentra llaves sin cerrar en el archivo"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    brace_count = 0
    paren_count = 0
    in_script = False
    in_string = False
    string_char = None
    in_template = False
    
    errors = []
    
    for line_num, line in enumerate(lines, 1):
        # Detectar inicio y fin de bloques script
        if '<script' in line:
            in_script = True
            continue
        elif '</script>' in line:
            in_script = False
            continue
        
        if not in_script:
            continue
        
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
            elif not in_string and not in_template:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
            
            # Check for problems on this line
            if brace_count < 0:
                errors.append(f"Línea {line_num}: '}}' sin '{{{{' correspondiente")
                brace_count = 0
            if paren_count < 0:
                errors.append(f"Línea {line_num}: ')' sin '(' correspondiente")
                paren_count = 0
            
            i += 1
        
        # Check for unclosed strings at end of line
        if in_string and line.strip().endswith(string_char):
            in_string = False
            string_char = None
        elif in_string and not line.strip().endswith('\\'):
            # String continues to next line - this might be a problem
            pass
    
    # Final checks
    if brace_count > 0:
        errors.append(f"Archivo: {brace_count} llaves '{{{{' sin cerrar al final")
    if paren_count > 0:
        errors.append(f"Archivo: {paren_count} paréntesis '(' sin cerrar al final")
    if in_string:
        errors.append(f"Archivo: String sin cerrar al final del archivo")
    if in_template:
        errors.append(f"Archivo: Template literal sin cerrar al final del archivo")
    
    return errors

if __name__ == "__main__":
    file_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\conflict_monitoring.html"
    
    print("🔍 Buscando errores de sintaxis específicos...")
    errors = find_unclosed_braces(file_path)
    
    if errors:
        print(f"\n❌ Se encontraron {len(errors)} errores:")
        for error in errors:
            print(f"  • {error}")
    else:
        print("\n✅ No se encontraron errores de sintaxis")
