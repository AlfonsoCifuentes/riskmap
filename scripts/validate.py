#!/usr/bin/env python3
import subprocess
import sys

def main():
    print("Validando código...")
    
    # Ruff check
    result = subprocess.run(['ruff', 'check', '.'])
    if result.returncode != 0:
        print("Errores de ruff encontrados")
        return False
    
    # MyPy check
    result = subprocess.run(['mypy', 'src/'])
    if result.returncode != 0:
        print("Errores de tipo encontrados")
        return False
    
    # Tests
    result = subprocess.run(['pytest', 'tests/'])
    if result.returncode != 0:
        print("Tests fallaron")
        return False
    
    print("Validación completada exitosamente")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)