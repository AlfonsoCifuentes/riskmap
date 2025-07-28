#!/usr/bin/env python3
"""
Script para probar el dashboard y verificar que carga datos
"""
import sys
import os
from pathlib import Path
import requests
import time
import threading

# Configurar el entorno
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

def test_endpoints():
    """Probar los endpoints del dashboard"""
    base_url = "http://127.0.0.1:5000"
    
    endpoints = [
        "/api/dashboard/stats",
        "/api/articles",
        "/api/events", 
        "/api/risk-analysis",
        "/api/heatmap"
    ]
    
    print("🧪 Probando endpoints del dashboard...")
    time.sleep(3)  # Esperar que el servidor se inicie
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: OK")
                
                # Mostrar algunos datos
                if endpoint == "/api/articles" and isinstance(data, list):
                    print(f"   📰 {len(data)} artículos cargados")
                    if data:
                        print(f"   📄 Último: {data[0]['title'][:50]}...")
                
                elif endpoint == "/api/events" and isinstance(data, list):
                    print(f"   🔔 {len(data)} eventos cargados")
                    if data:
                        print(f"   📄 Último: {data[0]['title'][:50]}...")
                
                elif endpoint == "/api/dashboard/stats":
                    stats = data.get('stats', {})
                    print(f"   📊 Artículos: {stats.get('total_articles', 0)}")
                    print(f"   ⚠️  Alto riesgo: {stats.get('high_risk_events', 0)}")
                
                elif endpoint == "/api/risk-analysis":
                    top_article = data.get('top_risk_article', {})
                    print(f"   🚨 Artículo de mayor riesgo: {top_article.get('title', 'N/A')[:50]}...")
                
                elif endpoint == "/api/heatmap" and isinstance(data, list):
                    print(f"   🗺️  {len(data)} puntos en el mapa")
                    
            else:
                print(f"❌ {endpoint}: Error {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: No se puede conectar")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")
    
    print("\n🌐 Dashboard disponible en: http://127.0.0.1:5000")

def run_server():
    """Ejecutar el servidor Flask"""
    try:
        from src.dashboard.app_modern import app
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Error al ejecutar el servidor: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando test del dashboard...")
    
    # Ejecutar servidor en un hilo separado
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Probar endpoints
    test_endpoints()
    
    print("\n✅ Test completado. El servidor sigue ejecutándose...")
    print("🔄 Para detener: Ctrl+C")
    
    try:
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido")