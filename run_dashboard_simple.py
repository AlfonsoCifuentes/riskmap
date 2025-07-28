#!/usr/bin/env python3
"""
Script simple y directo para ejecutar el dashboard
"""
import sys
import os
from pathlib import Path

# Configurar el entorno
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

print("🚀 Iniciando Riskmap Dashboard...")
print("📂 Directorio de trabajo:", current_dir)

try:
    # Importar FastAPI y crear la aplicación
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
    from fastapi.templating import Jinja2Templates
    from fastapi.staticfiles import StaticFiles
    import json
    import sqlite3
    from pathlib import Path
    
    # Crear aplicación FastAPI
    app = FastAPI(title="Riskmap Dashboard", version="1.0")
    
    # Configurar templates y archivos estáticos
    dashboard_dir = current_dir / "src" / "dashboard"
    templates = Jinja2Templates(directory=str(dashboard_dir))
    app.mount('/static', StaticFiles(directory=str(dashboard_dir / 'static')), name='static')
    
    # Configuración de base de datos
    DB_PATH = str(current_dir / "data" / "geopolitical_intel.db")
    
    # Ruta principal
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home(request: Request):
        try:
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "status": {"status": "ok", "message": "Dashboard running"},
                "quality": {"quality": "good", "issues": 0},
                "translations": {"title": "Riskmap Dashboard", "welcome": "Welcome"},
                "lang": "en",
                "langs": ["en", "es"]
            })
        except Exception as e:
            return HTMLResponse(f"<h1>Dashboard Error</h1><p>{str(e)}</p>", status_code=500)
    
    # Ruta de prueba
    @app.get("/test")
    async def test():
        return {"status": "ok", "message": "Dashboard is working!"}
    
    # Ruta para eventos
    @app.get("/events")
    async def events():
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            conn.close()
            return {"events_count": count, "status": "ok"}
        except Exception as e:
            return {"error": str(e), "events_count": 0}
    
    # Favicon
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = dashboard_dir / "static" / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        return JSONResponse({"error": "Favicon not found"}, status_code=404)
    
    # Iniciar servidor
    import uvicorn
    
    print("✅ Aplicación configurada correctamente")
    print("🌐 Iniciando servidor en http://localhost:8082")
    print("🔄 Para detener: Ctrl+C")
    
    uvicorn.run(app, host="127.0.0.1", port=8082, log_level="info")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("💡 Instala las dependencias: pip install fastapi uvicorn")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)