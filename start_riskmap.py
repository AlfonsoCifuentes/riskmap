#!/usr/bin/env python3
"""
LANZADOR SIMPLE PARA RISKMAP A.I.
============================

Script de lanzamiento simplificado para el sistema Riskmap A.I.

Uso: python start_riskmap.py

Autor: GitHub Copilot
Fecha: 2025
"""

import os
import sys
import subprocess
import webbrowser
import time

def launch_riskmap():
    """Lanzar el sistema Riskmap A.I."""
    print("🚀 INICIANDO RISKMAP A.I. - SISTEMA DE ANÁLISIS GEOPOLÍTICO")
    print("=" * 80)
    
    # Verificar que el archivo principal existe
    if not os.path.exists("legacy/RISKMAP.py"):
        print("❌ Error: legacy/RISKMAP.py no encontrado")
        print("   Asegúrate de estar en el directorio correcto")
        return False
    
    print("✅ Archivo legacy encontrado: legacy/RISKMAP.py")
    print()
    print("🔧 Iniciando sistema completo...")
    print("   - Ingesta automática de noticias")
    print("   - Procesamiento NLP en tiempo real")
    print("   - Análisis histórico multivariable")
    print("   - Dashboards interactivos")
    print("   - API REST completa")
    print()
    print("🌐 El sistema estará disponible en:")
    print("   📱 Interfaz Principal: http://localhost:5001")
    print("   📊 Dashboard Histórico: http://localhost:5001/dashboard")
    print("   🔗 Análisis Multivariable: http://localhost:5001/multivariate")
    print("   🔌 API REST: http://localhost:5001/api/v1/docs")
    print()
    print("⏳ Iniciando servidor...")
    print("   (Esto puede tomar unos segundos)")
    print()
    print("💡 CONSEJOS:")
    print("   - Usa Ctrl+C para detener el servidor")
    print("   - El navegador se abrirá automáticamente en unos segundos")
    print("   - Todos los procesos funcionan automáticamente")
    print()
    
    # Abrir navegador después de unos segundos
    def open_browser():
        time.sleep(5)  # Esperar 5 segundos para que el servidor inicie
        try:
            webbrowser.open('http://localhost:5001')
            print("🌐 Navegador abierto automáticamente")
        except Exception as e:
            print(f"⚠️  No se pudo abrir el navegador automáticamente: {e}")
            print("   Accede manualmente a: http://localhost:5001")
    
    # Iniciar el navegador en un hilo separado
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Ejecutar RISKMAP.py
    try:
        result = subprocess.run([sys.executable, "legacy/RISKMAP.py"], check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido por el usuario")
        return True
    except Exception as e:
        print(f"❌ Error ejecutando legacy/RISKMAP.py: {e}")
        return False

if __name__ == "__main__":
    print()
    success = launch_riskmap()
    print()
    if success:
        print("✅ RISKMAP A.I. ejecutado correctamente")
    else:
        print("❌ Hubo problemas ejecutando RISKMAP A.I.")
    print("=" * 80)