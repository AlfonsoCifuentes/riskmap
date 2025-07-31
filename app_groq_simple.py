"""
Versión corregida del archivo app_bert_fixed.py solo con la funcionalidad de Groq
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
import logging
import json
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    template_folder='src/dashboard/templates',
    static_folder='src/dashboard/static')
CORS(app)

def generate_groq_geopolitical_analysis(articles):
    """
    Genera un análisis geopolítico usando Groq API
    """
    try:
        # Importar Groq de manera tardía para evitar errores si no está instalado
        from groq import Groq
        
        # Configurar cliente Groq (necesitarás tu API key)
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            logger.warning("GROQ_API_KEY no encontrada en variables de entorno")
            return generate_fallback_analysis(articles)
        
        client = Groq(api_key=groq_api_key)
        
        # Preparar el contexto de los artículos
        articles_context = "\n\n".join([
            f"ARTÍCULO {i+1}:\nTítulo: {article.get('title', '')}\nContenido: {article.get('content', '')}\nUbicación: {article.get('location', '')}\nNivel de riesgo: {article.get('risk_level', '')}"
            for i, article in enumerate(articles[:20])
        ])
        
        # Prompt para el análisis geopolítico
        prompt = f"""
Eres un periodista especializado en geopolítica con 20 años de experiencia escribiendo para periódicos internacionales de prestigio. Tu estilo es riguroso pero accesible, humilde pero informado, y no temes nombrar líderes políticos, países y conflictos específicos.

Basándote en estos {len(articles)} artículos de noticias recientes, escribe un análisis geopolítico en formato HTML que será publicado en un periódico digital.

ARTÍCULOS ANALIZADOS:
{articles_context}

INSTRUCCIONES ESPECÍFICAS:
1. Escribe como un periodista humano, no como IA
2. Incluye opiniones fundamentadas y predicciones humildes
3. Nombra líderes políticos específicos (Putin, Xi Jinping, Biden, Zelensky, etc.)
4. Menciona países y regiones específicas
5. Conecta los eventos actuales con tendencias históricas
6. Expresa preocupaciones e incertidumbres de manera honesta
7. Usa un tono profesional pero humano
8. Estructura el artículo en párrafos bien definidos

FORMATO REQUERIDO:
- Un titular principal impactante pero veraz
- Un subtítulo que complemente el titular
- El artículo dividido en párrafos de 150-200 palabras cada uno
- Primera letra del primer párrafo será estilizada como en periódicos clásicos
- Uso ocasional de elementos destacados para conceptos clave
- Conclusión reflexiva y prudente

Responde SOLO con un objeto JSON con esta estructura:
{{
    "title": "Titular principal del artículo",
    "subtitle": "Subtítulo explicativo",
    "content": "Contenido completo del artículo en HTML con párrafos <p>, ocasionales <strong> para destacar, pero SIN usar <h1>, <h2> o <h3>",
    "sources_count": {len(articles)},
    "analysis_date": "{datetime.now().isoformat()}"
}}

IMPORTANTE: El contenido debe estar en HTML pero usando SOLO etiquetas <p> y ocasionales <strong>. NO uses encabezados <h1>, <h2>, etc.
"""

        # Llamar a Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un periodista especializado en geopolítica que escribe análisis rigurosos y bien fundamentados. Respondes SIEMPRE en formato JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",  # Modelo actualizado y disponible
            temperature=0.7,  # Balance entre creatividad y coherencia
            max_tokens=4000
        )
        
        response_content = chat_completion.choices[0].message.content
        logger.info("✅ Análisis Groq generado exitosamente")
        
        # Parsear respuesta JSON
        try:
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Groq JSON response: {e}")
            logger.error(f"Response content: {response_content[:500]}...")
            return generate_fallback_analysis(articles)
            
    except ImportError:
        logger.error("Groq library not installed. pip install groq")
        return generate_fallback_analysis(articles)
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return generate_fallback_analysis(articles)

def generate_fallback_analysis(articles):
    """
    Genera análisis de respaldo cuando Groq no está disponible
    """
    content = """
