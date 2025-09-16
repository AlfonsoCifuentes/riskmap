# Enhanced Geopolitical Intelligence System

## Sistema Profesional de Monitoreo de Conflictos con IA Avanzada

Este sistema implementa un monitoreo profesional de conflictos activos utilizando inteligencia artificial avanzada, incluyendo modelos de redes neuronales, computer vision, y análisis predictivo para proporcionar inteligencia geopolítica en tiempo real.

## 🚀 Características Principales

### 🧠 Inteligencia Artificial Avanzada
- **NLP Multilingüe**: Procesamiento de texto en múltiples idiomas usando XLM-RoBERTa
- **Reconocimiento de Entidades (NER)**: Extracción automática de actores, países, organizaciones
- **Clasificación de Conflictos**: Análisis automático de tipos e intensidad de conflictos
- **Análisis de Sentimiento**: Evaluación del tono y sentimiento en tiempo real

### 👁️ Computer Vision
- **YOLOv8**: Detección de objetos en imágenes satelitales y de noticias
- **Análisis de Daños**: Evaluación automática de destrucción e infraestructura
- **Detección Militar**: Identificación de vehículos y equipamiento militar
- **Análisis de Multitudes**: Detección de manifestaciones y desplazamientos

### 📈 Análisis Predictivo
- **LSTM Networks**: Predicción de evolución de conflictos (30-90 días)
- **Prophet**: Análisis de tendencias temporales y estacionalidad
- **Detección de Anomalías**: Identificación de patrones inusuales
- **Clustering**: Agrupación de eventos y actores similares

### 🚨 Sistema de Alertas Tempranas
- **Scoring Multicriterio**: Evaluación automática de niveles de amenaza
- **Alertas en Tiempo Real**: Notificaciones inmediatas por múltiples canales
- **Configuración Personalizable**: Filtros por región, tipo y gravedad
- **Trazabilidad Completa**: Registro auditable de todas las alertas

### 📊 Reportes Ejecutivos Automáticos
- **Generación con IA**: Resúmenes automáticos usando modelos de lenguaje
- **Múltiples Formatos**: HTML, PDF, JSON
- **Visualizaciones Dinámicas**: Gráficos interactivos con Plotly
- **Plantillas Personalizables**: Sistema de templates con Jinja2

## 🏗️ Arquitectura del Sistema

```
Enhanced Geopolitical Intelligence System
├── AI Models Layer
│   ├── Multilingual NER (XLM-RoBERTa)
│   ├── Conflict Classifier (BART, RoBERTa)
│   ├── Computer Vision (YOLOv8, SAM)
│   └── Predictive Models (LSTM, Prophet)
├── Analytics Layer
│   ├── Trend Prediction
│   ├── Anomaly Detection
│   ├── Pattern Analysis
│   └── Sentiment Analysis
├── Alert System
│   ├── Threat Scoring
│   ├── Alert Generation
│   ├── Notification Manager
│   └── Real-time Monitor
├── Reporting Layer
│   ├── Executive Reports
│   ├── Visualization Engine
│   └── Template System
└── API Layer
    ├── REST Endpoints
    ├── Real-time WebSockets
    └── File Upload/Download
```

## 🛠️ Instalación y Configuración

### Requisitos del Sistema
- Python 3.8+
- 8GB RAM mínimo (16GB recomendado)
- GPU compatible con CUDA (opcional, mejora rendimiento)
- 10GB espacio en disco

### Instalación Rápida

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd riskmap
```

2. **Instalar dependencias mejoradas**
```bash
pip install -r requirements_enhanced.txt
```

3. **Configurar el sistema**
```bash
python start_enhanced_system.py setup
```

4. **Ejecutar tests del sistema**
```bash
python start_enhanced_system.py test
```

5. **Iniciar el sistema completo**
```bash
python start_enhanced_system.py full
```

### Configuración Avanzada

#### Variables de Entorno
```bash
# API Keys
export OPENAI_API_KEY="your-openai-key"
export GROQ_API_KEY="your-groq-key"
export HUGGINGFACE_TOKEN="your-hf-token"

# Notification Settings
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
```

#### Configuración de Base de Datos
El sistema utiliza SQLite por defecto, pero puede configurarse para PostgreSQL:

```yaml
database:
  type: "postgresql"
  host: "localhost"
  port: 5432
  name: "geopolitical_intel"
  user: "username"
  password: "password"
```

## 🚀 Uso del Sistema

### Inicio Rápido

#### 1. Análisis Completo
```bash
python start_enhanced_system.py analyze
```

#### 2. Servidor API
```bash
python start_enhanced_system.py api --host 0.0.0.0 --port 8000
```

#### 3. Monitoreo en Tiempo Real
```bash
python start_enhanced_system.py monitor
```

### API Endpoints

#### Análisis de Texto
```bash
curl -X POST "http://localhost:8000/analysis/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Escalating conflict in Eastern Europe with military buildup",
    "language": "en",
    "analysis_types": ["entities", "classification", "sentiment"]
  }'
```

#### Análisis de Imágenes
```bash
curl -X POST "http://localhost:8000/analysis/image" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "https://example.com/satellite-image.jpg",
    "analysis_type": "comprehensive"
  }'
```

#### Predicciones de Tendencias
```bash
curl "http://localhost:8000/predictions/trends?days=30&confidence_interval=0.8"
```

#### Detección de Anomalías
```bash
curl "http://localhost:8000/anomalies/detect?method=isolation_forest&days=7"
```

#### Generación de Reportes
```bash
curl -X POST "http://localhost:8000/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "daily",
    "format_types": ["html", "pdf"],
    "period_days": 7
  }'
