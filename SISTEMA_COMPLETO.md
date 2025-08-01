# Sistema Completo de Análisis Geopolítico con IA

## 🎯 Descripción General

Este es un sistema completo de inteligencia artificial para el análisis de riesgo geopolítico en noticias. Utiliza técnicas avanzadas de NLP, computer vision y machine learning para clasificar automáticamente el nivel de riesgo de conflictos geopolíticos, identificar temas, ubicaciones y calcular factores de importancia.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
Sistema de Análisis Geopolítico
├── 📡 Ingesta de Datos (data_ingestion.py)
│   ├── RSS feeds de fuentes internacionales
│   ├── Web scraping para contenido completo
│   ├── Extracción de imágenes
│   └── Almacenamiento en BD
│
├── 🏷️ Etiquetado Automático (auto_labeler.py)
│   ├── Análisis de texto con patrones geopolíticos
│   ├── Integración con GDELT/ACLED
│   ├── Clasificación automática de riesgo
│   └── Creación de datasets de entrenamiento
│
├── 🤖 Modelo de IA (ai_training_bert_lora_geopolitical_intelligence.ipynb)
│   ├── BERT fine-tuned con LoRA
│   ├── Multi-task learning (riesgo, tema, ubicación)
│   ├── Entrenamiento eficiente con GPU
│   └── Métricas de evaluación
│
├── 🔮 Motor de Inferencia (inference_engine.py)
│   ├── Predicciones en tiempo real
│   ├── Análisis de imágenes con YOLO
│   ├── Cálculo de factor de importancia
│   └── Sistema de alertas automáticas
│
└── 🎛️ Orchestador Principal (geopolitical_system.py)
    ├── Pipeline automatizado completo
    ├── Modo monitoreo continuo
    ├── Gestión de dependencias
    └── Logging centralizado
```

## 🚀 Instalación y Configuración

### Requisitos del Sistema

- **Python**: 3.8 o superior
- **RAM**: 8GB mínimo (16GB recomendado)
- **GPU**: Opcional pero recomendada (NVIDIA con CUDA)
- **Espacio**: 10GB mínimo
- **Internet**: Para descargar modelos y RSS feeds

### Instalación Rápida

1. **Clonar o descargar el proyecto:**
```bash
cd E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap
```

2. **Instalar dependencias:**
```bash
pip install torch torchvision transformers peft datasets
pip install pandas numpy scikit-learn matplotlib seaborn
pip install requests beautifulsoup4 selenium feedparser
pip install opencv-python Pillow ultralytics
pip install jupyter nbconvert
```

3. **Configurar ChromeDriver para Selenium:**
   - Descargar ChromeDriver desde https://chromedriver.chromium.org
   - Añadir al PATH del sistema

4. **Verificar instalación:**
```bash
python geopolitical_system.py --mode ingestion
```

## 📊 Uso del Sistema

### Modo Automático Completo

```bash
# Ejecutar pipeline completo (recomendado para primera vez)
python geopolitical_system.py --mode full

# Ejecutar sin re-entrenar modelo
python geopolitical_system.py --mode full --skip-training
```

### Modos Individuales

```bash
# Solo ingesta de datos
python geopolitical_system.py --mode ingestion

# Solo etiquetado automático
python geopolitical_system.py --mode labeling

# Solo entrenamiento
python geopolitical_system.py --mode training

# Solo análisis de inferencia
python geopolitical_system.py --mode inference
```

### Modo Monitoreo Continuo

```bash
# Monitoreo cada 6 horas (por defecto)
python geopolitical_system.py --mode monitor

# Monitoreo cada 2 horas
python geopolitical_system.py --mode monitor --monitor-interval 2
```

## 🔧 Configuración Avanzada

### Base de Datos

El sistema utiliza dos bases de datos SQLite:

- **`geopolitical_intel.db`**: Base de datos original (debe existir)
- **`trained_analysis.db`**: Base de datos de análisis (se crea automáticamente)

### Fuentes RSS

El sistema incluye fuentes premium como:
- Reuters, BBC, Associated Press
- Foreign Affairs, International Crisis Group
- Al Jazeera, Financial Times
- Fuentes regionales especializadas

Puedes añadir más fuentes editando `data_ingestion.py`.

### Configuración del Modelo

En el notebook `ai_training_bert_lora_geopolitical_intelligence.ipynb`:

```python
class Config:
    # Modelo base
    BERT_MODEL = "bert-base-multilingual-cased"
    
    # Parámetros de entrenamiento
    MAX_LENGTH = 512
    BATCH_SIZE = 8  # Ajustar según GPU
    LEARNING_RATE = 2e-5
    NUM_EPOCHS = 5
    
    # LoRA configuración
    LORA_R = 16
    LORA_ALPHA = 32
    LORA_DROPOUT = 0.1
