#!/usr/bin/env python3
"""
Script para verificar si hay errores de sintaxis en app_BUENA.py
"""
import sys

def check_syntax():
    """Verificar sintaxis del archivo app_BUENA.py"""
    print("🔍 Verificando sintaxis de app_BUENA.py...")
    
    try:
        # Intentar compilar el archivo
        with open('app_BUENA.py', 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        compile(source_code, 'app_BUENA.py', 'exec')
        print("✅ Sintaxis correcta - No se encontraron errores")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis encontrado:")
        print(f"   Línea {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
        
    except Exception as e:
        print(f"❌ Error verificando sintaxis: {e}")
        return False

if __name__ == "__main__":
    if check_syntax():
        print("\n🎉 El archivo está listo para ejecutarse")
        sys.exit(0)
    else:
        print("\n⚠️  Se encontraron errores que deben corregirse")
        sys.exit(1)