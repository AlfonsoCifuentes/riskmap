#!/usr/bin/env python3
"""
Patch TensorFlow compatibility issues
"""

import sys
import os

def patch_tensorflow_compat():
    """Patch TensorFlow compatibility module for older TF versions"""
    try:
        import tensorflow as tf
        
        # Check if tensorflow.compat exists
        if not hasattr(tf, 'compat'):
            print("Patching tensorflow.compat...")
            
            # Create a simple compat module
            class TFCompat:
                def __init__(self):
                    self.v1 = tf
                    
            tf.compat = TFCompat()
            print("✅ tensorflow.compat patched successfully")
        else:
            print("✅ tensorflow.compat already available")
            
    except ImportError:
        print("❌ TensorFlow not available")
    except Exception as e:
        print(f"⚠️  Error patching tensorflow.compat: {e}")

if __name__ == "__main__":
    patch_tensorflow_compat()
