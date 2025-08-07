# Sistema CCTV de Monitoreo Inteligente

## Descripción

El sistema CCTV integrado utiliza inteligencia artificial para monitorear automáticamente feeds de cámaras públicas y detectar eventos de riesgo en tiempo real. Está diseñado para trabajar con webcams públicas, CCTV gubernamental y feeds de emergencia.

## Características Principales

### Detección Automática de Riesgos
- **Violencia y disturbios**: Detección de peleas, manifestaciones violentas
- **Armas**: Identificación de armas blancas y de fuego
- **Multitudes**: Análisis de densidad y comportamiento de masas
- **Incendios**: Detección de humo y llamas
- **Tráfico**: Análisis de congestión y accidentes

### Arquitectura Modular
```
cams/
├── __init__.py          # Sistema principal CCTV
├── detector.py          # Motor de detección YOLO+OpenCV
├── resolver.py          # Resolución de URLs de streams
├── recorder.py          # Grabación y almacenamiento
├── alerts.py            # Sistema de alertas inteligentes
├── routes.py            # Endpoints Flask + SocketIO
└── templates/           # Interfaz web moderna
    ├── cams_map.html    # Mapa de cámaras
    ├── cams_view.html   # Vista en vivo
    └── review.html      # Revisión de grabaciones
```

### Pipelines de Análisis

#### Tiempo Real
1. **Stream Resolution**: yt-dlp + resolvers personalizados
2. **Frame Extraction**: OpenCV con FPS configurable
3. **Object Detection**: YOLOv8 optimizado para riesgos
4. **Alert Generation**: Reglas inteligentes + confianza
5. **Real-time Broadcast**: SocketIO para updates instantáneos

#### Análisis Offline
1. **Historical Analysis**: Procesamiento de grabaciones existentes
2. **Batch Processing**: Análisis eficiente de múltiples videos
3. **Pattern Recognition**: Detección de patrones temporales
4. **Report Generation**: Informes automáticos con clips

## Configuración

### Variables de Entorno
```bash
# GPU/CPU selection
GPU_DEVICE=0  # Use 'cpu' for CPU-only processing

# Analysis parameters
FPS_ANALYZE=2  # Frames per second to analyze
ALERT_CLIP_SECONDS=30  # Duration of alert video clips

# Stream resolution (optional)
YT_COOKIE=/path/to/cookies.txt  # For restricted streams
```

### Estructura de Datos

#### Catálogo de Cámaras (`data/cameras.json`)
```json
{
  "cameras": [
    {
      "id": "gaza_001",
      "name": "Gaza City Center",
      "zone": "Gaza",
      "country": "Palestine",
      "coordinates": [31.5017, 34.4668],
      "stream_url": "https://youtube.com/watch?v=example",
      "backup_urls": ["http://backup.stream"],
      "status": "active",
      "risk_level": "high"
    }
  ]
}
```

#### Zonas de Conflicto (`data/conflict_zones.geojson`)
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Gaza Strip",
        "risk_level": "critical",
        "conflict_type": "armed_conflict"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[34.2, 31.2], [34.6, 31.2], [34.6, 31.6], [34.2, 31.6], [34.2, 31.2]]]
      }
    }
  ]
}
```

## API Endpoints

### Monitoreo en Tiempo Real
```javascript
// Iniciar monitoreo
POST /api/cams/start-monitoring
{
  "camera_ids": ["gaza_001", "ukraine_002"],
  "detection_types": ["violence", "weapon", "fire"],
  "alert_threshold": 0.7
}

// Obtener estado del sistema
GET /api/cams/system-status
{
  "status": "monitoring",
  "cameras_active": 5,
  "alerts_today": 12,
  "last_detection": "2024-01-15T10:30:00Z"
}

// Stream de alertas en tiempo real (SocketIO)
socket.on('cctv_alert', function(data) {
  console.log('Nueva alerta:', data.alert_type, data.confidence);
});
```

### Análisis Histórico
```javascript
// Analizar grabación histórica
POST /api/cams/analyze-historical
{
  "camera_id": "gaza_001",
  "start_time": "2024-01-15T00:00:00Z",
  "end_time": "2024-01-15T23:59:59Z",
  "detection_types": ["all"]
}

// Obtener resultados
GET /api/cams/analysis-results/{analysis_id}
{
  "status": "completed",
  "detections": [
    {
      "timestamp": 1640,
      "type": "violence",
      "confidence": 0.85,
      "bbox": [100, 150, 200, 300],
      "description": "Disturbio detectado con alta confianza"
    }
  ]
}
```

### Gestión de Cámaras
```javascript
// Listar cámaras disponibles
GET /api/cams/cameras
{
  "cameras": [...],
  "total": 25,
  "active": 20
}

// Agregar nueva cámara
POST /api/cams/cameras
{
  "name": "Nueva Cámara",
  "stream_url": "https://...",
  "coordinates": [lat, lon],
  "zone": "Zona de Conflicto"
}
```

## Instalación de Dependencias

### Instalación Completa
```bash
# Instalar todas las dependencias del sistema CCTV
pip install -r requirements_cctv.txt

# Verificar instalación de OpenCV
python -c "import cv2; print(f'OpenCV {cv2.__version__} instalado correctamente')"

# Verificar YOLO
python -c "from ultralytics import YOLO; print('YOLO disponible')"
```

### Instalación Manual por Componentes
```bash
# Computer Vision
pip install opencv-python opencv-contrib-python

# IA y Machine Learning
pip install torch torchvision ultralytics

# Procesamiento de video
pip install ffmpeg-python yt-dlp

