#!/bin/bash
# Quick start for Riskmap Dashboard (Linux/Mac)
cd "$(dirname "$0")"
pip install -r requirements.txt
pip install -r requirements-dev.txt
uvicorn src.dashboard.run_dashboard:app --reload --port 8080
