#!/usr/bin/env python3
"""
Quick template validation script
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
import traceback

def validate_template():
    try:
        # Setup Jinja2 environment
        template_dir = os.path.join('src', 'web', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Try to load the template
        template = env.get_template('conflict_monitoring.html')
        print("✅ Template conflict_monitoring.html loaded successfully!")
        
        # Try to render with minimal context
        test_context = {
            'fallback_active': False
        }
        rendered = template.render(**test_context)
        print("✅ Template rendered successfully!")
        print(f"Rendered size: {len(rendered)} characters")
        
        return True
        
    except TemplateSyntaxError as e:
        print(f"❌ Template Syntax Error:")
        print(f"   Line {e.lineno}: {e.message}")
        print(f"   File: {e.filename}")
        return False
        
    except Exception as e:
        print(f"❌ Error validating template:")
        print(f"   {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Validating conflict_monitoring.html template...")
    success = validate_template()
    sys.exit(0 if success else 1)
