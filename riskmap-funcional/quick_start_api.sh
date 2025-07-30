#!/bin/bash
# Quick start for Riskmap API (Linux/Mac)
cd "$(dirname "$0")"
pip install -r requirements.txt
pip install -r requirements-dev.txt
uvicorn src.api.rest_status:app --reload --port 8000
