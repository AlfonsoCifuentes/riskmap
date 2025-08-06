#!/usr/bin/env python3
"""
Script para probar la geocodificación con Groq
"""

import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_groq_geocoding():
    """Probar la geocodificación con Groq"""
    try:
        # Inicializar cliente Groq
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("❌ GROQ_API_KEY no encontrada en .env")
            return
        
        client = Groq(api_key=api_key)
        print(f"✅ Cliente Groq inicializado")
        
        # Títulos de prueba
        test_titles = [
            "Violence in Gaza Strip continues",
            "Protests in Kiev, Ukraine",
            "War in Syria escalates",
            "Bombing in Baghdad, Iraq",
            "Conflict in Sudan spreads",
            "Crisis in Venezuela deepens"
        ]
        
        print("\n🧪 Probando geocodificación...")
        
        for title in test_titles:
            print(f"\n📰 Título: {title}")
            
            # Extraer ubicaciones
            locations = extract_locations_simple(title)
            print(f"📍 Ubicaciones detectadas: {locations}")
            
            if locations:
                # Geocodificar primera ubicación
                coords = get_coordinates_from_groq(client, locations[0])
                if coords:
                    print(f"🗺️ Coordenadas: {coords}")
                else:
                    print("❌ No se pudieron obtener coordenadas")
            else:
                print("❌ No se detectaron ubicaciones")
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")

def extract_locations_simple(text: str):
    """Extraer ubicaciones usando patrones simples"""
    # Patrones específicos para ubicaciones conocidas
    patterns = [
        r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "in Location"
        r'\b([A-Z][a-z]+),\s*([A-Z][a-z]+)\b',  # "City, Country"
    ]
    
    locations = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                locations.extend([loc for loc in match if loc])
            else:
                locations.append(match)
    
    # Filtrar ubicaciones conocidas
    known_places = [
        'Gaza', 'Strip', 'Kiev', 'Ukraine', 'Syria', 'Baghdad', 'Iraq', 
        'Sudan', 'Venezuela', 'Palestine', 'Israel', 'Russia', 'China',
        'Afghanistan', 'Yemen', 'Lebanon', 'Turkey', 'Iran'
    ]
    
    filtered = [loc for loc in locations if any(place.lower() in loc.lower() for place in known_places)]
    return filtered[:2]  # Máximo 2

def get_coordinates_from_groq(client, location: str):
    """Obtener coordenadas usando Groq"""
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
            model="llama-3.3-70b-versatile",  # Modelo actualizado
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"🤖 Respuesta Groq: {response_text}")
        
        # Extraer JSON
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            coords_data = json.loads(json_match.group())
            if coords_data and 'latitude' in coords_data:
                return coords_data
        
        return None
        
    except Exception as e:
        print(f"❌ Error con Groq: {e}")
        return None

if __name__ == "__main__":
    test_groq_geocoding()
