# Guía para Configurar Modelos de IA Gratuitos

## Resumen de Modelos Disponibles

Tu sistema ya está configurado para usar múltiples modelos de IA con prioridad automática. Aquí te explico cómo obtener API keys gratuitas para cada servicio:

## 1. DeepSeek (RECOMENDADO - MUY BUENO Y GRATUITO)

**¿Por qué DeepSeek?**
- Modelo muy potente, comparable a GPT-4
- Tiene cuota gratuita generosa
- API compatible con OpenAI
- Excelente para análisis geopolítico

**Cómo obtener la API key:**
1. Ve a: https://platform.deepseek.com/
2. Regístrate con email
3. Ve a "API Keys" en el dashboard
4. Crea una nueva API key
5. Copia la key que empieza con `sk-`

**Configuración:**
```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxx
```

## 2. Groq (RÁPIDO Y GRATUITO)

**¿Por qué Groq?**
- Extremadamente rápido (más que OpenAI)
- Usa modelos Llama de Meta
- Cuota gratuita diaria
- Perfecto para análisis en tiempo real

**Cómo obtener la API key:**
1. Ve a: https://console.groq.com/
2. Regístrate con Google/GitHub
3. Ve a "API Keys"
4. Crea una nueva key
5. Copia la key que empieza con `gsk_`

**Configuración:**
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx
```

## 3. HuggingFace (MODELOS OPEN SOURCE)

**¿Por qué HuggingFace?**
- Acceso a cientos de modelos
- Completamente gratuito
- Modelos especializados disponibles
- Buena opción de respaldo

**Cómo obtener la API key:**
1. Ve a: https://huggingface.co/
2. Regístrate
3. Ve a Settings → Access Tokens
4. Crea un nuevo token
5. Copia el token que empieza con `hf_`

**Configuración:**
```env
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxx
```

## 4. Configuración del Archivo .env

Edita tu archivo `.env` y agrega las API keys que obtengas:

```env
# Prioridad de modelos (puedes cambiar el orden)
AI_MODEL_PRIORITY=deepseek,groq,huggingface,openai,local

# API Keys
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxx
```

## 5. Modelos Locales con Ollama (Opcional)

Si quieres modelos 100% locales sin internet:

**Instalar Ollama:**
1. Descarga de: https://ollama.ai/
2. Instala en tu sistema
3. Ejecuta: `ollama pull llama2` o `ollama pull codellama`

El sistema detectará automáticamente Ollama si está instalado.

## 6. Recomendaciones por Caso de Uso

**Para análisis geopolítico diario:**
- **Mejor opción**: DeepSeek (calidad + gratuito)
- **Más rápido**: Groq (tiempo real)
- **Más modelos**: HuggingFace (variedad)

**Para desarrollo/testing:**
- Groq es ideal por su velocidad
- HuggingFace para experimentar con diferentes modelos

**Para producción:**
- DeepSeek como principal
- Groq como backup
- HuggingFace como tercer nivel
- Fallback local siempre funciona

## 7. Verificación

Después de configurar las API keys, ejecuta:

```bash
python test_ai_models.py
```

Esto te mostrará qué modelos están funcionando y cuál está siendo usado para generar el análisis.

## 8. Costos y Límites

- **DeepSeek**: $0.14/1M tokens input, $0.28/1M tokens output (cuota gratuita inicial)
- **Groq**: Gratuito con límites por minuto/día
- **HuggingFace**: Gratuito (con límites de rate)
- **Ollama**: Gratuito, solo usa recursos locales

## 9. Troubleshooting

**Si un modelo falla:**
- El sistema automáticamente usa el siguiente en la lista
- Revisa que la API key esté correcta en `.env`
- Verifica que tengas cuota disponible
- Consulta los logs del dashboard para detalles

**Logs útiles:**
```bash
# Ver qué modelo se está usando
curl http://localhost:5000/api/ai_analysis
```

El sistema está diseñado para ser robusto: siempre tendrás análisis disponible, incluso si todos los modelos fallan.
