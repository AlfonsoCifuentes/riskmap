#!/bin/bash

echo "================================================================"
echo "🚀 INICIANDO SISTEMA RISKMAP CON IA AVANZADA"
echo "================================================================"
echo "🧠 BERT + 🤖 Groq + 📊 Dashboard Unificado"
echo "Puerto: 5003"
echo "================================================================"
echo ""

echo "📦 Verificando dependencias..."
python3 -c "import torch, transformers, groq, flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Faltan dependencias. Instalando..."
    pip3 install -r requirements_ai.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error instalando dependencias"
        exit 1
    fi
else
    echo "✅ Dependencias verificadas"
fi

echo ""
echo "🔑 Verificando API Key de Groq..."
if [ ! -f .env ]; then
    echo "❌ Archivo .env no encontrado"
    echo "Por favor crea un archivo .env con tu GROQ_API_KEY"
    exit 1
fi

if ! grep -q "GROQ_API_KEY" .env; then
    echo "❌ GROQ_API_KEY no encontrada en .env"
    echo "Por favor agrega tu GROQ_API_KEY al archivo .env"
    exit 1
else
    echo "✅ API Key de Groq configurada"
fi

echo ""
echo "🧠 Iniciando servidor con BERT + Groq..."
echo "⏳ Esto puede tomar unos minutos para cargar BERT..."
echo ""
echo "📱 URLs que estarán disponibles:"
echo "   🌐 Dashboard Principal: http://127.0.0.1:5003"
echo "   🧠 API BERT: http://127.0.0.1:5003/api/analyze-importance"
echo "   🤖 API Groq: http://127.0.0.1:5003/api/generate-ai-analysis"
echo "   📊 Estadísticas: http://127.0.0.1:5003/api/dashboard/stats"
echo ""
echo "================================================================"
echo "🎯 Presiona Ctrl+C para detener el servidor"
echo "================================================================"
echo ""

python3 app_bert_fixed.py

echo ""
echo "👋 Servidor detenido"
