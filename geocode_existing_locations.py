#!/usr/bin/env python3
"""
Script RÁPIDO para geocodificar ubicaciones existentes en GDELT
Usa cache local y modelos optimizados para velocidad
"""

import os
import sqlite3
import json
import re
import requests
import time
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Cache de coordenadas para ubicaciones conocidas (ACTUALIZADO)
LOCATION_CACHE = {
    'gaza': {'latitude': 31.5075, 'longitude': 34.4522, 'country': 'Palestine'},
    'gaza strip': {'latitude': 31.5075, 'longitude': 34.4522, 'country': 'Palestine'},
    'ukraine': {'latitude': 50.4501, 'longitude': 30.5236, 'country': 'Ukraine'},
    'kyiv': {'latitude': 50.4501, 'longitude': 30.5236, 'country': 'Ukraine'},
    'kiev': {'latitude': 50.4501, 'longitude': 30.5236, 'country': 'Ukraine'},
    'russia': {'latitude': 55.7558, 'longitude': 37.6176, 'country': 'Russia'},
    'moscow': {'latitude': 55.7558, 'longitude': 37.6176, 'country': 'Russia'},
    'syria': {'latitude': 35.0, 'longitude': 38.0, 'country': 'Syria'},
    'damascus': {'latitude': 33.5138, 'longitude': 36.2765, 'country': 'Syria'},
    'israel': {'latitude': 31.5, 'longitude': 34.8, 'country': 'Israel'},
    'iran': {'latitude': 32.0, 'longitude': 53.0, 'country': 'Iran'},
    'tehran': {'latitude': 35.6944, 'longitude': 51.4215, 'country': 'Iran'},
    'iraq': {'latitude': 33.0, 'longitude': 44.0, 'country': 'Iraq'},
    'baghdad': {'latitude': 33.3152, 'longitude': 44.4361, 'country': 'Iraq'},
    'afghanistan': {'latitude': 34.0, 'longitude': 66.0, 'country': 'Afghanistan'},
    'kabul': {'latitude': 34.5553, 'longitude': 69.2075, 'country': 'Afghanistan'},
    'yemen': {'latitude': 15.0, 'longitude': 44.0, 'country': 'Yemen'},
    'sudan': {'latitude': 15.0, 'longitude': 30.0, 'country': 'Sudan'},
    'khartoum': {'latitude': 15.5007, 'longitude': 32.5599, 'country': 'Sudan'},
    'libya': {'latitude': 27.0, 'longitude': 17.0, 'country': 'Libya'},
    'tripoli': {'latitude': 32.8872, 'longitude': 13.1913, 'country': 'Libya'},
    'lebanon': {'latitude': 34.0, 'longitude': 36.0, 'country': 'Lebanon'},
    'beirut': {'latitude': 33.8938, 'longitude': 35.5018, 'country': 'Lebanon'},
    'turkey': {'latitude': 39.0, 'longitude': 35.0, 'country': 'Turkey'},
    'ankara': {'latitude': 39.9334, 'longitude': 32.8597, 'country': 'Turkey'},
    'pakistan': {'latitude': 30.0, 'longitude': 70.0, 'country': 'Pakistan'},
    'islamabad': {'latitude': 33.6844, 'longitude': 73.0479, 'country': 'Pakistan'},
    'india': {'latitude': 20.0, 'longitude': 77.0, 'country': 'India'},
    'new delhi': {'latitude': 28.6139, 'longitude': 77.2090, 'country': 'India'},
    'china': {'latitude': 35.0, 'longitude': 105.0, 'country': 'China'},
    'beijing': {'latitude': 39.9042, 'longitude': 116.4074, 'country': 'China'},
    'myanmar': {'latitude': 22.0, 'longitude': 98.0, 'country': 'Myanmar'},
    'thailand': {'latitude': 15.0, 'longitude': 100.0, 'country': 'Thailand'},
    'bangkok': {'latitude': 13.7563, 'longitude': 100.5018, 'country': 'Thailand'},
    'venezuela': {'latitude': 8.0, 'longitude': -66.0, 'country': 'Venezuela'},
    'caracas': {'latitude': 10.4806, 'longitude': -66.9036, 'country': 'Venezuela'},
    'colombia': {'latitude': 4.0, 'longitude': -74.0, 'country': 'Colombia'},
    'bogota': {'latitude': 4.7110, 'longitude': -74.0721, 'country': 'Colombia'},
    'haiti': {'latitude': 19.0, 'longitude': -72.0, 'country': 'Haiti'},
    'crimea': {'latitude': 45.3, 'longitude': 34.4, 'country': 'Ukraine'},
    'jiangyou': {'latitude': 31.7667, 'longitude': 104.7333, 'country': 'China'},
    'japan': {'latitude': 36.0, 'longitude': 138.0, 'country': 'Japan'},
    'tokyo': {'latitude': 35.6762, 'longitude': 139.6503, 'country': 'Japan'},
    'vinnitsa': {'latitude': 49.2333, 'longitude': 28.4667, 'country': 'Ukraine'},
    'vinnytsia': {'latitude': 49.2333, 'longitude': 28.4667, 'country': 'Ukraine'},
    'crocus city hall': {'latitude': 55.8317, 'longitude': 37.4603, 'country': 'Russia'},
    'crocus': {'latitude': 55.8317, 'longitude': 37.4603, 'country': 'Russia'},
}

