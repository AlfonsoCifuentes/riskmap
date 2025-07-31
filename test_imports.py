#!/usr/bin/env python3
"""
Script de prueba para verificar todos los imports de la aplicación
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔍 Verificando imports...")

try:
    from src.orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator
    print("✅ GeopoliticalIntelligenceOrchestrator - OK")
except Exception as e:
    print(f"❌ GeopoliticalIntelligenceOrchestrator - FAILED: {e}")

try:
    from src.orchestration.task_scheduler import TaskScheduler
    print("✅ TaskScheduler - OK")
except Exception as e:
    print(f"❌ TaskScheduler - FAILED: {e}")

try:
    from src.analytics.enhanced_historical_orchestrator import EnhancedHistoricalOrchestrator
    print("✅ EnhancedHistoricalOrchestrator - OK")
except Exception as e:
    print(f"❌ EnhancedHistoricalOrchestrator - FAILED: {e}")

try:
    from src.visualization.historical_dashboard import HistoricalDashboard
    print("✅ HistoricalDashboard - OK")
except Exception as e:
    print(f"❌ HistoricalDashboard - FAILED: {e}")

try:
    from src.visualization.multivariate_dashboard import MultivariateRelationshipDashboard
    print("✅ MultivariateRelationshipDashboard - OK")
except Exception as e:
    print(f"❌ MultivariateRelationshipDashboard - FAILED: {e}")

try:
    from src.api.rest_status import create_api_blueprint
    print("✅ create_api_blueprint - OK")
except Exception as e:
    print(f"❌ create_api_blueprint - FAILED: {e}")

try:
    from src.utils.config import logger
    print("✅ logger from config - OK")
except Exception as e:
    print(f"❌ logger from config - FAILED: {e}")

print("\n🎯 Resultado: Si todos los imports están OK, el problema está en otro lugar.")
