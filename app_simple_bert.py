"""
Simplified Flask Dashboard with BERT Integration
Versión simplificada para evitar conflictos de dependencias
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import random

# Add project root to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Simple logger
class SimpleLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")

logger = SimpleLogger()

# Flask app setup
app = Flask(__name__, 
    template_folder=str(current_dir / 'src' / 'dashboard' / 'templates'),
    static_folder=str(current_dir / 'src' / 'dashboard' / 'static'))
CORS(app)

# Database path
DB_PATH = current_dir / 'intelligence_data.db'

def get_db_connection():
    """Get database connection with proper settings."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main dashboard route."""
    return render_template('modern_dashboard_updated.html')

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get stats from articles table
        cursor.execute("SELECT COUNT(*) FROM articles WHERE date(created_at) = date('now')")
        today_articles = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level = 'high'")
        high_risk_count = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(DISTINCT country) FROM articles WHERE country IS NOT NULL")
        countries_monitored = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'total_articles': total_articles,
            'today_articles': today_articles,
            'high_risk_alerts': high_risk_count,
            'countries_monitored': countries_monitored,
            'last_update': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'total_articles': 0,
            'today_articles': 0,
            'high_risk_alerts': 0,
            'countries_monitored': 0,
            'last_update': datetime.now().isoformat()
        }), 500