<p>El panorama geopolítico mundial atraviesa uno de sus momentos más complejos de las últimas décadas. Las tensiones que se extienden desde Europa Oriental hasta el Pacífico están redibujando las alianzas internacionales y poniendo a prueba el orden establecido tras la Guerra Fría.</p>

<p>En Europa, el conflicto en Ucrania ha consolidado la posición de la OTAN como un actor determinante en la seguridad continental. La respuesta occidental, liderada por Estados Unidos y respaldada firmemente por Reino Unido y Polonia, ha demostrado una cohesión que pocos predecían. Sin embargo, las fisuras emergen cuando se analiza la dependencia energética europea, particularmente de Alemania, que se ve obligada a reconsiderar décadas de política energética.</p>

<p>El presidente <strong>Volodymyr Zelensky</strong> ha logrado mantener el apoyo internacional, aunque las elecciones en Estados Unidos podrían alterar significativamente este respaldo. La fatiga bélica en algunos sectores de la opinión pública occidental es palpable, y líderes como <strong>Viktor Orbán</strong> en Hungría han sido voces discordantes dentro de la alianza europea.</p>

<p>En el frente asiático, las tensiones en el estrecho de Taiwán han escalado a niveles que recuerdan los momentos más álgidos de la Guerra Fría. <strong>Xi Jinping</strong> ha intensificado la retórica sobre la reunificación, mientras que la administración estadounidense, junto con Japón y Australia, han reforzado su presencia militar en la región. Corea del Norte, bajo <strong>Kim Jong-un</strong>, ha aprovechado estas tensiones para acelerar su programa nuclear.</p>

<p>La crisis energética global ha puesto de manifiesto la vulnerabilidad de las cadenas de suministro internacionales. Los países del Golfo, liderados por Arabia Saudí y Emiratos Árabes Unidos, han recuperado protagonismo geopolítico, navegando hábilmente entre las presiones occidentales y sus relaciones con Rusia y China. <strong>Mohammed bin Salman</strong> ha demostrado una diplomacia pragmática que desafía las expectativas tradicionales.</p>

<p>Como observadores de este complejo tablero, debemos resistir la tentación de las predicciones categóricas. La historia nos enseña que los momentos de mayor incertidumbre son también los de mayor oportunidad para el cambio. Lo que sí parece claro es que el orden mundial tal como lo conocemos está siendo desafiado desde múltiples frentes, y las decisiones que tomen los líderes mundiales en los próximos meses definirán el rumbo de las próximas décadas.</p>
"""
    
    return {
        "title": "El Tablero Geopolítico se Reconfigura en Tiempo Real",
        "subtitle": "Tensiones globales y nuevas alianzas redefinen el orden mundial mientras la incertidumbre marca el rumbo internacional",
        "content": content,
        "sources_count": len(articles),
        "analysis_date": datetime.now().isoformat()
    }

@app.route('/')
def index():
    """Main dashboard route."""
    return render_template('modern_dashboard_updated.html')

@app.route('/api/generate-ai-analysis', methods=['POST'])
def generate_ai_analysis():
    """
    Endpoint para generar análisis geopolítico con Groq
    """
    try:
        data = request.get_json()
        
        if not data or 'articles' not in data:
            return jsonify({
                'error': 'No articles provided for analysis'
            }), 400
        
        articles = data['articles']
        analysis_type = data.get('analysis_type', 'geopolitical_journalistic')
        
        logger.info(f"🧠 Generando análisis {analysis_type} con {len(articles)} artículos")
        
        # Generar análisis con Groq
        analysis_result = generate_groq_geopolitical_analysis(articles)
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"❌ Error en generate_ai_analysis: {e}")
        return jsonify({
            'error': f'Error generating analysis: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard con Análisis Geopolítico Groq")
    print("🧠 Endpoint disponible en: http://localhost:5004/api/generate-ai-analysis")
    print("🌐 Dashboard: http://localhost:5004")
    print("-" * 60)
    
    try:
        app.run(host='127.0.0.1', port=5004, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido por el usuario")
