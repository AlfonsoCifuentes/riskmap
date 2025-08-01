#!/usr/bin/env python3
"""
Script para instalar paquetes basado en los toolsets definidos en Claude.toolsets.jsonc
"""

import json
import subprocess
import sys
from pathlib import Path

def load_toolsets():
    """Carga los toolsets desde el archivo JSON"""
    toolsets_file = Path("Claude.toolsets.jsonc")
    if not toolsets_file.exists():
        print("❌ No se encontró Claude.toolsets.jsonc")
        return None
    
    with open(toolsets_file, 'r', encoding='utf-8') as f:
        # Remover comentarios JSON para parsing
        content = f.read()
        # Simple removal de comentarios (no perfecto pero funcional)
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            if '//' not in line and '/*' not in line:
                clean_lines.append(line)
        clean_content = '\n'.join(clean_lines)
        
        return json.loads(clean_content)

def install_toolset(toolset_name, toolsets):
    """Instala un toolset específico"""
    if toolset_name not in toolsets:
        print(f"❌ Toolset '{toolset_name}' no encontrado")
        return False
    
    tools = toolsets[toolset_name]["tools"]
    description = toolsets[toolset_name]["description"]
    
    print(f"\n🚀 Instalando toolset: {toolset_name}")
    print(f"📝 Descripción: {description}")
    print(f"🔧 Paquetes: {', '.join(tools)}")
    
    try:
        # Instalar todos los paquetes del toolset
        cmd = [sys.executable, "-m", "pip", "install"] + tools
        subprocess.run(cmd, check=True)
        print(f"✅ Toolset '{toolset_name}' instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando toolset '{toolset_name}': {e}")
        return False

def main():
    """Función principal"""
    print("🎯 Instalador de Toolsets Claude")
    print("=" * 50)
    
    toolsets = load_toolsets()
    if not toolsets:
        return
    
    print("\n📦 Toolsets disponibles:")
    for i, (name, config) in enumerate(toolsets.items(), 1):
        print(f"{i:2d}. {name:20s} - {config['description'][:60]}...")
    
    print(f"\n{len(toolsets)+1:2d}. Instalar todo")
    print(f"{len(toolsets)+2:2d}. Salir")
    
    try:
        choice = input("\n🔢 Selecciona una opción (número): ").strip()
        
        if choice == str(len(toolsets)+2):  # Salir
            print("👋 ¡Hasta luego!")
            return
        elif choice == str(len(toolsets)+1):  # Instalar todo
            print("\n🌟 Instalando todos los toolsets...")
            for toolset_name in toolsets.keys():
                install_toolset(toolset_name, toolsets)
        else:
            # Instalar toolset específico
            choice_idx = int(choice) - 1
            toolset_names = list(toolsets.keys())
            if 0 <= choice_idx < len(toolset_names):
                toolset_name = toolset_names[choice_idx]
                install_toolset(toolset_name, toolsets)
            else:
                print("❌ Opción inválida")
    
    except (ValueError, KeyboardInterrupt):
        print("\n👋 Operación cancelada")

if __name__ == "__main__":
    main()
