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
    """Importar TensorFlow de manera segura con timeout compatible con Windows"""
    import threading
    import time
    import sys
    
    try:
        print("🧠 Intentando importar TensorFlow...")
        
        # Variable para controlar el resultado de la importación
        tf_result = [None]
        error_result = [None]
        
        def import_tf():
            try:
                import tensorflow as tf
                # Configurar TensorFlow para usar CPU
                tf.config.set_visible_devices([], 'GPU')
                # Suprimir logs adicionales
                tf.get_logger().setLevel('ERROR')
                tf.autograph.set_verbosity(0)
                tf_result[0] = tf
            except Exception as e:
                error_result[0] = e
        
        # Ejecutar importación en hilo separado con timeout
        import_thread = threading.Thread(target=import_tf)
        import_thread.daemon = True
        import_thread.start()
        import_thread.join(timeout=15)  # 15 segundos de timeout
        
        if import_thread.is_alive():
            print("⚠️  TensorFlow import timeout (>15s) - saltando")
            return None
        
        if error_result[0]:
            raise error_result[0]
        
        if tf_result[0]:
            print(f"✅ TensorFlow {tf_result[0].__version__} cargado (CPU mode)")
            return tf_result[0]
        else:
            print("⚠️  TensorFlow no se pudo importar")
            return None
            
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
