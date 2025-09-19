#!/usr/bin/env python3
"""
Script para encontrar y probar artículos con ubicaciones conocidas
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

def test_articles_with_known_locations():
    """Probar artículos que contengan ubicaciones conocidas"""
    try:
        # Conectar a la base de datos
        db_path = Path(__file__).parent / "data" / "geopolitical_intel.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Buscar artículos que contengan ubicaciones específicas
        known_locations = ['Gaza', 'Ukraine', 'Iran', 'Syria', 'Israel', 'Russia']
        
        for location in known_locations:
            print(f"\n🔍 Buscando artículos que contengan '{location}'...")
            
            cursor.execute("""
                SELECT global_event_id, article_title, action_location, action_latitude, action_longitude
                FROM gdelt_events 
                WHERE article_title LIKE ? OR action_location LIKE ?
                LIMIT 3
            """, (f'%{location}%', f'%{location}%'))
            
            articles = cursor.fetchall()
            
            if articles:
                print(f"📋 Encontrados {len(articles)} artículos con '{location}':")
                
                # Inicializar cliente Groq si no existe
                api_key = os.getenv('GROQ_API_KEY')
                if api_key:
                    client = Groq(api_key=api_key)
                else:
                    client = None
                    print("⚠️ Sin cliente Groq")
                
                for event_id, title, current_location, lat, lon in articles:
                    print(f"\n📰 {event_id}")
                    print(f"📄 Título: {title}")
                    print(f"📍 Ubicación actual: {current_location}")
                    
                    if lat and lon:
                        print(f"🗺️ Ya tiene coordenadas: ({lat}, {lon})")
                    else:
                        print("❌ Sin coordenadas")
                        
                        # Probar extracción de ubicaciones
                        locations = extract_locations_simple(title)
                        print(f"🔍 Ubicaciones extraídas: {locations}")
                        
                        # Si encontramos ubicaciones y tenemos cliente Groq, geocodificar
                        if locations and client:
                            coords = get_coordinates_simple(client, locations[0])
                            if coords:
                                print(f"✅ Coordenadas obtenidas: {coords}")
                                
                                # Actualizar la base de datos con las coordenadas
                                update_coordinates(event_id, coords)
                            else:
                                print("❌ Geocodificación falló")
            else:
                print(f"❌ No se encontraron artículos con '{location}'")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def extract_locations_simple(text: str):
    """Extracción simple de ubicaciones conocidas"""
    known_places = [
        'Gaza', 'Israel', 'Palestine', 'Ukraine', 'Russia', 'Syria', 'Iraq', 
        'Iran', 'Afghanistan', 'Yemen', 'Libya', 'Sudan', 'Somalia', 'Turkey',
        'Lebanon', 'Jordan', 'Egypt', 'Venezuela', 'Colombia', 'China', 'India',
        'Pakistan', 'Myanmar', 'Thailand', 'Philippines', 'Vietnam', 'Taiwan'
    ]
    
    locations = []
    text_lower = text.lower()
    
    for place in known_places:
        if place.lower() in text_lower:
            locations.append(place)
    
    return locations[:2]

def get_coordinates_simple(client, location: str):
    """Geocodificación simple"""
    try:
        prompt = f"Coordenadas exactas de {location} en formato JSON: {{\"latitude\": number, \"longitude\": number, \"country\": \"string\"}}"
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Limpiar formato
        if '```' in response_text:
            response_text = re.sub(r'```[a-z]*\n?', '', response_text).replace('```', '').strip()
        
        # Extraer JSON
        json_match = re.search(r'\{[^{}]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        
        return None
        
    except Exception as e:
        print(f"❌ Error Groq: {e}")
        return None

def update_coordinates(event_id: str, coords: dict):
    """Actualizar coordenadas en la base de datos"""
    try:
        db_path = Path(__file__).parent / "data" / "geopolitical_intel.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE gdelt_events 
            SET action_latitude = ?, action_longitude = ?, action_country = ?
            WHERE global_event_id = ?
        """, (
            coords.get('latitude'),
            coords.get('longitude'), 
            coords.get('country', ''),
            event_id
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Coordenadas actualizadas para {event_id}")
        
    except Exception as e:
        print(f"❌ Error actualizando coordenadas: {e}")

if __name__ == "__main__":
    test_articles_with_known_locations()
