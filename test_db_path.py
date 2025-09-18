#!/usr/bin/env python3
"""
Test exact database path resolution from backend
"""
import os

def test_database_path():
    print("🔍 TESTING DATABASE PATH RESOLUTION")
    print("="*50)
    
    # Test 1: Try the import method
    try:
        from src.utils.config import get_database_path
        db_path = get_database_path()
        print(f"✅ get_database_path() worked: {db_path}")
        exists = os.path.exists(db_path)
        print(f"   File exists: {exists}")
    except ImportError as e:
        print(f"❌ get_database_path() failed: {e}")
        db_path = r"data\geopolitical_intel.db"
        print(f"   Using fallback path: {db_path}")
        exists = os.path.exists(db_path)
        print(f"   Fallback file exists: {exists}")
    
    # Test 2: Alternative paths
    alternative_paths = [
        "data/geopolitical_intel.db",
        "./data/geopolitical_intel.db",
        "data\\geopolitical_intel.db",
        ".\\data\\geopolitical_intel.db"
    ]
    
    print(f"\n🔍 TESTING ALTERNATIVE PATHS:")
    for path in alternative_paths:
        exists = os.path.exists(path)
        print(f"   {path}: {'✅' if exists else '❌'}")
    
    # Test 3: Current working directory
    print(f"\n🔍 CURRENT WORKING DIRECTORY: {os.getcwd()}")
    print(f"   Files in current dir: {os.listdir('.')[:10]}")
    if os.path.exists('data'):
        print(f"   Files in data dir: {os.listdir('data')[:10]}")

if __name__ == "__main__":
    test_database_path()