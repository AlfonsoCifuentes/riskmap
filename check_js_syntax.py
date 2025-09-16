#!/usr/bin/env python3
"""
Verificar que el dashboard corregido no tiene errores de sintaxis JavaScript
"""
import re

def check_js_syntax():
    dashboard_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\dashboard_BUENO.html"
    
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 Verificando sintaxis JavaScript...")
        
        # Extract JavaScript content
        js_matches = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        
        issues_found = []
        
        for i, js_code in enumerate(js_matches):
            print(f"\n📋 Verificando bloque JavaScript {i+1}...")
            
            # Check for common syntax issues
            lines = js_code.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check for trailing commas before closing brackets
                if re.search(r',\s*[\]\}]', line):
                    issues_found.append(f"Bloque {i+1}, línea {line_num}: Coma final antes de cierre")
                
                # Check for double commas
                if ',,' in line:
                    issues_found.append(f"Bloque {i+1}, línea {line_num}: Comas dobles")
                
                # Check for unclosed brackets (basic check)
                open_brackets = line.count('[') + line.count('{') + line.count('(')
                close_brackets = line.count(']') + line.count('}') + line.count(')')
                
                if open_brackets > 0 and close_brackets == 0:
                    # This line opens brackets but doesn't close them
                    continue
                elif close_brackets > open_brackets and ']' in line:
                    # More closing than opening - potential issue
                    if line.strip().startswith(']'):
                        # Check if previous non-empty line ends with comma
                        for prev_line_idx in range(line_num - 2, -1, -1):
                            prev_line = lines[prev_line_idx].strip()
                            if prev_line:
                                if prev_line.endswith(','):
                                    issues_found.append(f"Bloque {i+1}, línea {line_num}: Posible coma extra antes de ']'")
                                break
        
        # Check for openHeroArticleModal function definition
        if 'function openHeroArticleModal' in content:
            print("✅ Función openHeroArticleModal encontrada")
        else:
            issues_found.append("Función openHeroArticleModal no encontrada")
        
        # Summary
        if issues_found:
            print(f"\n❌ Se encontraron {len(issues_found)} posibles problemas:")
            for issue in issues_found[:10]:  # Show first 10
                print(f"   - {issue}")
            if len(issues_found) > 10:
                print(f"   ... y {len(issues_found) - 10} más")
        else:
            print("\n✅ No se encontraron problemas evidentes de sintaxis JavaScript")
        
        # Check for port configuration
        if 'flask_port\': 5001' in content:
            print("✅ Puerto configurado correctamente a 5001")
        
        return len(issues_found) == 0
        
    except Exception as e:
        print(f"❌ Error verificando archivo: {e}")
        return False

if __name__ == "__main__":
    check_js_syntax()
