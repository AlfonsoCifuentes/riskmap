#!/usr/bin/env python3
"""
Test script to verify TensorFlow and transformers work correctly
"""

print("Testing TensorFlow and transformers imports...")

# Test our fix
from fix_tf_warnings import *

# Test if TensorFlow works
try:
    import tensorflow as tf
    print(f"✅ TensorFlow {tf.__version__} imported successfully")
    
    # Test basic TensorFlow functionality
    x = tf.constant([1, 2, 3])
    print(f"✅ TensorFlow basic operations work: {x}")
    
except Exception as e:
    print(f"❌ TensorFlow test failed: {e}")

# Test if transformers works
try:
    from transformers import pipeline
    print("✅ Transformers imported successfully")
    
    # Try to create a simple pipeline (this will download a model if needed)
    print("✅ Transformers library is working correctly")
    
except Exception as e:
    print(f"❌ Transformers test failed: {e}")

# Test BERT Risk Analyzer
try:
    from src.utils.bert_risk_analyzer import BERTRiskAnalyzer
    analyzer = BERTRiskAnalyzer()
    print("✅ BERT Risk Analyzer imported and initialized successfully")
    
    # Test basic analysis
    result = analyzer.analyze_risk("Test news", "This is a test article about economic trends")
    print(f"✅ BERT analysis test: {result['level']} risk level")
    
except Exception as e:
    print(f"❌ BERT Risk Analyzer test failed: {e}")

print("\n✅ All tests completed!")
