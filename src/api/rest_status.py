from fastapi import FastAPI
from fastapi.responses import JSONResponse
from monitoring.system_monitor import system_monitor
from data_quality.validator import data_validator
from utils.config import config

app = FastAPI(title="Riskmap System Status API", version="1.0")

@app.get("/status", tags=["system"])
def get_system_status():
    """Devuelve el estado general del sistema y métricas clave."""
    status = system_monitor.check_system_health()
    return JSONResponse(content=status)

@app.get("/quality_report", tags=["data"])
def get_quality_report(days: int = 7):
    """Devuelve un reporte de calidad de los artículos recientes."""
    report = data_validator.get_quality_report(days=days)
    return JSONResponse(content=report)

@app.get("/config", tags=["system"])
def get_config():
    """Devuelve la configuración actual del sistema (solo lectura)."""
    return JSONResponse(content=config.dict())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.rest_status:app", host="0.0.0.0", port=8000, reload=True)
