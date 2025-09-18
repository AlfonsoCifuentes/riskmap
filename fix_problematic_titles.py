import sqlite3
import re

def identify_problematic_titles():
    """Identificar artículos con títulos que parecen ser contenido completo"""

    conn = sqlite3.connect('./data/geopolitical_intel.db')
    cursor = conn.cursor()

    # Buscar artículos con títulos sospechosos
    cursor.execute("""
        SELECT id, title, length(title) as title_len, content
        FROM articles
        WHERE length(title) > 100
        ORDER BY title_len DESC
        LIMIT 20
    """)

    problematic_articles = cursor.fetchall()

    print("Artículos con títulos potencialmente problemáticos:")
    print("=" * 80)

    for article_id, title, title_len, content in problematic_articles:
        print(f"\nID: {article_id}")
        print(f"Longitud del título: {title_len}")
        print(f"Título: {title[:200]}...")

        # Intentar extraer un título real del contenido del título
        # Buscar patrones comunes de títulos en contenido largo
        title_candidates = []

        # 1. Buscar frases que terminan con puntos
        sentences = re.split(r'[.!?]', title)
        for sentence in sentences[:3]:  # Primeras 3 oraciones
            sentence = sentence.strip()
            if 20 <= len(sentence) <= 100:  # Longitud razonable para un título
                title_candidates.append(sentence)

        # 2. Buscar frases con mayúsculas al inicio
        words = title.split()
        if words and words[0][0].isupper():
            # Tomar primera frase hasta puntuación
            first_sentence = ""
            for word in words:
                first_sentence += word + " "
                if word.endswith(('.', '!', '?', ':')):
                    break
            if 20 <= len(first_sentence.strip()) <= 100:
                title_candidates.append(first_sentence.strip())

        print(f"Candidatos para título real: {title_candidates[:2]}")

    conn.close()

def fix_problematic_titles():
    """Corregir títulos problemáticos extrayendo títulos reales"""

    conn = sqlite3.connect('./data/geopolitical_intel.db')
    cursor = conn.cursor()

    # Buscar artículos con títulos muy largos
    cursor.execute("""
        SELECT id, title, content
        FROM articles
        WHERE length(title) > 100
        ORDER BY length(title) DESC
    """)

    articles_to_fix = cursor.fetchall()
    fixed_count = 0

    for article_id, title, content in articles_to_fix:
        # Intentar extraer un título mejor
        new_title = extract_real_title(title, content)

        if new_title and new_title != title and len(new_title) < len(title):
            print(f"Corregiendo artículo {article_id}:")
            print(f"  Título original: {title[:100]}...")
            print(f"  Nuevo título: {new_title}")

            cursor.execute("""
                UPDATE articles
                SET title = ?
                WHERE id = ?
            """, (new_title, article_id))

            fixed_count += 1

    conn.commit()
    conn.close()

    print(f"\nSe corrigieron {fixed_count} artículos")

def extract_real_title(title, content):
    """Extraer un título real de un texto largo"""

    # Si el título ya es razonable, devolverlo
    if len(title) <= 80:
        return title

    # Método 1: Buscar la primera oración completa
    sentences = re.split(r'[.!?]', title)
    for sentence in sentences:
        sentence = sentence.strip()
        if 20 <= len(sentence) <= 80:
            return sentence

    # Método 2: Tomar las primeras palabras hasta un delimitador lógico
    words = title.split()
    if len(words) > 15:
        # Buscar puntos de corte naturales
        cut_points = []
        for i, word in enumerate(words[:20]):
            if word.endswith(('.', '!', '?', ':')) or word.lower() in ['que', 'como', 'cuando', 'donde']:
                cut_points.append(i + 1)

        if cut_points:
            cut_index = min(cut_points[0], 15)  # No más de 15 palabras
            candidate = ' '.join(words[:cut_index])
            if 20 <= len(candidate) <= 80:
                return candidate

    # Método 3: Tomar las primeras 12-15 palabras
    if len(words) >= 12:
        candidate = ' '.join(words[:12])
        if len(candidate) <= 80:
            return candidate + '...'

    # Si nada funciona, truncar directamente
    return title[:77] + '...'

if __name__ == "__main__":
    print("Identificando artículos con títulos problemáticos...")
    identify_problematic_titles()

    print("\n¿Desea corregir estos títulos? (s/n): ", end="")
    response = input().lower().strip()

    if response == 's':
        fix_problematic_titles()
        print("Corrección completada")
    else:
        print("Operación cancelada")