#!/usr/bin/env python3
"""
Start RiskMap with 3D Earth Background
Quick startup script to test the 3D implementation
"""

import os
import sys
from pathlib import Path

def main():
    """Start the RiskMap application"""
    print("🌍 Starting RiskMap with 3D Earth Background")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir(Path(__file__).parent)
    
    # Check that 3D files exist
    files = ['tierra.fbx', 'tierra.mtl', 'espacio.jpg']
    missing = []
    
    for file in files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"❌ Missing 3D files: {missing}")
        print("Please ensure the 3D Earth files are in the root directory.")
        return False
    
    print("✅ All 3D files found")
    
    # Import and start the app
    try:
        from app_BUENA import RiskMapUnifiedApplication
        
        print("🚀 Starting Flask application...")
        app = RiskMapUnifiedApplication()
        
        print("\n🌐 Server starting at http://localhost:5000")
        print("📄 Main dashboard: http://localhost:5000/")
        print("📝 About page: http://localhost:5000/about")
        print("\n🌍 3D Earth should be visible as background on all pages")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start the Flask development server
        app.flask_app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Avoid reloader issues with complex initialization
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
