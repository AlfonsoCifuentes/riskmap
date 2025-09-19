#!/usr/bin/env python3
"""
Test de importaciones críticas para verificar que app_BUENA.py puede arrancar
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_critical_imports():
    """Test de las importaciones más críticas"""
    
    print("🔄 TESTING CRITICAL IMPORTS FOR APP_BUENA.PY")
    print("=" * 60)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # Test 1: DatabaseManager from correct location
    print("1. Testing DatabaseManager import...")
    try:
        from src.utils.config import DatabaseManager
        print("   ✅ DatabaseManager imported successfully")
        test_results['passed'] += 1
    except ImportError as e:
        print(f"   ❌ DatabaseManager import failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"DatabaseManager: {e}")
    
    # Test 2: Main orchestrator
    print("2. Testing GeopoliticalIntelligenceOrchestrator import...")
    try:
        from src.orchestration.main_orchestrator import GeopoliticalIntelligenceOrchestrator
        print("   ✅ GeopoliticalIntelligenceOrchestrator imported successfully")
        test_results['passed'] += 1
    except ImportError as e:
        print(f"   ❌ GeopoliticalIntelligenceOrchestrator import failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"GeopoliticalIntelligenceOrchestrator: {e}")
    
    # Test 3: Task scheduler
    print("3. Testing TaskScheduler import...")
    try:
        from src.orchestration.task_scheduler import TaskScheduler
        print("   ✅ TaskScheduler imported successfully")
        test_results['passed'] += 1
    except ImportError as e:
        print(f"   ❌ TaskScheduler import failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"TaskScheduler: {e}")
    
    # Test 4: Basic database connection
    print("4. Testing database connection...")
    try:
        from src.utils.config import DatabaseManager, config
        db_manager = DatabaseManager(config)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"   ✅ Database connection successful - {count} articles found")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Database connection: {e}")
    
    # Test 5: Basic Flask import (should always work)
    print("5. Testing Flask import...")
    try:
        from flask import Flask
        print("   ✅ Flask imported successfully")
        test_results['passed'] += 1
    except ImportError as e:
        print(f"   ❌ Flask import failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Flask: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 IMPORT TEST RESULTS:")
    print(f"   ✅ Passed: {test_results['passed']}")
    print(f"   ❌ Failed: {test_results['failed']}")
    print(f"   📊 Success Rate: {(test_results['passed']/(test_results['passed']+test_results['failed'])*100):.1f}%")
    
    if test_results['errors']:
        print(f"\n❌ ERRORS FOUND:")
        for i, error in enumerate(test_results['errors'], 1):
            print(f"   {i}. {error}")
    
    if test_results['failed'] == 0:
        print("\n🎉 ALL CRITICAL IMPORTS SUCCESSFUL!")
        print("   app_BUENA.py should start without import errors")
        return True
    else:
        print(f"\n⚠️  {test_results['failed']} CRITICAL IMPORTS FAILED")
        print("   app_BUENA.py may have startup issues")
        return False

if __name__ == "__main__":
    success = test_critical_imports()
    if success:
        print("\n✅ Import test completed successfully")
    else:
        print("\n❌ Import test found issues")