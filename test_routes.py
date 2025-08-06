from flask import Flask, render_template
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear Flask app
app = Flask(__name__, template_folder='src/web/templates')

@app.route('/')
def index():
    logger.info("✅ Ruta / accedida")
    return "<h1>RISKMAP TEST</h1><p>Servidor funcionando</p><a href='/about'>Ir a About</a>"

@app.route('/about')
def about():
    logger.info("✅ Ruta /about accedida")
    try:
        return render_template('about.html')
    except Exception as e:
        logger.error(f"Error en about: {e}")
        return f"<h1>About RISKMAP</h1><p>Sistema de análisis geopolítico</p><p>Error: {e}</p>"

@app.route('/test')
def test():
    logger.info("✅ Ruta /test accedida")
    return "<h1>TEST OK</h1><p>Las rutas funcionan correctamente</p>"

if __name__ == '__main__':
    logger.info("🚀 Iniciando servidor de prueba en puerto 5002...")
    app.run(debug=True, port=5002, host='127.0.0.1')
