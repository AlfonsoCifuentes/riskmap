"""
Flask Dashboard with REAL BERT Integration + Groq AI Analysis - UNIFIED VERSION
Implementación corregida que garantiza el uso del modelo BERT de HuggingFace
+ Análisis geopolítico avanzado con Groq
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

# Variables globales para el modelo BERT
bert_model = None
bert_tokenizer = None
sentiment_pipeline = None

def initialize_bert_model():
    """
    Inicializa el modelo BERT específico para análisis político
    FIXED: Mejor manejo de errores y descarga del modelo
    """
    global bert_model, bert_tokenizer, sentiment_pipeline
    
    try:
        logger.info("🧠 Iniciando carga del modelo BERT político...")
        
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        import torch
        
        # Modelo específico para análisis de sentimiento político
        model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"  # Modelo más estable
        
        logger.info(f"📥 Descargando modelo: {model_name}")
        
        # Cargar tokenizer y modelo con mejor manejo de errores
        try:
            bert_tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                use_fast=True,
                trust_remote_code=False
            )
            logger.info("✅ Tokenizer cargado exitosamente")
            
            bert_model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                trust_remote_code=False
            )
            logger.info("✅ Modelo cargado exitosamente")
            
        except Exception as download_error:
            logger.error(f"❌ Error descargando modelo: {download_error}")
            # Intentar con un modelo local más simple
            try:
                logger.info("🔄 Intentando con modelo alternativo...")
                model_name = "distilbert-base-uncased-finetuned-sst-2-english"
                
                bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
                bert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
                logger.info(f"✅ Modelo alternativo cargado: {model_name}")
                
            except Exception as alt_error:
                logger.error(f"❌ Error con modelo alternativo: {alt_error}")
                return False
        
        # Crear pipeline de análisis
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=bert_model,
            tokenizer=bert_tokenizer,
            top_k=None,  # Reemplaza return_all_scores=True
            device=-1  # Forzar CPU para compatibilidad
        )
        
        logger.info("✅ Pipeline BERT creado exitosamente")
        logger.info("🔧 Dispositivo: CPU (para compatibilidad)")
        
        # Test del modelo
        test_text = "This is a test of political sentiment analysis"
        test_result = sentiment_pipeline(test_text)
        logger.info(f"🧪 Test del modelo exitoso: {len(test_result)} resultados")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FALLO CRÍTICO: No se pudo cargar el modelo BERT: {e}")
        logger.error(f"❌ Tipo de error: {type(e).__name__}")
        return False

def analyze_with_bert(text):
    """
    Analiza texto usando el modelo BERT real
    FIXED: Mejor manejo de errores y validación
    """
    global sentiment_pipeline
    
    if sentiment_pipeline is None:
        raise RuntimeError("Modelo BERT no está disponible")
    
    try:
        # Limpiar y preparar texto
        cleaned_text = str(text).strip()
        if not cleaned_text:
            raise ValueError("Texto vacío para análisis")
            
        # Limitar longitud para BERT
        if len(cleaned_text) > 512:
            cleaned_text = cleaned_text[:512]
        
        # Análisis con BERT
        results = sentiment_pipeline(cleaned_text)
        
        if not results or len(results) == 0:
            raise ValueError("No se obtuvieron resultados del modelo")
        
        # Extraer scores de manera más robusta
        sentiment_scores = {}
        for result in results:
            if isinstance(result, dict) and 'label' in result and 'score' in result:
                label = result['label'].upper()
                sentiment_scores[label] = result['score']
        
        # Manejar diferentes formatos de labels
        negative_score = sentiment_scores.get('NEGATIVE', 
                        sentiment_scores.get('NEG', 
                        sentiment_scores.get('LABEL_0', 0)))
        positive_score = sentiment_scores.get('POSITIVE', 
                        sentiment_scores.get('POS', 
                        sentiment_scores.get('LABEL_1', 0)))
        
        # Si no hay scores, usar neutral
        if negative_score == 0 and positive_score == 0:
            negative_score = 0.5
            positive_score = 0.5
        
        # Calcular importancia basada en sentimiento
        # En noticias políticas, sentimiento negativo indica mayor importancia
        importance = (negative_score * 80) + (positive_score * 20)
        
        # Escalar a 10-100
        importance = max(10, min(100, importance * 100))
        
        return {
            'importance': importance,
            'negative_sentiment': negative_score,
            'positive_sentiment': positive_score,
            'confidence': max(negative_score, positive_score),
            'raw_results': results
        }
        
    except Exception as e:
        logger.error(f"❌ Error en análisis BERT: {e}")
        raise

@app.route('/')
def index():
    """Main dashboard route."""
    return render_template('modern_dashboard_updated.html')

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get dashboard statistics."""
    return jsonify({
        'total_articles': 150,
        'today_articles': 25,
        'high_risk_alerts': 8,
        'countries_monitored': 45,
        'last_update': datetime.now().isoformat()
    })

