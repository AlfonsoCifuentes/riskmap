#!/usr/bin/env python3
"""
Script simple para iniciar el dashboard sin problemas de importación
"""
import sys
import os
from pathlib import Path

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Cambiar al directorio correcto
os.chdir(current_dir)

try:
    import uvicorn
    from src.dashboard.run_dashboard import app
    
    print("🚀 Iniciando Riskmap Dashboard...")
    print("📍 URL: http://localhost:8081")
    print("🔄 Para detener: Ctrl+C")
    
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("💡 Asegúrate de que todas las dependencias estén instaladas")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error al iniciar el dashboard: {e}")
    sys.exit(1)