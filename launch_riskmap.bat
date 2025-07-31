@echo off
echo ========================================
echo   RiskMap Unified - BERT + Groq AI
echo ========================================
echo.
echo Iniciando sistema unificado...
echo Puerto: http://127.0.0.1:5003
echo.

cd /d "%~dp0"
python app_bert_fixed.py

echo.
echo Sistema detenido. Presiona cualquier tecla para salir...
pause > nul
