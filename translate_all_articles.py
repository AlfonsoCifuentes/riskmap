#!/usr/bin/env python3
"""
Script para traducir masivamente todos los artículos en la base de datos
Aplica traducción robusta a títulos y resúmenes usando robust_translation_v3.py
"""

import sqlite3
import logging
import sys
import os
from robust_translation_v3 import UltraRobustTranslationService
from tqdm import tqdm

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation_mass.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Función principal para traducir todos los artículos"""
    
    # Inicializar servicio de traducción
    try:
        translator = UltraRobustTranslationService()
        print("✅ Sistema de traducción robusto inicializado")
    except Exception as e:
        print(f"❌ Error inicializando traductor: {e}")
        return False
    
    # Conectar a la base de datos
    db_path = "./data/geopolitical_intel.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Obtener todos los artículos que necesitan traducción
        print("🔍 Buscando artículos para traducir...")
        cursor.execute("""
            SELECT id, title, summary, auto_generated_summary, content, url
            FROM articles
            WHERE created_at >= datetime('now', '-30 days')
            ORDER BY created_at DESC
        """)
        
        articles = cursor.fetchall()
        print(f"📰 Encontrados {len(articles)} artículos para procesar")
        
        if not articles:
            print("ℹ️ No hay artículos para traducir")
            return True
        
        # Contadores para estadísticas
        translated_count = 0
        error_count = 0
        
        # Procesar cada artículo
        for article_data in tqdm(articles, desc="Traduciendo artículos"):
            article_id, title, summary, auto_generated_summary, content, url = article_data
            
            try:
                updates = {}
                update_needed = False
                
                # Traducir título si existe
                if title and len(title.strip()) > 3:
                    try:
                        translated_title, detected_lang = translator.translate_text(title, 'es')
                        if translated_title and translated_title != title and len(translated_title) > 3:
                            updates['title'] = translated_title
                            update_needed = True
                            logger.info(f"✅ Título traducido para artículo {article_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error traduciendo título de artículo {article_id}: {e}")
                
                # Traducir summary si existe
                if summary and len(summary.strip()) > 10:
                    try:
                        translated_summary, detected_lang = translator.translate_text(summary, 'es')
                        if translated_summary and translated_summary != summary and len(translated_summary) > 10:
                            updates['summary'] = translated_summary
                            update_needed = True
                            logger.info(f"✅ Summary traducido para artículo {article_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error traduciendo summary de artículo {article_id}: {e}")
                
                # Traducir auto_generated_summary si existe
                if auto_generated_summary and len(auto_generated_summary.strip()) > 10:
                    try:
                        translated_auto_summary, detected_lang = translator.translate_text(auto_generated_summary, 'es')
                        if translated_auto_summary and translated_auto_summary != auto_generated_summary and len(translated_auto_summary) > 10:
                            updates['auto_generated_summary'] = translated_auto_summary
                            update_needed = True
                            logger.info(f"✅ Auto summary traducido para artículo {article_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error traduciendo auto_generated_summary de artículo {article_id}: {e}")
                
                # Aplicar actualizaciones si es necesario
                if update_needed and updates:
                    update_fields = []
                    update_values = []
                    
                    for field, value in updates.items():
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                    
                    update_values.append(article_id)  # Para la clausula WHERE
                    
                    update_query = f"""
                        UPDATE articles 
                        SET {', '.join(update_fields)}
                        WHERE id = ?
                    """
                    
                    cursor.execute(update_query, update_values)
                    translated_count += 1
                    
                    print(f"✅ Artículo {article_id} actualizado con {len(updates)} traducciones")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error procesando artículo {article_id}: {e}")
                continue
        
        # Guardar cambios
        conn.commit()
        
        # Mostrar estadísticas finales
        print("\n" + "="*50)
        print("📊 RESUMEN DE TRADUCCIÓN MASIVA")
        print("="*50)
        print(f"✅ Artículos procesados: {len(articles)}")
        print(f"🌍 Artículos traducidos: {translated_count}")
        print(f"❌ Errores: {error_count}")
        print(f"📈 Tasa de éxito: {(translated_count/len(articles)*100):.1f}%")
        
        if translated_count > 0:
            print("\n🎉 ¡Traducción masiva completada exitosamente!")
            return True
        else:
            print("\n⚠️ No se tradujeron artículos (posiblemente ya estaban en español)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error durante el proceso: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🌍 Iniciando traducción masiva de artículos...")
    success = main()
    
    if success:
        print("\n✅ Proceso completado. Los artículos han sido traducidos.")
    else:
        print("\n❌ El proceso falló o no se realizaron traducciones.")
    
    sys.exit(0 if success else 1)