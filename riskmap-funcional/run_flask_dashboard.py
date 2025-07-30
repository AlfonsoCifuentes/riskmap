#!/usr/bin/env python3
"""
Script para ejecutar el dashboard Flask moderno
"""
import sys
import os
from pathlib import Path

# Configurar el entorno
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

print("🚀 Iniciando Riskmap Dashboard (Flask)...")
print(f"📂 Directorio: {current_dir}")

try:
    # Importar la aplicación Flask
    from src.dashboard.app_modern import app
    
    print("✅ Aplicación Flask cargada correctamente")
    print("🌐 Iniciando servidor en http://localhost:5000")
    print("🔄 Para detener: Ctrl+C")
    print("-" * 50)
    
    # Ejecutar la aplicación
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=False  # Evitar problemas con el reloader
    )
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("💡 Verifica que Flask esté instalado: pip install flask flask-cors")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error al iniciar el dashboard: {e}")
    sys.exit(1)