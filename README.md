# 🌍 RISKMAP - Plataforma de Inteligencia Geopolítica

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-brightgreen.svg)]()

> Plataforma avanzada de inteligencia geopolítica para el análisis y monitoreo de riesgos globales en tiempo real mediante IA y datos satelitales.

## 🚀 Características Principales

### 🤖 Inteligencia Artificial
- **Análisis automático** de noticias geopolíticas
- **Procesamiento de lenguaje natural** para extracción de entidades
- **Computer Vision** para análisis de imágenes
- **Detección de patrones** y anomalías en tiempo real

### 🛰️ Análisis Satelital
- **Integración SentinelHub** para imágenes satelitales
- **Análisis automático** de zonas de conflicto
- **Detección de cambios** en infraestructura y vegetación
- **Generación automática** de GeoJSON

### 📊 Monitoreo en Tiempo Real
- **GDELT integration** para eventos globales
- **RSS feeds** de fuentes confiables
- **Alertas automáticas** por nivel de riesgo
- **Dashboard unificado** con métricas en vivo

### 🗺️ Visualización Avanzada
- **Mapas de calor** interactivos
- **Globo 3D** con eventos geopolíticos
- **Gráficos temporales** de tendencias
- **Exportación** en múltiples formatos

## 📋 Tabla de Contenidos

- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [API Documentation](#-api-documentation)
- [Arquitectura](#-arquitectura)
- [Stack Tecnológico](#-stack-tecnológico)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

## 🛠️ Instalación

### Requisitos Previos
- Python 3.9+
- Git
- Conexión a internet (para APIs)

### Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/AlfonsoCifuentes/riskmap.git
cd riskmap

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

### Variables de Entorno Requeridas

```bash
# APIs Requeridas
GROQ_API_KEY=tu_groq_api_key
SENTINELHUB_CLIENT_ID=tu_sentinelhub_client_id
SENTINELHUB_CLIENT_SECRET=tu_sentinelhub_client_secret
MAPBOX_TOKEN=tu_mapbox_token

# Base de Datos
DATABASE_URL=sqlite:///geopolitical_intelligence.db

# Configuración Flask
FLASK_ENV=production
SECRET_KEY=tu_secret_key_seguro
```

## 🚀 Uso

### Ejecutar la Aplicación

```bash
# Modo producción
python app_BUENA.py

# La aplicación estará disponible en:
# http://localhost:5000
```

### Endpoints Principales

- **Dashboard**: `/dashboard-unificado`
- **Mapa de Calor**: `/mapa-calor`
- **GDELT**: `/gdelt-dashboard`
- **Reportes**: `/reportes`
- **About**: `/about`

## 📡 API Documentation

### Endpoints Principales

#### Artículos y Análisis
```bash
GET /api/articles                    # Obtener artículos
GET /api/articles/enhanced           # Artículos con análisis IA
POST /api/articles/analyze           # Analizar artículo específico
```

#### Datos Geográficos
```bash
GET /api/heatmap/data               # Datos mapa de calor
GET /api/heatmap/zones              # Zonas de riesgo
GET /api/geojson/list               # Archivos GeoJSON
POST /api/geojson/auto-upload       # Subida automática
```

#### GDELT Integration
```bash
GET /api/gdelt/events               # Eventos GDELT recientes
GET /api/gdelt/statistics           # Estadísticas GDELT
GET /api/gdelt/geographic           # Análisis geográfico
POST /api/gdelt/refresh             # Actualizar datos
```

#### Satelital
```bash
GET /api/satellite/images           # Imágenes satelitales
POST /api/satellite/analyze         # Analizar zona específica
GET /api/satellite/analysis         # Resultados análisis
```

### Ejemplos de Uso

```python
import requests

# Obtener artículos recientes
response = requests.get('http://localhost:5000/api/articles?limit=10')
articles = response.json()

# Analizar zona geográfica
data = {
    'latitude': 40.7128,
    'longitude': -74.0060,
    'size_km': 10
}
response = requests.post('http://localhost:5000/api/satellite/analyze', json=data)
analysis = response.json()
```

## 🏗️ Arquitectura

```
RISKMAP/
├── app_BUENA.py              # Aplicación principal
├── src/
│   ├── web/                  # Frontend
│   │   ├── templates/        # Templates HTML
│   │   └── static/           # CSS, JS, imágenes
│   ├── maps/                 # Motor de mapas
│   ├── satellite/            # Análisis satelital
│   ├── analysis/             # Computer Vision
│   ├── cache/                # Sistema de cache
│   └── upload/               # Subida archivos
├── data/                     # Bases de datos
├── reports/                  # Reportes generados
├── logs/                     # Archivos de log
└── tests/                    # Tests unitarios
```

## 💻 Stack Tecnológico

### Backend
- **Python 3.9+** - Lenguaje principal
- **Flask 2.3+** - Framework web
- **SQLite** - Base de datos principal
- **OpenCV** - Computer Vision
- **GDELT** - Datos geopolíticos
- **SentinelHub API** - Imágenes satelitales

### Frontend
- **Bootstrap 5** - Framework CSS
- **Plotly.js** - Gráficos interactivos
- **Mapbox GL** - Mapas avanzados
- **Chart.js** - Visualizaciones
- **Font Awesome** - Iconografía

### APIs y Servicios
- **GROQ API** - Modelos de IA
- **SentinelHub** - Imágenes satelitales
- **GDELT Project** - Eventos globales
- **Mapbox** - Servicios de mapas

### Herramientas de Desarrollo
- **Git** - Control de versiones
- **pytest** - Testing
- **Black** - Formateo de código
- **Flake8** - Linting

## 🔧 Configuración Avanzada

### Base de Datos
El sistema utiliza SQLite por defecto, pero puede configurarse para PostgreSQL:

```python
# En app_BUENA.py
DATABASE_URL = "postgresql://user:pass@localhost/riskmap"
```

### Cache
Sistema de cache inteligente configurable:

```python
CACHE_CONFIG = {
    'maps': {'ttl': 3600, 'max_size': 100},
    'satellite': {'ttl': 7200, 'max_size': 50},
    'analysis': {'ttl': 86400, 'max_size': 1000}
}
```

### Logging
Configuración de logs por módulo:

```python
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/riskmap.log'
}
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests específicos
pytest tests/test_api.py
pytest tests/test_analysis.py

# Coverage
pytest --cov=src tests/
```

## 📈 Monitoreo y Métricas

### Métricas Disponibles
- Artículos procesados por día
- Tiempo de respuesta de APIs
- Uso de cache y memoria
- Alertas generadas por hora
- Cobertura de análisis satelital

### Health Checks
```bash
GET /health                 # Estado general del sistema
GET /health/database        # Estado base de datos
GET /health/apis           # Estado APIs externas
```

## 🔒 Seguridad

- **API Keys** almacenadas en variables de entorno
- **Rate limiting** en endpoints públicos
- **Validación** de entrada en todas las APIs
- **Logs de seguridad** para monitoreo
- **HTTPS** recomendado en producción

## 🌟 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

### Guías de Contribución
- Seguir PEP 8 para código Python
- Documentar nuevas funciones
- Incluir tests para nuevas características
- Actualizar README si es necesario

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

**Alfonso Cifuentes Alonso**
- GitHub: [@AlfonsoCifuentes](https://github.com/AlfonsoCifuentes)
- LinkedIn: [Alfonso Cifuentes Alonso](https://es.linkedin.com/in/alfonso-cifuentes-alonso-13b186b3)
- Email: alfonso.cifuentes@example.com

## 🙏 Agradecimientos

- **GDELT Project** por los datos geopolíticos
- **SentinelHub** por las imágenes satelitales
- **OpenStreetMap** por los datos geográficos
- **Comunidad Open Source** por las bibliotecas utilizadas

## 📊 Estadísticas del Proyecto

- **Líneas de código**: ~15,000
- **Archivos Python**: 50+
- **APIs integradas**: 4+
- **Tests unitarios**: 100+
- **Cobertura**: 85%+

---

<div align="center">
  <h3>🌍 Monitoreo Global • 🤖 IA Avanzada • 🛰️ Análisis Satelital</h3>
  <p>Desarrollado con ❤️ para la comunidad de inteligencia geopolítica</p>
</div>
