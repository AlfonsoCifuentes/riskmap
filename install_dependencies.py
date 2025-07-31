#!/usr/bin/env python3
"""
Script para instalar dependencias paso a paso y solucionar conflictos
"""

import subprocess
import sys
import importlib
import os

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    print(f"🐍 Versión de Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠️ Se recomienda Python 3.8 o superior")
        return False
    
    if version.major == 3 and version.minor >= 11:
        print("⚠️ Python 3.11+ puede tener problemas de compatibilidad con algunas librerías")
    
    return True

def install_package(package_name, upgrade=False):
    """Instalar un paquete individual"""
    try:
        cmd = [sys.executable, '-m', 'pip', 'install']
        if upgrade:
            cmd.append('--upgrade')
        cmd.append(package_name)
        
        print(f"📦 Instalando {package_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {package_name} instalado correctamente")
            return True
        else:
            print(f"❌ Error instalando {package_name}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error inesperado instalando {package_name}: {e}")
        return False

def install_core_dependencies():
    """Instalar dependencias básicas primero"""
    core_packages = [
        "wheel",
        "setuptools",
        "pip",
        "numpy>=1.21.0,<1.24.0",
        "pandas>=1.5.0,<2.0.0",
        "requests>=2.28.0",
        "python-dotenv>=0.19.0",
        "PyYAML>=6.0",
        "pydantic>=1.10.0,<2.0.0"
    ]
    
    print("🔧 Instalando dependencias básicas...")
    
    for package in core_packages:
        if not install_package(package, upgrade=True):
            print(f"⚠️ Falló instalación de {package}, continuando...")
    
    print("✅ Dependencias básicas instaladas")

def install_web_framework():
    """Instalar Flask y dependencias web"""
    web_packages = [
        "Flask>=2.2.0,<3.0.0",
        "Flask-Cors>=3.0.0",
        "werkzeug>=2.2.0,<3.0.0",
        "Jinja2>=3.1.0",
        "Flask-Babel>=2.0.0"
    ]
    
    print("🌐 Instalando framework web...")
    
    for package in web_packages:
        install_package(package)
    
    print("✅ Framework web instalado")

def install_ml_packages():
    """Instalar paquetes de machine learning"""
    ml_packages = [
        "scikit-learn>=1.1.0",
        "scipy>=1.9.0",
        "statsmodels>=0.13.0"
    ]
    
    print("🤖 Instalando paquetes de ML...")
    
    for package in ml_packages:
        install_package(package)
    
    print("✅ Paquetes de ML instalados")

def install_visualization():
    """Instalar paquetes de visualización"""
    viz_packages = [
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "plotly>=5.10.0"
    ]
    
    print("📊 Instalando paquetes de visualización...")
    
    for package in viz_packages:
        install_package(package)
    
    # Dash por separado debido a posibles conflictos
    print("📊 Instalando Dash...")
    install_package("dash>=2.6.0,<2.15.0")
    install_package("dash-bootstrap-components>=1.2.0")
    
    print("✅ Paquetes de visualización instalados")

def install_optional_packages():
    """Instalar paquetes opcionales"""
    optional_packages = [
        "transformers>=4.21.0,<5.0.0",
        "aiohttp>=3.8.0",
        "schedule>=1.2.0",
        "feedparser>=6.0.0",
        "APScheduler>=3.9.0",
        "tqdm>=4.64.0",
        "psutil>=5.9.0",
        "python-dateutil>=2.8.0",
        "pytz>=2022.1"
    ]
    
    print("📋 Instalando paquetes opcionales...")
    
    for package in optional_packages:
        if not install_package(package):
            print(f"⚠️ Paquete opcional {package} falló, continuando...")
    
    print("✅ Instalación de paquetes opcionales completada")

def test_imports():
    """Probar importaciones críticas"""
    critical_modules = [
        'flask',
        'pandas',
        'numpy',
        'requests',
        'plotly',
        'dash'
    ]
    
    print("🧪 Probando importaciones críticas...")
    
    failed_imports = []
    
    for module in critical_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️ Módulos que fallaron: {', '.join(failed_imports)}")
        return False
    else:
        print("\n🎉 Todas las importaciones críticas exitosas!")
        return True

def main():
    """Función principal de instalación"""
    print("🚀 INSTALADOR DE DEPENDENCIAS RISKMAP")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        print("❌ Versión de Python no compatible")
        return False
    
    try:
        # Actualizar pip
        print("📦 Actualizando pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      capture_output=True)
        
        # Instalar por fases
        install_core_dependencies()
        install_web_framework()
        install_ml_packages()
        install_visualization()
        install_optional_packages()
        
        # Probar importaciones
        if test_imports():
            print("\n🎉 ¡Instalación completada exitosamente!")
            print("Ahora puedes ejecutar la aplicación RiskMap")
            return True
        else:
            print("\n⚠️ Instalación completada con algunos errores")
            print("La aplicación puede funcionar parcialmente")
            return False
            
    except Exception as e:
        print(f"\n❌ Error durante la instalación: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 SOLUCIONES SUGERIDAS:")
        print("1. Crear un nuevo entorno virtual:")
        print("   python -m venv new_env")
        print("   new_env\\Scripts\\activate")
        print("   python install_dependencies.py")
        print("\n2. Usar Python 3.9 o 3.10 para mejor compatibilidad")
        print("\n3. Instalar dependencias manualmente:")
        print("   pip install flask pandas numpy plotly dash requests")
