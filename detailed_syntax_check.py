#!/usr/bin/env python3
"""
Encontrar exactamente dónde están los errores de sintaxis
"""

def find_exact_errors(file_path):
    """Encuentra la ubicación exacta de errores de sintaxis"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    brace_stack = []  # Para rastrear llaves abiertas
    in_script = False
    in_string = False
    string_char = None
    in_template = False
    
    print("🔍 Analizando línea por línea...")
    
    for line_num, line in enumerate(lines, 1):
        # Detectar inicio y fin de bloques script
        if '<script' in line:
            in_script = True
            print(f"📝 Línea {line_num}: Iniciando bloque script")
            continue
        elif '</script>' in line:
            in_script = False
            print(f"📝 Línea {line_num}: Finalizando bloque script")
            continue
        
        if not in_script:
            continue
        
        # Procesar caracteres
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
                    print(f"🔤 Línea {line_num}: String abierto con {char}")
                elif char == string_char:
                    in_string = False
                    string_char = None
                    print(f"🔤 Línea {line_num}: String cerrado")
            elif char == '`' and not in_string:
                in_template = not in_template
                if in_template:
                    print(f"📜 Línea {line_num}: Template literal abierto")
                else:
                    print(f"📜 Línea {line_num}: Template literal cerrado")
            elif not in_string and not in_template:
                if char == '{':
                    brace_stack.append((line_num, i))
                    print(f"🔗 Línea {line_num}: Llave '{char}' abierta (total: {len(brace_stack)})")
                elif char == '}':
                    if brace_stack:
                        brace_stack.pop()
                        print(f"🔗 Línea {line_num}: Llave '{char}' cerrada (total: {len(brace_stack)})")
                    else:
                        print(f"❌ Línea {line_num}: Llave '{char}' sin apertura correspondiente")
            
            i += 1
    
    # Reporte final
    print(f"\n📊 Resumen final:")
    if brace_stack:
        print(f"❌ {len(brace_stack)} llaves sin cerrar:")
        for line_num, pos in brace_stack:
            print(f"   • Línea {line_num}, posición {pos}")
    
    if in_string:
        print(f"❌ String sin cerrar (iniciado con {string_char})")
    
    if in_template:
        print(f"❌ Template literal sin cerrar")
    
    if not brace_stack and not in_string and not in_template:
        print(f"✅ Todo está correctamente cerrado")

if __name__ == "__main__":
    file_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\conflict_monitoring.html"
    find_exact_errors(file_path)