```

## 📈 Características Principales

### 1. Clasificación Multi-tarea

- **Nivel de Riesgo**: Escala 1-5 (Muy Bajo → Muy Alto)
- **Clasificación de Tópicos**: 
  - Conflicto armado
  - Tensión diplomática
  - Sanciones económicas
  - Disturbios civiles
  - Terrorismo
  - Cooperación diplomática
  - Noticias rutinarias
- **Detección de Ubicación**: Identificación geográfica automática

### 2. Factor de Importancia Avanzado

Combina múltiples factores:
- **Recencia** (35%): Noticias recientes = mayor importancia
- **Nivel de riesgo** (25%): Riesgo alto = mayor importancia  
- **Ubicación** (20%): Regiones conflictivas = mayor importancia
- **Credibilidad fuente** (10%): Fuentes confiables = mayor peso
- **Calidad contenido** (5%): Artículos completos = mejor análisis
- **Indicadores visuales** (5%): Imágenes de riesgo = factor adicional

### 3. Análisis Visual

- **Detección de objetos**: Vehículos militares, armas, fuego
- **Análisis de color**: Detección de rojos (peligro) y grises (humo)
- **Score visual**: Contribuye al factor de importancia

### 4. Sistema de Alertas

- **Alerta Crítica**: Riesgo nivel 5 con alta confianza
- **Escalamiento**: Riesgo nivel 4 con alta importancia
- **Noticia en Desarrollo**: Riesgo medio muy reciente

## 📊 Métricas y Evaluación

### Rendimiento del Modelo

El sistema reporta automáticamente:
- **Accuracy**: Precisión general del modelo
- **Precision/Recall/F1**: Métricas detalladas por clase
- **AUC**: Área bajo la curva ROC
- **Matriz de confusión**: Visualización de errores

### Ejemplo de Métricas Típicas

```
Clasificación de Riesgo:
• Accuracy: 0.847
• Precision: 0.851  
• Recall: 0.847
• F1-Score: 0.842
• AUC: 0.924

Clasificación de Tópicos:
• Accuracy: 0.782
• Precision: 0.789
• Recall: 0.782
• F1-Score: 0.779
```

## 🔍 Ejemplos de Uso

### Análisis Individual

```python
from inference_engine import GeopoliticalInferenceEngine

# Crear motor
engine = GeopoliticalInferenceEngine(
    model_path="models/trained/best_model.pt",
    db_path="data/trained_analysis.db"
)

# Analizar artículo específico
result = engine.analyze_article(article_id=123)

print(f"Riesgo: {result['predicted_risk_level']}/5")
print(f"Tópico: {result['predicted_topic']}")
print(f"Importancia: {result['importance_score']:.3f}")
```

### Dashboard en Tiempo Real

```python
# Obtener datos para dashboard
dashboard = engine.get_dashboard_data()

