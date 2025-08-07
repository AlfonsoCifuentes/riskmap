#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas de importación
"""

import sys
import traceback

def test_basic_imports():
    """Probar importaciones básicas"""
    print("🔍 Diagnóstico de importaciones...")
    print("=" * 50)
    
    # Test 1: Imports básicos
    try:
        import os
        import sys
        print("✅ os, sys - OK")
    except Exception as e:
        print(f"❌ os, sys - Error: {e}")
        return False
    
    # Test 2: Flask
    try:
        import flask
        print("✅ Flask - OK")
    except Exception as e:
        print(f"❌ Flask - Error: {e}")
    
    # Test 3: Requests
    try:
        import requests
        print("✅ Requests - OK")
    except Exception as e:
        print(f"❌ Requests - Error: {e}")
    
    # Test 4: SQLite
    try:
        import sqlite3
        print("✅ SQLite3 - OK")
    except Exception as e:
        print(f"❌ SQLite3 - Error: {e}")
    
    # Test 5: Threading
    try:
        import threading
        print("✅ Threading - OK")
    except Exception as e:
        print(f"❌ Threading - Error: {e}")
    
    print("\n🧪 Probando importación específica...")
    
    # Test 6: Clase principal
    try:
        # Importar solo la clase sin ejecutar
        sys.path.insert(0, '.')
        
        # Leer el archivo línea por línea para identificar problemas
        with open('app_BUENA.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📄 Archivo app_BUENA.py tiene {len(lines)} líneas")
        
        # Verificar si hay problemas específicos en las primeras líneas
        for i, line in enumerate(lines[:30], 1):
            if 'from fix_tf_warnings' in line:
                print(f"⚠️  Línea {i}: {line.strip()}")
            elif 'import tensorflow' in line.lower():
                print(f"⚠️  Línea {i}: {line.strip()}")
        
        print("✅ Archivo leído correctamente")
        
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        traceback.print_exc()
    
    return True

def test_server_start():
    """Intentar iniciar solo la clase base"""
    print("\n🚀 Probando inicialización básica...")
    try:
        # Solo importar la clase sin crear instancia
        from app_BUENA import RiskMapUnifiedApplication
        print("✅ Clase RiskMapUnifiedApplication importada")
        
        # Crear instancia simple
        app = RiskMapUnifiedApplication()
        print("✅ Instancia creada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        traceback.print_exc()
        return False

def main():
    print("🔧 DIAGNÓSTICO DE PROBLEMAS DE IMPORTACIÓN")
    print("=" * 60)
    
    if test_basic_imports():
        test_server_start()
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("1. Si hay errores de TensorFlow, el fix_tf_warnings.py ya está renombrado")
    print("2. Si hay otros errores, revisar las dependencias mostradas arriba")
    print("3. Una vez sin errores, probar: python app_BUENA.py")

if __name__ == "__main__":
    main()
