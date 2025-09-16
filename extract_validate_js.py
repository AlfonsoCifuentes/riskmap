#!/usr/bin/env python3
"""
Extraer y validar todo el JavaScript del dashboard
"""
import re
import tempfile
import subprocess
import os

def extract_and_validate_js():
    dashboard_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\dashboard_BUENO.html"
    
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer todos los bloques de JavaScript
        js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        
        print(f"🔍 Encontrados {len(js_blocks)} bloques de JavaScript")
        
        all_js = ""
        for i, js_block in enumerate(js_blocks):
            print(f"\n📋 Procesando bloque {i+1} ({len(js_block)} caracteres)...")
            
            # Limpiar comentarios HTML que puedan estar dentro
            js_clean = re.sub(r'<!--.*?-->', '', js_block, flags=re.DOTALL)
            
            all_js += f"\n// ===== BLOQUE {i+1} =====\n"
            all_js += js_clean
            all_js += f"\n// ===== FIN BLOQUE {i+1} =====\n"
        
        # Guardar JavaScript combinado en archivo temporal
        temp_js_path = "temp_combined.js"
        with open(temp_js_path, 'w', encoding='utf-8') as f:
            f.write(all_js)
        
        print(f"✅ JavaScript combinado guardado en {temp_js_path}")
        
        # Buscar patrones problemáticos específicos
        problem_patterns = [
            (r',\s*\]', "Coma antes de ]"),
            (r',\s*\}', "Coma antes de }"),
            (r'\[\s*,', "Coma después de ["),
            (r'\{\s*,', "Coma después de {"),
            (r'}\s*{', "Objetos sin coma"),
            (r']\s*\[', "Arrays sin coma"),
            (r',\s*,', "Comas dobles"),
            (r'}\s*\[', "Objeto seguido de array sin coma"),
            (r']\s*\{', "Array seguido de objeto sin coma")
        ]
        
        issues_found = []
        
        for pattern, description in problem_patterns:
            matches = list(re.finditer(pattern, all_js))
            if matches:
                for match in matches[:5]:  # Mostrar solo los primeros 5
                    line_num = all_js[:match.start()].count('\n') + 1
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(all_js), match.end() + 50)
                    context = all_js[context_start:context_end]
                    
                    issues_found.append({
                        'pattern': description,
                        'line': line_num,
                        'match': match.group(),
                        'context': context.replace('\n', '\\n')
                    })
        
        if issues_found:
            print(f"\n❌ Encontrados {len(issues_found)} problemas de sintaxis:")
            for issue in issues_found:
                print(f"\n📍 {issue['pattern']} en línea ~{issue['line']}")
                print(f"   Match: '{issue['match']}'")
                print(f"   Contexto: ...{issue['context'][:100]}...")
        else:
            print("✅ No se encontraron patrones problemáticos comunes")
        
        # Buscar específicamente arrays grandes que podrían tener problemas
        array_pattern = r'\[[\s\S]*?\]'
        arrays = re.findall(array_pattern, all_js)
        
        print(f"\n🔍 Revisando {len(arrays)} arrays encontrados...")
        
        for i, array in enumerate(arrays):
            if len(array) > 1000:  # Arrays grandes
                print(f"   Array {i+1}: {len(array)} caracteres")
                
                # Verificar estructura del array
                if array.count('[') != array.count(']'):
                    print(f"   ⚠️  Array {i+1}: Desbalanceado [ vs ]")
                
                if re.search(r',\s*\]', array):
                    print(f"   ⚠️  Array {i+1}: Coma antes de ]")
        
        print(f"\n📁 Archivo temporal creado: {temp_js_path}")
        print("   Puedes revisarlo manualmente para más detalles")
        
        return len(issues_found) == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    extract_and_validate_js()
