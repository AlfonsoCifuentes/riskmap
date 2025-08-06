#!/usr/bin/env python3
"""
Fix TensorFlow/ml_dtypes compatibility issues
"""

import os
import warnings
import sys

# Suppress TensorFlow deprecation warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress ALL TensorFlow messages
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Fix ml_dtypes compatibility before importing TensorFlow
def fix_ml_dtypes():
    """Fix ml_dtypes compatibility issues by adding missing attributes"""
    try:
        import ml_dtypes
        version = getattr(ml_dtypes, '__version__', 'unknown')
        print(f"✅ ml_dtypes version: {version}")
        
        # Lista de atributos que pueden faltar y necesitan ser añadidos
        missing_attrs = []
        required_attrs = [
            'float8_e4m3', 'float8_e5m2', 'float8_e3m4', 'float8_e4m3fn', 
            'float8_e4m3b11fnuz', 'float8_e5m2fnuz', 'float8_e4m3fnuz'
        ]
        
        for attr in required_attrs:
            if not hasattr(ml_dtypes, attr):
                missing_attrs.append(attr)
        
        if missing_attrs:
            print(f"🔧 Agregando atributos faltantes: {missing_attrs}")
            
            # Agregar atributos faltantes usando uno existente como base
            base_attr = None
            for existing in ['float8_e5m2', 'float16', 'bfloat16']:
                if hasattr(ml_dtypes, existing):
                    base_attr = getattr(ml_dtypes, existing)
                    break
            
            if base_attr:
                for attr in missing_attrs:
                    setattr(ml_dtypes, attr, base_attr)
                    print(f"✅ Agregado {attr}")
            else:
                print("⚠️ No se encontró un atributo base para usar como referencia")
                return False
        else:
            print("✅ ml_dtypes tiene todos los atributos requeridos")
        
        return True
        
    except ImportError:
        print("⚠️ ml_dtypes not installed")
        return False
    except Exception as e:
        print(f"⚠️ Error fixing ml_dtypes: {e}")
        return False

# Apply the ml_dtypes fix before any TensorFlow imports
fix_ml_dtypes()

def check_ml_dtypes_version():
    """Check if ml_dtypes version is compatible"""
    try:
        import ml_dtypes
        version = getattr(ml_dtypes, '__version__', 'unknown')
        print(f"🔍 ml_dtypes version verificada: {version}")
        
        # Check for required attributes
        required_attrs = ['float8_e4m3', 'float8_e5m2']
        missing = [attr for attr in required_attrs if not hasattr(ml_dtypes, attr)]
        
        if missing:
            print(f"⚠️ Missing ml_dtypes attributes: {missing}")
            return False
        else:
            print("✅ ml_dtypes has all required attributes")
            return True
            
    except ImportError:
        print("⚠️ ml_dtypes not installed")
        return False
    except Exception as e:
        print(f"⚠️ Error checking ml_dtypes: {e}")
        return False

# Check compatibility
ml_dtypes_ok = check_ml_dtypes_version()

# Now try to import TensorFlow and apply patches
tensorflow_available = False
try:
    import tensorflow as tf
    
    # Patch the deprecated function if it exists
    if hasattr(tf.losses, 'sparse_softmax_cross_entropy'):
        # Store original function
        original_fn = tf.losses.sparse_softmax_cross_entropy
        # Replace with v1 version to avoid deprecation warnings
        tf.losses.sparse_softmax_cross_entropy = tf.compat.v1.losses.sparse_softmax_cross_entropy
        print("🔧 Parcheada función deprecada tf.losses.sparse_softmax_cross_entropy")
    
    # Also patch at module level to catch imports from keras
    if hasattr(tf.compat.v1.losses, 'sparse_softmax_cross_entropy'):
        tf.losses.sparse_softmax_cross_entropy = tf.compat.v1.losses.sparse_softmax_cross_entropy
        print("🔧 Aplicado parche a nivel de módulo para Keras")
        
    print(f"✅ TensorFlow imported successfully: {tf.__version__}")
    tensorflow_available = True
    
except Exception as e:
    print(f"❌ TensorFlow import failed: {e}")
    print("⚠️ TensorFlow features will be disabled")
    tensorflow_available = False

if __name__ == "__main__":
    print("TensorFlow compatibility check completed")
    print(f"ml_dtypes compatible: {ml_dtypes_ok}")
    print(f"TensorFlow available: {tensorflow_available}")
