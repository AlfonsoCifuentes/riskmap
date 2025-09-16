@echo off
REM Quick start for Riskmap API (Windows)
cd /d %~dp0
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
uvicorn src.api.rest_status:app --reload --port 8000
