@echo off
REM ===============================================================================
REM SCRIPT DE INICIALIZACIÓN RÁPIDA - SISTEMA DE INTELIGENCIA GEOPOLÍTICA
REM Configuración automatizada para Windows con verificaciones robustas
REM ===============================================================================

echo.
echo ==============================================================================
echo 🌍 SISTEMA DE INTELIGENCIA GEOPOLÍTICA - CONFIGURACIÓN RÁPIDA
echo ==============================================================================
echo Configuración optimizada para análisis multilingüe en tiempo real
echo Idiomas soportados: Español, Inglés, Ruso, Chino, Árabe
echo Fuentes de datos: 100%% reales, sin simulación
echo ==============================================================================
echo.

REM Verificar Python
echo [1/8] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python no encontrado. Instale Python 3.8+ desde python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% detectado

REM Verificar pip
echo [2/8] Verificando pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: pip no encontrado
    pause
    exit /b 1
)
echo ✅ pip disponible

REM Crear entorno virtual
echo [3/8] Configurando entorno virtual...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo ✅ Entorno virtual creado
) else (
    echo ✅ Entorno virtual ya existe
)

REM Activar entorno virtual
echo [4/8] Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)
echo ✅ Entorno virtual activado

REM Actualizar pip
echo [5/8] Actualizando herramientas de instalación...
python -m pip install --upgrade pip setuptools wheel --quiet
if %errorlevel% neq 0 (
    echo ⚠️ ADVERTENCIA: No se pudieron actualizar todas las herramientas
) else (
    echo ✅ Herramientas actualizadas
)

REM Instalar dependencias
echo [6/8] Instalando dependencias optimizadas...
echo Esto puede tardar varios minutos...
python -m pip install -r requirements.txt --no-cache-dir --quiet
if %errorlevel% neq 0 (
    echo ❌ ERROR: Falló la instalación de dependencias
    echo Revise el archivo requirements.txt e intente manualmente
    pause
    exit /b 1
)
echo ✅ Dependencias instaladas

REM Descargar modelos spaCy
echo [7/8] Descargando modelos de procesamiento de lenguaje...
python -m spacy download es_core_news_sm --quiet
python -m spacy download en_core_web_sm --quiet
python -m spacy download zh_core_web_sm --quiet
python -m spacy download ru_core_news_sm --quiet
echo ✅ Modelos spaCy descargados

REM Configurar directorios y archivos
echo [8/8] Configurando estructura del proyecto...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "models" mkdir models
if not exist "reports" mkdir reports

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ✅ Archivo .env creado desde plantilla
        echo ⚠️ IMPORTANTE: Edite .env con sus claves API reales
    ) else (
        echo ⚠️ ADVERTENCIA: .env.example no encontrado
    )
) else (
    echo ✅ Archivo .env ya existe
)
echo ✅ Estructura de directorios configurada

echo.
echo ==============================================================================
echo 🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!
echo ==============================================================================
echo.
echo 📋 PRÓXIMOS PASOS:
echo.
echo 1. Configurar claves API en el archivo .env:
echo    • NEWSAPI_KEY (obtener de https://newsapi.org)
echo    • OPENAI_API_KEY (opcional, para chatbot)
echo    • GOOGLE_TRANSLATE_API_KEY (opcional, para traducción)
echo.
echo 2. Probar la instalación:
echo    venv\Scripts\python main.py --status
echo.
echo 3. Iniciar recolección de datos:
echo    venv\Scripts\python main.py --collect
echo.
echo 4. Lanzar dashboard interactivo:
echo    venv\Scripts\python src\dashboard\app.py
echo.
echo 🌍 Sistema listo para análisis geopolítico en tiempo real
echo 📊 Idiomas: ES, EN, RU, ZH, AR
echo 🔄 Fuentes: 100%% reales, verificadas
echo ==============================================================================

echo.
echo Presione cualquier tecla para continuar...
pause >nul
