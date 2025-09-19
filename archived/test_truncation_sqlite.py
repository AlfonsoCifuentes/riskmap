#!/usr/bin/env python3
"""
Prueba directa de truncamiento leyendo la base de datos SQLite directamente
"""
import sqlite3
from pathlib import Path

def truncate_title(title, max_length=80):
    """Función de truncamiento igual a la del backend"""
    if len(title) <= max_length:
        return title

    # Buscar el mejor punto para truncar (espacio, punto o coma)
    truncated = title[:max_length]

    # Buscar puntos de corte en orden de preferencia
    last_space = truncated.rfind(' ')
    last_period = truncated.rfind('.')
    last_comma = truncated.rfind(',')
    last_dash = truncated.rfind('-')

    # Elegir el mejor punto de corte (el más cercano al límite)
    cut_points = [cp for cp in [last_space, last_period, last_comma, last_dash] if cp > 10]  # Mínimo 10 chars

    if cut_points:
        # Tomar el punto de corte más cercano al límite máximo
        best_cut = max(cut_points)
        return title[:best_cut] + "..."
    else:
        # Si no hay puntos de corte buenos, truncar directamente
        return title[:max_length-3] + "..."

def test_truncation_sqlite():
    """Probar truncamiento leyendo directamente de SQLite"""

    db_path = Path("./data/geopolitical_intel.db")

    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Obtener artículos con títulos largos
        cursor.execute("""
            SELECT id, title, LENGTH(title) as title_length
            FROM articles
            WHERE LENGTH(title) > 80
            ORDER BY LENGTH(title) DESC
            LIMIT 10
        """)

        articles = cursor.fetchall()

        print("🧪 PRUEBA DE TRUNCAMIENTO CON DATOS DE SQLITE:")
        print("=" * 80)

        for article_id, original_title, original_length in articles:
            truncated_title = truncate_title(original_title)
            truncated_length = len(truncated_title)

            print(f"\n📄 Artículo ID {article_id}:")
            print(f"📏 Longitud original: {original_length} caracteres")
            print(f"📏 Longitud truncada: {truncated_length} caracteres")
            print(f"📝 Original: {original_title[:100]}{'...' if len(original_title) > 100 else ''}")
            print(f"✂️  Truncado: {truncated_title}")

            if truncated_length <= 83:  # 80 + 3 para "..."
                print("✅ Truncamiento correcto")
            else:
                print("❌ Truncamiento fallido")

        print("\n📊 RESUMEN:")
        print(f"📄 Total artículos largos probados: {len(articles)}")
        successful_truncations = sum(1 for _, title, _ in articles if len(truncate_title(title)) <= 83)
        print(f"✅ Títulos correctamente truncados: {successful_truncations}")

        if successful_truncations == len(articles):
            print("🎉 TODOS los títulos se truncan correctamente!")
        else:
            print(f"⚠️  {len(articles) - successful_truncations} títulos necesitan revisión")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_truncation_sqlite()