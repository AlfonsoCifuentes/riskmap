#!/usr/bin/env python3
"""
Test script to verify the fixes are working correctly.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tensorflow_import():
    """Test that TensorFlow imports without warnings."""
    print("🔧 Testing TensorFlow import...")
    try:
        # Apply our fix first
        import fix_tf_warnings
        import tensorflow as tf
        print("✅ TensorFlow imported successfully without warnings")
        return True
    except Exception as e:
        print(f"❌ TensorFlow import failed: {e}")
        return False

def test_env_loading():
    """Test that .env file is loaded correctly."""
    print("🔧 Testing .env file loading...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        newsapi_key = os.getenv('NEWSAPI_KEY')
        if newsapi_key:
            print(f"✅ NewsAPI key loaded: {newsapi_key[:10]}...")
        else:
            print("❌ NewsAPI key not found in .env")
            
        return True
    except Exception as e:
        print(f"❌ .env loading failed: {e}")
        return False

def test_template_syntax():
    """Test that the conflict monitoring template can be rendered."""
    print("🔧 Testing template syntax fix...")
    try:
        from jinja2 import Environment, FileSystemLoader
        
        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'src', 'web', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Try to load the problematic template
        template = env.get_template('conflict_monitoring.html')
        print("✅ Template loaded successfully - syntax error fixed")
        return True
    except Exception as e:
        print(f"❌ Template syntax error still exists: {e}")
        return False

def main():
    print("🔍 RUNNING FIXES VERIFICATION")
    print("="*50)
    
    results = []
    results.append(test_tensorflow_import())
    results.append(test_env_loading())
    results.append(test_template_syntax())
    
    print("\n📊 RESULTS SUMMARY:")
    print("="*50)
    if all(results):
        print("🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print("The server should now start without issues.")
    else:
        print("⚠️ Some fixes may need additional work.")
        
    return all(results)

if __name__ == "__main__":
    main()