def check_database_cache(location: str):
    """Verificar si ya tenemos coordenadas para esta ubicación en la BD"""
    try:
        db_path = Path(__file__).parent / "data" / "geopolitical_intel.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT action_latitude, action_longitude, action_country
            FROM gdelt_events 
            WHERE action_location = ? 
            AND action_latitude IS NOT NULL 
            AND action_longitude IS NOT NULL
            LIMIT 1
        """, (location,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] and result[1]:
            return {
                'latitude': result[0],
                'longitude': result[1], 
                'country': result[2] or '',
                'precision': 'cached'
            }
        
        return None
        
    except Exception:
        return None

def check_ollama_availability():
    """Verificar si Ollama está disponible"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def get_best_ollama_model():
    """Obtener el mejor modelo disponible de Ollama"""
    preferred_models = ["gemma2:2b", "qwen3:latest", "llama3:latest", "deepseek-r1:7b"]
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            available_models = [model['name'] for model in response.json().get('models', [])]
            for model in preferred_models:
                if model in available_models:
                    return model
    except Exception:
        pass
    
    return None

def geocode_existing_locations():
    """Geocodificar ubicaciones GDELT existentes que no tienen coordenadas"""
    
    try:
        # Inicializar cliente Groq
        groq_client = None
        api_key = os.getenv('GROQ_API_KEY')
        if api_key:
            try:
                groq_client = Groq(api_key=api_key)
                print("✅ Cliente Groq inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando Groq: {e}")
        
        # Verificar Ollama
        ollama_available = check_ollama_availability()
        if ollama_available:
            print("✅ Ollama disponible como fallback")
        else:
            print("⚠️ Ollama no disponible")
        
        if not groq_client and not ollama_available:
            print("❌ Ni Groq ni Ollama están disponibles")
            return
        
        # Conectar a la base de datos
        db_path = Path(__file__).parent / "data" / "geopolitical_intel.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Obtener ubicaciones sin coordenadas pero CON título para contexto
        cursor.execute("""
            SELECT global_event_id, action_location, article_title
            FROM gdelt_events 
            WHERE action_location != '' 
            AND action_location IS NOT NULL
            AND (action_latitude IS NULL OR action_longitude IS NULL)
            AND LENGTH(action_location) > 3
            ORDER BY event_date DESC
            LIMIT 50
        """)
        
        locations_to_geocode = cursor.fetchall()
        
        if not locations_to_geocode:
            print("❌ No se encontraron ubicaciones para geocodificar")
            conn.close()
            return
        
        print(f"🔍 Encontradas {len(locations_to_geocode)} ubicaciones para geocodificar")
        
        updated_count = 0
        
        for event_id, location, title in locations_to_geocode:
            print(f"\n📍 Geocodificando: {location}")
            print(f"📰 Contexto: {title[:100]}...")
            
            try:
                # Obtener coordenadas con fallback
                coords = get_coordinates_with_fallback(groq_client, location, title)
                
                if coords:
                    # Actualizar en la base de datos
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
                    
                    updated_count += 1
                    print(f"✅ Actualizado: {location} -> ({coords['latitude']}, {coords['longitude']})")
                else:
                    print(f"❌ No se pudieron obtener coordenadas para: {location}")
                
                # Commit cada 10 actualizaciones
                if updated_count % 10 == 0:
                    conn.commit()
                    print(f"💾 Guardadas {updated_count} actualizaciones...")
                
            except Exception as e:
                print(f"❌ Error geocodificando {location}: {e}")
        
        # Commit final
        conn.commit()
        conn.close()
        
        print(f"\n✅ Proceso completado: {updated_count} ubicaciones geocodificadas")
        
    except Exception as e:
        print(f"❌ Error en proceso de geocodificación: {e}")

