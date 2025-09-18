#!/usr/bin/env python3
"""
Prueba de la lógica de truncamiento de títulos
"""

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

def test_truncation():
    """Probar la función de truncamiento con títulos de ejemplo"""

    test_titles = [
        "Estados Unidos: el juicio de Luigi Mangione, acusado de haber matado al jefe de la primera aseguradora de salud privada del país, comenzará el 1 de diciembre ᵉʳ",
        "Casey Bloys Talks 'The Pitt's Emmy Breakthrough & Putting HBO Doubts To Rest, Confirms 'White Lotus' S4 Location, Gives 'HoD' & 'Rehearsal' Updates - Deadline",
        "U.S. Department of Education Makes Historic Grant Investments in Programs That Bolster Educational Outcomes - U.S. Department of Education (.gov)",
        "Un duro informe encargado por Naciones Unidas confirma un genocidio en Gaza y apunta contra Netanyahu y el presidente israelí Isaac Herzog",
        "Título corto normal",
        "Otro título que es más largo de lo normal pero no tanto como los anteriores casos extremos de prueba"
    ]

    print("🧪 PRUEBA DE LÓGICA DE TRUNCAMIENTO:")
    print("=" * 80)

    for i, title in enumerate(test_titles, 1):
        truncated = truncate_title(title)
        original_len = len(title)
        truncated_len = len(truncated)

        print(f"\n📝 Título {i}:")
        print(f"📏 Longitud original: {original_len} caracteres")
        print(f"📏 Longitud truncada: {truncated_len} caracteres")
        print(f"📄 Original: {title}")
        print(f"✂️  Truncado: {truncated}")

        if truncated_len <= 83:  # 80 + 3 para "..."
            print("✅ Truncamiento correcto")
        else:
            print("❌ Truncamiento fallido")

if __name__ == "__main__":
    test_truncation()