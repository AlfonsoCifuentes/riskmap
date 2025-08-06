#!/usr/bin/env python3
"""
Script para probar el proceso completo de extracción y geocodificación con datos reales
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_real_gdelt_processing():
    """Probar el procesamiento completo con datos reales de GDELT"""
    try:
        # Conectar a la base de datos
        db_path = Path(__file__).parent / "data" / "geopolitical_intel.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Obtener algunos artículos recientes sin coordenadas
        cursor.execute("""
            SELECT global_event_id, article_title
            FROM gdelt_events 
            WHERE action_latitude IS NULL 
            AND article_title IS NOT NULL
            ORDER BY event_date DESC 
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            print("❌ No se encontraron artículos para probar")
            return
        
        print(f"🧪 Probando con {len(articles)} artículos reales...")
        
        # Inicializar cliente Groq
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("❌ GROQ_API_KEY no encontrada")
            return
        
        client = Groq(api_key=api_key)
        
        for event_id, title in articles:
            print(f"\n📰 {event_id}")
            print(f"🔤 Título: {title}")
            
            # Extraer ubicaciones
            locations = extract_locations_improved(title)
            print(f"📍 Ubicaciones extraídas: {locations}")
            
            if locations:
                # Geocodificar primera ubicación
                coords = get_coordinates_groq(client, locations[0])
                if coords:
                    print(f"🗺️ Coordenadas obtenidas: {coords}")
                else:
                    print("❌ Geocodificación falló")
            else:
                print("❌ No se detectaron ubicaciones")
            
            print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")

def extract_locations_improved(text: str):
    """Extracción de ubicaciones mejorada"""
    locations = []
    
    # Patrones específicos para ubicaciones
    patterns = [
        # Países y regiones conocidas
        r'\b(Gaza|Israel|Palestine|Ukraine|Russia|Syria|Iraq|Iran|Afghanistan|Yemen|Libya|Sudan|Somalia|Nigeria|Mali|Chad|Turkey|Lebanon|Jordan|Egypt|Morocco|Algeria|Tunisia|Venezuela|Colombia|Mexico|China|India|Pakistan|Bangladesh|Myanmar|Thailand|Philippines|North Korea|South Korea|Taiwan|Japan|Vietnam|Indonesia|Malaysia|Singapore|Australia|New Zealand)\b',
        # Ciudad, País format
        r'\b([A-Z][a-zA-Z]+),\s*([A-Z][a-zA-Z]+)\b',
        # "in Location" format  
        r'\bin\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
    ]
    
    exclude_words = {
        'the', 'and', 'or', 'but', 'for', 'with', 'by', 'at', 'on', 'in', 'to', 'from',
        'president', 'minister', 'government', 'army', 'military', 'police', 'forces',
        'party', 'group', 'people', 'war', 'conflict', 'crisis', 'attack', 'violence',
        'protest', 'news', 'report', 'statement', 'pride', 'apple', 'germany', 'europe'
    }
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                for location in match:
                    if location and location.lower() not in exclude_words and len(location) > 2:
                        locations.append(location)
            else:
                if match and match.lower() not in exclude_words and len(match) > 2:
                    locations.append(match)
    
    # Remover duplicados
    seen = set()
    unique_locations = []
    for loc in locations:
        if loc.lower() not in seen:
            seen.add(loc.lower())
            unique_locations.append(loc)
    
    return unique_locations[:2]

def get_coordinates_groq(client, location: str):
    """Geocodificar con Groq"""
    try:
        prompt = f"""
        Para la ubicación "{location}", proporciona las coordenadas geográficas exactas.
        
        Responde SOLO con un JSON válido:
        {{
            "latitude": número_decimal,
            "longitude": número_decimal,
            "country": "nombre_del_país"
        }}
        
        Si no puedes determinar la ubicación, responde: null
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Limpiar formato markdown
        if '```json' in response_text:
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Extraer JSON
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            coords_data = json.loads(json_match.group())
            if coords_data and 'latitude' in coords_data:
                return coords_data
        
        return None
        
    except Exception as e:
        print(f"❌ Error Groq: {e}")
        return None

if __name__ == "__main__":
    test_real_gdelt_processing()
