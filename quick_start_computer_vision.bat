@echo off
echo 🤖 SISTEMA DE COMPUTER VISION - RISKMAP
echo =======================================

echo 📋 Verificando sistema...
python -c "import cv2, numpy, PIL, sklearn; print('✅ Dependencias CV instaladas')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias de Computer Vision
    echo 💡 Ejecutando instalación...
    pip install opencv-python pillow scikit-learn numpy
)

echo 🔍 Probando integración de Computer Vision...
python test_computer_vision.py

echo.
echo 🚀 Iniciando dashboard con Computer Vision...
python app_BUENA.py

pause
