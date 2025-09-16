#!/usr/bin/env python3
"""
fix_dependencies.py
Script para reparar dependencias problemáticas
"""

import subprocess
import sys
import os
import logging

def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✅ {description} completado")
            return True
        else:
            print(f"❌ Error en {description}:")
            print(result.stderr[:500])
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout en {description}")
        return False
    except Exception as e:
        print(f"💥 Error ejecutando {description}: {e}")
        return False

def fix_huggingface_hub():
    """Reparar problema de HuggingFace Hub"""
    print("🚑 Reparando HuggingFace Hub...")
    
    commands = [
        ("pip uninstall -y huggingface_hub transformers tokenizers", "Desinstalando versiones problemáticas"),
        ("pip install huggingface_hub==0.23.5", "Instalando HuggingFace Hub compatible"),
        ("pip install transformers==4.41.2", "Instalando Transformers compatible"),
        ("pip install tokenizers==0.19.1", "Instalando Tokenizers compatible"),
    ]
    
    success_count = 0
    for command, description in commands:
        if run_command(command, description):
            success_count += 1
    
    return success_count == len(commands)

def install_missing_packages():
    """Instalar paquetes faltantes críticos"""
    print("📦 Instalando paquetes faltantes...")
    
    packages = [
        ("spacy", "Procesamiento NLP"),
        ("python -m spacy download en_core_web_sm", "Modelo Spacy inglés"),
        ("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu", "PyTorch CPU"),
    ]
    
    for package, description in packages:
        command = f"pip install {package}" if not package.startswith(("python", "pip")) else package
        run_command(command, f"Instalando {description}")

def create_database_tables():
    """Crear tablas de base de datos faltantes"""
    print("🗄️ Creando tablas de base de datos...")
    
    script_content = '''
import sqlite3
import os

def create_missing_tables():
    """Crear tablas faltantes en la base de datos"""
    db_path = "./data/geopolitical_intel.db"
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla processed_data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT,
            source TEXT,
            published_date TEXT,
            processed_date TEXT DEFAULT CURRENT_TIMESTAMP,
            category TEXT,
            sentiment REAL,
            risk_score REAL,
            geolocation TEXT,
            language TEXT DEFAULT 'en',
            raw_data TEXT
        )
    """)
    
    # Tabla satellite_zones con columnas correctas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS satellite_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            bbox_coords TEXT,
            priority INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Tablas creadas correctamente")

if __name__ == "__main__":
    create_missing_tables()
'''
    
    with open("temp_create_tables.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    run_command("python temp_create_tables.py", "Creando tablas de base de datos")
    
    # Limpiar archivo temporal
    try:
        os.remove("temp_create_tables.py")
    except:
        pass

def main():
    """Función principal de reparación"""
    print("🚑 INICIANDO REPARACIÓN DE DEPENDENCIAS")
    print("=" * 50)
    
    success_count = 0
    total_tasks = 3
    
    # 1. Reparar HuggingFace Hub
    if fix_huggingface_hub():
        success_count += 1
    
    # 2. Instalar paquetes faltantes
    install_missing_packages()
    success_count += 1
    
    # 3. Crear tablas de base de datos
    create_database_tables()
    success_count += 1
    
    print("=" * 50)
    print(f"🏁 REPARACIÓN COMPLETADA: {success_count}/{total_tasks} tareas exitosas")
    
    if success_count == total_tasks:
        print("✅ Todas las reparaciones fueron exitosas")
        print("🚀 El sistema debería funcionar correctamente ahora")
    else:
        print("⚠️ Algunas reparaciones fallaron")
        print("🔄 Es posible que necesites ejecutar el script nuevamente")

if __name__ == "__main__":
    main()