# Comunicación en tiempo real
pip install flask-socketio

# Procesamiento en segundo plano
pip install celery[redis]

# Utilidades geoespaciales
pip install geopandas shapely pillow
```

### Dependencias del Sistema

#### FFmpeg (requerido)
```bash
# Windows (Chocolatey)
choco install ffmpeg

# Windows (manual)
# Descargar desde https://ffmpeg.org/download.html
# Agregar al PATH del sistema

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

#### Redis (para procesamiento en segundo plano)
```bash
# Docker (recomendado)
docker run -d -p 6379:6379 --name redis redis:alpine

# Windows
# Descargar desde https://redis.io/download

# Linux
sudo apt install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

## Uso de la Interfaz Web

### 1. Mapa de Cámaras (`/cctv`)
- **Vista de mapa**: Ubicación geográfica de todas las cámaras
- **Estado en tiempo real**: Indicadores de estado y actividad
- **Filtros**: Por zona, tipo de riesgo, estado
- **Panel de control**: Iniciar/detener monitoreo masivo

### 2. Vista en Vivo (`/cctv/live`)
- **Streams múltiples**: Hasta 9 cámaras simultáneas
- **Detecciones overlaid**: Bounding boxes en tiempo real
- **Panel de alertas**: Lista de alertas recientes
- **Grabación manual**: Botones de grabación por cámara

### 3. Revisión de Grabaciones (`/cctv/review`)
- **Timeline interactivo**: Navegación temporal con marcadores
- **Análisis retrospectivo**: Subida y análisis de videos
- **Exportación**: PDF reports, video clips, datos JSON
- **Filtros avanzados**: Por tipo de detección, confianza, tiempo

## Configuración Avanzada

### Optimización de Rendimiento
```python
# config en __init__.py o app_BUENA.py
cctv_config = {
    'gpu_device': 0,  # GPU ID o 'cpu'
    'fps_analyze': 1,  # Reducir para mejor performance
    'max_concurrent_streams': 4,  # Limitar streams simultáneos
    'detection_confidence': 0.6,  # Umbral de confianza
    'alert_cooldown': 30,  # Segundos entre alertas similares
}
```

### Reglas de Alertas Personalizadas
```python
# En alerts.py - configuración de reglas
ALERT_RULES = {
    'violence': {
        'confidence_threshold': 0.7,
        'min_duration': 3,  # segundos
        'cooldown': 60,
        'priority': 'high'
    },
    'weapon': {
        'confidence_threshold': 0.8,
        'min_duration': 1,
        'cooldown': 30,
        'priority': 'critical'
    },
    'crowd': {
        'confidence_threshold': 0.6,
        'min_duration': 10,
        'cooldown': 300,
        'priority': 'medium'
    }
}
```

## Troubleshooting

### Problemas Comunes

#### 1. Error de importación OpenCV
```bash
# Reinstalar OpenCV
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python==4.8.1.78 opencv-contrib-python==4.8.1.78
```

#### 2. CUDA/GPU no detectada
```bash
# Verificar PyTorch con CUDA
python -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}')"

# Instalar versión específica de PyTorch con CUDA
pip install torch==2.0.0+cu118 torchvision==0.15.0+cu118 -f https://download.pytorch.org/whl/cu118/torch_stable.html
```

#### 3. Streams no se resuelven
```bash
# Actualizar yt-dlp
pip install --upgrade yt-dlp

# Verificar conectividad
python -c "import yt_dlp; ydl = yt_dlp.YoutubeDL(); print('yt-dlp OK')"
```

#### 4. Redis no conecta
```bash
# Verificar estado de Redis
redis-cli ping

# Reiniciar Redis
sudo systemctl restart redis  # Linux
brew services restart redis   # macOS
```

### Logs y Debugging
```python
# Habilitar logs detallados
import logging
logging.getLogger('cams').setLevel(logging.DEBUG)

# Verificar estado del sistema
cctv_system = CCTVSystem()
status = cctv_system.get_system_status()
print(f"Estado: {status}")
```

## Integración con RiskMap

El sistema CCTV se integra automáticamente con la aplicación principal RiskMap:

1. **Inicialización automática** en `app_BUENA.py`
2. **Rutas registradas** en el sistema de navegación
3. **APIs disponibles** bajo `/api/cams/`
4. **Dashboard integrado** con métricas CCTV
5. **Alertas unificadas** con el sistema de notificaciones

### Ejemplo de Uso Completo
```python
# En app_BUENA.py - el sistema se inicializa automáticamente
app = RiskMapUnifiedApplication()

# El sistema CCTV estará disponible si las dependencias están instaladas
if app.cctv_system:
    print("✅ Sistema CCTV activo y listo")
    
    # Iniciar monitoreo automático de zonas de alto riesgo
    app.cctv_system.start_monitoring_high_risk_zones()
else:
    print("⚠️  Sistema CCTV no disponible - verificar dependencias")
```

## Contribuir

Para contribuir al desarrollo del sistema CCTV:

1. **Fork** el repositorio
2. **Instalar** todas las dependencias: `pip install -r requirements_cctv.txt`
3. **Ejecutar tests**: `python -m pytest tests/test_cctv.py`
4. **Crear branch** para nuevas características
5. **Submit PR** con descripción detallada

### Áreas de Mejora
- [ ] Soporte para más tipos de streams (RTSP, WebRTC)
- [ ] Modelos YOLO especializados por región
- [ ] Integración con sistemas de alerta gubernamentales
- [ ] Análisis de audio para detección de disparos/explosiones
- [ ] Dashboard 3D para visualización geoespacial avanzada