def get_coordinates_with_fallback(groq_client, location: str, title: str = ""):
    """Obtener coordenadas usando cache primero, luego Groq/Ollama"""
    
    # 1. Verificar cache local primero
    location_key = location.lower().strip()
    if location_key in LOCATION_CACHE:
        coords = LOCATION_CACHE[location_key]
        print(f"💾 Cache: {location} -> {coords}")
        return coords
    
    # 2. Verificar si ya existe en la base de datos
    cached_coords = check_database_cache(location)
    if cached_coords:
        print(f"🗄️ DB Cache: {location} -> {cached_coords}")
        return cached_coords
    
    # 3. Intentar con Groq primero
    if groq_client:
        try:
            coords = get_coordinates_groq(groq_client, location, title)
            if coords and coords.get('latitude') and coords.get('longitude'):
                print(f"🤖 Groq: {location} -> {coords}")
                # Guardar en cache local para futuras consultas
                LOCATION_CACHE[location_key] = coords
                return coords
        except Exception as e:
            if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                print("⚠️ Groq rate limit alcanzado, usando Ollama...")
            else:
                print(f"⚠️ Error Groq: {e}, intentando Ollama...")
    
    # 4. Fallback a Ollama
    try:
        coords = get_coordinates_ollama(location, title)
        if coords and coords.get('latitude') and coords.get('longitude'):
            print(f"🦙 Ollama: {location} -> {coords}")
            # Guardar en cache local para futuras consultas
            LOCATION_CACHE[location_key] = coords
            return coords
    except Exception as e:
        print(f"❌ Error Ollama: {e}")
    
    return None

def get_coordinates_ollama(location: str, title: str = ""):
    """Obtener coordenadas usando Ollama con prompt especializado en conflictos"""
    try:
        model = get_best_ollama_model()
        if not model:
            return None
        
        # Prompt especializado para análisis de conflictos
        prompt = f"""ANÁLISIS GEOGRÁFICO DE CONFLICTO:

Ubicación reportada: "{location}"
Contexto de la noticia: "{title}"

INSTRUCCIONES CRÍTICAS:
- Analiza la ubicación específica del conflicto mencionado
- Las coordenadas serán usadas para análisis de satélite de alta precisión
- Debes ser EXTREMADAMENTE PRECISO - área máxima de 10-20 km²
- Si es una ciudad, da coordenadas del centro urbano específico
- Si es una región, identifica el punto más probable del conflicto
- NO des coordenadas de países enteros

Responde SOLO en formato JSON:
{{"latitude": número_decimal_preciso, "longitude": número_decimal_preciso, "country": "país", "precision": "high|medium|low"}}

Si no puedes ser preciso, responde: null"""
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 150
            }
        }
        
        response = requests.post("http://localhost:11434/api/generate", 
                               json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()
            
            # Limpiar formato
            if '```' in response_text:
                response_text = re.sub(r'```[a-z]*\n?', '', response_text).replace('```', '').strip()
            
            # Extraer JSON
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                coords_data = json.loads(json_match.group())
                if coords_data and 'latitude' in coords_data:
                    return coords_data
        
        return None
        
    except Exception as e:
        print(f"❌ Error Ollama API: {e}")
        return None

def get_coordinates_groq(client, location: str, title: str = ""):
    """Obtener coordenadas usando Groq con prompt especializado en conflictos"""
    try:
        # Prompt especializado para análisis de conflictos y precisión geográfica
        prompt = f"""ANÁLISIS GEOGRÁFICO DE CONFLICTO - ALTA PRECISIÓN REQUERIDA

Ubicación del conflicto: "{location}"
Contexto de la noticia: "{title}"

INSTRUCCIONES CRÍTICAS:
🎯 Necesito coordenadas EXACTAS para análisis satelital de alta resolución
🎯 Las coordenadas mapearán un área específica de máximo 10-20 km²
🎯 Si es una ciudad: coordenadas del centro o área específica del conflicto
🎯 Si es una región: identifica la zona más probable del conflicto
🎯 NO proporciones coordenadas de países enteros - deben ser PRECISAS

ANÁLISIS REQUERIDO:
- Identifica la ubicación geográfica EXACTA del conflicto
- Considera el tipo de evento para determinar la zona específica
- Prioriza centros urbanos, bases militares, o áreas de disputa conocidas

Responde ÚNICAMENTE en formato JSON válido:
{{
    "latitude": número_decimal_con_4_decimales,
    "longitude": número_decimal_con_4_decimales,
    "country": "nombre_del_país",
    "precision": "high|medium|low",
    "area_type": "urban|rural|military|border"
}}

Si no puedes ser PRECISO y ESPECÍFICO, responde: null"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Limpiar formato markdown
        if '```' in response_text:
            response_text = re.sub(r'```[a-z]*\n?', '', response_text).replace('```', '').strip()
        
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
    geocode_existing_locations()
