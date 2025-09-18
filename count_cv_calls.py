#!/usr/bin/env python3
"""
Script simple para contar llamadas CV exactas
"""

def count_cv_calls():
    dashboard_file = "src/web/templates/dashboard_BUENO.html"
    
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Contar llamadas exactas
    active_calls = content.count("applyComputerVisionToMosaic();")
    commented_calls = content.count("//     applyComputerVisionToMosaic();")
    
    print(f"Llamadas activas: {active_calls}")
    print(f"Llamadas comentadas: {commented_calls}")
    
    # Buscar líneas específicas
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "applyComputerVisionToMosaic();" in line:
            print(f"Línea {i+1}: {line.strip()}")

if __name__ == "__main__":
    count_cv_calls()