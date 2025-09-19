#!/usr/bin/env python3
"""
Verificación Final de Dependencias - RiskMap AI
============================================

Este script verifica que todas las dependencias críticas estén instaladas
y funcionando correctamente.

Funcionalidades:
- Verificar dependencias de NLP (sentence-transformers, transformers)
- Verificar dependencias de visión (ultralytics, torch, cv2)
- Verificar dependencias de tracking (motpy, filterpy)
- Verificar dependencias estándar (email.mime.text)
- Verificar parches aplicados (yolo_permanent_patch)

Uso:
    python final_dependency_check.py
"""

import sys
import importlib
import os

def check_dependency(module_name, friendly_name=None, optional=False):
    """
    Verificar si un módulo está disponible
    """
    if friendly_name is None:
        friendly_name = module_name
    
    try:
        importlib.import_module(module_name)
        status = "✅"
        message = f"{friendly_name} - INSTALADO"
        success = True
    except ImportError as e:
        status = "⚠️" if optional else "❌"
        message = f"{friendly_name} - NO DISPONIBLE"
        if not optional:
            message += f" (ERROR: {str(e)[:100]}...)"
        success = False
    except Exception as e:
        status = "⚠️" if optional else "❌"
        message = f"{friendly_name} - ERROR AL VERIFICAR: {str(e)[:100]}..."
        success = False
    
    print(f"{status} {message}")
    return success

def check_yolo_patch():
    """
    Verificar que el parche permanente de YOLO esté aplicado
    """
    patch_file = "yolo_permanent_patch.py"
    if os.path.exists(patch_file):
        print("✅ Parche permanente YOLO - APLICADO")
        return True
    else:
        print("❌ Parche permanente YOLO - NO ENCONTRADO")
        return False

def main():
    print("🔍 VERIFICACIÓN FINAL DE DEPENDENCIAS - RiskMap AI")
    print("=" * 60)
    
    dependencies_ok = True
    
    print("\n📦 DEPENDENCIAS CRÍTICAS:")
    critical_deps = [
        ("flask", "Flask"),
        ("sqlite3", "SQLite3"),
        ("requests", "Requests"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
    ]
    
    for module, name in critical_deps:
        if not check_dependency(module, name):
            dependencies_ok = False
    
    print("\n🧠 DEPENDENCIAS NLP:")
    nlp_deps = [
        ("sentence_transformers", "Sentence Transformers"),
        ("transformers", "HuggingFace Transformers"),
        ("torch", "PyTorch"),
    ]
    
    for module, name in nlp_deps:
        if not check_dependency(module, name):
            dependencies_ok = False
    
    print("\n👁️ DEPENDENCIAS VISIÓN:")
    vision_deps = [
        ("ultralytics", "YOLO (Ultralytics)"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
    ]
    
    for module, name in vision_deps:
        check_dependency(module, name, optional=True)
    
    print("\n🎯 DEPENDENCIAS TRACKING:")
    tracking_deps = [
        ("motpy", "MOTpy (Object Tracking)"),
        ("filterpy", "FilterPy (Kalman Filters)"),
    ]
    
    for module, name in tracking_deps:
        check_dependency(module, name, optional=True)
    
    print("\n📧 DEPENDENCIAS ESTÁNDAR:")
    standard_deps = [
        ("email.mime.text", "MIMEText (Email)"),
        ("json", "JSON"),
        ("datetime", "DateTime"),
    ]
    
    for module, name in standard_deps:
        check_dependency(module, name)
    
    print("\n🔧 PARCHES APLICADOS:")
    check_yolo_patch()
    
    print("\n" + "=" * 60)
    if dependencies_ok:
        print("✅ VERIFICACIÓN COMPLETADA - TODAS LAS DEPENDENCIAS CRÍTICAS ESTÁN OK")
        print("📝 Notas:")
        print("   - Dependencias de visión y tracking son opcionales")
        print("   - El sistema funciona con fallbacks cuando no están disponibles")
        print("   - Parche permanente YOLO aplicado para compatibilidad PyTorch")
    else:
        print("❌ VERIFICACIÓN FALLIDA - INSTALAR DEPENDENCIAS FALTANTES")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())