#!/usr/bin/env python3
"""
Encontrar específicamente el array desbalanceado
"""
import re

def find_unbalanced_array():
    dashboard_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\dashboard_BUENO.html"
    
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer JavaScript
        js_matches = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        
        if not js_matches:
            print("❌ No se encontró JavaScript")
            return
        
        js_content = js_matches[0]  # Primer bloque
        
        # Buscar todos los arrays
        lines = js_content.split('\n')
        
        bracket_stack = []
        in_array = False
        array_start_line = 0
        
        for line_num, line in enumerate(lines, 1):
            for char_pos, char in enumerate(line):
                if char == '[':
                    bracket_stack.append((line_num, char_pos, '['))
                    if not in_array:
                        in_array = True
                        array_start_line = line_num
                        
                elif char == ']':
                    if bracket_stack and bracket_stack[-1][2] == '[':
                        bracket_stack.pop()
                        if len(bracket_stack) == 0:
                            in_array = False
                    else:
                        # ¡Aquí está el problema!
                        print(f"❌ ENCONTRADO: ] sin [ correspondiente en línea {line_num}, posición {char_pos}")
                        print(f"   Línea: {line.strip()}")
                        
                        # Mostrar contexto
                        start_context = max(0, line_num - 5)
                        end_context = min(len(lines), line_num + 5)
                        
                        print("\n📋 Contexto:")
                        for i in range(start_context, end_context):
                            marker = ">>> " if i == line_num - 1 else "    "
                            print(f"{marker}{i+1:4d}: {lines[i].rstrip()}")
                        
                        return line_num
        
        # Verificar si quedaron [ sin cerrar
        if bracket_stack:
            print(f"❌ ENCONTRADO: {len(bracket_stack)} '[' sin cerrar:")
            for line_num, char_pos, bracket in bracket_stack:
                print(f"   Línea {line_num}, posición {char_pos}")
                print(f"   Contenido: {lines[line_num-1].strip()}")
        
        if not bracket_stack:
            print("✅ Todos los arrays están balanceados")
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    find_unbalanced_array()