print(f"Artículos analizados (24h): {dashboard['stats']['total_articles']}")
print(f"Riesgo promedio: {dashboard['stats']['avg_risk']:.2f}")
print(f"Alertas activas: {len(dashboard['active_alerts'])}")
```

## 🚨 Sistema de Alertas

### Tipos de Alertas

1. **🚨 ALERTA CRÍTICA**
   - Riesgo nivel 5 con confianza >80%
   - Notificación inmediata
   - Requiere atención urgente

2. **⚠️ ESCALAMIENTO**
   - Riesgo nivel 4 con importancia >80%
   - Situación en desarrollo
   - Monitoreo frecuente recomendado

3. **📢 NOTICIA EN DESARROLLO**
   - Riesgo medio pero muy reciente (<2 horas)
   - Potencial evolución

### Configuración de Alertas

Las alertas se almacenan automáticamente en la tabla `geopolitical_alerts` con:
- Timestamp de creación
- Nivel de severidad
- Mensaje descriptivo
- Estado de acknowledgment

## 📁 Estructura de Archivos

```
riskmap/
├── 📄 geopolitical_system.py          # Orchestador principal
├── 📄 data_ingestion.py               # Ingesta de datos
├── 📄 auto_labeler.py                 # Etiquetado automático
├── 📄 inference_engine.py             # Motor de inferencia
├── 📄 examine_db.py                   # Utilidad para examinar BD
├── 📄 SISTEMA_COMPLETO.md             # Esta documentación
│
├── 📁 data/
│   ├── 💾 geopolitical_intel.db       # BD original
│   ├── 💾 trained_analysis.db         # BD de análisis
│   └── 📁 image_cache/                # Cache de imágenes
│
├── 📁 models/trained/
│   ├── 📓 ai_training_bert_lora_geopolitical_intelligence.ipynb
│   ├── 🤖 best_model.pt               # Modelo entrenado
│   ├── 📄 evaluation_metrics.json     # Métricas del modelo
│   └── 📁 deployment_package/         # Paquete para producción
│
├── 📁 logs/                           # Logs del sistema
├── 📁 output/                         # Resultados y reportes
└── 📁 requirements.txt                # Dependencias
```

## 🔧 Solución de Problemas

### Problemas Comunes

1. **Error de memoria GPU**
   ```
   Solución: Reducir BATCH_SIZE en la configuración
   ```

2. **ChromeDriver no encontrado**
   ```
   Solución: Instalar ChromeDriver y añadir al PATH
   ```

3. **Timeout en RSS feeds**
   ```
   Solución: Verificar conexión a internet y firewall
   ```

4. **Base de datos bloqueada**
   ```
   Solución: Cerrar otras conexiones a la BD
   ```

### Logs y Debugging

Todos los logs se guardan en:
- `geopolitical_system.log`: Log principal
- `data_ingestion.log`: Log de ingesta
- `advanced_orchestrator.log`: Log de procesamiento

Usa los logs para diagnosticar problemas:
```bash
tail -f geopolitical_system.log
```

## 🚀 Despliegue en Producción

### Servidor Dedicado

1. **Configurar servidor con GPU** (recomendado)
2. **Instalar dependencias del sistema**
3. **Configurar base de datos** (PostgreSQL para producción)
4. **Configurar monitoreo** (Prometheus + Grafana)
5. **Configurar alertas** (Slack, Email, etc.)

### Docker (Opcional)

```dockerfile
FROM pytorch/pytorch:2.1-cuda11.8-devel

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "geopolitical_system.py", "--mode", "monitor"]
```

### Escalabilidad

- **Múltiples instancias**: Para mayor throughput
- **Load balancer**: Distribuir carga de análisis
- **Cache Redis**: Para resultados frecuentes
- **API REST**: Para integración con otros sistemas

## 📚 API y Integración

### API REST (Futuro)

```python
# Ejemplo de endpoints planificados
POST /api/analyze
GET /api/alerts
GET /api/dashboard
GET /api/articles/{id}/analysis
```

### Webhooks

```python
# Configurar webhooks para alertas críticas
WEBHOOK_URL = "https://hooks.slack.com/services/..."
```

## 🔄 Mantenimiento

### Actualizaciones Regulares

- **Reentrenar modelo**: Cada 1-2 semanas con nuevos datos
- **Actualizar fuentes RSS**: Verificar feeds activos
- **Limpiar cache de imágenes**: Eliminar archivos antiguos
- **Optimizar base de datos**: VACUUM y REINDEX periódicos

### Monitoreo de Rendimiento

```python
# Métricas a monitorear
- Tiempo de procesamiento por artículo
- Accuracy del modelo en nuevos datos
- Tasa de acierto de alertas
- Uso de recursos (CPU, GPU, memoria)
```

## 🤝 Contribución y Desarrollo

### Extensiones Posibles

1. **Análisis de sentimiento avanzado**
2. **Detección de fake news**
3. **Análisis de tendencias temporales**
4. **Integración con redes sociales**
5. **Análisis de video/audio**
6. **Predicción de escalamiento**

### Estructura de Desarrollo

```bash
# Crear rama para nueva feature
git checkout -b feature/nueva-funcionalidad

# Desarrollar y probar
python -m pytest tests/

# Commit y push
git commit -m "Añadir nueva funcionalidad"
git push origin feature/nueva-funcionalidad
```

## 📞 Soporte

Para preguntas o problemas:

1. **Revisar logs** en `/logs/`
2. **Consultar documentación** en código
3. **Verificar configuración** en archivos config
4. **Probar componentes** individualmente

## 🎉 Conclusión

Este sistema representa una solución completa y avanzada para el análisis automatizado de riesgo geopolítico. Combina:

- **IA Moderna**: BERT con LoRA para eficiencia
- **Múltiples Fuentes**: RSS, web scraping, análisis visual
- **Automatización Completa**: Pipeline end-to-end
- **Escalabilidad**: Diseño modular y extensible
- **Productividad**: Factor de importancia inteligente

El sistema está diseñado para ser tanto una herramienta de investigación como una solución de producción para análisis de inteligencia geopolítica en tiempo real.

---

**Versión**: 1.0  
**Fecha**: Agosto 2025  
**Autor**: Sistema de IA Geopolítica  
**Licencia**: Uso interno y educativo
