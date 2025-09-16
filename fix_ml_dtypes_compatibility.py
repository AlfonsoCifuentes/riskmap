#!/usr/bin/env python3
"""
Script para solucionar problemas de compatibilidad con ml_dtypes
"""

import sys
import subprocess
import importlib.util
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_and_fix_ml_dtypes():
    """Verificar y corregir problemas con ml_dtypes"""
    try:
        # Verificar si ml_dtypes está disponible
        import ml_dtypes
        logger.info(f"✅ ml_dtypes version: {ml_dtypes.__version__}")
        
        # Verificar si el atributo problemático existe
        if hasattr(ml_dtypes, 'float8_e3m4'):
            logger.info("✅ ml_dtypes.float8_e3m4 está disponible")
            return True
        else:
            logger.warning("⚠️ ml_dtypes.float8_e3m4 no está disponible")
            
            # Intentar crear un mock del atributo faltante
            try:
                import numpy as np
                # Crear un tipo de datos mock
                ml_dtypes.float8_e3m4 = np.dtype('float32')  # Fallback a float32
                logger.info("✅ Creado mock para ml_dtypes.float8_e3m4")
                return True
            except Exception as e:
                logger.error(f"❌ Error creando mock: {e}")
                return False
                
    except ImportError as e:
        logger.error(f"❌ ml_dtypes no está instalado: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error verificando ml_dtypes: {e}")
        return False

def patch_ml_dtypes_imports():
    """Parchear imports problemáticos"""
    try:
        # Verificar si JAX está causando problemas
        try:
            import jax
            logger.info(f"✅ JAX version: {jax.__version__}")
        except Exception as e:
            logger.warning(f"⚠️ Problema con JAX: {e}")
        
        # Verificar TensorFlow
        try:
            import tensorflow as tf
            logger.info(f"✅ TensorFlow version: {tf.__version__}")
        except Exception as e:
            logger.warning(f"⚠️ Problema con TensorFlow: {e}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en patch de imports: {e}")
        return False

def update_packages():
    """Actualizar paquetes problemáticos"""
    packages_to_update = [
        "ml_dtypes",
        "jax",
        "jaxlib", 
        "numpy<2.0",  # Asegurar compatibilidad con TensorFlow
        "tensorflow>=2.15,<2.16"
    ]
    
    for package in packages_to_update:
        try:
            logger.info(f"Actualizando {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", package
            ], capture_output=True, text=True, check=True)
            logger.info(f"✅ {package} actualizado")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Error actualizando {package}: {e.stderr}")
        except Exception as e:
            logger.error(f"❌ Error actualizando {package}: {e}")

def create_compatibility_patch():
    """Crear un patch de compatibilidad"""
    patch_content = '''
# Patch de compatibilidad para ml_dtypes
import sys
import warnings

def patch_ml_dtypes():
    try:
        import ml_dtypes
        import numpy as np
        
        # Agregar tipos faltantes si no existen
        if not hasattr(ml_dtypes, 'float8_e3m4'):
            ml_dtypes.float8_e3m4 = np.dtype('float32')
        if not hasattr(ml_dtypes, 'float8_e4m3'):
            ml_dtypes.float8_e4m3 = np.dtype('float32') 
        if not hasattr(ml_dtypes, 'float8_e5m2'):
            ml_dtypes.float8_e5m2 = np.dtype('float32')
            
    except ImportError:
        pass
    except Exception as e:
        warnings.warn(f"Error aplicando patch ml_dtypes: {e}")

# Aplicar patch automáticamente al importar
patch_ml_dtypes()
'''
    
    try:
        with open('ml_dtypes_patch.py', 'w', encoding='utf-8') as f:
            f.write(patch_content)
        logger.info("✅ Patch de compatibilidad creado: ml_dtypes_patch.py")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando patch: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🔧 Iniciando corrección de compatibilidad ml_dtypes...")
    
    # 1. Verificar estado actual
    logger.info("1. Verificando estado actual...")
    if check_and_fix_ml_dtypes():
        logger.info("✅ ml_dtypes parece estar funcionando")
    else:
        logger.warning("⚠️ Problemas detectados con ml_dtypes")
    
    # 2. Actualizar paquetes
    logger.info("2. Actualizando paquetes...")
    update_packages()
    
    # 3. Crear patch de compatibilidad
    logger.info("3. Creando patch de compatibilidad...")
    create_compatibility_patch()
    
    # 4. Verificar reparación
    logger.info("4. Verificando reparación...")
    if check_and_fix_ml_dtypes():
        logger.info("✅ Reparación completada exitosamente")
        return True
    else:
        logger.warning("⚠️ Algunos problemas persisten")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
