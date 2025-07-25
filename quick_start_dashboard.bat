@echo off
REM Quick start for Riskmap Dashboard (Windows)
cd /d %~dp0
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
uvicorn src.dashboard.run_dashboard:app --reload --port 8080
