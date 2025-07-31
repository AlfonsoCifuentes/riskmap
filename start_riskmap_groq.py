#!/usr/bin/env python3
"""
Script de inicio para RiskMap con Groq integrado
"""
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

def main():
    """Función principal de inicio"""
    print("🗺️ Iniciando RiskMap con Groq AI integrado...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar Groq
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key:
        print(f"✅ Groq API configurada: {groq_api_key[:10]}...")
    else:
        print("⚠️ Groq API no configurada - funcionará con análisis de respaldo")
    
    try:
        # Importar y inicializar la aplicación
        from app_moderncopia31alas945 import RiskMapUnifiedApplication
        
        print("🚀 Inicializando aplicación unificada...")
        
        app = RiskMapUnifiedApplication()
        
        print("✅ Aplicación inicializada correctamente")
        print("🌐 Iniciando servidor web...")
        
        # Iniciar la aplicación
        app.start_application()
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando aplicación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
