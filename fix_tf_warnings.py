#!/usr/bin/env python3
"""
fix_tf_warnings.py
Configuraciones para suprimir warnings de TensorFlow y optimizar carga
"""

import os
import sys
import warnings

def setup_tensorflow_environment():
    """Configurar variables de entorno para TensorFlow"""
    # Suprimir warnings de TensorFlow
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Solo errores
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Deshabilitar OneDNN
    
    # Configuraciones adicionales para estabilidad
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Forzar CPU
    os.environ['PYTHONHASHSEED'] = '0'  # Reproducibilidad
    
    print("🛠️  Variables de entorno TensorFlow configuradas")

def suppress_warnings():
    """Suprimir warnings generales de Python"""
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    
    # Suprimir warnings específicos de TensorFlow/Keras
    warnings.filterwarnings('ignore', message='.*tensorflow.*')
    warnings.filterwarnings('ignore', message='.*keras.*')
    warnings.filterwarnings('ignore', message='.*absl.*')
    
    print("🔇 Warnings suprimidos")

def safe_tensorflow_import():
    """Importar TensorFlow de manera segura"""
    try:
        print("🧠 Intentando importar TensorFlow...")
        import tensorflow as tf
        
        # Configurar TensorFlow para usar CPU
        tf.config.set_visible_devices([], 'GPU')
        
        # Suprimir logs adicionales
        tf.get_logger().setLevel('ERROR')
        tf.autograph.set_verbosity(0)
        
        print(f"✅ TensorFlow {tf.__version__} cargado (CPU mode)")
        return tf
    except ImportError:
        print("⚠️  TensorFlow no está instalado")
        return None
    except Exception as e:
        print(f"⚠️  Error cargando TensorFlow: {e}")
        return None

def initialize_fix_tf_warnings():
    """Función principal para inicializar todas las correcciones"""
    try:
        # 1. Configurar entorno
        setup_tensorflow_environment()
        
        # 2. Suprimir warnings
        suppress_warnings()
        
        # 3. Importar TensorFlow de manera segura
        tf = safe_tensorflow_import()
        
        print("🎯 fix_tf_warnings inicializado correctamente")
        return True
        
    except Exception as e:
        print(f"💥 Error en fix_tf_warnings: {e}")
        return False

# Ejecutar automáticamente al importar el módulo
if __name__ == "__main__":
    initialize_fix_tf_warnings()
else:
    # Cuando se importa con "from fix_tf_warnings import *"
    initialize_fix_tf_warnings()
