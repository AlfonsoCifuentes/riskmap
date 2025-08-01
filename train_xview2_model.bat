@echo off
echo 🛰️ Iniciando entrenamiento del modelo xView2...
echo.

REM Cambiar al directorio del proyecto
cd /d "e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap"

REM Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call .venv\Scripts\activate.bat
) else (
    echo Usando Python del sistema...
)

REM Instalar dependencias necesarias
echo Instalando dependencias...
python -m pip install tensorflow opencv-python scikit-learn matplotlib pandas tqdm

REM Verificar que existen imágenes satelitales
if not exist "data\satellite_images\*.png" (
    echo ⚠️  No se encontraron imágenes satelitales en data\satellite_images\
    echo Generando imágenes de muestra...
    python test_satellite_system.py
)

REM Ejecutar entrenamiento
echo.
echo 🚀 Iniciando entrenamiento...
python train_xview2.py --epochs 25 --batch-size 16 --use-satellite --verbose

echo.
echo ✅ Entrenamiento completado!
echo Los resultados están en models\xview2_damage\
pause
