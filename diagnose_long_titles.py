#!/usr/bin/env python3
"""
Diagnóstico para identificar textos largos en títulos de artículos
"""
import sqlite3
import os
from pathlib import Path

def diagnose_long_titles():
    """Identifica artículos con títulos sospechosamente largos"""
    db_path = Path("./data/geopolitical_intel.db")

    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Obtener artículos con títulos largos (>100 caracteres)
        cursor.execute("""
            SELECT id, title, LENGTH(title) as title_length,
                   summary, LENGTH(summary) as summary_length,
                   content, LENGTH(content) as content_length,
                   source, published_at
            FROM articles
            WHERE LENGTH(title) > 100
            ORDER BY LENGTH(title) DESC
            LIMIT 20
        """)

        long_title_articles = cursor.fetchall()

        print("🔍 ARTÍCULOS CON TÍTULOS SOSPECHOSAMENTE LARGOS (>100 caracteres):")
        print("=" * 80)

        for article in long_title_articles:
            article_id, title, title_len, summary, summary_len, content, content_len, source, published_at = article

            print(f"\n📄 ID: {article_id}")
            print(f"📅 Fecha: {published_at}")
            print(f"📰 Fuente: {source}")
            print(f"📏 Longitud título: {title_len} caracteres")
            print(f"📏 Longitud resumen: {summary_len if summary_len else 0} caracteres")
            print(f"📏 Longitud contenido: {content_len if content_len else 0} caracteres")

            # Mostrar primeros 200 caracteres del título
            print(f"📝 Título (primeros 200 chars): {title[:200]}{'...' if len(title) > 200 else ''}")

            # Verificar si el título parece ser contenido completo
            if title_len > 200:
                print("⚠️  POSIBLE PROBLEMA: Título muy largo, podría ser contenido completo")

                # Comparar con resumen
                if summary and len(summary) > 50:
                    similarity = len(set(title.lower().split()) & set(summary.lower().split())) / len(set(title.lower().split()))
                    if similarity > 0.8:
                        print("🔍 PATRÓN DETECTADO: Título parece ser igual al resumen")

                # Comparar con contenido
                if content and len(content) > 50:
                    similarity = len(set(title.lower().split()) & set(content.lower().split())) / len(set(title.lower().split()))
                    if similarity > 0.8:
                        print("🔍 PATRÓN DETECTADO: Título parece ser igual al contenido")

        # Estadísticas generales
        cursor.execute("""
            SELECT
                COUNT(*) as total_articles,
                AVG(LENGTH(title)) as avg_title_length,
                MAX(LENGTH(title)) as max_title_length,
                COUNT(CASE WHEN LENGTH(title) > 100 THEN 1 END) as long_titles_count
            FROM articles
        """)

        stats = cursor.fetchone()
        total, avg_len, max_len, long_count = stats

        print("\n📊 ESTADÍSTICAS GENERALES:")
        print(f"📄 Total artículos: {total}")
        print(f"📏 Longitud promedio título: {avg_len:.1f} caracteres")
        print(f"📏 Longitud máxima título: {max_len} caracteres")
        print(f"⚠️  Artículos con títulos >100 chars: {long_count} ({long_count/total*100:.1f}%)")

        conn.close()

    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")

if __name__ == "__main__":
    diagnose_long_titles()