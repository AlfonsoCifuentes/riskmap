#!/usr/bin/env python3
"""
Script de instalación automática para el Sistema de Análisis Geopolítico
"""

import subprocess
import sys
import os
from pathlib import Path

def install_package(package):
    """Instalar un paquete con manejo de errores"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando {package}: {e}")
        return False

def main():
    """Instalación completa del sistema"""
    print("🚀 Instalando Sistema de Análisis Geopolítico")
    print("=" * 50)
    
    # Verificar Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"❌ Python 3.8+ requerido. Versión actual: {python_version.major}.{python_version.minor}")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Librerías principales
    print("\n📦 Instalando librerías principales...")
    core_packages = [
        "torch>=2.1.0",
        "torchvision>=0.16.0",
        "transformers>=4.36.0",
        "peft>=0.7.0",
        "datasets>=2.14.0",
        "accelerate>=0.24.0",
        "bitsandbytes>=0.41.0"  # Para quantización
    ]
    
    for package in core_packages:
        if not install_package(package):
            print(f"⚠️ Fallo instalando {package}, continuando...")
    
    # Análisis de datos
    print("\n📊 Instalando librerías de análisis...")
    analysis_packages = [
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "plotly>=5.15.0"
    ]
    
    for package in analysis_packages:
        install_package(package)
    
    # Computer Vision
    print("\n👁️ Instalando librerías de visión...")
    cv_packages = [
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0", 
        "imagehash>=4.3.1",
        "ultralytics>=8.0.0",  # YOLOv8
        "timm>=0.9.0"
    ]
    
    for package in cv_packages:
        install_package(package)
    
    # Web scraping
    print("\n🌐 Instalando librerías web...")
    web_packages = [
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "selenium>=4.15.0",
        "feedparser>=6.0.10",
        "newspaper3k>=0.2.8"
    ]
    
    for package in web_packages:
        install_package(package)
    
    # Utilidades adicionales
    print("\n🔧 Instalando utilidades...")
    util_packages = [
        "jupyter>=1.0.0",
        "nbconvert>=7.0.0",
        "geopy>=2.3.0",
        "python-dateutil>=2.8.0",
        "tqdm>=4.65.0"
    ]
    
    for package in util_packages:
        install_package(package)
    
    # Crear directorios
    print("\n📁 Creando estructura de directorios...")
    project_root = Path(__file__).parent
    
    directories = [
        project_root / "data",
        project_root / "data" / "image_cache",
        project_root / "models" / "trained",
        project_root / "logs",
        project_root / "output"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}")
    
    # Verificar CUDA
    print("\n🔥 Verificando soporte GPU...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA disponible - GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️ CUDA no disponible - se usará CPU (más lento)")
    except ImportError:
        print("❌ PyTorch no instalado correctamente")
    
    # Instrucciones adicionales
    print("\n" + "=" * 50)
    print("✅ INSTALACIÓN COMPLETADA")
    print("=" * 50)
    
    print("\n📋 Próximos pasos:")
    print("1. Descargar ChromeDriver:")
    print("   https://chromedriver.chromium.org")
    print("   Añadir al PATH del sistema")
    
    print("\n2. Verificar base de datos:")
    print("   Asegurar que geopolitical_intel.db existe en data/")
    
    print("\n3. Ejecutar sistema:")
    print("   python geopolitical_system.py --mode ingestion")
    
    print("\n4. Ejecutar pipeline completo:")
    print("   python geopolitical_system.py --mode full")
    
    print("\n📖 Ver documentación completa en:")
    print("   SISTEMA_COMPLETO.md")
    
    return True

if __name__ == "__main__":
    main()
