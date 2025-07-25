#!/usr/bin/env python3
"""
Script to suppress TensorFlow warnings and set environment variables
"""

import os
import warnings

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress INFO and WARNING messages
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations to avoid warnings

# Suppress other warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Import TensorFlow after setting environment variables
try:
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
except ImportError:
    pass

print("TensorFlow warnings suppressed")