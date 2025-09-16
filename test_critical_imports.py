#!/usr/bin/env python3
"""
Test specific imports that were failing before
"""

print("Testing critical imports...")

# Test our fix first
try:
    import fix_tf_warnings
    print("✅ fix_tf_warnings imported")
except Exception as e:
    print(f"❌ fix_tf_warnings failed: {e}")

# Test TensorFlow import
try:
    import tensorflow as tf
    print(f"✅ TensorFlow imported: {tf.__version__}")
except Exception as e:
    print(f"❌ TensorFlow failed: {e}")

# Test transformers import
try:
    from transformers import pipeline
    print("✅ Transformers imported")
except Exception as e:
    print(f"❌ Transformers failed: {e}")

# Test the main orchestrator import that was failing
try:
    from src.orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator
    print("✅ GeopoliticalIntelligenceOrchestrator imported")
except Exception as e:
    print(f"❌ GeopoliticalIntelligenceOrchestrator failed: {e}")

# Test BERT analyzer
try:
    from src.utils.bert_risk_analyzer import BERTRiskAnalyzer
    print("✅ BERTRiskAnalyzer imported")
except Exception as e:
    print(f"❌ BERTRiskAnalyzer failed: {e}")

print("✅ All critical imports tested!")
