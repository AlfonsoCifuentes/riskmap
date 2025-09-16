"""
Re-análisis de todos los artículos con el nuevo analizador BERT simplificado
"""
import sqlite3
import logging
from datetime import datetime
from src.ai.bert_simple_analyzer import SimpleBertRiskAnalyzer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Re-analizar todos los artículos en la base de datos"""
    
    # Conectar a la base de datos
    conn = sqlite3.connect('geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Crear analizador
    analyzer = SimpleBertRiskAnalyzer()
    
    try:
        # Obtener todos los artículos
        cursor.execute("""
            SELECT id, title, content, summary 
            FROM news_articles 
            ORDER BY id
        """)
        
        articles = cursor.fetchall()
        total_articles = len(articles)
        
        logger.info(f"Iniciando re-análisis de {total_articles} artículos...")
        
        # Contadores de estadísticas
        stats = {
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'updated': 0,
            'errors': 0
        }
        
        # Procesar cada artículo
        for i, (article_id, title, content, summary) in enumerate(articles, 1):
            try:
                # Analizar riesgo
                risk_level, risk_score = analyzer.analyze_risk(title, content, summary)
                
                # Actualizar en la base de datos
                cursor.execute("""
                    UPDATE news_articles 
                    SET risk_level = ?, risk_score = ?, last_analyzed = ?
                    WHERE id = ?
                """, (risk_level, risk_score, datetime.now().isoformat(), article_id))
                
                stats[risk_level] += 1
                stats['updated'] += 1
                
                # Log cada 50 artículos procesados
                if i % 50 == 0:
                    logger.info(f"Procesados {i}/{total_articles} artículos...")
                    
            except Exception as e:
                logger.error(f"Error procesando artículo {article_id}: {e}")
                stats['errors'] += 1
                continue
        
        # Commit cambios
        conn.commit()
        
        # Mostrar estadísticas finales
        logger.info("\n" + "="*50)
        logger.info("RE-ANÁLISIS COMPLETADO")
        logger.info("="*50)
        logger.info(f"Total artículos procesados: {total_articles}")
        logger.info(f"Artículos actualizados: {stats['updated']}")
        logger.info(f"Errores: {stats['errors']}")
        logger.info("\nDistribución de niveles de riesgo:")
        logger.info(f"HIGH: {stats['HIGH']} ({stats['HIGH']/total_articles*100:.1f}%)")
        logger.info(f"MEDIUM: {stats['MEDIUM']} ({stats['MEDIUM']/total_articles*100:.1f}%)")
        logger.info(f"LOW: {stats['LOW']} ({stats['LOW']/total_articles*100:.1f}%)")
        
        # Verificar la distribución actualizada
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM news_articles 
            GROUP BY risk_level 
            ORDER BY count DESC
        """)
        
        verification = cursor.fetchall()
        logger.info("\nVerificación en base de datos:")
        for risk_level, count in verification:
            percentage = (count / total_articles) * 100
            logger.info(f"{risk_level}: {count} ({percentage:.1f}%)")
            
    except Exception as e:
        logger.error(f"Error durante el re-análisis: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
