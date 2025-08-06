#!/usr/bin/env python3
"""
Script rápido para verificar configuración
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

def test_config():
    """Probar configuración"""
    try:
        from app_BUENA import RiskMapUnifiedApplication
        
        app = RiskMapUnifiedApplication()
        
        print("🔧 Configuración actual:")
        print(f"   auto_geocoding: {app.config.get('auto_geocoding', False)}")
        print(f"   auto_translation: {app.config.get('auto_translation', False)}")
        print(f"   geocoding_interval_hours: {app.config.get('geocoding_interval_hours', 'NO_CONFIG')}")
        print(f"   translation_interval_hours: {app.config.get('translation_interval_hours', 'NO_CONFIG')}")
        
        if app.config.get('auto_geocoding', False) and app.config.get('auto_translation', False):
            print("✅ Configuración automática activada correctamente")
            return True
        else:
            print("❌ Configuración automática NO activada")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_config()
