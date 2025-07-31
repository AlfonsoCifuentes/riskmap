"""
Minimal Flask Dashboard with BERT Integration - DEBUG VERSION
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__, 
    template_folder='src/dashboard/templates',
    static_folder='src/dashboard/static')
CORS(app)

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
            'title': 'Military tensions escalate in Eastern Europe',
            'content': 'Recent developments show increased military activity',
            'location': 'Ukraine',
            'risk_level': 'high',
            'risk_score': 0.8,
            'created_at': datetime.now().isoformat(),
            'country': 'Ukraine'
        },
        {
            'id': 2,
            'title': 'Economic summit reaches agreement',
            'content': 'World leaders agree on trade policies',
            'location': 'Geneva',
            'risk_level': 'low',
            'risk_score': 0.3,
            'created_at': datetime.now().isoformat(),
            'country': 'Switzerland'
        }
    ] * 6  # Repeat to have 12 articles
    
    return jsonify({
        'articles': mock_articles,
        'page': 1,
        'total': len(mock_articles)
    })

@app.route('/api/test-bert')
def test_bert_route():
    """Test route to verify routing works"""
    print("✅ Test BERT route called successfully!")
    return jsonify({'message': 'BERT endpoint is working!', 'status': 'OK'})

@app.route('/api/analyze-importance', methods=['POST'])
def analyze_importance_bert():
    """
    BERT importance analysis endpoint
    """
    print("🧠 BERT analyze-importance endpoint called!")
    
    try:
        article_data = request.get_json()
        print(f"📰 Received article data: {article_data}")
        
        if not article_data:
            return jsonify({
                'error': 'No article data provided',
                'importance_factor': 30.0,
                'risk_factor': 30.0
            }), 400
        
        # Simple fallback calculation for now
        title = article_data.get('title', '').lower()
        
        # Basic scoring based on keywords
        importance = 50  # base score
        
        critical_words = ['war', 'attack', 'crisis', 'nuclear', 'terrorism', 'conflict']
        for word in critical_words:
            if word in title:
                importance += 20
        
        high_risk_words = ['military', 'army', 'bomb', 'missile', 'violence']
        for word in high_risk_words:
            if word in title:
                importance += 10
        
        # Cap at 100
        importance = min(100, importance)
        
        result = {
            'importance_factor': importance,
            'risk_factor': importance,
            'bert_analysis': {
                'negative_sentiment': 0.6,
                'positive_sentiment': 0.4,
                'confidence': 0.8
            },
            'article_metadata': {
                'title': article_data.get('title', '')[:100],
                'location': article_data.get('location', ''),
                'risk_level': article_data.get('risk_level', 'unknown'),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'model_info': {
                'primary_model': 'fallback-keyword-analysis',
                'analysis_type': 'basic_keyword_scoring',
                'fallback_used': True
            }
        }
        
        print(f"📊 Returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in BERT analysis: {e}")
        return jsonify({
            'importance_factor': 40,
            'risk_factor': 40,
            'error': str(e),
            'fallback_used': True,
            'analysis_timestamp': datetime.now().isoformat()
        }), 200

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard Minimal con BERT...")
    print("🌐 URL: http://localhost:5001")
    print("🧠 BERT Endpoint: http://localhost:5001/api/analyze-importance")
    print("🧪 Test Endpoint: http://localhost:5001/api/test-bert")
    print("-" * 50)
    
    app.run(host='127.0.0.1', port=5001, debug=True, use_reloader=False)
