#!/usr/bin/env python3
"""Test Groq API for precise geolocation"""

import os
import requests
import json
from dotenv import load_dotenv

def test_groq_precise_geolocation():
    """Test que Groq puede dar coordenadas precisas"""
    
    # Cargar variables de entorno
    load_dotenv()
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    
    if not groq_api_key:
        print("❌ GROQ_API_KEY no encontrada")
        return False
    
    print(f"✅ Groq API Key encontrada: {groq_api_key[:20]}...")
    
    # Test content - un artículo sobre Gaza con ubicación específica
    test_content = """
    Título: Israeli forces raid Gaza hospital amid ongoing hostage negotiations

    Contenido: Israeli military forces conducted a targeted operation at Al-Shifa Hospital in Gaza City early Wednesday morning, following intelligence reports about militant activity in the medical facility. The raid occurred in the northern district of Gaza, specifically in the Rimal neighborhood where the hospital is located. Local residents reported gunfire and explosions near the hospital compound around 3 AM local time. The operation lasted approximately 4 hours and involved special forces units. Al-Shifa Hospital, Gaza's largest medical facility, has been a focal point of the conflict.
    """
    
    prompt = f"""Eres un analista geopolítico especializado en geolocalización precisa de conflictos. 

NOTICIA: {test_content[:1500]}

UBICACIÓN SUGERIDA: Gaza

TAREA: Busca en fuentes actuales (noticias, mapas, reportes) las coordenadas exactas donde está ocurriendo este conflicto específico. NO uses coordenadas generales de países o ciudades.

INSTRUCCIONES:
1. Identifica el lugar EXACTO donde está el conflicto (barrio, distrito, base militar, frontera específica, etc.)
2. Busca las coordenadas GPS precisas de ESE lugar específico
3. El área debe ser pequeña (máximo 5-10 km²) para análisis satelital eficiente
4. Si hay múltiples ubicaciones, elige la MÁS IMPORTANTE del conflicto

RESPONDE SOLO CON JSON VÁLIDO:
{{
    "precise_location": "nombre exacto del lugar específico",
    "latitude": número_decimal_con_4_decimales,
    "longitude": número_decimal_con_4_decimales,
    "confidence": 0.0-1.0,
    "area_description": "descripción del área específica",
    "area_size_km": tamaño_estimado_en_km,
    "source_confidence": "high|medium|low",
    "reasoning": "por qué elegiste estas coordenadas específicas"
}}

IMPORTANTE: Coordenadas deben ser ESPECÍFICAS del lugar de conflicto, no de la ciudad general."""

    try:
        headers = {
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": "llama-3.3-70b-versatile",  # Modelo actual disponible en Groq
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        print("🔍 Enviando petición a Groq...")
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"📡 Respuesta de Groq: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print("📝 Respuesta completa de Groq:")
            print(content)
            print()
            
            # Extraer JSON de la respuesta
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                try:
                    geo_data = json.loads(json_str)
                    
                    print("✅ JSON parseado exitosamente:")
                    print(f"   📍 Ubicación precisa: {geo_data.get('precise_location', 'N/A')}")
                    print(f"   🎯 Coordenadas: {geo_data.get('latitude', 'N/A')}, {geo_data.get('longitude', 'N/A')}")
                    print(f"   📏 Área: {geo_data.get('area_size_km', 'N/A')} km²")
                    print(f"   🎰 Confianza: {geo_data.get('confidence', 'N/A')}")
                    print(f"   💭 Razonamiento: {geo_data.get('reasoning', 'N/A')}")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Error parseando JSON: {e}")
                    print(f"JSON extraído: {json_str}")
                    return False
            else:
                print("❌ No se encontró JSON válido en la respuesta")
                return False
        else:
            print(f"❌ Error en Groq API: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de Groq: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando Groq API para geolocalización precisa...")
    success = test_groq_precise_geolocation()
    
    if success:
        print("\n🎉 ¡Test exitoso! Groq puede proporcionar coordenadas precisas")
    else:
        print("\n💥 Test falló. Revisar configuración de Groq")
