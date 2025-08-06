#!/usr/bin/env python3
"""
Test completo de TensorFlow tras aplicar los fixes
"""

# Aplicar nuestros fixes primero
from fix_tf_warnings import *

print("\n🧪 Probando imports críticos...")

# Test TensorFlow
try:
    import tensorflow as tf
    print(f"✅ TensorFlow: {tf.__version__}")
    
    # Test basic TensorFlow operation
    x = tf.constant([1.0, 2.0, 3.0])
    y = tf.square(x)
    print(f"✅ TensorFlow operación básica: {y.numpy()}")
    
except Exception as e:
    print(f"❌ TensorFlow failed: {e}")

# Test Keras
try:
    import keras
    print(f"✅ Keras: {keras.__version__}")
except Exception as e:
    print(f"❌ Keras failed: {e}")

# Test transformers
try:
    from transformers import pipeline
    print("✅ Transformers pipeline imported successfully")
except Exception as e:
    print(f"❌ Transformers failed: {e}")

# Test BERT analyzer
try:
    from src.utils.bert_risk_analyzer import BERTRiskAnalyzer
    analyzer = BERTRiskAnalyzer()
    print("✅ BERTRiskAnalyzer imported and initialized")
    
    # Test analysis
    result = analyzer.analyze_risk("Test", "This is a test article about politics")
    print(f"✅ Risk analysis test: {result.get('level', 'unknown')} level")
    
except Exception as e:
    print(f"❌ BERTRiskAnalyzer failed: {e}")

print("\n🎉 Test completado!")
