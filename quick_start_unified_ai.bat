@echo off
echo ================================================================
echo 🚀 INICIANDO SISTEMA RISKMAP CON IA AVANZADA
echo ================================================================
echo 🧠 BERT + 🤖 Groq + 📊 Dashboard Unificado
echo Puerto: 5003
echo ================================================================
echo.

echo 📦 Verificando dependencias...
python -c "import torch, transformers, groq, flask" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias. Instalando...
    pip install -r requirements_ai.txt
    if errorlevel 1 (
        echo ❌ Error instalando dependencias
        pause
        exit /b 1
    )
) else (
    echo ✅ Dependencias verificadas
)

echo.
echo 🔑 Verificando API Key de Groq...
if not exist .env (
    echo ❌ Archivo .env no encontrado
    echo Por favor crea un archivo .env con tu GROQ_API_KEY
    pause
    exit /b 1
)

findstr /C:"GROQ_API_KEY" .env >nul
if errorlevel 1 (
    echo ❌ GROQ_API_KEY no encontrada en .env
    echo Por favor agrega tu GROQ_API_KEY al archivo .env
    pause
    exit /b 1
) else (
    echo ✅ API Key de Groq configurada
)

echo.
echo 🧠 Iniciando servidor con BERT + Groq...
echo ⏳ Esto puede tomar unos minutos para cargar BERT...
echo.
echo 📱 URLs que estarán disponibles:
echo    🌐 Dashboard Principal: http://127.0.0.1:5003
echo    🧠 API BERT: http://127.0.0.1:5003/api/analyze-importance  
echo    🤖 API Groq: http://127.0.0.1:5003/api/generate-ai-analysis
echo    📊 Estadísticas: http://127.0.0.1:5003/api/dashboard/stats
echo.
echo ================================================================
echo 🎯 Presiona Ctrl+C para detener el servidor
echo ================================================================
echo.

python app_bert_fixed.py

echo.
echo 👋 Servidor detenido
pause
