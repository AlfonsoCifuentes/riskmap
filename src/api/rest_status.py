"""
Flask API Blueprint for RiskMap System Status
Provides REST endpoints for system status, health checks, and configuration
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def create_api_blueprint(core_orchestrator=None):
    """
    Create Flask API blueprint with system status endpoints
    
    Args:
        core_orchestrator: The main orchestrator instance
    
    Returns:
        Flask Blueprint with API endpoints
    """
    api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
    
    @api_bp.route('/status', methods=['GET'])
    def get_system_status():
        """Get comprehensive system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy',
                'version': '1.0.0',
                'components': {}
            }
            
            # Check core orchestrator
            if core_orchestrator:
                try:
                    health = core_orchestrator.health_check()
                    status['components']['core_orchestrator'] = {
                        'status': health.get('overall_status', 'unknown'),
                        'last_update': health.get('last_update'),
                        'stats': health.get('stats', {})
                    }
                except Exception as e:
                    status['components']['core_orchestrator'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                status['components']['core_orchestrator'] = {
                    'status': 'not_initialized'
                }
            
            # Overall status determination
            component_statuses = [comp.get('status') for comp in status['components'].values()]
            if 'error' in component_statuses:
                status['status'] = 'degraded'
            elif 'not_initialized' in component_statuses:
                status['status'] = 'initializing'
            
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }), 500
    
    @api_bp.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint"""
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat()
        })
    
    @api_bp.route('/stats', methods=['GET'])
    def get_statistics():
        """Get system statistics"""
        try:
            if core_orchestrator:
                stats = core_orchestrator.get_statistics()
                return jsonify(stats)
            else:
                return jsonify({
                    'error': 'Core orchestrator not available'
                }), 503
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @api_bp.route('/config', methods=['GET'])
    def get_config():
        """Get system configuration (read-only)"""
        try:
            # Return basic configuration info
            config_info = {
                'system': 'RiskMap Geopolitical Intelligence',
                'version': '1.0.0',
                'features': {
                    'rss_ingestion': True,
                    'nlp_processing': True,
                    'historical_analysis': True,
                    'real_time_alerts': True
                }
            }
            
            if core_orchestrator:
                # Add orchestrator-specific config if available
                try:
                    orchestrator_config = core_orchestrator.get_config()
                    config_info['orchestrator'] = orchestrator_config
                except:
                    pass
            
            return jsonify(config_info)
            
        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @api_bp.route('/articles/recent', methods=['GET'])
    def get_recent_articles():
        """Get recent articles"""
        try:
            limit = request.args.get('limit', 10, type=int)
            
            if core_orchestrator:
                articles = core_orchestrator.get_recent_articles(limit=limit)
                return jsonify({
                    'articles': articles,
                    'count': len(articles),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'error': 'Core orchestrator not available'
                }), 503
                
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @api_bp.route('/articles/search', methods=['GET'])
    def search_articles():
        """Search articles"""
        try:
            query = request.args.get('q', '')
            limit = request.args.get('limit', 10, type=int)
            
            if not query:
                return jsonify({
                    'error': 'Query parameter "q" is required'
                }), 400
            
            if core_orchestrator:
                articles = core_orchestrator.search_articles(query=query, limit=limit)
                return jsonify({
                    'query': query,
                    'articles': articles,
                    'count': len(articles),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'error': 'Core orchestrator not available'
                }), 503
                
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    return api_bp
