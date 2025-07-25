#!/usr/bin/env python3
"""
Script para actualizar las fuentes de artículos que están marcados como "RSS Feed"
usando análisis BERT para detectar la fuente real.
"""

import sqlite3
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from dashboard.ai_models.source_detector import source_detector
from utils.config import logger

def update_rss_feed_sources(limit=None, dry_run=False):
    """
    Actualiza las fuentes de artículos marcados como 'RSS Feed'
    
    Args:
        limit: Número máximo de artículos a procesar (None para todos)
        dry_run: Si True, solo muestra qué cambios se harían sin aplicarlos
    """
    
    # Conectar a la base de datos
    db_path = Path(__file__).parent / 'data' / 'geopolitical_intel.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Obtener art��culos con fuente "RSS Feed"
        query = """
            SELECT id, title, content, url, source 
            FROM articles 
            WHERE source = 'RSS Feed' OR source = 'RSS' OR source = 'Feed'
            ORDER BY created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        articles = cursor.fetchall()
        
        if not articles:
            print("✅ No se encontraron artículos con fuente 'RSS Feed' para procesar")
            return
        
        print(f"🔍 Encontrados {len(articles)} artículos con fuente RSS para procesar")
        
        updated_count = 0
        failed_count = 0
        
        for i, (article_id, title, content, url, current_source) in enumerate(articles, 1):
            try:
                print(f"\n📰 Procesando artículo {i}/{len(articles)}: {title[:60]}...")
                
                # Preparar datos del artículo para el detector
                article_data = {
                    'id': article_id,
                    'title': title or '',
                    'content': content or '',
                    'url': url or '',
                    'source': current_source
                }
                
                # Detectar la fuente real
                detected_source = source_detector.analyze_article_metadata(article_data)
                
                # Solo actualizar si se detectó una fuente diferente y válida
                if detected_source and detected_source != current_source and detected_source not in ['RSS Feed', 'Feed', 'RSS', 'Agencia Internacional']:
                    print(f"   🎯 Fuente detectada: {detected_source}")
                    
                    if not dry_run:
                        # Actualizar en la base de datos
                        cursor.execute(
                            "UPDATE articles SET source = ? WHERE id = ?",
                            (detected_source, article_id)
                        )
                        updated_count += 1
                        print(f"   ✅ Actualizado: {current_source} → {detected_source}")
                    else:
                        print(f"   🔄 [DRY RUN] Cambiaría: {current_source} → {detected_source}")
                        updated_count += 1
                else:
                    print(f"   ⚠️  No se pudo detectar fuente específica (detectado: {detected_source})")
                    failed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error procesando artículo {article_id}: {e}")
                failed_count += 1
                continue
        
        if not dry_run:
            # Confirmar cambios
            conn.commit()
            print(f"\n✅ Proceso completado:")
            print(f"   📊 Artículos actualizados: {updated_count}")
            print(f"   ❌ Artículos fallidos: {failed_count}")
        else:
            print(f"\n🔄 [DRY RUN] Resumen:")
            print(f"   📊 Artículos que se actualizarían: {updated_count}")
            print(f"   ❌ Artículos que fallarían: {failed_count}")
        
        # Mostrar estadísticas de fuentes después del procesamiento
        print(f"\n📈 Estadísticas de fuentes actualizadas:")
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM articles 
            WHERE source IS NOT NULL 
            GROUP BY source 
            ORDER BY count DESC 
            LIMIT 15
        """)
        
        for source, count in cursor.fetchall():
            print(f"   {source}: {count} artículos")
            
    except Exception as e:
        logger.error(f"Error en update_rss_feed_sources: {e}")
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def show_rss_feed_stats():
    """Muestra estadísticas de artículos con fuente RSS Feed"""
    db_path = Path(__file__).parent / 'data' / 'geopolitical_intel.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Contar artículos con RSS Feed
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles 
            WHERE source IN ('RSS Feed', 'RSS', 'Feed')
        """)
        rss_count = cursor.fetchone()[0]
        
        # Contar total de artículos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_count = cursor.fetchone()[0]
        
        print(f"📊 Estadísticas de fuentes RSS:")
        print(f"   📰 Total de artículos: {total_count}")
        print(f"   📡 Artículos con 'RSS Feed': {rss_count}")
        print(f"   📈 Porcentaje RSS: {(rss_count/total_count*100):.1f}%")
        
        # Mostrar ejemplos de artículos RSS
        cursor.execute("""
            SELECT id, title, url, created_at 
            FROM articles 
            WHERE source IN ('RSS Feed', 'RSS', 'Feed')
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        print(f"\n🔍 Ejemplos de artículos con fuente RSS:")
        for article_id, title, url, created_at in cursor.fetchall():
            print(f"   {article_id}: {title[:50]}...")
            if url:
                print(f"      URL: {url}")
            print(f"      Fecha: {created_at}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Actualizar fuentes RSS con detección BERT")
    parser.add_argument("--limit", type=int, help="Número máximo de artículos a procesar")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar cambios sin aplicarlos")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas de fuentes RSS")
    
    args = parser.parse_args()
    
    if args.stats:
        show_rss_feed_stats()
    else:
        print("🚀 Iniciando actualización de fuentes RSS con detección BERT...")
        update_rss_feed_sources(limit=args.limit, dry_run=args.dry_run)