#!/usr/bin/env python3
"""
Test script to verify all critical imports for the RiskMap system
"""

import sys
import traceback

def test_import(module_name, description=""):
    """Test importing a module and report the result"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} {description} - ERROR: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} {description} - UNEXPECTED ERROR: {e}")
        return False

def main():
    print("🔍 TESTING CRITICAL IMPORTS FOR RISKMAP SYSTEM")
    print("=" * 60)
    
    all_passed = True
    
    # Core Python libraries
    print("\n📦 CORE DEPENDENCIES:")
    all_passed &= test_import("pandas", "(Data processing)")
    all_passed &= test_import("numpy", "(Numerical computing)")
    all_passed &= test_import("flask", "(Web framework)")
    all_passed &= test_import("dash", "(Dashboard framework)")
    all_passed &= test_import("sqlite3", "(Database)")
    all_passed &= test_import("requests", "(HTTP requests)")
    
    # AI/ML libraries
    print("\n🤖 AI/ML DEPENDENCIES:")
    all_passed &= test_import("transformers", "(Hugging Face transformers)")
    all_passed &= test_import("tensorflow", "(TensorFlow)")
    all_passed &= test_import("keras", "(Keras)")
    all_passed &= test_import("groq", "(Groq API)")
    all_passed &= test_import("torch", "(PyTorch)")
    
    # RiskMap orchestrators
    print("\n🎯 RISKMAP ORCHESTRATORS:")
    try:
        from src.orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator
        print("✅ GeopoliticalIntelligenceOrchestrator")
        core_orch_available = True
    except Exception as e:
        print(f"❌ GeopoliticalIntelligenceOrchestrator - ERROR: {e}")
        core_orch_available = False
        all_passed = False
    
    try:
        from src.orchestration.enhanced_historical_orchestrator import EnhancedHistoricalOrchestrator  
        print("✅ EnhancedHistoricalOrchestrator")
        hist_orch_available = True
    except Exception as e:
        print(f"❌ EnhancedHistoricalOrchestrator - ERROR: {e}")
        hist_orch_available = False
        all_passed = False
    
    # Dashboard components
    print("\n📊 DASHBOARD COMPONENTS:")
    try:
        from src.dashboard.main_dashboard import MainDashboard
        print("✅ MainDashboard")
    except Exception as e:
        print(f"❌ MainDashboard - ERROR: {e}")
        all_passed = False
    
    try:
        from src.dashboard.historical_dashboard import HistoricalDashboard  
        print("✅ HistoricalDashboard")
    except Exception as e:
        print(f"❌ HistoricalDashboard - ERROR: {e}")
        all_passed = False
    
    # API components
    print("\n🔌 API COMPONENTS:")
    try:
        from src.api.rest_status import create_api_blueprint
        print("✅ create_api_blueprint")
    except Exception as e:
        print(f"❌ create_api_blueprint - ERROR: {e}")
        all_passed = False
    
    # Test TensorFlow compatibility
    print("\n🔧 TENSORFLOW COMPATIBILITY:")
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow version: {tf.__version__}")
        
        # Test if we can access keras
        try:
            import keras
            print(f"✅ Keras version: {keras.__version__}")
        except:
            try:
                from tensorflow import keras as tf_keras
                print(f"✅ TensorFlow.Keras available")
            except:
                print("❌ Neither keras nor tensorflow.keras available")
                all_passed = False
                
    except Exception as e:
        print(f"❌ TensorFlow compatibility - ERROR: {e}")
        all_passed = False
    
    # Test Groq functionality  
    print("\n🚀 GROQ FUNCTIONALITY:")
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GROQ_API_KEY')
        if api_key:
            print("✅ GROQ_API_KEY loaded from environment")
            
            from groq import Groq
            client = Groq(api_key=api_key)
            print("✅ Groq client created successfully")
        else:
            print("⚠️  GROQ_API_KEY not found in environment")
            
    except Exception as e:
        print(f"❌ Groq functionality - ERROR: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL CRITICAL IMPORTS SUCCESSFUL!")
        print("✅ System is ready to run")
        return 0
    else:
        print("⚠️  SOME IMPORTS FAILED")
        print("❌ System may have limited functionality")
        return 1

if __name__ == "__main__":
    sys.exit(main())
