#!/usr/bin/env python3
"""
Revertir endpoint deduplicated a su funcionalidad original para debuggear
"""

# Backup del endpoint actual
CURRENT_ENDPOINT = '''        @self.flask_app.route('/api/articles/deduplicated', methods=['GET'])
        def api_deduplicated_articles():
            """API: Test ultra minimalista - NO DB ACCESS"""
            try:
                return jsonify({
                    'success': True,
                    'test_mode': True,
                    'message': 'Endpoint ultra minimalista funcionando',
                    'hero': {
                        'id': 999,
                        'title': 'Test Article Ultra Minimal',
                        'image_url': 'https://via.placeholder.com/300x200',
                        'risk_level': 'low',
                        'original_url': '#'
                    },
                    'mosaic': [],
                    'stats': {
                        'total_processed': 0,
                        'duplicates_removed': 0,
                        'unique_articles': 1,
                        'hero_id': 999,
                        'mosaic_count': 0
                    }
                })
            except Exception as e:
                import traceback
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }), 500'''

# Endpoint original restaurado (con debugging)
ORIGINAL_ENDPOINT = '''        @self.flask_app.route('/api/articles/deduplicated', methods=['GET'])
        def api_deduplicated_articles():
            """API: Obtener artículos geopolíticos deduplicados con manejo robusto de errores"""
            try:
                # Parámetros
                hours = request.args.get('hours', 24, type=int)
                limit = request.args.get('limit', 20, type=int)
                offset = request.args.get('offset', 0, type=int)
                
                logger.info(f"🔍 Deduplicated API called: hours={hours}, limit={limit}, offset={offset}")
                
                # Intentar usar el sistema de deduplicación primero
                if self.news_deduplicator and NEWS_DEDUPLICATION_AVAILABLE:
                    logger.info("📰 Using news deduplicator system")
                    try:
                        # Obtener artículo héroe (más importante)
                        hero_articles = self.get_top_articles_from_db(1)
                        hero_id = hero_articles[0]['id'] if hero_articles else None
                        
                        # Obtener el resto de artículos (sin incluir el héroe)
                        articles = self.get_top_articles_from_db(limit + offset, exclude_hero_id=hero_id)
                        
                        # Procesar con deduplicación
                        result = self.news_deduplicator.process_articles_for_display(hours=hours)
                        
                        logger.info(f"✅ News deduplicator returned: {len(articles)} articles")
                        
                        return jsonify({
                            'success': True,
                            'hero': result.get('hero'),
                            'mosaic': articles[offset:offset+limit] if offset < len(articles) else [],
                            'stats': {
                                'total_processed': len(articles),
                                'duplicates_removed': result.get('duplicates_removed', 0),
                                'unique_articles': len(articles),
                                'hero_id': hero_id,
                                'mosaic_count': len(articles[offset:offset+limit] if offset < len(articles) else [])
                            }
                        })
                        
                    except Exception as dedup_error:
                        logger.error(f"❌ News deduplicator failed: {dedup_error}")
                        # Caer al método fallback
                        pass
                
                # Método fallback sin deduplicación - usar artículos directos de BD
                logger.info("📊 Using fallback method (direct DB)")
                articles = self._get_real_articles_from_db(limit + 5)  # Más artículos para hero selection
                
                if not articles:
                    return jsonify({
                        'success': True,
                        'hero': None,
                        'mosaic': [],
                        'stats': {
                            'total_processed': 0,
                            'duplicates_removed': 0,
                            'unique_articles': 0,
                            'hero_id': None,
                            'mosaic_count': 0
                        }
                    })
                
                # Seleccionar héroe (el más importante) y mosaico
                hero = articles[0] if articles else None
                hero_id = hero['id'] if hero else None
                mosaic = articles[1:limit+1] if len(articles) > 1 else []
                
                logger.info(f"✅ Fallback method returned: hero_id={hero_id}, mosaic_count={len(mosaic)}")
                
                return jsonify({
                    'success': True,
                    'hero': hero,
                    'mosaic': mosaic,
                    'stats': {
                        'total_processed': len(articles),
                        'duplicates_removed': 0,  # Sin deduplicación en fallback
                        'unique_articles': len(articles),
                        'hero_id': hero_id,
                        'mosaic_count': len(mosaic)
                    }
                })
                
            except Exception as e:
                logger.error(f"💥 ERROR en api_deduplicated_articles: {e}")
                logger.error(f"   Traceback: {traceback.format_exc()}")
                
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }), 500'''

print("ENDPOINT ORIGINAL PARA RESTAURAR:")
print("=" * 60)
print(ORIGINAL_ENDPOINT)

print(f"\n\n🔄 Para restaurar el endpoint original, reemplazar las líneas correspondientes en RISKMAP.py")