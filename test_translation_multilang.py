#!/usr/bin/env python3
"""
Script para probar traducción e ingesta GDELT con títulos multiidioma
"""

import sqlite3
from pathlib import Path
from deep_translator import GoogleTranslator

def test_translation():
    """Probar traducción de títulos reales de GDELT"""
    
    # Inicializar traductor
    translator = GoogleTranslator(source='auto', target='en')
    
    # Conectar a la base de datos para obtener títulos reales
    db_path = Path(__file__).parent / "data" / "geopolitical_intel.db"
    
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Obtener 10 títulos diversos de la base de datos
        cursor.execute("""
            SELECT article_title, action_location 
            FROM gdelt_events 
            WHERE article_title != '' 
            ORDER BY RANDOM() 
            LIMIT 10
        """)
        
        titles = cursor.fetchall()
        conn.close()
        
        print("🧪 Probando traducción de títulos GDELT reales...\n")
        
        for i, (title, location) in enumerate(titles, 1):
            print(f"📰 {i}. Original: {title}")
            
            try:
                # Traducir título
                translated = translator.translate(title)
                print(f"🔄 Traducido: {translated}")
                
                # Extraer ubicaciones del título traducido
                locations = extract_locations_simple(translated)
                print(f"📍 Ubicaciones detectadas: {locations}")
                
                if location:
                    print(f"💾 Ubicación guardada: {location}")
                
            except Exception as e:
                print(f"❌ Error traduciendo: {e}")
            
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")

def extract_locations_simple(text: str):
    """Extraer ubicaciones usando patrones simples"""
    import re
    
    # Patrones para ubicaciones en inglés
    patterns = [
        r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "in Location"
        r'\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "from Location"
        r'\b([A-Z][a-z]+),\s*([A-Z][a-z]+)\b',  # "City, Country"
    ]
    
    # Ubicaciones conocidas de conflictos
    known_places = [
        'Gaza', 'Strip', 'Ukraine', 'Russia', 'Syria', 'Iraq', 'Iran', 
        'Afghanistan', 'Yemen', 'Sudan', 'Somalia', 'Nigeria', 'Mali',
        'Israel', 'Palestine', 'Lebanon', 'Turkey', 'Pakistan', 'India',
        'China', 'Myanmar', 'Thailand', 'Venezuela', 'Colombia', 'Haiti'
    ]
    
    locations = []
    
    # Buscar patrones
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                locations.extend([loc for loc in match if loc])
            else:
                locations.append(match)
    
    # Buscar ubicaciones conocidas
    text_upper = text
    for place in known_places:
        if place.lower() in text.lower():
            locations.append(place)
    
    # Remover duplicados
    seen = set()
    unique_locations = []
    for loc in locations:
        if loc not in seen and len(loc) > 2:
            seen.add(loc)
            unique_locations.append(loc)
    
    return unique_locations[:3]

if __name__ == "__main__":
    test_translation()