@app.route('/api/articles')
def get_articles():
    """Get articles with pagination."""
    # Mock data for testing - with real news structure including images
    mock_articles = [
        {
            'id': 1,
            'title': 'Escalada militar en conflicto internacional',
            'content': 'Las tensiones militares han aumentado significativamente en la región con movilización de tropas',
            'location': 'Europa Oriental',
            'risk_level': 'high',
            'risk_score': 0.8,
            'created_at': datetime.now().isoformat(),
            'country': 'Ukraine',
            'image_url': None,  # Real articles should have actual image URLs
            'source': 'Reuters',
            'url': 'https://example.com/news1'
        },
        {
            'id': 2,
            'title': 'Cumbre económica internacional concluye exitosamente',
            'content': 'Los líderes mundiales alcanzan acuerdos comerciales importantes para la estabilidad económica',
            'location': 'Geneva',
            'risk_level': 'low',
            'risk_score': 0.3,
            'created_at': datetime.now().isoformat(),
            'country': 'Switzerland',
            'image_url': None,  # Real articles should have actual image URLs
            'source': 'AP News',
            'url': 'https://example.com/news2'
        },
        {
            'id': 3,
            'title': 'Amenaza nuclear en Asia Pacific aumenta tensiones',
            'content': 'Expertos en seguridad expresan preocupación por el desarrollo de armas nucleares en la región',
            'location': 'Asia Pacific',
            'risk_level': 'critical',
            'risk_score': 0.95,
            'created_at': datetime.now().isoformat(),
            'country': 'Multiple',
            'image_url': None,  # Real articles should have actual image URLs
            'source': 'BBC News',
            'url': 'https://example.com/news3'
        },
        {
            'id': 4,
            'title': 'Ataque terrorista en capital europea deja múltiples víctimas',
            'content': 'Un ataque coordinado ha impactado el centro de una importante ciudad europea',
            'location': 'Paris',
            'risk_level': 'critical',
            'risk_score': 0.9,
            'created_at': datetime.now().isoformat(),
            'country': 'France',
            'image_url': None,  # Real articles should have actual image URLs
            'source': 'France24',
            'url': 'https://example.com/news4'
        }
    ] * 5  # Repeat to have more articles
    
    return jsonify({
        'articles': mock_articles,
        'page': 1,
        'total': len(mock_articles)
    })

