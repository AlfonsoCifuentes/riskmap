#!/usr/bin/env python3
"""
Script de prueba rápida para verificar el estado de las dependencias
"""

import sys
import subprocess

def quick_test():
    print("🔍 Verificación rápida de dependencias")
    print("=" * 40)
    
    # Verificar qué versiones están instaladas
    packages = ['tensorflow', 'keras', 'ml-dtypes', 'jax', 'jaxlib', 'transformers']
    
    for package in packages:
        try:
            result = subprocess.run([sys.executable, '-c', f'import {package.replace("-", "_")}; print({package.replace("-", "_")}.__version__)'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {package}: {result.stdout.strip()}")
            else:
                print(f"❌ {package}: Not installed or error")
        except:
            print(f"⚠️ {package}: Check failed")
    
    # Verificar compatibilidad
    print("\n🔍 Verificando compatibilidad...")
    result = subprocess.run([sys.executable, '-m', 'pip', 'check'], 
                          capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        print("✅ Sin conflictos de dependencias")
    else:
        print("⚠️ Conflictos encontrados:")
        print(result.stderr[:500])  # Primeros 500 caracteres

if __name__ == "__main__":
    quick_test()
