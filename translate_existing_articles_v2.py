#!/usr/bin/env python3
"""
Traducir Artículos Existentes usando RobustTranslationSystem
Aplica traducción a todos los artículos existentes para mejorar rendimiento.
"""

import sqlite3
import sys
import os
from datetime import datetime

# Añadir el directorio principal al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def translate_existing_articles():
    """Traduce artículos existentes en la base de datos"""
    
    try:
        # Importar el sistema de traducción
        from robust_translation_v3 import RobustTranslationSystem
        
        print("🚀 TRADUCCIÓN MASIVA DE ARTÍCULOS EXISTENTES")
        print("=" * 60)
        print(f"🕒 Iniciado: {datetime.now().strftime('%H:%M:%S')}")
        
        # Inicializar sistema de traducción
        translation_system = RobustTranslationSystem()
        print("✅ Sistema de traducción inicializado")
        
        # Conectar a la base de datos
        db_path = "./data/geopolitical_intel.db"
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print(f"✅ Conectado a base de datos: {db_path}")
        
        # Obtener artículos que necesitan traducción
        cursor.execute("""
            SELECT id, title, content, summary
            FROM articles 
            WHERE title IS NOT NULL 
            AND content IS NOT NULL
            AND (title_es IS NULL OR content_es IS NULL)
            LIMIT 50
        """)
        
        articles = cursor.fetchall()
        print(f"📊 Artículos a traducir: {len(articles)}")
        
        if not articles:
            print("✅ No hay artículos que requieran traducción")
            conn.close()
            return
        
        # Añadir columnas de traducción si no existen
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN title_es TEXT")
            cursor.execute("ALTER TABLE articles ADD COLUMN content_es TEXT") 
            cursor.execute("ALTER TABLE articles ADD COLUMN summary_es TEXT")
            print("✅ Columnas de traducción añadidas")
        except sqlite3.OperationalError:
            print("✅ Columnas de traducción ya existen")
        
        # Traducir artículos
        translated_count = 0
        for i, article in enumerate(articles, 1):
            try:
                article_id = article['id']
                title = article['title']
                content = article['content'] 
                summary = article['summary']
                
                print(f"🔄 [{i}/{len(articles)}] Traduciendo artículo ID {article_id}...")
                print(f"   Título original: {title[:50]}...")
                
                # Traducir título
                title_es = translation_system.translate_text(title, target_language='es')
                
                # Traducir contenido (limitar a 3000 caracteres para evitar timeouts)
                content_truncated = content[:3000] if content and len(content) > 3000 else content
                content_es = translation_system.translate_text(content_truncated, target_language='es') if content else None
                
                # Traducir resumen si existe
                summary_es = translation_system.translate_text(summary, target_language='es') if summary else None
                
                # Actualizar en base de datos
                cursor.execute("""
                    UPDATE articles 
                    SET title_es = ?, content_es = ?, summary_es = ?
                    WHERE id = ?
                """, (title_es, content_es, summary_es, article_id))
                
                print(f"   Título traducido: {title_es[:50]}...")
                translated_count += 1
                
                # Commit cada 10 artículos
                if translated_count % 10 == 0:
                    conn.commit()
                    print(f"   ✅ Guardados {translated_count} artículos traducidos")
                
            except Exception as e:
                print(f"   ❌ Error traduciendo artículo ID {article_id}: {e}")
                continue
        
        # Commit final
        conn.commit()
        conn.close()
        
        print("=" * 60)
        print("✅ TRADUCCIÓN MASIVA COMPLETADA")
        print(f"📊 Artículos procesados: {len(articles)}")
        print(f"🎯 Artículos traducidos: {translated_count}")
        print(f"🕒 Finalizado: {datetime.now().strftime('%H:%M:%S')}")
        print()
        print("🎯 PRÓXIMOS PASOS:")
        print("   1. Reinicia app_BUENA.py si está ejecutándose")
        print("   2. Los artículos ahora se sirven desde las columnas traducidas")
        print("   3. Ejecuta test_integrated_translation.py para verificar")
        
    except ImportError as e:
        print(f"❌ Error importando sistema de traducción: {e}")
        print("💡 Asegúrate de que robust_translation_v3.py esté disponible")
    except Exception as e:
        print(f"❌ Error general: {e}")

def update_app_to_use_translated_columns():
    """Genera código para actualizar app_BUENA.py para usar columnas traducidas"""
    
    print("\n" + "=" * 60)
    print("📝 ACTUALIZACIÓN DE CÓDIGO REQUERIDA")
    print("=" * 60)
    print("Para optimizar rendimiento, actualiza los endpoints en app_BUENA.py")
    print("para usar las columnas traducidas directamente:")
    print()
    print("🔄 CAMBIOS RECOMENDADOS:")
    print()
    print("1. En lugar de traducir en tiempo real:")
    print("   translated_title = self.translation_system.translate_text(...)")
    print()
    print("2. Usa las columnas pretraducidas:")
    print("   title = article.get('title_es') or article.get('title')")
    print("   content = article.get('content_es') or article.get('content')")
    print("   summary = article.get('summary_es') or article.get('summary')")
    print()
    print("3. Esto mejorará significativamente el rendimiento")
    print("   y reducirá la carga en los servicios de traducción")

if __name__ == "__main__":
    print("🌍 SISTEMA DE TRADUCCIÓN MASIVA PARA GEOPOLITICAL INTEL")
    print()
    
    try:
        translate_existing_articles()
        update_app_to_use_translated_columns()
    except KeyboardInterrupt:
        print("\n❌ Proceso interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error general: {e}")
    
    print("\n" + "=" * 60)