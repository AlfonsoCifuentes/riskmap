#!/usr/bin/env python3
"""
Script para inicializar la base de datos con el esquema correcto
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import Config, DatabaseManager

def init_database():
    """Inicializar la base de datos con todas las tablas necesarias"""
    print("🔧 Inicializando base de datos...")
    
    # Cargar configuración
    config = Config()
    
    # Inicializar gestor de base de datos
    db_manager = DatabaseManager(config)
    
    print(f"✅ Base de datos inicializada en: {config.database.path}")
    print("✅ Todas las tablas creadas correctamente")

if __name__ == "__main__":
    init_database()
