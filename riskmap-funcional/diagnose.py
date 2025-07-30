#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas con el dashboard
"""
import sys
import os
from pathlib import Path
import subprocess

def check_python_environment():
    """Verificar el entorno de Python"""
    print("🐍 Verificando entorno de Python...")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Current working directory: {os.getcwd()}")
    print()

def check_dependencies():
    """Verificar dependencias instaladas"""
    print("📦 Verificando dependencias...")
    required_packages = ['fastapi', 'uvicorn', 'jinja2', 'sqlite3']
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
                print(f"   ✅ {package}: {sqlite3.version}")
            else:
                __import__(package)
                print(f"   ✅ {package}: instalado")
        except ImportError:
            print(f"   ❌ {package}: NO instalado")
    print()

def check_files():
    """Verificar archivos necesarios"""
    print("📁 Verificando archivos necesarios...")
    current_dir = Path(__file__).parent
    
    files_to_check = [
        "src/dashboard/run_dashboard.py",
        "src/dashboard/templates/dashboard.html",
        "src/dashboard/static/css/modern_dashboard.css",
        "data/geopolitical_intel.db",
        "src/dashboard/i18n/en.json"
    ]
    
    for file_path in files_to_check:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - NO EXISTE")
    print()

def check_database():
    """Verificar base de datos"""
    print("🗄️  Verificando base de datos...")
    try:
        import sqlite3
        db_path = Path(__file__).parent / "data" / "geopolitical_intel.db"
        
        if not db_path.exists():
            print(f"   ❌ Base de datos no existe: {db_path}")
            return
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"   ✅ Base de datos existe con {len(tables)} tablas")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"      - {table_name}: {count} registros")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error al verificar base de datos: {e}")
    print()

def check_ports():
    """Verificar puertos disponibles"""
    print("🔌 Verificando puertos...")
    import socket
    
    ports_to_check = [8080, 8081, 8082, 8083]
    
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"   ❌ Puerto {port}: EN USO")
        else:
            print(f"   ✅ Puerto {port}: DISPONIBLE")
    print()

def test_simple_fastapi():
    """Probar una aplicación FastAPI simple"""
    print("🧪 Probando FastAPI simple...")
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "FastAPI funciona correctamente"}
        
        print("   ✅ FastAPI se puede importar y crear aplicación")
        
        # Intentar iniciar servidor en un puerto libre
        import uvicorn
        import threading
        import time
        import requests
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=8090, log_level="critical")
        
        # Iniciar servidor en un hilo separado
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Esperar un poco y probar conexión
        time.sleep(2)
        
        try:
            response = requests.get("http://127.0.0.1:8090/", timeout=5)
            if response.status_code == 200:
                print("   ✅ Servidor FastAPI funciona correctamente")
            else:
                print(f"   ❌ Servidor responde con código {response.status_code}")
        except Exception as e:
            print(f"   ❌ No se puede conectar al servidor: {e}")
            
    except Exception as e:
        print(f"   ❌ Error al probar FastAPI: {e}")
    print()

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DEL DASHBOARD RISKMAP")
    print("=" * 50)
    
    check_python_environment()
    check_dependencies()
    check_files()
    check_database()
    check_ports()
    test_simple_fastapi()
    
    print("🏁 Diagnóstico completado")
    print("💡 Si hay errores, revisa los elementos marcados con ❌")