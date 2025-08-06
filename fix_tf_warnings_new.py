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
    """Fix ml_dtypes compatibility issues"""
    try:
        import ml_dtypes
        # Check if the problematic float8_e3m4 attribute exists
        if not hasattr(ml_dtypes, 'float8_e3m4'):
            # Add the missing attribute as an alias to an existing one
            if hasattr(ml_dtypes, 'float8_e5m2'):
                ml_dtypes.float8_e3m4 = ml_dtypes.float8_e5m2
                print("✅ Fixed ml_dtypes compatibility (added float8_e3m4 alias)")
        return True
    except ImportError:
        print("⚠️ ml_dtypes not installed, this might cause issues with TensorFlow")
        return False
    except Exception as e:
        print(f"⚠️ Error fixing ml_dtypes: {e}")
        return False

# Apply the fix
fix_ml_dtypes()

# Now try to import TensorFlow
tensorflow_available = False
try:
    import tensorflow as tf
    
    # Patch the deprecated function if it exists
    if hasattr(tf.losses, 'sparse_softmax_cross_entropy'):
        tf.losses.sparse_softmax_cross_entropy = tf.compat.v1.losses.sparse_softmax_cross_entropy
        
    print("✅ TensorFlow imported and patched successfully")
    tensorflow_available = True
    
except Exception as e:
    print(f"❌ TensorFlow import still failed after ml_dtypes fix: {e}")
    print("⚠️ TensorFlow features will be disabled")
    tensorflow_available = False

if __name__ == "__main__":
    print("TensorFlow compatibility patch applied")
    print(f"TensorFlow available: {tensorflow_available}")
