#!/usr/bin/env python3
"""
Test minimalista de Flask solo para servicio de imágenes
"""
import os
from flask import Flask, send_from_directory

def create_minimal_flask_app():
    """Crear Flask app minimalista solo para test de imágenes"""
    app = Flask(__name__)
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        print(f"🔍 Solicitado: /static/{filename}")
        
        # Check if it's a news image first (in root static folder)  
        if filename.startswith('images/news/'):
            static_path = f'static/{filename}'
            print(f"   📰 Es imagen de noticias, chequeando: {static_path}")
            if os.path.exists(static_path):
                print(f"   ✅ Archivo existe, sirviendo desde static/")
                return send_from_directory('static', filename)
            else:
                print(f"   ❌ Archivo no existe")
        
        # Otherwise serve from src/web/static
        print(f"   📁 Sirviendo desde src/web/static/")
        return send_from_directory('src/web/static', filename)
    
    @app.route('/test')
    def test():
        return """
        <h1>Test de Imágenes</h1>
        <h2>Imágenes de noticias:</h2>
        <img src="/static/images/news/news_951d3aa44203.jpg" width="200"><br>
        <img src="/static/images/news/news_1f73950908b0.jpg" width="200"><br>
        <img src="/static/images/news/news_08ad704b863a.jpg" width="200"><br>
        """
    
    return app

if __name__ == "__main__":
    print("🚀 Iniciando Flask minimalista para test de imágenes...")
    app = create_minimal_flask_app()
    print("🌐 Accede a: http://localhost:5002/test")
    print("📸 Test de imágenes en curso...")
    
    try:
        app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Flask detenido")