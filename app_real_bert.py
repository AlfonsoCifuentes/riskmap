"""
Flask Dashboard with REAL BERT Integration - NO FALLBACK VERSION
Implementación que garantiza el uso del modelo BERT de HuggingFace
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
import logging

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
    CRITICAL: Esta función debe cargar el modelo real o fallar
    """
    global bert_model, bert_tokenizer, sentiment_pipeline
    
    try:
        logger.info("🧠 Iniciando carga del modelo BERT político...")
        
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        import torch
        
        # Modelo específico para análisis de sentimiento político
        model_name = "leroyrr/bert-for-political-news-sentiment-analysis-lora"
        
        logger.info(f"📥 Descargando modelo: {model_name}")
        
        # Cargar tokenizer y modelo
        bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
        bert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Crear pipeline de análisis
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=bert_model,
            tokenizer=bert_tokenizer,
            return_all_scores=True,
            device=0 if torch.cuda.is_available() else -1  # GPU si está disponible
        )
        
        logger.info("✅ Modelo BERT cargado exitosamente")
        logger.info(f"🔧 Dispositivo: {'GPU' if torch.cuda.is_available() else 'CPU'}")
        
        # Test del modelo
        test_result = sentiment_pipeline("This is a test of political sentiment analysis")
        logger.info(f"🧪 Test del modelo: {test_result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FALLO CRÍTICO: No se pudo cargar el modelo BERT: {e}")
        return False

def analyze_with_bert(text):
    """
    Analiza texto usando el modelo BERT político real
    """
    global sentiment_pipeline
    
    if sentiment_pipeline is None:
        raise RuntimeError("Modelo BERT no está disponible")
    
    try:
        # Limpiar y preparar texto
        cleaned_text = text.strip()[:512]  # BERT tiene límite de tokens
        
        # Análisis con BERT
        results = sentiment_pipeline(cleaned_text)
        
        # Extraer scores
        sentiment_scores = {result['label']: result['score'] for result in results}
        
        # Calcular importancia basada en sentimiento político
        negative_score = sentiment_scores.get('NEGATIVE', sentiment_scores.get('negative', 0))
        positive_score = sentiment_scores.get('POSITIVE', sentiment_scores.get('positive', 0))
        
        # En noticias políticas, sentimiento negativo suele indicar mayor importancia
        importance = (negative_score * 85) + (positive_score * 15)
        
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
    # Mock data for testing
    mock_articles = [
        {
            'id': 1,
            'title': 'Escalada militar en conflicto internacional',
            'content': 'Las tensiones militares han aumentado significativamente en la región con movilización de tropas',
            'location': 'Europa Oriental',
            'risk_level': 'high',
            'risk_score': 0.8,
            'created_at': datetime.now().isoformat(),
            'country': 'Ukraine'
        },
        {
            'id': 2,
            'title': 'Cumbre económica internacional concluye exitosamente',
            'content': 'Los líderes mundiales alcanzan acuerdos comerciales importantes para la estabilidad económica',
            'location': 'Geneva',
            'risk_level': 'low',
            'risk_score': 0.3,
            'created_at': datetime.now().isoformat(),
            'country': 'Switzerland'
        },
        {
            'id': 3,
            'title': 'Amenaza nuclear en Asia Pacific aumenta tensiones',
            'content': 'Expertos en seguridad expresan preocupación por el desarrollo de armas nucleares en la región',
            'location': 'Asia Pacific',
            'risk_level': 'critical',
            'risk_score': 0.95,
            'created_at': datetime.now().isoformat(),
            'country': 'Multiple'
        },
        {
            'id': 4,
            'title': 'Ataque terrorista en capital europea deja múltiples víctimas',
            'content': 'Un ataque coordinado ha impactado el centro de una importante ciudad europea',
            'location': 'Paris',
            'risk_level': 'critical',
            'risk_score': 0.9,
            'created_at': datetime.now().isoformat(),
            'country': 'France'
        }
    ] * 5  # Repeat to have more articles
    
    return jsonify({
        'articles': mock_articles,
        'page': 1,
        'total': len(mock_articles)
    })

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
    ANÁLISIS BERT REAL - NO HAY FALLBACK
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
                'model_used': 'leroyrr/bert-for-political-news-sentiment-analysis-lora'
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
                'primary_model': 'leroyrr/bert-for-political-news-sentiment-analysis-lora',
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

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard con BERT REAL - NO FALLBACK")
    print("🧠 Cargando modelo BERT para análisis político...")
    
    # CRÍTICO: Cargar modelo BERT antes de iniciar servidor
    if not initialize_bert_model():
        print("❌ FALLO CRÍTICO: No se pudo cargar modelo BERT")
        print("🛑 El servidor NO se iniciará sin el modelo de IA")
        exit(1)
    
    print("✅ Modelo BERT cargado exitosamente")
    print("🌐 URL: http://localhost:5002")
    print("🧠 BERT Endpoint: http://localhost:5002/api/analyze-importance")
    print("🧪 Test BERT: http://localhost:5002/api/test-bert")
    print("-" * 60)
    
    try:
        app.run(host='127.0.0.1', port=5002, debug=False)  # Debug=False para estabilidad
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido por el usuario")
