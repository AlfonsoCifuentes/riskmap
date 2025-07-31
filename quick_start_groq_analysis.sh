#!/bin/bash
# Script de inicio rápido para el análisis geopolítico con Groq

echo "====================================================="
echo "🧠 STRATOSIGHT - ANÁLISIS GEOPOLITICO CON GROQ"
echo "====================================================="
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python no está instalado"
        echo "💡 Instala Python desde: https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "✅ Python detectado: $($PYTHON_CMD --version)"
echo ""

# Instalar dependencias de IA
echo "📦 Instalando dependencias de IA..."
$PYTHON_CMD -m pip install -r requirements_ai.txt
if [ $? -ne 0 ]; then
    echo "⚠️  Error instalando dependencias, intentando con pip básico..."
    $PYTHON_CMD -m pip install groq flask flask-cors transformers torch
fi
echo ""

# Verificar si la API key está configurada
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  GROQ_API_KEY no está configurada"
    echo ""
    echo "🔑 Para obtener una API key gratuita:"
    echo "   1. Visita: https://console.groq.com/"
    echo "   2. Crea una cuenta gratuita"
    echo "   3. Genera una API key"
    echo "   4. Configúrala con: export GROQ_API_KEY='tu_api_key'"
    echo ""
    read -p "❓ ¿Quieres configurar la API key ahora? (s/n): " response
    if [[ "$response" =~ ^[Ss]$ ]]; then
        echo ""
        read -p "🔑 Introduce tu API key de Groq: " groq_key
        export GROQ_API_KEY="$groq_key"
        echo "✅ API key configurada para esta sesión"
    else
        echo "ℹ️  El sistema funcionará en modo fallback sin Groq"
    fi
else
    echo "✅ GROQ_API_KEY configurada: ${GROQ_API_KEY:0:20}..."
fi
echo ""

# Ejecutar prueba opcional
read -p "🧪 ¿Quieres ejecutar una prueba rápida? (s/n): " test_response
if [[ "$test_response" =~ ^[Ss]$ ]]; then
    echo ""
    echo "🧪 Ejecutando prueba..."
    $PYTHON_CMD test_groq_analysis.py
    echo ""
    read -p "⏸️  Presiona Enter para continuar con el dashboard..."
fi

# Iniciar el dashboard
echo "🚀 Iniciando dashboard con análisis geopolítico..."
echo ""
echo "🌐 Dashboard disponible en: http://localhost:5003"
echo "🧠 Endpoint de análisis: http://localhost:5003/api/generate-ai-analysis"
echo "🧪 Test BERT: http://localhost:5003/api/test-bert"
echo ""
echo "⏹️  Para detener el servidor, presiona Ctrl+C"
echo "===================================================="
echo ""

$PYTHON_CMD app_bert_fixed.py

echo ""
echo "👋 Dashboard detenido"
