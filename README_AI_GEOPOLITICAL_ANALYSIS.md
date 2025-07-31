# Análisis Geopolítico con IA - Groq Integration

## 🧠 Funcionalidad

Esta nueva característica del dashboard de Stratosight genera artículos periodísticos de análisis geopolítico utilizando inteligencia artificial avanzada a través de la API de Groq.

## ✨ Características

### Análisis Periodístico Profesional
- **Estilo Humano**: El artículo se genera con un tono periodístico profesional, no como contenido de IA genérico
- **Opiniones Fundamentadas**: Incluye predicciones y análisis desde una perspectiva humilde pero informada
- **Líderes y Países Específicos**: Nombra líderes políticos reales (Putin, Xi Jinping, Biden, Zelensky, etc.)
- **Contexto Histórico**: Conecta eventos actuales con tendencias históricas

### Diseño Tipo Periódico
- **Titular Principal**: Un encabezado impactante pero veraz
- **Subtítulo Explicativo**: Complementa el titular principal
- **Diseño de 4 Columnas**: Responsive que se adapta a 3, 2 o 1 columna según el ancho de pantalla
- **Primera Letra Grande**: Como en los periódicos tradicionales
- **Colores Coherentes**: Integrados con el tema visual del dashboard

### Funcionalidades Interactivas
- **Generación Automática**: Se carga automáticamente al abrir el dashboard
- **Actualización Manual**: Botón para regenerar el análisis
- **Exportación HTML**: Descarga el artículo como archivo HTML independiente

## 🛠 Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements_ai.txt
```

### 2. Configurar API Key de Groq

Necesitas obtener una API key gratuita de [Groq](https://console.groq.com/):

**Opción A: Variable de Entorno**
```bash
# Windows PowerShell
$env:GROQ_API_KEY = "tu_api_key_aqui"

# Windows CMD
set GROQ_API_KEY=tu_api_key_aqui

# Linux/Mac
export GROQ_API_KEY="tu_api_key_aqui"
```

**Opción B: Archivo .env**
```bash
# Crear archivo .env en la raíz del proyecto
echo "GROQ_API_KEY=tu_api_key_aqui" > .env
```

### 3. Ejecutar el Dashboard

```bash
python app_bert_fixed.py
```

## 🎯 Uso

### Interfaz Web
1. Abre http://localhost:5003
2. El análisis se genera automáticamente después de 2 segundos
3. Usa el botón "Actualizar Análisis" para regenerar
4. Usa "Exportar Artículo" para descargar como HTML

### API Endpoint
```bash
# POST /api/generate-ai-analysis
curl -X POST http://localhost:5003/api/generate-ai-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "title": "Título del artículo",
        "content": "Contenido del artículo",
        "location": "Ubicación",
        "risk_level": "high"
      }
    ],
    "analysis_type": "geopolitical_journalistic",
    "language": "spanish"
  }'
```

## 📝 Estructura del Artículo Generado

### HTML Generado
```html
<div class="ai-article-content">
  <div class="ai-article-header">
    <h1 class="ai-article-title">Titular Principal</h1>
    <p class="ai-article-subtitle">Subtítulo explicativo</p>
    <div class="ai-article-meta">
      <!-- Metadatos del artículo -->
    </div>
  </div>
  <div class="ai-article-body">
    <!-- Contenido en columnas con primera letra grande -->
  </div>
  <div class="ai-article-footer">
    <!-- Información del análisis de IA -->
  </div>
</div>
```

### CSS Responsivo
- **Desktop (>1024px)**: 4 columnas
- **Tablet (768-1024px)**: 3 columnas  
- **Mobile (480-768px)**: 2 columnas
- **Móvil pequeño (<480px)**: 1 columna

## 🔧 Configuración Avanzada

### Personalizar el Prompt de Groq
Edita la función `generate_groq_geopolitical_analysis()` en `app_bert_fixed.py` para modificar el comportamiento del análisis.

### Cambiar Modelo de Groq
```python
# En la función generate_groq_geopolitical_analysis()
model="llama-3.1-70b-versatile",  # Modelo actual
# Alternativas:
# model="llama-3.1-8b-instant",   # Más rápido
# model="mixtral-8x7b-32768",     # Mayor contexto
```

### Ajustar Parámetros de Generación
```python
temperature=0.7,    # Creatividad (0.0-1.0)
max_tokens=4000,    # Longitud máxima
```

## 🚨 Resolución de Problemas

### Error: "GROQ_API_KEY no encontrada"
- Verifica que la variable de entorno esté configurada
- Reinicia el terminal después de configurar la variable
- Verifica que la API key sea válida en [Groq Console](https://console.groq.com/)

### Error: "Groq library not installed"
```bash
pip install groq>=0.4.1
```

### Análisis de Fallback
Si Groq no está disponible, el sistema automáticamente genera un artículo de ejemplo bien estructurado para demostrar la funcionalidad.

## 📊 Monitoring y Logs

El sistema registra todas las operaciones en el log:
- ✅ Análisis Groq generado exitosamente
- ⚠️ GROQ_API_KEY no encontrada - usando fallback
- ❌ Error calling Groq API - detalles del error

## 🔐 Seguridad

- **API Key**: Nunca hardcodees la API key en el código
- **Rate Limiting**: Groq tiene límites de uso gratuito
- **Error Handling**: El sistema maneja graciosamente los fallos de API

## 📚 Recursos Adicionales

- [Documentación de Groq](https://console.groq.com/docs)
- [Modelos Disponibles](https://console.groq.com/docs/models)
- [Límites de Rate](https://console.groq.com/docs/rate-limits)

---

**Nota**: Esta funcionalidad está diseñada para proporcionar análisis geopolíticos informativos y educativos. Las opiniones generadas por IA deben ser consideradas como análisis automatizado y no como asesoramiento profesional.
