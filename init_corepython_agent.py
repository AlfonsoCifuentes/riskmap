#!/usr/bin/env python3
"""
Script de inicialización del modo agente con toolset CorePython
Configura el entorno de desarrollo con las mejores prácticas
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def setup_pre_commit():
    """Configura pre-commit hooks con las herramientas del CorePython toolset"""
    pre_commit_config = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.12.7
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]
"""
    
    with open('.pre-commit-config.yaml', 'w') as f:
        f.write(pre_commit_config.strip())
    
    # Instalar hooks
    subprocess.run(['pre-commit', 'install'], check=True)
    print("✅ Pre-commit hooks configurados")

def setup_ruff_config():
    """Configura ruff con reglas estrictas"""
    ruff_config = """
[tool.ruff]
line-length = 88
target-version = "py311"
exclude = [".venv", "__pycache__", ".git"]

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings  
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = ["E501"]  # line too long

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
"""
    
    with open('pyproject.toml', 'w') as f:
        f.write(ruff_config.strip())
    print("✅ Configuración de ruff creada")

def setup_mypy_config():
    """Configura mypy para type checking estricto"""
    mypy_config = """
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-tests.*]
disallow_untyped_defs = False
"""
    
    with open('mypy.ini', 'w') as f:
        f.write(mypy_config.strip())
    print("✅ Configuración de mypy creada")

def setup_pytest_config():
    """Configura pytest para testing"""
    pytest_config = """
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config", 
    "--verbose",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html"
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests"
]
"""
    
    # Agregar al pyproject.toml existente
    with open('pyproject.toml', 'a') as f:
        f.write('\n' + pytest_config.strip())
    print("✅ Configuración de pytest agregada")

def verify_toolset_installation():
    """Verifica que todas las herramientas del CorePython toolset estén instaladas"""
    tools = {
        'ipython': 'IPython',
        'black': 'Black', 
        'ruff': 'Ruff',
        'mypy': 'MyPy',
        'pytest': 'Pytest',
        'pre-commit': 'Pre-commit'
    }
    
    print("Verificando instalación del toolset CorePython...")
    
    for tool, name in tools.items():
        try:
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True, check=True)
            version = result.stdout.strip().split('\n')[0]
            print(f"✅ {name}: {version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {name}: No instalado o no encontrado")
            return False
    
    return True

def create_development_scripts():
    """Crea scripts útiles para desarrollo"""
    
    # Script de formato de código
    format_script = """#!/usr/bin/env python3
import subprocess
import sys

def main():
    print("Formateando código...")
    subprocess.run(['black', '.'], check=True)
    subprocess.run(['ruff', 'format', '.'], check=True)
    print("Código formateado exitosamente")

if __name__ == '__main__':
    main()
"""
    
    # Script de validación de código
    validate_script = """#!/usr/bin/env python3
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
"""
    
    # Crear directorio scripts si no existe
    os.makedirs('scripts', exist_ok=True)
    
    with open('scripts/format.py', 'w', encoding='utf-8') as f:
        f.write(format_script.strip())
    
    with open('scripts/validate.py', 'w', encoding='utf-8') as f:
        f.write(validate_script.strip())
    
    print("✅ Scripts de desarrollo creados")

def main():
    """Función principal de inicialización"""
    print("Inicializando modo agente con toolset CorePython")
    print("=" * 50)
    
    # Verificar instalación
    if not verify_toolset_installation():
        print("Faltan herramientas del toolset CorePython")
        return False
    
    try:
        # Configurar herramientas
        setup_ruff_config()
        setup_mypy_config() 
        setup_pytest_config()
        setup_pre_commit()
        create_development_scripts()
        
        print("\nInicialización completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. Ejecuta 'python scripts/format.py' para formatear código")
        print("2. Ejecuta 'python scripts/validate.py' para validar código")
        print("3. Usa 'pre-commit run --all-files' para ejecutar hooks")
        print("4. El modo agente de Copilot está configurado con CorePython")
        
        return True
        
    except Exception as e:
        print(f"Error durante la inicialización: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
