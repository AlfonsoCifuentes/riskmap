"""
Advanced REST API for the Geopolitical Intelligence System.
Provides comprehensive endpoints for data access, system monitoring, and management.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import logging
from functools import wraps
import time

# Import system modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config, logger
from monitoring.system_monitor import system_monitor
from data_quality.validator import data_validator
from reporting.report_generator import ReportGenerator


app = Flask(__name__)
CORS(app)

# Configure Flask logging
app.logger.setLevel(logging.INFO)

# Database path
DB_PATH = config.get('database', {}).get('path', 'data/riskmap.db')

# Rate limiting decorator
def rate_limit(max_requests=100, window=3600):
    """Simple rate limiting decorator."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Simple in-memory rate limiting (for production, use Redis)
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            current_time = time.time()
            
            if not hasattr(wrapper, 'requests'):
                wrapper.requests = {}
            
            if client_ip not in wrapper.requests:
                wrapper.requests[client_ip] = []
            
            # Clean old requests
            wrapper.requests[client_ip] = [
                req_time for req_time in wrapper.requests[client_ip]
                if current_time - req_time < window
            ]
            
            if len(wrapper.requests[client_ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            wrapper.requests[client_ip].append(current_time)
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/v1/health', methods=['GET'])
@rate_limit(max_requests=50, window=3600)
def api_health():
    """Get system health status."""
    try:
        health_status = system_monitor.check_system_health()
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Error in health check API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/metrics', methods=['GET'])
@rate_limit(max_requests=50, window=3600)
def api_metrics():
    """Get system performance metrics."""
    try:
        hours = request.args.get('hours', 24, type=int)
        if hours > 168:  # Limit to 1 week
            hours = 168
        
        metrics = system_monitor.get_performance_metrics(hours=hours)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error in metrics API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/articles', methods=['GET'])
@rate_limit(max_requests=200, window=3600)
def api_articles():
    """Get articles with filtering and pagination."""
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        language = request.args.get('language')
        sentiment = request.args.get('sentiment')
        risk_level = request.args.get('risk_level')
        days = request.args.get('days', 7, type=int)
        search = request.args.get('search')
        
        # Build query
        query = """
            SELECT a.*, ar.sentiment, ar.risk_level, ar.summary, ar.entities
            FROM articles a
            LEFT JOIN analysis_results ar ON a.id = ar.article_id
            WHERE a.created_at > datetime('now', '-{} days')
        """.format(days)
        
        params = []
        
        if language:
            query += " AND a.language = ?"
            params.append(language)
        
        if sentiment:
            query += " AND ar.sentiment = ?"
            params.append(sentiment)
        
        if risk_level:
            query += " AND ar.risk_level = ?"
            params.append(risk_level)
        
        if search:
            query += " AND (a.title LIKE ? OR a.content LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        # Add ordering and pagination
        query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        # Execute query
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        articles = [dict(row) for row in cursor.fetchall()]
        
        # Get total count for pagination
        count_query = query.split(' LIMIT')[0].replace('a.*, ar.sentiment, ar.risk_level, ar.summary, ar.entities', 'COUNT(*)')
        cursor.execute(count_query, params[:-2])  # Remove LIMIT and OFFSET params
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Parse JSON fields
        for article in articles:
            if article.get('entities'):
                try:
                    article['entities'] = json.loads(article['entities'])
                except (json.JSONDecodeError, TypeError):
                    article['entities'] = []
        
        return jsonify({
            'articles': articles,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error in articles API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/articles/<int:article_id>', methods=['GET'])
@rate_limit(max_requests=200, window=3600)
def api_article_detail(article_id):
    """Get detailed information about a specific article."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.*, ar.sentiment, ar.risk_level, ar.summary, ar.entities,
                   ar.translated_content, ar.key_topics, ar.confidence_score
            FROM articles a
            LEFT JOIN analysis_results ar ON a.id = ar.article_id
            WHERE a.id = ?
        """, (article_id,))
        
        article = cursor.fetchone()
        conn.close()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        article_dict = dict(article)
        
        # Parse JSON fields
        for field in ['entities', 'key_topics']:
            if article_dict.get(field):
                try:
                    article_dict[field] = json.loads(article_dict[field])
                except (json.JSONDecodeError, TypeError):
                    article_dict[field] = []
        
        return jsonify(article_dict)
        
    except Exception as e:
        logger.error(f"Error in article detail API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/analytics/sentiment', methods=['GET'])
@rate_limit(max_requests=50, window=3600)
def api_sentiment_analytics():
    """Get sentiment analytics over time."""
    try:
        days = request.args.get('days', 7, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(a.created_at) as date,
                ar.sentiment,
                COUNT(*) as count
            FROM articles a
            JOIN analysis_results ar ON a.id = ar.article_id
            WHERE a.created_at > datetime('now', '-{} days')
            AND ar.sentiment IS NOT NULL
            GROUP BY DATE(a.created_at), ar.sentiment
            ORDER BY date DESC
        """.format(days))
        
        results = cursor.fetchall()
        conn.close()
        
        # Organize data by date
        analytics = {}
        for date, sentiment, count in results:
            if date not in analytics:
                analytics[date] = {'positive': 0, 'negative': 0, 'neutral': 0}
            analytics[date][sentiment] = count
        
        return jsonify({
            'period_days': days,
            'sentiment_by_date': analytics
        })
        
    except Exception as e:
        logger.error(f"Error in sentiment analytics API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/analytics/risk', methods=['GET'])
@rate_limit(max_requests=50, window=3600)
def api_risk_analytics():
    """Get risk level analytics."""
    try:
        days = request.args.get('days', 7, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ar.risk_level,
                COUNT(*) as count,
                AVG(ar.confidence_score) as avg_confidence
            FROM articles a
            JOIN analysis_results ar ON a.id = ar.article_id
            WHERE a.created_at > datetime('now', '-{} days')
            AND ar.risk_level IS NOT NULL
            GROUP BY ar.risk_level
        """.format(days))
        
        results = cursor.fetchall()
        conn.close()
        
        risk_analytics = {
            'period_days': days,
            'risk_distribution': {
                risk_level: {
                    'count': count,
                    'avg_confidence': round(avg_confidence, 2) if avg_confidence else 0
                }
                for risk_level, count, avg_confidence in results
            }
        }
        
        return jsonify(risk_analytics)
        
    except Exception as e:
        logger.error(f"Error in risk analytics API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/analytics/entities', methods=['GET'])
@rate_limit(max_requests=50, window=3600)
def api_entities_analytics():
    """Get most mentioned entities."""
    try:
        days = request.args.get('days', 7, type=int)
        limit = min(request.args.get('limit', 20, type=int), 100)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ar.entities
            FROM articles a
            JOIN analysis_results ar ON a.id = ar.article_id
            WHERE a.created_at > datetime('now', '-{} days')
            AND ar.entities IS NOT NULL
            AND ar.entities != ''
        """.format(days))
        
        results = cursor.fetchall()
        conn.close()
        
        # Count entity mentions
        entity_counts = {}
        for (entities_json,) in results:
            try:
                entities = json.loads(entities_json)
                for entity in entities:
                    if isinstance(entity, dict) and 'text' in entity:
                        text = entity['text']
                        entity_type = entity.get('type', 'UNKNOWN')
                        
                        if text not in entity_counts:
                            entity_counts[text] = {'count': 0, 'type': entity_type}
                        entity_counts[text]['count'] += 1
                        
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Sort by count and limit
        top_entities = sorted(
            [(text, data) for text, data in entity_counts.items()],
            key=lambda x: x[1]['count'],
            reverse=True
        )[:limit]
        
        return jsonify({
            'period_days': days,
            'top_entities': [
                {
                    'entity': text,
                    'count': data['count'],
                    'type': data['type']
                }
                for text, data in top_entities
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in entities analytics API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/data-quality', methods=['GET'])
@rate_limit(max_requests=20, window=3600)
def api_data_quality():
    """Get data quality report."""
    try:
        days = request.args.get('days', 7, type=int)
        quality_report = data_validator.get_quality_report(days=days)
        return jsonify(quality_report)
    except Exception as e:
        logger.error(f"Error in data quality API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/reports/generate', methods=['POST'])
@rate_limit(max_requests=10, window=3600)
def api_generate_report():
    """Generate a new report on demand."""
    try:
        data = request.get_json()
        report_type = data.get('type', 'daily')
        
        if report_type not in ['daily', 'weekly']:
            return jsonify({'error': 'Invalid report type'}), 400
        
        reporter = ReportGenerator()
        
        if report_type == 'daily':
            reports = reporter.generate_daily_report()
        else:
            reports = reporter.generate_weekly_report()
        
        return jsonify({
            'success': True,
            'report_type': report_type,
            'files_generated': reports
        })
        
    except Exception as e:
        logger.error(f"Error generating report via API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/search', methods=['GET'])
@rate_limit(max_requests=100, window=3600)
def api_search():
    """Advanced search across articles."""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        language = request.args.get('language')
        sentiment = request.args.get('sentiment')
        risk_level = request.args.get('risk_level')
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        # Build search query
        search_query = """
            SELECT a.id, a.title, a.url, a.created_at, a.language,
                   ar.sentiment, ar.risk_level, ar.summary,
                   (CASE 
                    WHEN a.title LIKE ? THEN 3 
                    WHEN a.content LIKE ? THEN 2 
                    WHEN ar.summary LIKE ? THEN 1 
                    ELSE 0 END) as relevance_score
            FROM articles a
            LEFT JOIN analysis_results ar ON a.id = ar.article_id
            WHERE (a.title LIKE ? OR a.content LIKE ? OR ar.summary LIKE ?)
        """
        
        search_term = f"%{query}%"
        params = [search_term] * 6
        
        if language:
            search_query += " AND a.language = ?"
            params.append(language)
        
        if sentiment:
            search_query += " AND ar.sentiment = ?"
            params.append(sentiment)
        
        if risk_level:
            search_query += " AND ar.risk_level = ?"
            params.append(risk_level)
        
        search_query += " ORDER BY relevance_score DESC, a.created_at DESC LIMIT ?"
        params.append(limit)
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(search_query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'query': query,
            'results': results,
            'total_found': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error in search API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/stats', methods=['GET'])
@rate_limit(max_requests=50, window=3600)
def api_stats():
    """Get general system statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        analyzed_articles = cursor.fetchone()[0]
        
        # Recent activity (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
        """)
        recent_articles = cursor.fetchone()[0]
        
        # Language distribution
        cursor.execute("""
            SELECT language, COUNT(*) 
            FROM articles 
            WHERE language IS NOT NULL 
            GROUP BY language 
            ORDER BY COUNT(*) DESC
        """)
        language_dist = dict(cursor.fetchall())
        
        # Processing statistics
        processing_rate = (analyzed_articles / total_articles * 100) if total_articles > 0 else 0
        
        conn.close()
        
        return jsonify({
            'total_articles': total_articles,
            'analyzed_articles': analyzed_articles,
            'processing_rate': round(processing_rate, 2),
            'recent_articles_24h': recent_articles,
            'language_distribution': language_dist,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in stats API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/info', methods=['GET'])
def api_info():
    """Get API information and endpoints."""
    return jsonify({
        'name': 'Geopolitical Intelligence System API',
        'version': '1.0',
        'endpoints': {
            'GET /api/v1/health': 'System health check',
            'GET /api/v1/metrics': 'Performance metrics',
            'GET /api/v1/articles': 'List articles with filters',
            'GET /api/v1/articles/<id>': 'Get article details',
            'GET /api/v1/analytics/sentiment': 'Sentiment analytics',
            'GET /api/v1/analytics/risk': 'Risk analytics',
            'GET /api/v1/analytics/entities': 'Entity analytics',
            'GET /api/v1/data-quality': 'Data quality report',
            'POST /api/v1/reports/generate': 'Generate reports',
            'GET /api/v1/search': 'Search articles',
            'GET /api/v1/stats': 'System statistics',
            'GET /api/v1/info': 'API information'
        }
    })


@app.route('/api/v1/collection/global', methods=['POST'])
@rate_limit(max_requests=10, window=3600)
def api_global_collection():
    """API endpoint to trigger global news collection."""
    try:
        data = request.get_json() or {}
        languages = data.get('languages', ['en', 'es', 'fr', 'de', 'ru', 'zh', 'ar'])
        include_intelligence = data.get('include_intelligence', True)
        
        # Import and run global collection
        from data_ingestion.global_news_collector import GlobalNewsSourcesRegistry, EnhancedNewsAPICollector, GlobalRSSCollector
        from data_ingestion.intelligence_sources import IntelligenceCollector
        
        # Initialize collectors
        global_registry = GlobalNewsSourcesRegistry()
        newsapi_collector = EnhancedNewsAPICollector()
        rss_collector = GlobalRSSCollector()
        intel_collector = IntelligenceCollector()
        
        total_articles = 0
        results = {}
        
        # Collect from global RSS sources
        for language in languages:
            try:
                sources = global_registry.get_sources_by_language(language)
                articles = rss_collector.collect_from_sources(sources)
                total_articles += len(articles)
                results[f'rss_{language}'] = len(articles)
                logger.info(f"Global RSS collection for {language}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"RSS collection failed for {language}: {e}")
                results[f'rss_{language}_error'] = str(e)
        
        # Collect from enhanced NewsAPI
        for language in languages:
            try:
                articles = newsapi_collector.collect_multilingual_headlines(language)
                total_articles += len(articles)
                results[f'newsapi_{language}'] = len(articles)
                logger.info(f"NewsAPI collection for {language}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"NewsAPI collection failed for {language}: {e}")
                results[f'newsapi_{language}_error'] = str(e)
        
        # Collect from intelligence sources
        if include_intelligence:
            try:
                intel_articles = intel_collector.collect_all_sources()
                total_articles += len(intel_articles)
                results['intelligence'] = len(intel_articles)
                logger.info(f"Intelligence collection: {len(intel_articles)} articles")
            except Exception as e:
                logger.error(f"Intelligence collection failed: {e}")
                results['intelligence_error'] = str(e)
        
        return jsonify({
            'status': 'success',
            'total_articles_collected': total_articles,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in global collection API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/collection/regional/<region>', methods=['POST'])
@rate_limit(max_requests=10, window=3600)
def api_regional_collection(region):
    """API endpoint to trigger regional news collection."""
    try:
        valid_regions = ['americas', 'europe', 'asia_pacific', 'middle_east', 'africa']
        if region not in valid_regions:
            return jsonify({'error': f'Invalid region. Must be one of: {valid_regions}'}), 400
        
        data = request.get_json() or {}
        max_articles_per_source = data.get('max_articles_per_source', 15)
        
        # Import collectors
        from data_ingestion.global_news_collector import GlobalNewsSourcesRegistry, GlobalRSSCollector
        
        global_registry = GlobalNewsSourcesRegistry()
        rss_collector = GlobalRSSCollector()
        
        # Determine priority languages for region
        priority_languages = ['en']  # Default fallback
        if region == 'americas':
            priority_languages = ['en', 'es', 'pt']
        elif region == 'europe':
            priority_languages = ['en', 'de', 'fr', 'es', 'it', 'ru', 'nl']
        elif region == 'asia_pacific':
            priority_languages = ['en', 'zh', 'ja', 'ko']
        elif region == 'middle_east':
            priority_languages = ['ar', 'en']
        elif region == 'africa':
            priority_languages = ['en', 'fr', 'ar']
        
        total_articles = 0
        results = {}
        
        for language in priority_languages:
            try:
                sources = global_registry.get_sources_by_region(language, region)
                if sources:
                    articles = rss_collector.collect_from_sources(sources, max_articles_per_source)
                    total_articles += len(articles)
                    results[f'{region}_{language}'] = len(articles)
                    logger.info(f"Regional collection {region}/{language}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"Regional collection failed for {region}/{language}: {e}")
                results[f'{region}_{language}_error'] = str(e)
        
        return jsonify({
            'status': 'success',
            'region': region,
            'total_articles_collected': total_articles,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in regional collection API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/sources/global', methods=['GET'])
@rate_limit(max_requests=50, window=3600)
def api_global_sources():
    """Get information about available global news sources."""
    try:
        from data_ingestion.global_news_collector import GlobalNewsSourcesRegistry
        from data_ingestion.intelligence_sources import IntelligenceSourcesRegistry
        
        global_registry = GlobalNewsSourcesRegistry()
        intel_registry = IntelligenceSourcesRegistry()
        
        # Get source information
        global_sources = global_registry.get_all_sources()
        intel_sources = intel_registry.get_all_sources()
        
        # Organize by categories
        source_info = {
            'global_news': {
                'total_sources': len(global_sources),
                'languages': global_registry.get_supported_languages(),
                'sources_by_language': {},
                'sample_sources': global_sources[:10]  # First 10 as sample
            },
            'intelligence': {
                'total_sources': len(intel_sources),
                'categories': ['think_tanks', 'academic_institutions', 'government_sources'],
                'high_credibility_count': len([s for s in intel_sources if s.get('credibility') == 'high']),
                'sample_sources': intel_sources[:5]  # First 5 as sample
            }
        }
        
        # Count sources by language
        for lang in global_registry.get_supported_languages():
            lang_sources = global_registry.get_sources_by_language(lang)
            source_info['global_news']['sources_by_language'][lang] = len(lang_sources)
        
        return jsonify(source_info)
        
    except Exception as e:
        logger.error(f"Error getting global sources: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/sources/intelligence/<category>', methods=['GET'])
@rate_limit(max_requests=50, window=3600)
def api_intelligence_sources(category):
    """Get intelligence sources by category."""
    try:
        valid_categories = ['think_tanks', 'academic_institutions', 'government_sources']
        if category not in valid_categories:
            return jsonify({'error': f'Invalid category. Must be one of: {valid_categories}'}), 400
        
        from data_ingestion.intelligence_sources import IntelligenceSourcesRegistry
        
        intel_registry = IntelligenceSourcesRegistry()
        sources = intel_registry.get_sources_by_category(category)
        
        return jsonify({
            'category': category,
            'total_sources': len(sources),
            'sources': sources
        })
        
    except Exception as e:
        logger.error(f"Error getting intelligence sources: {e}")
        return jsonify({'error': str(e)}), 500
    

def run_api_server(host='0.0.0.0', port=5001, debug=False):
    """Run the API server."""
    logger.info(f"Starting Geopolitical Intelligence API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Geopolitical Intelligence System API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    run_api_server(host=args.host, port=args.port, debug=args.debug)
