#!/usr/bin/env python3
"""
Activador del modo agente Copilot con toolset CorePython
Este script activa el entorno de desarrollo optimizado
"""

import os
import sys
import json
from pathlib import Path

def load_toolset_config():
    """Carga la configuración del toolset CorePython"""
    config_path = Path("./_vscode/Claude.toolsets.jsonc")
    if not config_path.exists():
        print("❌ No se encontró la configuración de toolsets")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Remover comentarios JSON simples
            lines = []
            for line in content.split('\n'):
                if not line.strip().startswith('//'):
                    lines.append(line)
            clean_content = '\n'.join(lines)
            return json.loads(clean_content)
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return None

def show_agent_status():
    """Muestra el estado actual del modo agente"""
    print("=" * 60)
    print("🤖 MODO AGENTE COPILOT - TOOLSET COREPYTHON")
    print("=" * 60)
    
    # Cargar configuración
    toolsets = load_toolset_config()
    if not toolsets:
        return False
    
    core_python = toolsets.get('CorePython', {})
    tools = core_python.get('tools', [])
    
    print(f"📦 Toolset activo: CorePython")
    print(f"📝 Descripción: {core_python.get('description', 'N/A')}")
    print(f"🔧 Herramientas instaladas: {len(tools)}")
    
    for tool in tools:
        print(f"   • {tool}")
    
    print(f"\n🎯 Proyecto: RiskMap - Análisis de Riesgo Geopolítico")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📁 Directorio: {os.getcwd()}")
    
    # Verificar archivos de configuración
    config_files = {
        ".pre-commit-config.yaml": "Pre-commit hooks",
        "pyproject.toml": "Configuración de herramientas",
        "mypy.ini": "Configuración de MyPy",
        ".vscode/settings.json": "Configuración de VS Code",
        ".vscode/copilot-agent.json": "Configuración del agente"
    }
    
    print(f"\n📋 Estado de configuraciones:")
    for file_path, description in config_files.items():
        if Path(file_path).exists():
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} (falta {file_path})")
    
    return True

def show_available_commands():
    """Muestra comandos disponibles para el desarrollo"""
    print(f"\n🚀 COMANDOS DISPONIBLES:")
    print(f"━" * 40)
    
    commands = {
        "Formateo de código": [
            "python scripts/format.py",
            "black .",
            "ruff format ."
        ],
        "Validación de código": [
            "python scripts/validate.py", 
            "ruff check .",
            "mypy src/"
        ],
        "Testing": [
            "pytest tests/",
            "pytest --cov=src tests/",
            "pytest -v tests/"
        ],
        "Pre-commit": [
            "pre-commit run --all-files",
            "pre-commit install",
            "pre-commit autoupdate"
        ],
        "Desarrollo": [
            "ipython",
            "python app_moderncopia31alas945.py",
            "python -m pytest tests/ -v"
        ]
    }
    
    for category, cmds in commands.items():
        print(f"\n📂 {category}:")
        for cmd in cmds:
            print(f"   • {cmd}")

def main():
    """Función principal"""
    if not show_agent_status():
        return False
    
    show_available_commands()
    
    print(f"\n💡 MODO DE USO:")
    print(f"━" * 40)
    print(f"1. 🎨 Formatea tu código: python scripts/format.py")
    print(f"2. 🔍 Valida tu código: python scripts/validate.py") 
    print(f"3. 🧪 Ejecuta tests: pytest tests/")
    print(f"4. 🚀 Inicia la app: python app_moderncopia31alas945.py")
    print(f"5. 💬 Usa GitHub Copilot con contexto optimizado")
    
    print(f"\n🤝 COPILOT INTEGRADO:")
    print(f"   • Toolset CorePython cargado automáticamente")
    print(f"   • Contexto del proyecto riskmap activo")
    print(f"   • Sugerencias optimizadas para análisis de riesgo")
    print(f"   • Estándares de código aplicados automáticamente")
    
    print(f"\n✨ ¡El modo agente está listo para usar!")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
