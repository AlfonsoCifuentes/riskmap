#!/usr/bin/env python3
"""
Prueba directa de truncamiento sin servidor completo
"""
import sys
import os
sys.path.append('.')

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

def test_truncation_with_real_data():
    """Probar truncamiento con datos reales de la base de datos"""

    # Importar solo lo necesario para acceder a la DB
    try:
        from src.database.db_manager import DatabaseManager

        db = DatabaseManager()
        articles = db.get_articles(limit=10)  # Obtener 10 artículos

        print("🧪 PRUEBA DE TRUNCAMIENTO CON DATOS REALES:")
        print("=" * 80)

        for i, article in enumerate(articles, 1):
            original_title = article.get('title', '')
            original_length = len(original_title)

            truncated_title = truncate_title(original_title)
            truncated_length = len(truncated_title)

            print(f"\n📄 Artículo {i}:")
            print(f"📏 Longitud original: {original_length} caracteres")
            print(f"📏 Longitud truncada: {truncated_length} caracteres")
            print(f"📝 Original: {original_title}")
            print(f"✂️  Truncado: {truncated_title}")

            if truncated_length <= 83:  # 80 + 3 para "..."
                print("✅ Truncamiento correcto")
            else:
                print("❌ Truncamiento fallido")

        print("\n📊 RESUMEN:")
        long_titles = [a for a in articles if len(a.get('title', '')) > 80]
        truncated_correctly = [a for a in articles if len(truncate_title(a.get('title', ''))) <= 83]

        print(f"📄 Total artículos: {len(articles)}")
        print(f"⚠️  Títulos largos originales: {len(long_titles)}")
        print(f"✅ Títulos correctamente truncados: {len(truncated_correctly)}")

    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")

if __name__ == "__main__":
    test_truncation_with_real_data()