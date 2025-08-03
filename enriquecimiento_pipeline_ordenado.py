"""
Script de Enriquecimiento Masivo con Pipeline Ordenado
Pipeline: NLP (BERT) → Computer Vision (YOLO) → Fallback AI (Groq/Ollama)
Clasifica riesgo geopolítico y enriquece todos los artículos de la BD
"""

import sqlite3
import logging
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir directorio principal al path
sys.path.append(str(Path(__file__).parent))

# Base de datos path - actualizada para la BD correcta
DB_PATH = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"

def verificar_articulos():
    """Verificar cuántos artículos existen y su estado"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Total de artículos
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            
            # Por estado de enriquecimiento
            cursor.execute("""
                SELECT 
                    COALESCE(enrichment_status, 'null') as status,
                    COUNT(*) as count
                FROM articles 
                GROUP BY enrichment_status
            """)
            
            stats = cursor.fetchall()
            
            print(f"\n📊 Estado de Artículos:")
            print(f"  Total artículos: {total}")
            print(f"  Por estado:")
            for status, count in stats:
                print(f"    {status}: {count}")
            
            # Artículos con análisis de riesgo
            cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level IS NOT NULL")
            risk_analyzed = cursor.fetchone()[0]
            
            # Artículos con análisis de sentimiento
            cursor.execute("SELECT COUNT(*) FROM articles WHERE sentiment_score IS NOT NULL") 
            sentiment_analyzed = cursor.fetchone()[0]
            
            # Artículos con análisis de imagen
            cursor.execute("SELECT COUNT(*) FROM articles WHERE visual_analysis_json IS NOT NULL")
            vision_analyzed = cursor.fetchone()[0]
            
            print(f"\n🔍 Análisis completados:")
            print(f"  Riesgo geopolítico: {risk_analyzed}/{total}")
            print(f"  Análisis sentimiento: {sentiment_analyzed}/{total}")
            print(f"  Computer Vision: {vision_analyzed}/{total}")
            
            return total
            
    except Exception as e:
        logger.error(f"Error verificando artículos: {e}")
        return 0

def enrichment_pipeline_step(article_id: int, article_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pipeline de enriquecimiento ordenado: NLP → CV → Fallback AI
    """
    updates = {}
    pipeline_log = []
    
    try:
        # ====== PASO 1: ANÁLISIS NLP CON BERT ======
        print(f"  🧠 [{article_id}] Paso 1: Análisis NLP con BERT...")
        pipeline_log.append("BERT NLP Analysis")
        
        # Importar análisis de riesgo BERT
        from src.utils.bert_risk_analyzer import BERTRiskAnalyzer
        from src.utils.ai_risk_analyzer import AdvancedRiskAnalyzer
        
        full_text = f"{article_data.get('title', '')} {article_data.get('content', '')}"
        
        # Análisis de riesgo geopolítico (PRIORITARIO)
        if not article_data.get('risk_level'):
            try:
                risk_analyzer = BERTRiskAnalyzer()
                risk_result = risk_analyzer.analyze_geopolitical_risk(
                    title=article_data.get('title', ''),
                    content=article_data.get('content', ''),
                    context={
                        'source': article_data.get('source', ''),
                        'country': article_data.get('country', ''),
                        'published_at': article_data.get('published_at', '')
                    }
                )
                
                if risk_result and risk_result.get('risk_level'):
                    updates['risk_level'] = risk_result['risk_level']
                    updates['risk_score'] = risk_result.get('risk_score', 0.5)
                    updates['conflict_probability'] = risk_result.get('conflict_probability', 0.5)
                    updates['importance_score'] = risk_result.get('importance_score', 0.5)
                    
                    print(f"    ✅ Riesgo clasificado: {risk_result['risk_level']} (score: {risk_result.get('risk_score', 0):.2f})")
                    
            except Exception as e:
                logger.warning(f"Error en análisis de riesgo BERT: {e}")
        
        # Análisis de sentimiento e importancia
        if not article_data.get('sentiment_score'):
            try:
                from src.ai.bert_service import BERTService
                bert_service = BERTService()
                
                sentiment_result = bert_service.analyze_sentiment(full_text)
                if sentiment_result:
                    updates['sentiment_score'] = sentiment_result.get('score', 0.5)
                    updates['sentiment_label'] = sentiment_result.get('label', 'neutral')
                    
                importance_result = bert_service.calculate_importance(full_text)
                if importance_result:
                    updates['importance_score'] = importance_result.get('score', 0.5)
                    
                print(f"    ✅ Sentimiento: {sentiment_result.get('label', 'N/A')} ({sentiment_result.get('score', 0):.2f})")
                    
            except Exception as e:
                logger.warning(f"Error en análisis de sentimiento: {e}")
        
        # ====== PASO 2: COMPUTER VISION CON YOLO ======
        if article_data.get('image_url') and not article_data.get('visual_analysis_json'):
            print(f"  👁️ [{article_id}] Paso 2: Computer Vision con YOLO...")
            pipeline_log.append("Computer Vision Analysis")
            
            try:
                from src.vision_analysis.image_risk_analyzer import ImageRiskAnalyzer
                
                image_analyzer = ImageRiskAnalyzer()
                cv_result = image_analyzer.analyze_image_risk(
                    image_url=article_data['image_url'],
                    article_context={
                        'title': article_data.get('title', ''),
                        'content': article_data.get('content', ''),
                        'risk_level': updates.get('risk_level', article_data.get('risk_level'))
                    }
                )
                
                if cv_result and not cv_result.get('error'):
                    updates['visual_analysis_json'] = json.dumps(cv_result)
                    updates['detected_objects'] = json.dumps(cv_result.get('detected_objects', []))
                    updates['visual_risk_score'] = cv_result.get('visual_risk_score', 0)
                    updates['has_faces'] = cv_result.get('has_people', False)
                    
                    # Combinar riesgo visual con riesgo textual
                    if cv_result.get('visual_risk_score', 0) > 7:
                        current_risk = updates.get('risk_score', article_data.get('risk_score', 0.5))
                        updates['risk_score'] = min(1.0, current_risk + 0.2)  # Aumentar riesgo
                    
                    print(f"    ✅ Objetos detectados: {len(cv_result.get('detected_objects', []))}")
                    print(f"    ✅ Riesgo visual: {cv_result.get('visual_risk_score', 0):.2f}")
                    
            except Exception as e:
                logger.warning(f"Error en Computer Vision: {e}")
        
        # ====== PASO 3: FALLBACK AI (GROQ/OLLAMA) ======
        print(f"  🤖 [{article_id}] Paso 3: Fallback AI (Groq/Ollama)...")
        pipeline_log.append("Fallback AI Enhancement")
        
        # Solo llenar campos faltantes con AI
        missing_fields = []
        if not article_data.get('country') and not updates.get('country'):
            missing_fields.append('country')
        if not article_data.get('region') and not updates.get('region'):
            missing_fields.append('region')
        if not article_data.get('conflict_type') and not updates.get('conflict_type'):
            missing_fields.append('conflict_type')
        if not article_data.get('summary') and not updates.get('summary'):
            missing_fields.append('summary')
        
        if missing_fields:
            try:
                from src.ai.unified_ai_service import unified_ai_service
                import asyncio
                
                ai_result = asyncio.run(unified_ai_service.analyze_geopolitical_content(
                    content=full_text,
                    prefer_local=True,  # Priorizar Ollama
                    analysis_type="enrichment"
                ))
                
                if ai_result.success and ai_result.metadata:
                    metadata = ai_result.metadata
                    
                    if 'country' in missing_fields and metadata.get('country'):
                        updates['country'] = metadata.get('country', '').split(',')[0]
                    
                    if 'region' in missing_fields and metadata.get('region'):
                        updates['region'] = metadata.get('region', '')
                    
                    if 'conflict_type' in missing_fields and metadata.get('conflict_type'):
                        updates['conflict_type'] = metadata.get('conflict_type', '')
                    
                    if 'summary' in missing_fields and metadata.get('summary'):
                        updates['summary'] = metadata.get('summary', '')
                    
                    print(f"    ✅ Campos completados con AI: {len([f for f in missing_fields if f in updates])}")
                    
            except Exception as e:
                logger.warning(f"Error en Fallback AI: {e}")
        
        # Metadatos de enriquecimiento
        updates['enrichment_status'] = 'completed'
        updates['last_enriched'] = datetime.now().isoformat()
        updates['enrichment_pipeline'] = json.dumps(pipeline_log)
        updates['enrichment_version'] = (article_data.get('enrichment_version') or 0) + 1
        
        return updates
        
    except Exception as e:
        logger.error(f"Error en pipeline de enriquecimiento para artículo {article_id}: {e}")
        return {
            'enrichment_status': 'error',
            'last_enriched': datetime.now().isoformat(),
            'enrichment_error': str(e)
        }

