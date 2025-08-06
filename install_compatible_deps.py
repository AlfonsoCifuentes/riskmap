#!/usr/bin/env python3
"""
Script simple para instalar dependencias compatibles paso a paso
"""

import subprocess
import sys

def run_command(command):
    """Ejecuta un comando y muestra el resultado"""
    print(f"🔄 Ejecutando: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Éxito")
        if result.stdout.strip():
            print(f"📝 {result.stdout.strip()}")
    else:
        print("❌ Error")
        if result.stderr.strip():
            print(f"⚠️ {result.stderr.strip()}")
    
    return result.returncode == 0

def main():
    print("🔧 Instalación Step-by-Step de Dependencias Compatibles")
    print("=" * 60)
    
    # Paso 1: Desinstalar versiones conflictivas
    print("\n📦 Paso 1: Limpiando instalaciones previas...")
    uninstall_packages = ['tensorflow', 'tensorflow-intel', 'keras', 'ml-dtypes', 'jax', 'jaxlib', 'transformers']
    
    for package in uninstall_packages:
        run_command([sys.executable, '-m', 'pip', 'uninstall', package, '-y'])
    
    # Paso 2: Instalar versiones específicas compatibles
    print("\n📦 Paso 2: Instalando versiones compatibles...")
    
    # Instalar en orden específico para evitar conflictos
    install_steps = [
        (['ml-dtypes==0.3.1'], "ml-dtypes base"),
        (['keras==2.15.0'], "Keras compatible"),
        (['tensorflow==2.15.0'], "TensorFlow compatible"),
        (['jaxlib==0.4.20'], "JAXlib compatible"),
        (['jax==0.4.20'], "JAX compatible"),
        (['transformers==4.35.0'], "Transformers compatible")
    ]
    
    all_success = True
    
    for packages, description in install_steps:
        print(f"\n🔧 Instalando {description}...")
        success = run_command([sys.executable, '-m', 'pip', 'install'] + packages)
        if not success:
            print(f"❌ Falló la instalación de {description}")
            all_success = False
        else:
            print(f"✅ {description} instalado exitosamente")
    
    # Paso 3: Verificar instalación
    print("\n🧪 Paso 3: Verificando instalación...")
    
    test_imports = [
        ('ml_dtypes', 'import ml_dtypes; print(f"ml_dtypes: {getattr(ml_dtypes, \\"__version__\\", \\"unknown\\")}")'),
        ('keras', 'import keras; print(f"Keras: {keras.__version__}")'),
        ('tensorflow', 'import tensorflow as tf; print(f"TensorFlow: {tf.__version__}")'),
        ('jax', 'import jax; print(f"JAX: {jax.__version__}")'),
        ('transformers', 'import transformers; print(f"Transformers: {transformers.__version__}")')
    ]
    
    for name, test_code in test_imports:
        print(f"\n🔍 Probando {name}...")
        result = subprocess.run([sys.executable, '-c', test_code], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            print(f"❌ {name} falló: {result.stderr.strip()}")
            all_success = False
    
    # Paso 4: Verificar dependencias
    print("\n🔍 Paso 4: Verificando compatibilidad de dependencias...")
    result = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Todas las dependencias son compatibles!")
    else:
        print("⚠️ Aún hay algunos conflictos:")
        print(result.stdout)
        print(result.stderr)
        all_success = False
    
    if all_success:
        print("\n🎉 ¡Instalación completada exitosamente!")
        print("✅ Todas las librerías están instaladas y son compatibles")
    else:
        print("\n⚠️ Instalación completada con algunos problemas")
        print("🔧 Puede que necesites ajustar manualmente algunas versiones")

if __name__ == "__main__":
    main()
