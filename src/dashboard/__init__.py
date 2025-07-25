"""
Dashboard package for the web interface.
"""

from .app_modern import app

def create_app():
    """Create and configure the Flask application."""
    return app

__all__ = ['app', 'create_app']
