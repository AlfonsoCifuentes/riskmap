#!/usr/bin/env python3
"""
Script para ejecutar el dashboard corregido
"""

import os
import sys
from pathlib import Path

# Cambiar al directorio del proyecto
project_root = Path(__file__).parent
os.chdir(project_root)

# Agregar el directorio al path
sys.path.insert(0, str(project_root))

print("🚀 Iniciando Dashboard Corregido...")
print(f"📂 Directorio: {project_root}")
print("🔧 Versión: Columnas de DB corregidas")
print("📰 Artículos: Cargando desde base de datos real")
print("🗺️ Mapas: 3 versiones disponibles")
print("-" * 50)

try:
    # Importar y ejecutar el dashboard
    from src.dashboard.app_modern import app, socketio
    
    print("✅ Dashboard cargado correctamente")
    print("🌐 Abriendo en: http://localhost:5000")
    print("📊 Análisis de noticias: http://localhost:5000/news-analysis")
    print("🧪 Test API: http://localhost:5000/api/test")
    print("📰 Artículos: http://localhost:5000/api/articles")
    print("🔥 Alto riesgo: http://localhost:5000/api/articles/high-risk")
    print("⭐ Destacado: http://localhost:5000/api/articles/featured")
    print("🗺️ Mapa de calor: http://localhost:5000/api/events/heatmap")
    print("-" * 50)
    print("🔄 Para detener: Ctrl+C")
    print()
    
    # Ejecutar el servidor
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    
except KeyboardInterrupt:
    print("\n🛑 Dashboard detenido por el usuario")
except Exception as e:
    print(f"❌ Error al ejecutar el dashboard: {e}")
    import traceback
    traceback.print_exc()