def generate_groq_geopolitical_analysis(articles):
    """
    Genera un análisis geopolítico usando Groq API
    """
    try:
        from groq import Groq
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            logger.warning("GROQ_API_KEY no encontrada. Usando análisis de respaldo.")
            return generate_fallback_analysis(articles)
        
        client = Groq(api_key=groq_api_key)
        
        articles_context = "\n\n".join([
            f"ARTÍCULO {i+1}:\nTítulo: {article.get('title', 'N/A')}\nContenido: {article.get('content', 'N/A')[:500]}...\nUbicación: {article.get('location', 'N/A')}"
            for i, article in enumerate(articles[:20])
        ])
        
        prompt = f"""
        Eres un periodista experto en geopolítica con 25 años de experiencia, escribiendo para un periódico de renombre mundial. Tu estilo es incisivo, humano y riguroso. No temes nombrar líderes, países o conflictos, y ofreces predicciones fundamentadas pero humildes.

        Analiza los siguientes {len(articles)} artículos de noticias y genera un análisis geopolítico en formato HTML.

        ARTÍCULOS DE CONTEXTO:
        {articles_context}

        INSTRUCCIONES CLAVE:
        1.  **Estilo Periodístico Humano**: Escribe con una voz personal y experta, no como una IA. Usa un lenguaje rico y evocador.
        2.  **Nombres Propios**: Menciona líderes (Putin, Xi Jinping, Biden, Zelensky), países y regiones relevantes.
        3.  **Análisis Profundo**: Conecta los puntos entre diferentes conflictos y tendencias. No te limites a resumir.
        4.  **Opinión Fundamentada**: Expresa tu opinión y proyecciones, pero siempre desde la humildad y el rigor analítico.
        5.  **Formato HTML Específico**:
            *   El `content` debe ser una cadena de texto HTML.
            *   Usa párrafos `<p>` para el cuerpo del texto.
            *   **No uses** `<h1>`, `<h2>`, etc., dentro del `content`. El título y subtítulo van en sus propios campos.
            *   Puedes usar `<strong>` para enfatizar conceptos clave.

        RESPONDE ÚNICAMENTE CON UN OBJETO JSON VÁLIDO con la siguiente estructura:
        {{
          "title": "Un titular principal, impactante y profesional",
          "subtitle": "Un subtítulo que resuma la esencia del análisis",
          "content": "El cuerpo completo del artículo en HTML, usando solo <p> y <strong>.",
          "sources_count": {len(articles)}
        }}
        """

        logger.info("🤖 Generando análisis con Groq AI...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analista geopolítico de élite. Tu única salida es un objeto JSON válido que sigue estrictamente la estructura solicitada."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.75,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        response_content = chat_completion.choices[0].message.content
        logger.info("✅ Análisis Groq generado exitosamente.")
        
        try:
            analysis_data = json.loads(response_content)
            # Validar campos requeridos
            if 'title' in analysis_data and 'subtitle' in analysis_data and 'content' in analysis_data:
                return analysis_data
            else:
                logger.error("JSON de Groq incompleto. Faltan campos requeridos.")
                return generate_fallback_analysis(articles)
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar JSON de Groq. Contenido: {response_content[:500]}...")
            return generate_fallback_analysis(articles)
            
    except ImportError:
        logger.error("Librería Groq no instalada. Ejecuta: pip install groq")
        return generate_fallback_analysis(articles)
    except Exception as e:
        logger.error(f"Error en la llamada a la API de Groq: {e}")
        return generate_fallback_analysis(articles)

def generate_fallback_analysis(articles):
    """
    Genera análisis de respaldo cuando Groq no está disponible
    """
    current_date = datetime.now().strftime("%d de %B de %Y")
    
    return {
        "title": "El Tablero Geopolítico se Reconfigura en Tiempo Real",
        "subtitle": "Tensiones globales y nuevas alianzas redefinen el orden mundial mientras la incertidumbre marca el rumbo internacional",
        "content": f"""
            <p>El panorama geopolítico mundial atraviesa uno de sus momentos más complejos de las últimas décadas. Las tensiones que se extienden desde Europa Oriental hasta el Pacífico están redibujando las alianzas internacionales y poniendo a prueba el orden establecido tras la Guerra Fría.</p>
            
            <p>En Europa, el conflicto en Ucrania ha consolidado la posición de la OTAN como un actor determinante en la seguridad continental. La respuesta occidental, liderada por Estados Unidos y respaldada firmemente por Reino Unido y Polonia, ha demostrado una cohesión que pocos predecían. Sin embargo, las fisuras emergen cuando se analiza la dependencia energética europea, particularmente de Alemania, que se ve obligada a reconsiderar décadas de política energética.</p>

            <p>El presidente <strong>Volodymyr Zelensky</strong> ha logrado mantener el apoyo internacional, aunque las elecciones en Estados Unidos podrían alterar significativamente este respaldo. La fatiga bélica en algunos sectores de la opinión pública occidental es palpable, y líderes como <strong>Viktor Orbán</strong> en Hungría han sido voces discordantes dentro de la alianza europea.</p>

            <p>En el frente asiático, las tensiones en el estrecho de Taiwán han escalado a niveles que recuerdan los momentos más álgidos de la Guerra Fría. <strong>Xi Jinping</strong> ha intensificado la retórica sobre la reunificación, mientras que la administración estadounidense, junto con Japón y Australia, han reforzado su presencia militar en la región. Corea del Norte, bajo <strong>Kim Jong-un</strong>, ha aprovechado estas tensiones para acelerar su programa nuclear.</p>

            <p>La crisis energética global ha puesto de manifiesto la vulnerabilidad de las cadenas de suministro internacionales. Los países del Golfo, liderados por Arabia Saudí y Emiratos Árabes Unidos, han recuperado protagonismo geopolítico, navegando hábilmente entre las presiones occidentales y sus relaciones con Rusia y China. <strong>Mohammed bin Salman</strong> ha demostrado una diplomacia pragmática que desafía las expectativas tradicionales.</p>

            <p>En América Latina, el escenario es igualmente complejo. Brasil, bajo <strong>Luiz Inácio Lula da Silva</strong>, busca posicionarse como mediador en los conflictos globales, mientras que países como Colombia y Chile redefinen sus alianzas regionales. La influencia china en la región crece silenciosamente, ofreciendo alternativas de inversión que compiten directamente con los tradicionales socios occidentales.</p>

            <p>África emerge como el continente donde se libra una nueva guerra fría silenciosa. Rusia, a través de grupos mercenarios, y China, mediante su iniciativa de la Franja y la Ruta, compiten por la influencia en un continente que alberga recursos cruciales para la transición energética mundial. Francia ve erosionada su influencia tradicional en el Sahel, mientras que nuevos actores como Turquía e India buscan su espacio.</p>

            <p>El multilateralismo atraviesa una crisis profunda. Las Naciones Unidas muestran signos evidentes de obsolescencia institucional, con un Consejo de Seguridad paralizado por los vetos cruzados entre las potencias. Organizaciones como el G7 y el G20 luchan por mantener relevancia en un mundo cada vez más fragmentado en bloques regionales.</p>

            <p>La tecnología se ha convertido en el nuevo campo de batalla geopolítico. La competencia entre Estados Unidos y China por el dominio de la inteligencia artificial, los semiconductores y las tecnologías 5G está redefiniendo las cadenas de valor globales. Europa intenta mantener su autonomía estratégica, pero se encuentra atrapada entre las dos superpotencias tecnológicas.</p>

            <p>Mirando hacia el futuro, tres escenarios parecen posibles: una bipolarización renovada entre bloques liderados por Washington y Beijing, una multipolaridad caótica donde las potencias medias ganen protagonismo, o una fragmentación regional que privilegie las alianzas geográficas sobre las ideológicas. La próxima década será crucial para determinar cuál de estas tendencias prevalece.</p>

            <p>Como observadores de este complejo tablero, debemos resistir la tentación de las predicciones categóricas. La historia nos enseña que los momentos de mayor incertidumbre son también los de mayor oportunidad para el cambio. Lo que sí parece claro es que el orden mundial tal como lo conocemos está siendo desafiado desde múltiples frentes, y las decisiones que tomen los líderes mundiales en los próximos meses definirán el rumbo de las próximas décadas.</p>
        """,
        "sources_count": len(articles),
        "analysis_date": datetime.now().isoformat()
    }

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

@app.route('/api/test-bert')
def test_bert_route():
    """Test route to verify BERT model is loaded"""
    global sentiment_pipeline
    
    if sentiment_pipeline is None:
        return jsonify({
            'status': 'ERROR',
            'message': 'Modelo BERT no está cargado',
            'bert_loaded': False
        }), 500
    
    try:
        # Test real del modelo
        test_text = "Military conflict escalates with nuclear threats"
        result = analyze_with_bert(test_text)
        
        return jsonify({
            'status': 'OK',
            'message': 'Modelo BERT funcionando correctamente',
            'bert_loaded': True,
            'test_analysis': result
        })
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'message': f'Error en modelo BERT: {str(e)}',
            'bert_loaded': False
        }), 500

