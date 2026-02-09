# Arquitectura del Sistema de Video-Vigilancia de Conflictos

## VISIÓN GENERAL

El nuevo sistema transformará el sistema existente de CCTV local a un **Monitor Global de Cámaras Públicas en Zonas de Conflicto** con detección automática de indicadores mediante Computer Vision.

## ARQUITECTURA TÉCNICA

### 1. Capas del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Interface                        │
│  - Dashboard en tiempo real                                 │
│  - Mapa interactivo de cámaras                              │
│  - Visualizador de streams                                  │
│  - Galería de capturas automáticas                         │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                  Orquestador Central                        │
│  - Coordinación de servicios                               │
│  - Gestión de estados                                       │
│  - API REST + WebSockets                                    │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────┬───────────────┬───────────────┬─────────────┐
│   Detector de   │    Sistema    │   Analizador  │  Sistema de │
│    Cámaras      │   Streaming   │      CV       │   Alertas   │
│  Públicas       │   + Captura   │  Conflictos   │ + Storage   │
│                 │               │               │             │
│ • APIs públicas │ • Stream mgmt │ • YOLO detect │ • DB SQLite │
│ • Geolocalizac. │ • Screenshots │ • Indicadores │ • Email     │
│ • Filtro zonas  │ • Scheduling  │ • Análisis IA │ • WebSockets│
└─────────────────┴───────────────┴───────────────┴─────────────┘
```

### 2. Flujo de Operación

```
1. Detección Geográfica:
   Artículos geopolíticos → Extracción coordenadas → Búsqueda cámaras públicas

2. Monitoreo Automático:
   Stream cámaras → Captura periódica → Análisis CV → Detección indicadores

3. Sistema de Alertas:
   Indicadores detectados → Clasificación riesgo → Notificación + Storage

4. Dashboard Tiempo Real:
   Estado cámaras → Alertas activas → Historial capturas → Análisis tendencias
```

## COMPONENTES ESPECÍFICOS

### A. Detector de Cámaras Públicas (`public_camera_detector.py`)

```python
class PublicCameraDetector:
    """
    Detecta cámaras públicas en zonas de conflicto usando:
    - APIs de cámaras de tráfico
    - Webcams turísticas públicas
    - Cámaras de seguridad municipales
    - Filtros geográficos por conflictos
    """
    
    def detect_cameras_in_conflict_zone(self, lat, lon, radius_km):
        # Buscar cámaras públicas en zona específica
        pass
    
    def get_cameras_for_article_location(self, article_id):
        # Obtener cámaras basadas en ubicación de artículo
        pass
```

### B. Analizador CV de Conflictos (`conflict_cv_analyzer.py`)

```python
class ConflictIndicatorAnalyzer:
    """
    Analiza frames de video para detectar:
    - Vehículos militares
    - Columnas de humo
    - Multitudes/protestas
    - Daños en infraestructura
    - Movimientos inusuales
    """
    
    def analyze_frame_for_conflict_indicators(self, frame):
        # Análisis mediante YOLO + modelos personalizados
        pass
    
    def generate_risk_score(self, detections):
        # Calcular puntuación de riesgo
        pass
```

### C. Sistema de Captura Inteligente (`smart_capture_system.py`)

```python
class SmartCaptureSystem:
    """
    Gestiona captura automática:
    - Intervalos adaptativos según riesgo
    - Captura de eventos específicos
    - Almacenamiento optimizado
    - Compresión inteligente
    """
    
    def schedule_captures_for_camera(self, camera_id, risk_level):
        # Programar capturas según nivel de riesgo
        pass
```

### D. Integración Geolocalizada (`geo_integration.py`)

```python
class GeoPoliticalIntegration:
    """
    Integra con sistema de artículos existente:
    - Extracción de coordenadas de noticias
    - Mapeo automático zona → cámaras
    - Activación por eventos en tiempo real
    """
    
    def activate_monitoring_for_location(self, article_data):
        # Activar monitoreo para ubicación de artículo
        pass