```

### Interfaz Web

Accede a la documentación interactiva en:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Componentes Técnicos

### Modelos de IA Utilizados

#### NLP Models
- **XLM-RoBERTa**: Reconocimiento de entidades multilingüe
- **BART**: Clasificación de conflictos y resumen
- **Twitter-XLM-RoBERTa**: Análisis de sentimiento multilingüe

#### Computer Vision
- **YOLOv8**: Detección de objetos en tiempo real
- **Segment Anything**: Segmentación avanzada de imágenes

#### Predictive Models
- **LSTM**: Redes neuronales para predicción temporal
- **Prophet**: Análisis de series temporales con estacionalidad
- **Isolation Forest**: Detección de anomalías
- **DBSCAN**: Clustering de eventos y patrones

### Pipelines de Procesamiento

#### 1. Ingesta de Datos
```python
# RSS Sources → Text Processing → Entity Extraction → Classification
rss_collector.collect_all_sources()
→ text_analyzer.process_content()
→ ner_processor.extract_entities()
→ conflict_classifier.classify_conflict_type()
```

#### 2. Análisis Visual
```python
# Image Input → Object Detection → Damage Assessment → Risk Scoring
vision_analyzer.analyze_image()
→ yolo_detection()
→ damage_analysis()
→ threat_assessment()
```

#### 3. Predicción de Tendencias
```python
# Historical Data → Feature Engineering → Model Training → Predictions
trend_predictor.prepare_time_series_data()
→ train_lstm_model()
→ train_prophet_model()
→ predict_future_trends()
```

## 📊 Métricas y Monitoreo

### Métricas del Sistema
- **Throughput**: Artículos procesados por minuto
- **Latencia**: Tiempo de respuesta de análisis
- **Precisión**: Accuracy de clasificaciones
- **Cobertura**: Porcentaje de fuentes monitoreadas

### Alertas de Sistema
- **Disponibilidad**: Uptime de componentes críticos
- **Rendimiento**: Degradación de performance
- **Errores**: Fallos en procesamiento
- **Capacidad**: Uso de recursos del sistema

### Dashboard de Monitoreo
```bash
# Acceder al dashboard de métricas
http://localhost:8000/system/status
```

## 🔒 Seguridad y Privacidad

### Medidas de Seguridad
- **Autenticación**: API keys y tokens de acceso
- **Encriptación**: HTTPS para todas las comunicaciones
- **Validación**: Sanitización de inputs
- **Auditoría**: Logs completos de actividad

### Privacidad de Datos
- **Anonimización**: Eliminación de datos personales
- **Retención**: Políticas de eliminación automática
- **Acceso**: Control granular de permisos
- **Cumplimiento**: GDPR y regulaciones locales

## 🚀 Casos de Uso

### 1. Análisis de Crisis Humanitaria
```python
# Detectar crisis emergentes
crisis_events = orchestrator.run_comprehensive_analysis(
    include_vision_analysis=True,
    focus_regions=['middle_east', 'africa']
)
```

### 2. Monitoreo de Fronteras
```python
# Análisis de imágenes satelitales
border_analysis = vision_analyzer.analyze_satellite_imagery(
    satellite_image_url,
    coordinates=(lat, lon)
)
```

### 3. Predicción de Escaladas
```python
# Predicción de conflictos
predictions = trend_predictor.predict_future_trends(
    periods=90,
    confidence_interval=0.95
)
```

### 4. Alertas Tempranas
```python
# Configurar alertas personalizadas
alert_config = {
    'severity_threshold': 'high',
    'regions': ['ukraine', 'syria'],
    'notification_channels': ['email', 'webhook']
}
```

## 📈 Roadmap y Mejoras Futuras

### Versión 2.1 (Q2 2024)
- [ ] Integración con APIs de redes sociales
- [ ] Análisis de audio y video
- [ ] Modelos de lenguaje más grandes (GPT-4)
- [ ] Clustering geoespacial avanzado

### Versión 2.2 (Q3 2024)
- [ ] Interfaz web completa
- [ ] Análisis de blockchain y criptomonedas
- [ ] Integración con sistemas GIS
- [ ] APIs de terceros (Google Earth Engine)

### Versión 3.0 (Q4 2024)
- [ ] Arquitectura distribuida (Kubernetes)
- [ ] Machine Learning federado
- [ ] Análisis de deep fakes
- [ ] Integración con IoT y sensores

## 🤝 Contribución

### Desarrollo
1. Fork el repositorio
2. Crear branch de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Reportar Issues
- Usar templates de GitHub Issues
- Incluir logs y contexto
- Especificar versión del sistema
- Proporcionar pasos para reproducir

## 📞 Soporte

### Documentación
- **API Docs**: http://localhost:8000/docs
- **Technical Docs**: `/docs` directory
- **Examples**: `/examples` directory

### Contacto
- **Email**: support@geopolitical-intel.com
- **Slack**: #geopolitical-intel
- **GitHub Issues**: Para bugs y features

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- **Hugging Face**: Por los modelos de transformers
- **Ultralytics**: Por YOLOv8
- **Facebook Research**: Por Prophet y BART
- **OpenAI**: Por GPT y tecnologías de IA
- **Comunidad Open Source**: Por las librerías utilizadas

---

**Enhanced Geopolitical Intelligence System v2.0**  
*Monitoreo profesional de conflictos con IA avanzada*

Para más información, consulta la documentación completa en `/docs` o visita http://localhost:8000/docs después de iniciar el sistema.