def enriquecer_lote_articulos(limit: int = 50, force: bool = False) -> Dict[str, Any]:
    """Enriquecer un lote de artículos siguiendo el pipeline ordenado"""
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Consulta para obtener artículos que necesitan enriquecimiento
            if force:
                query = "SELECT * FROM articles ORDER BY created_at DESC LIMIT ?"
                params = (limit,)
            else:
                query = """
                    SELECT * FROM articles 
                    WHERE enrichment_status IS NULL 
                       OR enrichment_status = 'pending'
                       OR enrichment_status = 'error'
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                params = (limit,)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                print("ℹ️ No hay artículos que necesiten enriquecimiento")
                return {'processed': 0, 'success': 0, 'errors': 0}
            
            columns = [desc[0] for desc in cursor.description]
            articles = [dict(zip(columns, row)) for row in rows]
            
            print(f"\n🚀 Procesando {len(articles)} artículos con pipeline ordenado...")
            
            success_count = 0
            error_count = 0
            start_time = time.time()
            
            for i, article in enumerate(articles, 1):
                article_id = article['id']
                print(f"\n[{i}/{len(articles)}] Procesando artículo {article_id}: {article.get('title', '')[:50]}...")
                
                try:
                    # Ejecutar pipeline de enriquecimiento
                    updates = enrichment_pipeline_step(article_id, article)
                    
                    if updates:
                        # Aplicar updates a la base de datos
                        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
                        values = list(updates.values()) + [article_id]
                        
                        cursor.execute(f"UPDATE articles SET {set_clause} WHERE id = ?", values)
                        conn.commit()
                        
                        success_count += 1
                        print(f"  ✅ Artículo {article_id} enriquecido: {len(updates)} campos actualizados")
                    else:
                        error_count += 1
                        print(f"  ❌ No se pudo enriquecer artículo {article_id}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error procesando artículo {article_id}: {e}")
                    
                    # Marcar como error en BD
                    cursor.execute("""
                        UPDATE articles 
                        SET enrichment_status = 'error', 
                            enrichment_error = ?,
                            last_enriched = ?
                        WHERE id = ?
                    """, (str(e), datetime.now().isoformat(), article_id))
                    conn.commit()
            
            total_time = time.time() - start_time
            
            print(f"\n✅ Enriquecimiento completado:")
            print(f"  Procesados: {len(articles)}")
            print(f"  Exitosos: {success_count}")
            print(f"  Errores: {error_count}")
            print(f"  Tiempo total: {total_time:.2f}s")
            print(f"  Tiempo promedio: {total_time/len(articles):.2f}s por artículo")
            
            return {
                'processed': len(articles),
                'success': success_count,
                'errors': error_count,
                'processing_time': total_time,
                'average_time': total_time / len(articles) if articles else 0
            }
            
    except Exception as e:
        logger.error(f"Error en enriquecimiento masivo: {e}")
        return {'processed': 0, 'success': 0, 'errors': 1, 'error': str(e)}

def main():
    """Función principal del script"""
    print("🚀 Iniciando Enriquecimiento Masivo con Pipeline Ordenado")
    print(f"📂 Base de datos: {DB_PATH}")
    print(f"🔄 Pipeline: NLP (BERT) → Computer Vision (YOLO) → Fallback AI (Groq/Ollama)")
    
    # Verificar que la BD existe
    if not Path(DB_PATH).exists():
        logger.error(f"❌ Base de datos no encontrada: {DB_PATH}")
        return
    
    # Verificar estado inicial
    total_articles = verificar_articulos()
    
    if total_articles == 0:
        logger.warning("❌ No se encontraron artículos para procesar")
        return
    
    # Preguntar al usuario
    print(f"\n📋 Opciones:")
    print(f"  1. Enriquecer solo artículos pendientes (recomendado)")
    print(f"  2. Forzar re-enriquecimiento de todos los artículos")
    
    try:
        opcion = input("\nSeleccionar opción (1/2) [1]: ").strip() or "1"
        force = (opcion == "2")
        
        limit = int(input("Límite de artículos a procesar [50]: ").strip() or "50")
        
        print(f"\n🎯 Configuración:")
        print(f"  Modo: {'Forzar re-enriquecimiento' if force else 'Solo pendientes'}")
        print(f"  Límite: {limit} artículos")
        
        confirmar = input("\n¿Continuar? (y/N): ").strip().lower()
        if confirmar not in ['y', 'yes', 's', 'si']:
            print("❌ Operación cancelada")
            return
        
        # Ejecutar enriquecimiento masivo
        print(f"\n{'='*60}")
        result = enriquecer_lote_articulos(limit=limit, force=force)
        print(f"{'='*60}")
        
        # Verificar estado final
        print("\n📊 Estado final:")
        verificar_articulos()
        
        if result.get('success', 0) > 0:
            print(f"\n🎉 ¡Enriquecimiento completado exitosamente!")
            print(f"   {result['success']} artículos procesados con el pipeline completo")
        
    except KeyboardInterrupt:
        print("\n❌ Operación interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error durante enriquecimiento: {e}")

if __name__ == "__main__":
    main()
