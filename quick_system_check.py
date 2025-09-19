#!/usr/bin/env python3
"""
VERIFICACIÓN RÁPIDA DEL SISTEMA RISKMAP
======================================

Script de verificación rápida para comprobar que todo esté funcionando
correctamente después de las correcciones aplicadas.

Uso: python quick_system_check.py

Autor: GitHub Copilot
Fecha: 2025
"""

import os
import sqlite3
from datetime import datetime

def quick_check():
    """Verificación rápida del sistema"""
    print("⚡ VERIFICACIÓN RÁPIDA DEL SISTEMA RISKMAP")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = []
    
    # 1. Base de datos
    print("🗄️ Base de datos...")
    try:
        if os.path.exists("data/geopolitical_intel.db"):
            conn = sqlite3.connect("data/geopolitical_intel.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE geopolitical_relevance = 1")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"   ✅ {count} artículos geopolíticos disponibles")
            checks.append(True)
        else:
            print(f"   ❌ Base de datos no encontrada")
            checks.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        checks.append(False)
    
    # 2. Aplicación principal
    print("🚀 Aplicación principal...")
    if os.path.exists("RISKMAP.py"):
        print(f"   ✅ RISKMAP.py encontrado")
        checks.append(True)
    else:
        print(f"   ❌ RISKMAP.py no encontrado")
        checks.append(False)
    
    # 3. Templates
    print("📄 Templates...")
    template_count = 0
    if os.path.exists("src/web/templates/"):
        templates = ['dashboard_BUENO.html', 'conflict_monitoring.html', 'satellite_analysis.html']
        for template in templates:
            if os.path.exists(f"src/web/templates/{template}"):
                template_count += 1
        print(f"   ✅ {template_count}/3 templates principales encontrados")
        checks.append(template_count >= 2)
    else:
        print(f"   ❌ Directorio templates no encontrado")
        checks.append(False)
    
    # 4. Configuración
    print("⚙️ Configuración...")
    if os.path.exists(".env"):
        print(f"   ✅ Archivo .env encontrado")
        checks.append(True)
    else:
        print(f"   ⚠️  Archivo .env no encontrado (puede usar variables por defecto)")
        checks.append(True)  # No crítico
    
    # Resumen
    passed = sum(checks)
    total = len(checks)
    
    print()
    print("=" * 60)
    if passed == total:
        print("🎉 SISTEMA OK - Todo funcionando correctamente")
        print("   Puedes ejecutar: python RISKMAP.py")
        print("   O usar el lanzador: python start_riskmap.py")
        print("   Y acceder a: http://localhost:5001")
    elif passed >= total - 1:
        print("⚠️  SISTEMA MAYORMENTE OK - Pequeños problemas menores")
        print("   El sistema debería funcionar, pero revisa las advertencias")
    else:
        print("❌ PROBLEMAS DETECTADOS - Revisar errores arriba")
    
    print(f"   Estado: {passed}/{total} verificaciones pasaron")
    print()

if __name__ == "__main__":
    quick_check()