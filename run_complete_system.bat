@echo off
echo ============================================
echo DASHBOARD GEOPOLITICO - BERT + GROQ AI
echo ============================================
echo.
echo Iniciando servidor con analisis completo...
echo - BERT para analisis de sentimiento
echo - Groq AI para analisis geopolitico
echo - Dashboard web en puerto 5003
echo.

cd /d "e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap"

echo Verificando dependencias...
python -m pip install -q flask flask-cors transformers torch python-dotenv groq

echo.
echo Iniciando servidor...
echo URL: http://localhost:5003
echo Endpoints disponibles:
echo   - GET  /                                    Dashboard principal
echo   - GET  /api/dashboard/stats                 Estadisticas
echo   - GET  /api/articles                        Articulos
echo   - POST /api/analyze-importance              Analisis BERT
echo   - POST /api/generate-ai-analysis            Analisis Groq AI
echo   - POST /api/generate-ai-analysis-v2         Analisis Groq AI v2
echo   - GET  /api/test-bert                       Test del modelo BERT
echo.

python app_bert_fixed.py

pause
