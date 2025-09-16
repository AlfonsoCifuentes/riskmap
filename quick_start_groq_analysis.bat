@echo off
REM Script de inicio rápido para el análisis geopolítico con Groq
echo =====================================================
echo 🧠 STRATOSIGHT - ANÁLISIS GEOPOLITICO CON GROQ
echo =====================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en el PATH
    echo 💡 Descarga Python desde: https://python.org
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Instalar dependencias de IA
echo 📦 Instalando dependencias de IA...
pip install -r requirements_ai.txt
if errorlevel 1 (
    echo ⚠️  Error instalando dependencias, intentando con pip básico...
    pip install groq flask flask-cors transformers torch
)
echo.

REM Verificar si la API key está configurada
if "%GROQ_API_KEY%"=="" (
    echo ⚠️  GROQ_API_KEY no está configurada
    echo.
    echo 🔑 Para obtener una API key gratuita:
    echo    1. Visita: https://console.groq.com/
    echo    2. Crea una cuenta gratuita
    echo    3. Genera una API key
    echo    4. Configúrala con: set GROQ_API_KEY=tu_api_key
    echo.
    echo ❓ ¿Quieres configurar la API key ahora? (s/n)
    set /p response="> "
    if /i "%response%"=="s" (
        echo.
        echo 🔑 Introduce tu API key de Groq:
        set /p groq_key="> "
        set GROQ_API_KEY=%groq_key%
        echo ✅ API key configurada para esta sesión
    ) else (
        echo ℹ️  El sistema funcionará en modo fallback sin Groq
    )
) else (
    echo ✅ GROQ_API_KEY configurada: %GROQ_API_KEY:~0,20%...
)
echo.

REM Ejecutar prueba opcional
echo 🧪 ¿Quieres ejecutar una prueba rápida? (s/n)
set /p test_response="> "
if /i "%test_response%"=="s" (
    echo.
    echo 🧪 Ejecutando prueba...
    python test_groq_analysis.py
    echo.
    echo ⏸️  Presiona cualquier tecla para continuar con el dashboard...
    pause >nul
)

REM Iniciar el dashboard
echo 🚀 Iniciando dashboard con análisis geopolítico...
echo.
echo 🌐 Dashboard disponible en: http://localhost:5003
echo 🧠 Endpoint de análisis: http://localhost:5003/api/generate-ai-analysis
echo 🧪 Test BERT: http://localhost:5003/api/test-bert
echo.
echo ⏹️  Para detener el servidor, presiona Ctrl+C
echo ====================================================
echo.

python app_bert_fixed.py

echo.
echo 👋 Dashboard detenido
pause
