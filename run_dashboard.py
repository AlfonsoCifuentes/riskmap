#!/usr/bin/env python3
"""
Script para ejecutar el dashboard y verificar que funciona
"""
import sys
import os
from pathlib import Path
import time
import requests

# Configurar el entorno
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

def test_api():
    """Probar que la API funciona"""
    print("🧪 Probando API del dashboard...")
    time.sleep(2)  # Esperar que el servidor se inicie
    
    try:
        # Probar endpoint de test
        response = requests.get("http://127.0.0.1:5000/api/test", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API funcionando: {data['message']}")
            print(f"📊 Artículos en DB: {data['database']['articles']}")
            print(f"🔔 Eventos en DB: {data['database']['events']}")
        else:
            print(f"❌ API error: {response.status_code}")
            
        # Probar endpoint de artículos
        response = requests.get("http://127.0.0.1:5000/api/articles?limit=3", timeout=5)
        if response.status_code == 200:
            articles = response.json()
            print(f"✅ Artículos cargados: {len(articles)}")
            if articles:
                print(f"📰 Último: {articles[0]['title'][:50]}...")
        else:
            print(f"❌ Artículos error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando Dashboard de Riskmap...")
    
    try:
        # Importar y ejecutar la aplicación
        from src.dashboard.app_modern import app
        
        # Ejecutar test en un hilo separado
        import threading
        test_thread = threading.Thread(target=test_api, daemon=True)
        test_thread.start()
        
        # Ejecutar el servidor
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)