@app.route('/api/articles')
def get_articles():
    """Get articles with pagination."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 12))
        offset = (page - 1) * limit
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM articles 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        articles = []
        for row in cursor.fetchall():
            article = dict(row)
            article['risk_score'] = article.get('risk_score', 0.5)
            articles.append(article)
        
        conn.close()
        
        return jsonify({
            'articles': articles,
            'page': page,
            'total': len(articles)
        })
        
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        return jsonify({'articles': [], 'page': 1, 'total': 0}), 500

# ==================== BERT IMPORTANCE ENDPOINT ====================

@app.route('/api/test-bert')
def test_bert_route():
    """Ruta de prueba para verificar que funciona"""
    return jsonify({'message': 'BERT endpoint is working!', 'status': 'OK'})

@app.route('/api/analyze-importance', methods=['POST'])
def analyze_importance_bert():
    """
    Advanced importance and risk factor analysis using BERT model for political news sentiment
    """
    try:
        # Get article data
        article_data = request.get_json()
        
        if not article_data:
            return jsonify({
                'error': 'No article data provided',
                'importance_factor': 30.0,
                'risk_factor': 30.0
            }), 400
        
        # Validate required fields
        if not article_data.get('title') and not article_data.get('content'):
            return jsonify({
                'error': 'At least title or content is required',
                'importance_factor': 30.0,
                'risk_factor': 30.0
            }), 400
        
        # Try to use BERT model for advanced analysis
        try:
            # Import BERT components only when needed to avoid startup errors
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
            import torch
            
            # Load the specific BERT model for political news sentiment analysis
            model_name = "leroyrr/bert-for-political-news-sentiment-analysis-lora"
            
            # Create sentiment analysis pipeline
            sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                return_all_scores=True
            )
            
            # Prepare text for analysis
            title = article_data.get('title', '')
            content = article_data.get('content', '')
            analysis_text = f"{title}. {content[:500]}"  # Limit text for performance
            
            # Analyze sentiment with BERT
            bert_results = sentiment_analyzer(analysis_text)
            
            # Extract sentiment scores
            sentiment_scores = {result['label']: result['score'] for result in bert_results}
            
            # Calculate advanced importance based on BERT analysis
            negative_sentiment = sentiment_scores.get('NEGATIVE', 0)
            positive_sentiment = sentiment_scores.get('POSITIVE', 0)
            
            # Higher negative sentiment in political news often indicates higher importance/risk
            bert_importance = (negative_sentiment * 80) + (positive_sentiment * 20)
            
            logger.info(f"BERT Analysis - Negative: {negative_sentiment:.3f}, Positive: {positive_sentiment:.3f}, Importance: {bert_importance:.2f}")
            
        except Exception as bert_error:
            logger.warning(f"BERT model not available, using fallback: {bert_error}")
            # Fallback to enhanced local calculation
            bert_importance = calculate_fallback_importance(article_data)
            sentiment_scores = {'NEGATIVE': 0.5, 'POSITIVE': 0.5}
        
        # Enhanced risk factor calculation
        risk_factor = calculate_enhanced_risk_factor(article_data, bert_importance)
        
        # Combined importance factor
        final_importance = (bert_importance * 0.7) + (risk_factor * 0.3)
        
        # Ensure score is between 10-100
        final_importance = max(10, min(100, final_importance))
        
        return jsonify({
            'importance_factor': round(final_importance, 2),
            'risk_factor': round(risk_factor, 2),
            'bert_analysis': {
                'negative_sentiment': round(sentiment_scores.get('NEGATIVE', 0), 3),
                'positive_sentiment': round(sentiment_scores.get('POSITIVE', 0), 3),
                'confidence': round(max(sentiment_scores.values()) if sentiment_scores else 0.5, 3)
            },
            'article_metadata': {
                'title': article_data.get('title', '')[:100],
                'location': article_data.get('location', ''),
                'risk_level': article_data.get('risk_level', 'unknown'),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'model_info': {
                'primary_model': 'leroyrr/bert-for-political-news-sentiment-analysis-lora',
                'analysis_type': 'advanced_political_sentiment',
                'fallback_used': 'bert_model' not in locals()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in BERT importance analysis: {e}")
        # Return fallback score on any error
        fallback_score = calculate_fallback_importance(article_data if 'article_data' in locals() else {})
        
        return jsonify({
            'importance_factor': fallback_score,
            'risk_factor': fallback_score,
            'error': str(e),
            'fallback_used': True,
            'analysis_timestamp': datetime.now().isoformat()
        }), 200

def calculate_fallback_importance(article_data):
    """Enhanced fallback calculation when BERT is not available"""
    if not article_data:
        return 30.0
    
    score = 0.0
    
    # Risk level analysis (40% weight)
    risk_level = article_data.get('risk_level', 'unknown').lower()
    risk_mapping = {
        'critical': 95, 'high': 85, 'medium': 60, 'low': 35, 'unknown': 45
    }
    score += risk_mapping.get(risk_level, 45) * 0.4
    
    # Temporal relevance (30% weight)
    recency_score = calculate_recency_score(article_data.get('created_at') or article_data.get('published_date'))
    score += recency_score * 0.3
    
    # Content analysis (20% weight)
    content_score = analyze_content_keywords(article_data)
    score += content_score * 0.2
    
    # Location importance (10% weight)
    location_score = analyze_location_importance(article_data.get('location', ''))
    score += location_score * 0.1
    
    return max(10, min(100, score))

def calculate_enhanced_risk_factor(article_data, bert_importance):
    """Calculate enhanced risk factor combining multiple signals"""
    base_risk = bert_importance * 0.6  # BERT contributes 60%
    
    # Geographic risk assessment
    location = article_data.get('location', '').lower()
    geo_risk = 40  # default
    
    high_risk_regions = {
        'ukraine': 95, 'gaza': 95, 'israel': 90, 'palestine': 90,
        'syria': 85, 'afghanistan': 80, 'yemen': 85, 'lebanon': 75,
        'iran': 80, 'iraq': 75, 'somalia': 70, 'sudan': 80
    }
    
    for region, risk_score in high_risk_regions.items():
        if region in location:
            geo_risk = risk_score
            break
    
    # Temporal escalation factor
    temporal_factor = calculate_recency_score(article_data.get('created_at'))
    
    # Combine factors
    final_risk = (base_risk * 0.5) + (geo_risk * 0.3) + (temporal_factor * 0.2)
    
    return max(10, min(100, final_risk))

def calculate_recency_score(date_str):
    """Calculate recency score based on article timestamp"""
    if not date_str:
        return 40.0
    
    try:
        from datetime import datetime, timezone
        
        if isinstance(date_str, str):
            # Handle multiple date formats
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    article_date = datetime.strptime(date_str.replace('Z', '').replace('+00:00', ''), fmt)
                    break
                except ValueError:
                    continue
            else:
                return 40.0
        else:
            article_date = date_str
        
        if article_date.tzinfo is None:
            article_date = article_date.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        hours_diff = (now - article_date).total_seconds() / 3600
        
        # More aggressive scoring for recent news
        if hours_diff < 1:
            return 100
        elif hours_diff < 3:
            return 90
        elif hours_diff < 12:
            return 75
        elif hours_diff < 24:
            return 60
        elif hours_diff < 48:
            return 45
        elif hours_diff < 168:  # 1 week
            return 30
        else:
            return 15
            
    except Exception:
        return 40.0

def analyze_content_keywords(article_data):
    """Enhanced keyword analysis for content importance"""
    title = (article_data.get('title', '') + ' ' + article_data.get('content', '')).lower()
    
    # Weighted keyword categories
    critical_keywords = {
        'nuclear': 100, 'war': 95, 'invasion': 95, 'attack': 90, 'bombing': 90,
        'missile': 85, 'crisis': 80, 'conflict': 75, 'terrorism': 95, 'coup': 90
    }
    
    high_impact_keywords = {
        'military': 70, 'army': 65, 'defense': 60, 'security': 55, 'border': 60,
        'government': 50, 'parliament': 45, 'election': 55, 'protest': 65
    }
    
    medium_impact_keywords = {
        'economic': 40, 'trade': 35, 'diplomatic': 45, 'alliance': 50, 'sanction': 70
    }
    
    score = 0
    word_count = len(title.split())
    
    # Check critical keywords
    for keyword, weight in critical_keywords.items():
        if keyword in title:
            score += weight / max(word_count / 10, 1)  # Normalize by content length
    
    # Check high impact keywords  
    for keyword, weight in high_impact_keywords.items():
        if keyword in title:
            score += weight / max(word_count / 15, 1)
            
    # Check medium impact keywords
    for keyword, weight in medium_impact_keywords.items():
        if keyword in title:
            score += weight / max(word_count / 20, 1)
    
    return min(100, score)

def analyze_location_importance(location):
    """Analyze geopolitical importance of location"""
    if not location:
        return 40
    
    location = location.lower()
    
    # Strategic importance mapping
    strategic_locations = {
        'washington': 90, 'moscow': 90, 'beijing': 85, 'london': 80, 'paris': 75,
        'berlin': 75, 'tokyo': 80, 'seoul': 70, 'new delhi': 75, 'tel aviv': 85,
        'tehran': 80, 'ankara': 70, 'cairo': 65, 'riyadh': 75, 'brasilia': 60
    }
    
    conflict_zones = {
        'ukraine': 95, 'gaza': 95, 'west bank': 90, 'syria': 85, 'afghanistan': 80,
        'yemen': 85, 'lebanon': 75, 'iraq': 75, 'somalia': 70, 'sudan': 80,
        'myanmar': 70, 'haiti': 65, 'libya': 70, 'mali': 65
    }
    
    # Check strategic locations
    for loc, importance in strategic_locations.items():
        if loc in location:
            return importance
    
    # Check conflict zones
    for loc, importance in conflict_zones.items():
        if loc in location:
            return importance
    
    # Default regional importance
    regions = {
        'europe': 60, 'asia': 55, 'middle east': 80, 'africa': 50,
        'america': 55, 'pacific': 50
    }
    
    for region, importance in regions.items():
        if region in location:
            return importance
    
    return 40  # Default score

# ==================== MAIN ====================

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard Simple con BERT...")
    print(f"📂 Base de datos: {DB_PATH}")
    print("🌐 URL: http://localhost:5000")
    print("🧠 BERT Endpoint: http://localhost:5000/api/analyze-importance")
    print("📊 Stats: http://localhost:5000/api/dashboard/stats")
    print("📰 Articles: http://localhost:5000/api/articles")
    print("🔄 Para detener: Ctrl+C")
    print("-" * 50)
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido por el usuario")
