"""
Script de Instalación Simplificado
==================================
Instala solo los paquetes esenciales paso a paso.
"""

import subprocess
import sys

def install_essential_packages():
    """Instalar solo los paquetes más importantes"""
    
    print("🚀 Instalando paquetes esenciales...")
    
    # Lista de paquetes prioritarios
    essential_packages = [
        "torch",
        "transformers", 
        "pandas",
        "numpy",
        "requests",
        "beautifulsoup4",
        "selenium",
        "feedparser",
        "opencv-python",
        "Pillow",
        "scikit-learn"
    ]
    
    success_count = 0
    
    for package in essential_packages:
        print(f"\n📦 Instalando {package}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode == 0:
                print(f"✅ {package} instalado correctamente")
                success_count += 1
            else:
                print(f"❌ Error instalando {package}:")
                print(f"   {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout instalando {package}")
        except Exception as e:
            print(f"❌ Error inesperado con {package}: {e}")
    
    print(f"\n📊 Resultado: {success_count}/{len(essential_packages)} paquetes instalados")
    
    # Verificar imports críticos
    print("\n🔍 Verificando imports críticos...")
    
    critical_imports = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("pandas", "Pandas"),
        ("requests", "Requests"),
        ("selenium", "Selenium")
    ]
    
    working_imports = 0
    
    for module_name, display_name in critical_imports:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
            working_imports += 1
        except ImportError as e:
            print(f"❌ {display_name}: {e}")
    
    print(f"\n📈 Imports funcionando: {working_imports}/{len(critical_imports)}")
    
    if working_imports >= 3:
        print("\n✅ ¡Instalación suficiente para continuar!")
        print("\n📋 Próximos pasos:")
        print("1. Ejecutar: python -c \"import torch; print('PyTorch version:', torch.__version__)\"")
        print("2. Probar ingesta: python data_ingestion.py")
        return True
    else:
        print("\n❌ Instalación insuficiente. Revisar errores arriba.")
        return False

if __name__ == "__main__":
    install_essential_packages()
