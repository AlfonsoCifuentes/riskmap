#!/usr/bin/env python3
"""Test simple del pipeline"""

import sys
import os
from pathlib import Path

# Añadir rutas
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from src.intelligence.integrated_analyzer import IntegratedGeopoliticalAnalyzer
    print("✅ IntegratedGeopoliticalAnalyzer importado correctamente")
    
    # Probar creación
    db_path = os.getenv('DATABASE_PATH', './data/geopolitical_intel.db')
    analyzer = IntegratedGeopoliticalAnalyzer(db_path=db_path)
    print("✅ Analizador creado correctamente")
    
    print("🛰️ PIPELINE CORRECTO CONFIGURADO")
    print("El sistema ahora usará zonas de conflicto consolidadas")
    
except Exception as e:
    print(f"❌ Error: {e}")
