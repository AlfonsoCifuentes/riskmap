#!/usr/bin/env python3
"""
Quick test for the conflict monitoring page to verify the template fix.
"""

from flask import Flask, render_template
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder='src/web/templates')

@app.route('/test-conflict-monitoring')
def test_conflict_monitoring():
    """Test route to verify conflict monitoring template works."""
    try:
        # Try to render the template
        return render_template('conflict_monitoring.html', 
                             conflicts=[],
                             statistics={},
                             title="Test Conflict Monitoring")
    except Exception as e:
        return f"Template Error: {str(e)}", 500

if __name__ == "__main__":
    print("🔧 Testing conflict monitoring template...")
    try:
        # Test rendering without starting server
        with app.app_context():
            result = test_conflict_monitoring()
            if isinstance(result, tuple):
                print(f"❌ Template error: {result[0]}")
            else:
                print("✅ Template renders successfully!")
                print("The template syntax error has been fixed.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
