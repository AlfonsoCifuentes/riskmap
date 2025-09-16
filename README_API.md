# Riskmap API

## Endpoints REST disponibles

- `GET /status` — Estado general del sistema, salud, métricas y alertas.
- `GET /quality_report?days=7` — Reporte de calidad de los artículos recientes (parámetro opcional `days`).
- `GET /config` — Configuración actual del sistema (solo lectura).

## Ejecución local

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
2. Ejecuta el servidor API:
   ```bash
   uvicorn src.api.rest_status:app --reload --port 8000
   ```
3. Accede a la documentación interactiva en:
   - [http://localhost:8000/docs](http://localhost:8000/docs)
   - [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Ejemplo de consulta

```bash
curl http://localhost:8000/status
```

## Ampliación
Puedes añadir nuevos endpoints en `src/api/rest_status.py` siguiendo el patrón de FastAPI.
