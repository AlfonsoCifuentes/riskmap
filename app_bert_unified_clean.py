"""
RiskMap - Aplicación Web Moderna Unificada con BERT + Groq AI
Sistema completo de análisis geopolítico con IA
"""

import logging
import os
import json
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Flask and web imports
from flask import Flask, jsonify, request, render_template_string

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('riskmap_unified.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variables globales para BERT y análisis
bert_model = None
bert_tokenizer = None 
sentiment_pipeline = None

class RiskMapUnifiedApplication:
    """Aplicación unificada de RiskMap con BERT y Groq AI"""
    
    def __init__(self):
        """Inicializar la aplicación"""
        self.flask_app = Flask(__name__)
        self.flask_app.secret_key = os.getenv('FLASK_SECRET_KEY', 'riskmap-unified-2024')
        
        # Estado del sistema
        self.system_state = {
            'bert_model_loaded': False,
            'groq_available': False,
            'test_articles': [],
            'server_running': False
        }
        
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Manejador de señales para cierre limpio"""
        logger.info(f"🛑 Señal recibida: {signum}. Cerrando aplicación...")
        sys.exit(0)

    def initialize_bert_model(self):
        """Inicializa el modelo BERT específico para análisis político"""
        global bert_model, bert_tokenizer, sentiment_pipeline
        
        try:
            logger.info("🧠 Iniciando carga del modelo BERT político...")
            
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
            import torch
            
            # Modelo específico para análisis de sentimiento político
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            
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
                top_k=None,
                device=-1  # Forzar CPU para compatibilidad
            )
            
            logger.info("✅ Pipeline BERT creado exitosamente")
            
            # Test del modelo
            test_text = "This is a test of political sentiment analysis"
            test_result = sentiment_pipeline(test_text)
            logger.info(f"🧪 Test del modelo exitoso: {len(test_result)} resultados")
            
            self.system_state['bert_model_loaded'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ FALLO CRÍTICO: No se pudo cargar el modelo BERT: {e}")
            self.system_state['bert_model_loaded'] = False
            return False

    def analyze_with_bert(self, text):
        """Analiza texto usando el modelo BERT real"""
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
            importance = (negative_score * 80) + (positive_score * 20)
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

    def generate_groq_geopolitical_analysis(self, articles):
        """Genera un análisis geopolítico usando Groq API"""
        try:
            from groq import Groq
            
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                logger.warning("GROQ_API_KEY no encontrada. Usando análisis de respaldo.")
                return self.generate_fallback_analysis(articles)
            
            client = Groq(api_key=groq_api_key)
            
            articles_context = "\n\n".join([
                f"ARTÍCULO {i+1}:\nTítulo: {article.get('title', 'N/A')}\nContenido: {article.get('content', 'N/A')[:500]}...\nUbicación: {article.get('location', 'N/A')}"
                for i, article in enumerate(articles[:20])
            ])
            
            prompt = f"""
            Eres un periodista experto en geopolítica con 25 años de experiencia. Analiza los siguientes {len(articles)} artículos de noticias y genera un análisis geopolítico profesional.

            ARTÍCULOS DE CONTEXTO:
            {articles_context}

            RESPONDE CON UN OBJETO JSON VÁLIDO con esta estructura:
            {{
              "title": "Un titular impactante y profesional",
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
                        "content": "Eres un analista geopolítico de élite. Tu única salida es un objeto JSON válido."
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
                if 'title' in analysis_data and 'subtitle' in analysis_data and 'content' in analysis_data:
                    self.system_state['groq_available'] = True
                    return analysis_data
                else:
                    logger.error("JSON de Groq incompleto.")
                    return self.generate_fallback_analysis(articles)
            except json.JSONDecodeError:
                logger.error(f"Error al decodificar JSON de Groq.")
                return self.generate_fallback_analysis(articles)
                
        except ImportError:
            logger.error("Librería Groq no instalada. Ejecuta: pip install groq")
            return self.generate_fallback_analysis(articles)
        except Exception as e:
            logger.error(f"Error en la llamada a la API de Groq: {e}")
            return self.generate_fallback_analysis(articles)

    def generate_fallback_analysis(self, articles):
        """Genera análisis de respaldo cuando Groq no está disponible"""
        return {
            "title": "El Tablero Geopolítico se Reconfigura en Tiempo Real",
            "subtitle": "Tensiones globales y nuevas alianzas redefinen el orden mundial",
            "content": """
                <p>El panorama geopolítico mundial atraviesa uno de sus momentos más complejos de las últimas décadas. Las tensiones que se extienden desde Europa Oriental hasta el Pacífico están redibujando las alianzas internacionales.</p>
                
                <p>En Europa, el conflicto en Ucrania ha consolidado la posición de la OTAN como un actor determinante en la seguridad continental. La respuesta occidental ha demostrado una cohesión que pocos predecían.</p>

                <p>En el frente asiático, las tensiones en el estrecho de Taiwán han escalado a niveles que recuerdan los momentos más álgidos de la Guerra Fría. <strong>Xi Jinping</strong> ha intensificado la retórica sobre la reunificación.</p>

                <p>La crisis energética global ha puesto de manifiesto la vulnerabilidad de las cadenas de suministro internacionales. Los países del Golfo han recuperado protagonismo geopolítico.</p>

                <p>Como observadores de este complejo tablero, debemos resistir la tentación de las predicciones categóricas. Lo que sí parece claro es que el orden mundial tal como lo conocemos está siendo desafiado desde múltiples frentes.</p>
            """,
            "sources_count": len(articles),
            "analysis_date": datetime.now().isoformat()
        }

    def create_test_data(self):
        """Crear datos de prueba para el sistema"""
        try:
            test_articles = [
                {
                    'title': 'Crisis Energética en Europa: Alemania Busca Alternativas al Gas Ruso',
                    'content': 'El gobierno alemán ha anunciado nuevas medidas para reducir la dependencia del gas ruso mientras enfrenta una crisis energética sin precedentes.',
                    'url': 'https://example.com/energia-europa',
                    'published_date': datetime.now() - timedelta(hours=2),
                    'location': 'Berlín, Alemania',
                    'importance': 85,
                    'is_processed': True,
                    'article_type': 'energy_crisis'
                },
                {
                    'title': 'Tensiones en el Mar de China Meridional: Nueva Escalada Militar',
                    'content': 'Las fuerzas navales chinas han incrementado su presencia en aguas disputadas, generando preocupación en Taiwan y países aliados de Estados Unidos.',
                    'url': 'https://example.com/china-pacifico',
                    'published_date': datetime.now() - timedelta(hours=1),
                    'location': 'Taipéi, Taiwán',
                    'importance': 92,
                    'is_processed': True,
                    'article_type': 'military_conflict'
                },
                {
                    'title': 'Elecciones en Brasil: Impacto en las Relaciones Internacionales',
                    'content': 'Los resultados electorales en Brasil podrían redefinir la política exterior del país más grande de América Latina.',
                    'url': 'https://example.com/brasil-elecciones',
                    'published_date': datetime.now() - timedelta(minutes=30),
                    'location': 'Brasília, Brasil',
                    'importance': 78,
                    'is_processed': True,
                    'article_type': 'elections'
                },
                {
                    'title': 'Conflicto en Medio Oriente: Nuevas Alianzas Diplomáticas',
                    'content': 'Los países del Golfo han iniciado conversaciones diplomáticas que podrían cambiar el equilibrio de poder en la región.',
                    'url': 'https://example.com/medio-oriente',
                    'published_date': datetime.now() - timedelta(minutes=45),
                    'location': 'Dubái, EAU',
                    'importance': 88,
                    'is_processed': True,
                    'article_type': 'diplomacy'
                },
                {
                    'title': 'África: Nueva Ruta de la Seda China vs Inversión Occidental',
                    'content': 'Los países africanos se encuentran en el centro de una nueva competencia geopolítica entre China y las potencias occidentales.',
                    'url': 'https://example.com/africa-inversiones',
                    'published_date': datetime.now() - timedelta(hours=3),
                    'location': 'Nairobi, Kenia',
                    'importance': 82,
                    'is_processed': True,
                    'article_type': 'economic_competition'
                },
                {
                    'title': 'Ucrania: Último Parte de Guerra y Apoyo Internacional',
                    'content': 'Las fuerzas ucranianas reportan avances en varios frentes mientras la comunidad internacional debate el apoyo a largo plazo.',
                    'url': 'https://example.com/ucrania-guerra',
                    'published_date': datetime.now() - timedelta(minutes=15),
                    'location': 'Kiev, Ucrania',
                    'importance': 95,
                    'is_processed': True,
                    'article_type': 'war_update'
                }
            ]
            
            self.system_state['test_articles'] = test_articles
            logger.info(f"✅ Datos de prueba creados: {len(test_articles)} artículos")
            return test_articles
            
        except Exception as e:
            logger.error(f"❌ Error creando datos de prueba: {e}")
            return []

    def setup_flask_routes(self):
        """Configura todas las rutas de Flask"""
        
        @self.flask_app.route('/')
        def index():
            """Página principal del dashboard"""
            try:
                return render_template_string(self.get_dashboard_template())
            except Exception as e:
                logger.error(f"Error en ruta index: {e}")
                return f"Error cargando dashboard: {e}", 500

        @self.flask_app.route('/api/dashboard/stats')
        def dashboard_stats():
            """Estadísticas del dashboard"""
            try:
                if not self.system_state.get('test_articles'):
                    self.create_test_data()
                
                articles = self.system_state.get('test_articles', [])
                stats = {
                    'total_articles': len(articles),
                    'high_importance': len([a for a in articles if a.get('importance', 0) > 85]),
                    'processed_today': len(articles),
                    'active_conflicts': 3,
                    'regions_monitored': 8,
                    'last_update': datetime.now().strftime('%H:%M:%S'),
                    'system_status': 'operational',
                    'ai_models_active': self.system_state.get('bert_model_loaded', False),
                    'groq_available': self.system_state.get('groq_available', False)
                }
                
                return jsonify(stats)
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas: {e}")
                return jsonify({'error': str(e)}), 500

        @self.flask_app.route('/api/articles')
        def get_articles():
            """Obtiene lista de artículos"""
            try:
                if not self.system_state.get('test_articles'):
                    self.create_test_data()
                
                articles = self.system_state.get('test_articles', [])
                
                formatted_articles = []
                for article in articles:
                    formatted_article = {
                        'id': hash(article.get('url', '')),
                        'title': article.get('title', ''),
                        'content': article.get('content', '')[:200] + '...',
                        'url': article.get('url', ''),
                        'published_date': article.get('published_date', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
                        'location': article.get('location', 'N/A'),
                        'importance': article.get('importance', 50),
                        'article_type': article.get('article_type', 'general')
                    }
                    formatted_articles.append(formatted_article)
                
                # Ordenar por importancia y fecha
                formatted_articles.sort(key=lambda x: (x['importance'], x['published_date']), reverse=True)
                
                return jsonify({
                    'articles': formatted_articles,
                    'total': len(formatted_articles),
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo artículos: {e}")
                return jsonify({
                    'error': str(e),
                    'articles': [],
                    'total': 0,
                    'success': False
                }), 500

        @self.flask_app.route('/api/generate-ai-analysis', methods=['POST'])
        def generate_ai_analysis():
            """Endpoint para generar análisis con IA (Groq)"""
            try:
                logger.info("🤖 Iniciando generación de análisis IA")
                
                if not self.system_state.get('test_articles'):
                    self.create_test_data()
                
                articles = self.system_state.get('test_articles', [])
                
                if not articles:
                    return jsonify({
                        'error': 'No hay artículos disponibles para análisis',
                        'success': False
                    }), 400
                
                # Generar análisis usando Groq
                analysis = self.generate_groq_geopolitical_analysis(articles)
                
                logger.info("✅ Análisis IA generado exitosamente")
                
                return jsonify({
                    'analysis': analysis,
                    'sources_used': len(articles),
                    'success': True,
                    'generated_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error generando análisis IA: {e}")
                return jsonify({
                    'error': f'Error generando análisis: {str(e)}',
                    'success': False
                }), 500

        @self.flask_app.route('/api/test-bert')
        def test_bert():
            """Endpoint para probar BERT"""
            try:
                if not self.system_state.get('bert_model_loaded', False):
                    return jsonify({
                        'error': 'Modelo BERT no está cargado',
                        'loaded': False,
                        'success': False
                    }), 503
                
                # Texto de prueba
                test_text = "The geopolitical situation in Eastern Europe remains tense as diplomatic efforts continue"
                
                # Analizar con BERT
                analysis_result = self.analyze_with_bert(test_text)
                
                return jsonify({
                    'test_text': test_text,
                    'analysis': analysis_result,
                    'model_loaded': True,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Error en test BERT: {e}")
                return jsonify({
                    'error': str(e),
                    'model_loaded': False,
                    'success': False
                }), 500

        @self.flask_app.route('/api/system/status')
        def system_status():
            """Estado del sistema"""
            try:
                status = {
                    'server_status': 'running',
                    'bert_model_loaded': self.system_state.get('bert_model_loaded', False),
                    'groq_available': self.system_state.get('groq_available', False),
                    'total_articles': len(self.system_state.get('test_articles', [])),
                    'uptime': datetime.now().isoformat(),
                    'version': '3.0.0-unified',
                    'features': {
                        'ai_analysis': True,
                        'bert_sentiment': self.system_state.get('bert_model_loaded', False),
                        'groq_generation': bool(os.getenv('GROQ_API_KEY')),
                        'dashboard': True,
                        'api': True
                    }
                }
                
                return jsonify(status)
                
            except Exception as e:
                logger.error(f"Error obteniendo estado del sistema: {e}")
                return jsonify({
                    'error': str(e),
                    'server_status': 'error'
                }), 500

        @self.flask_app.route('/api/articles/by-region')
        def articles_by_region():
            """Artículos agrupados por región"""
            try:
                articles = self.system_state.get('test_articles', [])
                
                regions = {}
                for article in articles:
                    location = article.get('location', 'Unknown')
                    if ',' in location:
                        region = location.split(',')[-1].strip()
                    else:
                        region = location
                    
                    if region not in regions:
                        regions[region] = []
                    
                    regions[region].append({
                        'title': article.get('title', ''),
                        'importance': article.get('importance', 50),
                        'type': article.get('article_type', 'general'),
                        'location': article.get('location', '')
                    })
                
                return jsonify({
                    'regions': regions,
                    'total_regions': len(regions),
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo artículos por región: {e}")
                return jsonify({
                    'error': str(e),
                    'regions': {},
                    'success': False
                }), 500

        @self.flask_app.route('/api/articles/importance-distribution')
        def importance_distribution():
            """Distribución de importancia de artículos"""
            try:
                articles = self.system_state.get('test_articles', [])
                
                distribution = {
                    'critical': 0,    # 90-100
                    'high': 0,        # 75-89
                    'medium': 0,      # 50-74
                    'low': 0          # 10-49
                }
                
                for article in articles:
                    importance = article.get('importance', 50)
                    
                    if importance >= 90:
                        distribution['critical'] += 1
                    elif importance >= 75:
                        distribution['high'] += 1
                    elif importance >= 50:
                        distribution['medium'] += 1
                    else:
                        distribution['low'] += 1
                
                return jsonify({
                    'distribution': distribution,
                    'total_articles': len(articles),
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Error calculando distribución: {e}")
                return jsonify({
                    'error': str(e),
                    'success': False
                }), 500

    def get_dashboard_template(self):
        """Retorna el template HTML del dashboard"""
        return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiskMap Unified - Dashboard Geopolítico con IA</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary-color: #1a237e;
            --secondary-color: #303f9f;
            --accent-color: #ff4081;
            --dark-bg: #121212;
            --card-bg: #1e1e1e;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --border-color: #333;
        }
        
        body {
            background: linear-gradient(135deg, var(--dark-bg) 0%, #1e3c72 100%);
            color: var(--text-primary);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }
        
        .navbar {
            background: rgba(26, 35, 126, 0.95) !important;
            backdrop-filter: blur(10px);
            border-bottom: 2px solid var(--accent-color);
        }
        
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(255, 64, 129, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(255, 64, 129, 0.2);
        }
        
        .stat-card {
            background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
            color: white;
            text-align: center;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 1rem;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .news-item {
            background: var(--card-bg);
            border-left: 4px solid var(--accent-color);
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 0 10px 10px 0;
            transition: all 0.3s ease;
        }
        
        .news-item:hover {
            background: rgba(255, 64, 129, 0.1);
            transform: translateX(5px);
        }
        
        .importance-badge {
            font-size: 0.8rem;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-weight: bold;
        }
        
        .importance-critical { background: #ff1744; color: white; }
        .importance-high { background: #ff9800; color: white; }
        .importance-medium { background: #2196f3; color: white; }
        .importance-low { background: #4caf50; color: white; }
        
        .ai-analysis {
            background: linear-gradient(45deg, #1a237e, #3f51b5);
            border-radius: 15px;
            padding: 2rem;
            margin: 2rem 0;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .btn-ai {
            background: linear-gradient(45deg, var(--accent-color), #e91e63);
            border: none;
            color: white;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .btn-ai:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255, 64, 129, 0.4);
            color: white;
        }
        
        .section-title {
            color: var(--accent-color);
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 1.5rem;
            position: relative;
        }
        
        .section-title::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 50px;
            height: 3px;
            background: var(--accent-color);
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online { background: #4caf50; }
        .status-offline { background: #f44336; }
        .status-warning { background: #ff9800; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="fas fa-globe-americas me-2"></i>
                <strong>RiskMap Unified</strong> <small class="text-light">v3.0</small>
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text">
                    <span class="status-indicator status-online"></span>
                    Sistema Operativo
                </span>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <!-- Statistics Row -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number" id="totalArticles">0</div>
                    <div class="stat-label">Artículos Monitoreados</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number" id="highImportance">0</div>
                    <div class="stat-label">Alta Importancia</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number" id="activeConflicts">0</div>
                    <div class="stat-label">Conflictos Activos</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number" id="regionsMonitored">0</div>
                    <div class="stat-label">Regiones Monitoreadas</div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Left Column: AI Analysis and News -->
            <div class="col-lg-8">
                <!-- AI Analysis Section -->
                <div class="card mb-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="section-title mb-0">
                            <i class="fas fa-robot me-2"></i>Análisis Geopolítico IA
                        </h5>
                        <button class="btn btn-ai" onclick="generateAIAnalysis()">
                            <i class="fas fa-magic me-2"></i>Generar Análisis
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="aiAnalysisContent">
                            <div class="text-center text-muted py-4">
                                <i class="fas fa-lightbulb fa-3x mb-3"></i>
                                <p>Haz clic en "Generar Análisis" para obtener un análisis geopolítico completo generado por IA</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Latest Articles -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="section-title mb-0">
                            <i class="fas fa-newspaper me-2"></i>Últimas Noticias Críticas
                        </h5>
                    </div>
                    <div class="card-body">
                        <div id="articlesContainer">
                            <div class="text-center">
                                <div class="loading-spinner"></div>
                                <p class="mt-2">Cargando artículos...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column: System Status and Analytics -->
            <div class="col-lg-4">
                <!-- System Status -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="section-title mb-0">
                            <i class="fas fa-server me-2"></i>Estado del Sistema
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span>Modelo BERT</span>
                            <span id="bertStatus" class="badge bg-secondary">Cargando...</span>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span>API Groq</span>
                            <span id="groqStatus" class="badge bg-secondary">Verificando...</span>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span>Dashboard</span>
                            <span class="badge bg-success">Operativo</span>
                        </div>
                        <div class="d-flex justify-content-between align-items-center">
                            <span>Última actualización</span>
                            <span id="lastUpdate" class="text-muted">--:--:--</span>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="section-title mb-0">
                            <i class="fas fa-bolt me-2"></i>Acciones Rápidas
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <button class="btn btn-outline-light" onclick="testBERT()">
                                <i class="fas fa-brain me-2"></i>Test BERT
                            </button>
                            <button class="btn btn-outline-light" onclick="refreshData()">
                                <i class="fas fa-sync-alt me-2"></i>Actualizar Datos
                            </button>
                            <button class="btn btn-outline-light" onclick="location.reload()">
                                <i class="fas fa-redo me-2"></i>Recargar Dashboard
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Regional Data -->
                <div class="card">
                    <div class="card-header">
                        <h5 class="section-title mb-0">
                            <i class="fas fa-map-marked-alt me-2"></i>Datos por Región
                        </h5>
                    </div>
                    <div class="card-body">
                        <div id="regionData" class="mt-3">
                            <div class="text-center">
                                <div class="loading-spinner"></div>
                                <p class="mt-2">Cargando datos regionales...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Initialize dashboard when page loads
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 Iniciando Dashboard RiskMap Unified');
            initializeDashboard();
        });

        function initializeDashboard() {
            loadDashboardStats();
            loadArticles();
            loadRegionalData();
            checkSystemStatus();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
        }

        async function loadDashboardStats() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();
                
                document.getElementById('totalArticles').textContent = data.total_articles || 0;
                document.getElementById('highImportance').textContent = data.high_importance || 0;
                document.getElementById('activeConflicts').textContent = data.active_conflicts || 0;
                document.getElementById('regionsMonitored').textContent = data.regions_monitored || 0;
                document.getElementById('lastUpdate').textContent = data.last_update || '--:--:--';
                
            } catch (error) {
                console.error('❌ Error loading dashboard stats:', error);
            }
        }

        async function loadArticles() {
            try {
                const response = await fetch('/api/articles');
                const data = await response.json();
                
                const container = document.getElementById('articlesContainer');
                
                if (data.success && data.articles && data.articles.length > 0) {
                    container.innerHTML = data.articles.map(article => `
                        <div class="news-item">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="mb-1">${article.title}</h6>
                                <span class="importance-badge importance-${getImportanceClass(article.importance)}">
                                    ${article.importance}
                                </span>
                            </div>
                            <p class="text-muted mb-2">${article.content}</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <small class="text-muted">
                                    <i class="fas fa-map-marker-alt me-1"></i>${article.location}
                                </small>
                                <small class="text-muted">${new Date(article.published_date).toLocaleString()}</small>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="text-center text-muted py-4"><i class="fas fa-exclamation-triangle fa-2x mb-3"></i><p>No hay artículos disponibles</p></div>';
                }
                
            } catch (error) {
                console.error('❌ Error loading articles:', error);
                document.getElementById('articlesContainer').innerHTML = '<div class="alert alert-danger">Error cargando artículos</div>';
            }
        }

        async function loadRegionalData() {
            try {
                const response = await fetch('/api/articles/by-region');
                const data = await response.json();
                
                const container = document.getElementById('regionData');
                
                if (data.success && data.regions) {
                    const regionHtml = Object.entries(data.regions).map(([region, articles]) => `
                        <div class="d-flex justify-content-between align-items-center p-2 border-bottom">
                            <span><i class="fas fa-flag me-2"></i>${region}</span>
                            <span class="badge bg-primary">${articles.length}</span>
                        </div>
                    `).join('');
                    
                    container.innerHTML = regionHtml || '<div class="text-muted text-center">No hay datos regionales</div>';
                } else {
                    container.innerHTML = '<div class="text-muted text-center">Error cargando datos regionales</div>';
                }
                
            } catch (error) {
                console.error('❌ Error loading regional data:', error);
                document.getElementById('regionData').innerHTML = '<div class="alert alert-danger">Error cargando datos regionales</div>';
            }
        }

        async function checkSystemStatus() {
            try {
                const response = await fetch('/api/system/status');
                const data = await response.json();
                
                // Update BERT status
                const bertStatus = document.getElementById('bertStatus');
                if (data.bert_model_loaded) {
                    bertStatus.className = 'badge bg-success';
                    bertStatus.textContent = 'Operativo';
                } else {
                    bertStatus.className = 'badge bg-danger';
                    bertStatus.textContent = 'Desconectado';
                }
                
                // Update Groq status
                const groqStatus = document.getElementById('groqStatus');
                if (data.groq_available) {
                    groqStatus.className = 'badge bg-success';
                    groqStatus.textContent = 'Disponible';
                } else {
                    groqStatus.className = 'badge bg-warning';
                    groqStatus.textContent = 'No disponible';
                }
                
            } catch (error) {
                console.error('❌ Error checking system status:', error);
            }
        }

        async function generateAIAnalysis() {
            const button = event.target;
            const originalText = button.innerHTML;
            const container = document.getElementById('aiAnalysisContent');
            
            try {
                button.innerHTML = '<div class="loading-spinner me-2"></div>Generando...';
                button.disabled = true;
                
                container.innerHTML = `
                    <div class="text-center py-4">
                        <div class="loading-spinner mb-3"></div>
                        <p>Generando análisis geopolítico con IA...</p>
                    </div>
                `;
                
                const response = await fetch('/api/generate-ai-analysis', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (data.success && data.analysis) {
                    const analysis = data.analysis;
                    container.innerHTML = `
                        <div class="ai-analysis">
                            <h4 class="text-white mb-3">${analysis.title}</h4>
                            <h6 class="text-light mb-4">${analysis.subtitle}</h6>
                            <div class="text-light">${analysis.content}</div>
                            <div class="mt-4 pt-3 border-top border-secondary">
                                <small class="text-light opacity-75">
                                    <i class="fas fa-chart-bar me-2"></i>Fuentes analizadas: ${analysis.sources_count}
                                    | <i class="fas fa-clock me-2"></i>Generado: ${new Date().toLocaleString()}
                                </small>
                            </div>
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Error generando análisis: ${data.error || 'Error desconocido'}
                        </div>
                    `;
                }
                
            } catch (error) {
                console.error('❌ Error generating AI analysis:', error);
                container.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error de conexión al generar análisis
                    </div>
                `;
            } finally {
                button.innerHTML = originalText;
                button.disabled = false;
            }
        }

        async function testBERT() {
            try {
                const response = await fetch('/api/test-bert');
                const data = await response.json();
                
                if (data.success) {
                    alert(`✅ Test BERT exitoso!\\n\\nTexto: ${data.test_text}\\n\\nImportancia: ${data.analysis.importance}\\nConfianza: ${(data.analysis.confidence * 100).toFixed(1)}%`);
                } else {
                    alert(`❌ Error en test BERT: ${data.error}`);
                }
                
            } catch (error) {
                console.error('❌ Error testing BERT:', error);
                alert('❌ Error de conexión al probar BERT');
            }
        }

        function refreshData() {
            console.log('🔄 Actualizando datos...');
            loadDashboardStats();
            loadArticles();
            loadRegionalData();
            checkSystemStatus();
        }

        function getImportanceClass(importance) {
            if (importance >= 90) return 'critical';
            if (importance >= 75) return 'high';
            if (importance >= 50) return 'medium';
            return 'low';
        }
    </script>
</body>
</html>"""

    def run_server(self):
        """Ejecuta el servidor Flask"""
        try:
            logger.info("🚀 Iniciando servidor Flask unificado...")
            logger.info(f"🌐 Dashboard disponible en: http://127.0.0.1:5003")
            logger.info(f"🔌 API disponible en: http://127.0.0.1:5003/api/")
            
            self.flask_app.run(host='127.0.0.1', port=5003, debug=False)
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando servidor: {e}")
            raise


# Función principal para ejecutar la aplicación
def main():
    """Función principal que ejecuta la aplicación unificada"""
    try:
        logger.info("="*60)
        logger.info("🚀 INICIANDO RISKMAP UNIFIED v3.0 - SISTEMA COMPLETO")
        logger.info("="*60)
        
        # Crear y configurar la aplicación
        app = RiskMapUnifiedApplication()
        
        # Crear datos de prueba
        app.create_test_data()
        
        # Inicializar BERT (no bloqueante)
        logger.info("🧠 Intentando cargar modelo BERT...")
        try:
            app.initialize_bert_model()
        except Exception as bert_error:
            logger.warning(f"⚠️  BERT no disponible: {bert_error}")
            logger.info("📝 Continuando con análisis de respaldo...")
        
        # Configurar rutas de Flask
        app.setup_flask_routes()
        
        # Ejecutar servidor
        app.run_server()
        
    except KeyboardInterrupt:
        logger.info("👋 Aplicación detenida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        raise


if __name__ == "__main__":
    main()