```

## INTERFACES DE USUARIO

### 1. Dashboard Principal
- **Mapa Global**: Cámaras activas en zonas de conflicto
- **Panel de Estado**: Estadísticas en tiempo real
- **Feed de Alertas**: Notificaciones automáticas

### 2. Visualizador de Streams
- **Multi-view**: Múltiples cámaras simultáneas
- **Overlay de Detecciones**: Marcadores CV en tiempo real
- **Controles**: Zoom, full-screen, grabación manual

### 3. Galería de Evidencias
- **Capturas Automáticas**: Organizadas por fecha/ubicación
- **Análisis Adjunto**: Detalles de detecciones CV
- **Exportación**: Para reportes y análisis

## BASES DE DATOS

### Nuevas Tablas:

```sql
-- Cámaras públicas monitoreadas
CREATE TABLE public_cameras (
    id INTEGER PRIMARY KEY,
    camera_id VARCHAR(100) UNIQUE,
    name VARCHAR(200),
    location VARCHAR(200),
    latitude REAL,
    longitude REAL,
    stream_url TEXT,
    provider VARCHAR(100),
    status VARCHAR(50),
    last_active TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Capturas automáticas
CREATE TABLE auto_captures (
    id INTEGER PRIMARY KEY,
    camera_id VARCHAR(100),
    capture_path TEXT,
    timestamp TIMESTAMP,
    cv_analysis TEXT,
    risk_score REAL,
    indicators_detected TEXT,
    alert_generated BOOLEAN DEFAULT 0,
    article_related_id INTEGER,
    FOREIGN KEY (article_related_id) REFERENCES unified_articles(id)
);

-- Alertas de conflicto
CREATE TABLE conflict_alerts (
    id INTEGER PRIMARY KEY,
    camera_id VARCHAR(100),
    capture_id INTEGER,
    alert_type VARCHAR(100),
    severity_level VARCHAR(50),
    description TEXT,
    coordinates TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT 0,
    FOREIGN KEY (capture_id) REFERENCES auto_captures(id)
);
```

## CARACTERÍSTICAS DESTACADAS

### 🔍 Detección Inteligente
- Uso de APIs públicas de cámaras
- Filtrado geográfico automático
- Integración con noticias geopolíticas

### 🤖 Computer Vision Avanzado
- Detección de vehículos militares
- Análisis de multitudes y disturbios
- Detección de humo y explosiones
- Clasificación de riesgo automatizada

### ⚡ Tiempo Real
- WebSockets para actualizaciones instantáneas
- Dashboard responsivo
- Notificaciones push

### 📊 Análisis Histórico
- Base de datos de capturas
- Tendencias por ubicación
- Correlación con eventos noticiosos

### 🛡️ Ético y Legal
- Solo cámaras públicamente accesibles
- Cumplimiento de privacidad
- Enfoque en seguridad geopolítica

## FLUJO DE IMPLEMENTACIÓN

1. **Fase 1**: Detector de cámaras públicas + API básica
2. **Fase 2**: Sistema de captura + almacenamiento
3. **Fase 3**: Analizador CV + detección de indicadores
4. **Fase 4**: Frontend renovado + dashboard tiempo real
5. **Fase 5**: Integración con sistema de artículos
6. **Fase 6**: Sistema de alertas + notificaciones
7. **Fase 7**: Optimización + testing completo

## TECNOLOGÍAS

- **Backend**: Python Flask + SocketIO
- **Computer Vision**: OpenCV + YOLO + PyTorch
- **Frontend**: HTML5 + JavaScript + WebRTC
- **Base de Datos**: SQLite (existente)
- **APIs**: Cámaras públicas + servicios de mapas
- **Tiempo Real**: WebSockets + Server-Sent Events

Este diseño mantiene la estabilidad del sistema actual mientras añade capacidades revolucionarias de monitoreo geopolítico.