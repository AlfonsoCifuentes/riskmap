# Riskmap

Sistema avanzado de inteligencia geopolítica y análisis de riesgos.

## Características principales
- Ingesta y análisis de noticias multilingües (OSINT)
- Clasificación de riesgo, tipo de conflicto, país y región
- Validación de calidad y detección de duplicados/spam
- Reportes ejecutivos y diarios en HTML/PDF
- Dashboard y API REST para monitorización y consulta
- Sistema de monitoreo de salud, recursos y APIs externas
- Modular, extensible y preparado para producción

## Estructura del proyecto
- `src/` — Código fuente principal
  - `api/` — Endpoints REST (FastAPI)
  - `monitoring/` — Monitoreo de sistema y alertas
  - `data_ingestion/` — Ingesta de datos y fuentes
  - `nlp_processing/` — Procesamiento de texto y NLP
  - `data_quality/` — Validación y control de calidad
  - `reporting/` — Generación de reportes
- `tests/` — Pruebas automáticas
- `requirements.txt` — Dependencias principales
- `requirements-dev.txt` — Dependencias de desarrollo/testing

## Ejecución rápida de la API

```bash
# Windows
quick_start_api.bat

# Linux/Mac
bash quick_start_api.sh
```

Accede a la documentación interactiva en [http://localhost:8000/docs](http://localhost:8000/docs)

## Ejecución de tests

```bash
python -m unittest discover -s tests
```

## Ampliación y contribución
- Añade nuevos endpoints en `src/api/rest_status.py`
- Añade nuevas fuentes en `src/data_ingestion/`
- Mejora la validación en `src/data_quality/`
- Añade visualizaciones en `src/reporting/`

## Licencia
MIT
