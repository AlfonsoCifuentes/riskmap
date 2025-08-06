#!/usr/bin/env python3
"""
Test TensorFlow and transformers step by step
"""

print("Testing step by step...")

# Step 1: Test ml_dtypes fix
print("Step 1: Testing ml_dtypes fix...")
try:
    import fix_tf_warnings
    print("✅ ml_dtypes fix applied")
except Exception as e:
    print(f"❌ ml_dtypes fix failed: {e}")

# Step 2: Test TensorFlow import
print("Step 2: Testing TensorFlow import...")
try:
    import tensorflow as tf
    print(f"✅ TensorFlow imported: {tf.__version__}")
except Exception as e:
    print(f"❌ TensorFlow failed: {e}")

# Step 3: Test transformers import specifically
print("Step 3: Testing transformers import...")
try:
    import transformers
    print(f"✅ Transformers module imported: {transformers.__version__}")
except Exception as e:
    print(f"❌ Transformers module failed: {e}")

# Step 4: Test pipeline import specifically
print("Step 4: Testing pipeline import...")
try:
    from transformers import pipeline
    print("✅ Pipeline imported from transformers")
except Exception as e:
    print(f"❌ Pipeline import failed: {e}")

print("✅ Diagnostic complete!")
