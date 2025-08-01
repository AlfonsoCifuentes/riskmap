#!/usr/bin/env python3
"""
Script para verificar todas las rutas registradas en Flask
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def check_routes():
    """Lista todas las rutas registradas en la aplicación Flask"""
    print("Rutas registradas en Flask:")
    print("-" * 50)
    
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        print(f"{rule.rule:<40} {methods}")
    
    print("-" * 50)
    print(f"Total de rutas: {len(list(app.url_map.iter_rules()))}")

if __name__ == "__main__":
    check_routes()