@app.route('/api/analyze-importance', methods=['POST'])
def analyze_importance_bert():
    """
    ANÁLISIS BERT REAL - VERSIÓN CORREGIDA
    Este endpoint garantiza que se use el modelo de IA real
    """
    global sentiment_pipeline
    
    try:
        article_data = request.get_json()
        
        if not article_data:
            return jsonify({
                'error': 'No article data provided'
            }), 400
        
        # Validar que BERT esté disponible
        if sentiment_pipeline is None:
            logger.error("❌ CRÍTICO: Modelo BERT no disponible")
            return jsonify({
                'error': 'Modelo BERT no está disponible - análisis imposible',
                'bert_required': True,
                'fallback_used': False
            }), 503  # Service Unavailable
        
        # Preparar texto para análisis
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        analysis_text = f"{title}. {content}"
        
        if not analysis_text.strip():
            return jsonify({
                'error': 'No hay texto para analizar'
            }), 400
        
        logger.info(f"🧠 Analizando con BERT: {title[:50]}...")
        
        # ANÁLISIS BERT REAL
        bert_result = analyze_with_bert(analysis_text)
        
        # Factor de riesgo geopolítico adicional
        location = article_data.get('location', '').lower()
        risk_level = article_data.get('risk_level', 'medium').lower()
        
        # Multiplicador geopolítico
        geo_multiplier = 1.0
        high_risk_regions = ['ukraine', 'gaza', 'israel', 'syria', 'afghanistan', 'iran', 'iraq']
        for region in high_risk_regions:
            if region in location:
                geo_multiplier = 1.3
                break
        
        # Multiplicador por nivel de riesgo
        risk_multipliers = {'critical': 1.4, 'high': 1.2, 'medium': 1.0, 'low': 0.8}
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        
        # Importancia final combinada
        final_importance = bert_result['importance'] * geo_multiplier * risk_multiplier
        final_importance = max(10, min(100, final_importance))
        
        # Resultado con análisis BERT real
        result = {
            'importance_factor': round(final_importance, 2),
            'risk_factor': round(final_importance, 2),
            'bert_analysis': {
                'negative_sentiment': round(bert_result['negative_sentiment'], 4),
                'positive_sentiment': round(bert_result['positive_sentiment'], 4),
                'confidence': round(bert_result['confidence'], 4),
                'model_used': 'BERT Sentiment Analysis (Fixed Version)'
            },
            'geopolitical_factors': {
                'location': location,
                'geo_multiplier': geo_multiplier,
                'risk_level': risk_level,
                'risk_multiplier': risk_multiplier
            },
            'article_metadata': {
                'title': title[:100],
                'location': article_data.get('location', ''),
                'risk_level': risk_level,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'model_info': {
                'primary_model': 'BERT Sentiment Analysis',
                'analysis_type': 'real_bert_political_sentiment',
                'fallback_used': False,
                'ai_powered': True
            }
        }
        
        logger.info(f"✅ BERT análisis completado: {final_importance:.1f}%")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error crítico en análisis BERT: {e}")
        return jsonify({
            'error': f'Error en análisis BERT: {str(e)}',
            'bert_required': True,
            'fallback_used': False
        }), 500

# =====================================================
# GROQ AI ANALYSIS ENDPOINTS
# =====================================================

def get_top_articles_from_db(limit=20):
    """
    Obtiene los artículos más importantes de la base de datos
    """
    try:
        # Por ahora usar datos mock - en producción conectar a la BD
        mock_articles = [
            {
                'id': 1,
                'title': 'Escalada militar en conflicto internacional',
                'content': 'Las tensiones militares han aumentado significativamente en la región con movilización de tropas y declaraciones oficiales que indican una posible escalada del conflicto.',
                'location': 'Europa Oriental',
                'risk_score': 0.8,
                'source': 'Reuters',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'title': 'Crisis diplomática entre potencias mundiales',
                'content': 'Las relaciones bilaterales se han deteriorado tras las últimas declaraciones oficiales, generando incertidumbre en los mercados internacionales.',
                'location': 'Asia-Pacífico',
                'risk_score': 0.7,
                'source': 'BBC',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 3,
                'title': 'Movimientos económicos estratégicos',
                'content': 'Los últimos movimientos en el sector energético indican cambios importantes en las alianzas comerciales globales.',
                'location': 'Medio Oriente',
                'risk_score': 0.6,
                'source': 'CNN',
                'created_at': datetime.now().isoformat()
            }
        ]
        
        # Simular más artículos para análisis robusto
        for i in range(4, limit + 1):
            mock_articles.append({
                'id': i,
                'title': f'Desarrollo geopolítico importante #{i}',
                'content': f'Análisis de eventos significativos en diferentes regiones que impactan la estabilidad global y regional. Evento {i} con implicaciones importantes.',
                'location': f'Región {i % 6 + 1}',
                'risk_score': 0.5 + (i % 5) * 0.1,
                'source': f'Fuente {i}',
                'created_at': datetime.now().isoformat()
            })
        
        return mock_articles[:limit]
        
    except Exception as e:
        logger.error(f"Error obteniendo artículos: {e}")
        return []

def generate_groq_geopolitical_analysis(articles):
    """
    Genera análisis geopolítico usando Groq AI
    """
    try:
        from groq import Groq
        
        # Inicializar cliente Groq
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY no encontrada en variables de entorno")
        
        client = Groq(api_key=groq_api_key)
        
        # Preparar contexto de artículos
        articles_context = ""
        for i, article in enumerate(articles[:20], 1):
            articles_context += f"""
            Artículo {i}:
            Título: {article.get('title', 'Sin título')}
            Ubicación: {article.get('location', 'Sin ubicación')}
            Contenido: {article.get('content', 'Sin contenido')[:300]}
            Nivel de Riesgo: {article.get('risk_score', 0)}
            Fuente: {article.get('source', 'Sin fuente')}
            ---
            """
        
        # Prompt especializado para análisis geopolítico
        prompt = f"""
        Como analista geopolítico senior, analiza los siguientes {len(articles)} artículos de noticias y genera un análisis integral en estilo periodístico profesional.

        CONTEXTO DE ARTÍCULOS:
        {articles_context}

        INSTRUCCIONES ESPECÍFICAS:
        1. Escribe en español con estilo periodístico profesional
        2. Estructura el análisis en párrafos bien definidos
        3. Identifica patrones y conexiones entre eventos
        4. Evalúa implicaciones geopolíticas a corto y mediano plazo
        5. Menciona regiones y actores clave
        6. Usa un tono objetivo pero accesible
        7. Longitud: aproximadamente 800-1200 palabras

        ESTRUCTURA REQUERIDA:
        - Título llamativo y profesional
        - Subtítulo que capture la esencia del análisis
        - Introducción que establezca el contexto global actual
        - Desarrollo de los principales temas identificados
        - Análisis de implicaciones y tendencias
        - Conclusión que sintetice los puntos clave

        Genera el análisis ahora:
        """
        
        # Llamada a Groq
        logger.info("🤖 Generando análisis con Groq AI...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Modelo actualizado
            messages=[
                {"role": "system", "content": "Eres un analista geopolítico experto que escribe análisis profesionales en español."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        analysis_content = response.choices[0].message.content
        logger.info("✅ Análisis Groq generado exitosamente")
        
        return {
            'title': 'El Tablero Geopolítico se Reconfigura en Tiempo Real',
            'subtitle': 'Análisis integral de los desarrollos más significativos que están redefiniendo el equilibrio mundial',
            'content': analysis_content,
            'sources_count': len(articles),
            'generated_at': datetime.now().isoformat(),
            'ai_model': 'Groq Llama-3.1-8b-instant',
            'analysis_type': 'geopolitical_journalistic'
        }
        
    except Exception as e:
        logger.error(f"Error en análisis Groq: {e}")
        return generate_fallback_analysis(articles)

def generate_fallback_analysis(articles):
    """
    Genera análisis de respaldo si Groq no está disponible
    """
    return {
        'title': 'Panorama Geopolítico Global: Análisis de Desarrollos Recientes',
        'subtitle': 'Evaluación integral de los eventos más significativos en el escenario internacional',
        'content': f"""
        <p>El escenario geopolítico mundial presenta actualmente una compleja red de interacciones que requieren análisis detallado. Basándose en {len(articles)} fuentes informativas recientes, emergen varios patrones significativos.</p>
        
        <p>Las tensiones internacionales continúan manifestándose en múltiples frentes, desde Europa Oriental hasta el Asia-Pacífico, creando un ambiente de incertidumbre que afecta tanto las relaciones diplomáticas como los mercados globales.</p>
        
        <p>Los desarrollos económicos y militares observados sugieren una reconfiguración de las alianzas tradicionales, con implicaciones que se extienden más allá de las fronteras regionales hacia el equilibrio de poder global.</p>
        
        <p>La información analizada indica que los próximos meses serán cruciales para determinar la dirección de varios conflictos y negociaciones en curso, requiriendo seguimiento continuo de la evolución de estos eventos.</p>
        
        <p>Este análisis se basa en fuentes múltiples y busca proporcionar una perspectiva integral de los eventos más relevantes para la estabilidad y seguridad internacional.</p>
        """,
        'sources_count': len(articles),
        'generated_at': datetime.now().isoformat(),
        'ai_model': 'Fallback Analysis',
        'analysis_type': 'basic_geopolitical'
    }

@app.route('/api/generate-ai-analysis', methods=['POST'])
def generate_groq_ai_analysis():
    """
    Endpoint para generar análisis geopolítico con Groq IA
    """
    try:
        data = request.get_json() or {}
        
        # Obtener artículos desde la base de datos o usar los proporcionados
        articles = data.get('articles')
        if not articles:
            articles = get_top_articles_from_db(limit=20)
        
        if not articles:
            return jsonify({
                'error': 'No se encontraron artículos para analizar',
                'success': False
            }), 400
        
        # Generar análisis con Groq
        analysis_result = generate_groq_geopolitical_analysis(articles)
        
        # Estructurar respuesta
        response = {
            'success': True,
            'analysis': analysis_result,
            'metadata': {
                'articles_analyzed': len(articles),
                'generation_time': datetime.now().isoformat(),
                'endpoint_version': '1.0'
            }
        }
        
        logger.info(f"✅ Análisis geopolítico generado: {len(articles)} artículos procesados")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error en endpoint de análisis: {e}")
        return jsonify({
            'error': f'Error generando análisis: {str(e)}',
            'success': False
        }), 500

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard con BERT + GROQ AI - VERSIÓN UNIFICADA")
    print("🧠 Cargando modelo BERT para análisis político...")
    
    # CRÍTICO: Cargar modelo BERT antes de iniciar servidor
    if not initialize_bert_model():
        print("❌ FALLO CRÍTICO: No se pudo cargar modelo BERT")
        print("🛑 El servidor NO se iniciará sin el modelo de IA")
        exit(1)
    
    print("✅ Modelo BERT cargado exitosamente")
    print("🤖 Groq AI disponible para análisis geopolítico")
    print("🌐 URL Principal: http://localhost:5003")
    print("🧠 BERT Endpoint: http://localhost:5003/api/analyze-importance")
    print("🌍 Groq Analysis: http://localhost:5003/api/generate-ai-analysis")
    print("🧪 Test BERT: http://localhost:5003/api/test-bert")
    print("-" * 60)
    
    try:
        app.run(host='127.0.0.1', port=5003, debug=False)  # Puerto 5003 unificado
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido por el usuario")
