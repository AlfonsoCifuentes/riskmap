#!/usr/bin/env python3
"""
SISTEMA MEJORADO DE TRADUCCIÓN Y ANÁLISIS GEOPOLÍTICO
Integra traducción automática y detección de regiones con IA local (Ollama)
Creado por: AI Assistant
Fecha: 2024
"""

import requests
import json
import sqlite3
import time
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

class EnhancedTranslationGeoSystem:
    """Sistema integrado de traducción y análisis geopolítico con IA local"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.translation_cache = {}
        self.geo_cache = {}
        
        # Modelos recomendados
        self.translation_model = "qwen2.5:7b-instruct"
        self.geo_analysis_model = "llama3.1:8b"
        self.fallback_model = "gemma2:2b"
        
        # Configuración
        self.max_retries = 3
        self.timeout = 30
        
    def check_ollama_status(self) -> Dict:
        """Verificar estado de Ollama y modelos disponibles"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                return {
                    'status': 'active',
                    'models': available_models,
                    'recommended_available': {
                        'translation': any(self.translation_model in model for model in available_models),
                        'geopolitical': any(self.geo_analysis_model in model for model in available_models),
                        'fallback': any(self.fallback_model in model for model in available_models)
                    }
                }
            else:
                return {'status': 'error', 'message': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'status': 'offline', 'error': str(e)}
    
    def install_recommended_models(self) -> Dict:
        """Instalar modelos recomendados si no están disponibles"""
        status = self.check_ollama_status()
        
        if status['status'] != 'active':
            return {'error': 'Ollama no está activo', 'details': status}
        
        results = {}
        recommended = {
            'translation': self.translation_model,
            'geopolitical': self.geo_analysis_model, 
            'fallback': self.fallback_model
        }
        
        for purpose, model in recommended.items():
            if not status['recommended_available'][purpose]:
                print(f"🔄 Instalando {model} para {purpose}...")
                try:
                    # Enviar solicitud de pull
                    pull_data = {'name': model}
                    response = requests.post(
                        f"{self.ollama_url}/api/pull",
                        json=pull_data,
                        timeout=300  # 5 minutos para descarga
                    )
                    
                    if response.status_code == 200:
                        results[purpose] = {'status': 'installed', 'model': model}
                        print(f"✅ {model} instalado correctamente")
                    else:
                        results[purpose] = {'status': 'error', 'model': model, 'error': response.text}
                        
                except Exception as e:
                    results[purpose] = {'status': 'error', 'model': model, 'error': str(e)}
            else:
                results[purpose] = {'status': 'already_available', 'model': model}
        
        return results
    
    def detect_language(self, text: str) -> str:
        """Detectar idioma del texto"""
        # Detección básica por patrones
        english_patterns = [
            r'\b(the|and|of|in|to|for|with|on|at|by|is|are|was|were)\b',
            r'\b(this|that|these|those|what|when|where|why|how)\b',
            r'\b(have|has|had|will|would|could|should|can|may)\b'
        ]
        
        spanish_patterns = [
            r'\b(el|la|los|las|un|una|de|en|que|y|a|es|son|fue|fueron)\b',
            r'\b(este|esta|estos|estas|ese|esa|esos|esas)\b',
            r'\b(tiene|tenía|será|podría|puede|debe)\b'
        ]
        
        text_lower = text.lower()
        english_matches = sum(len(re.findall(pattern, text_lower)) for pattern in english_patterns)
        spanish_matches = sum(len(re.findall(pattern, text_lower)) for pattern in spanish_patterns)
        
        if english_matches > spanish_matches * 1.5:
            return 'en'
        elif spanish_matches > english_matches * 1.5:
            return 'es'
        else:
            return 'unknown'
    
    def translate_with_ollama(self, text: str, target_lang: str = 'es') -> Optional[str]:
        """Traducir texto usando Ollama"""
        
        # Cache key
        cache_key = hashlib.md5(f"{text}_{target_lang}".encode()).hexdigest()
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # Prompt para traducción
        prompt = f"""Traduce el siguiente texto al español de forma natural y precisa. 
Mantén el contexto geopolítico y los nombres propios.
Responde ÚNICAMENTE con la traducción, sin explicaciones adicionales.

Texto a traducir:
{text}

Traducción:"""
        
        try:
            # Intentar con modelo principal
            model = self.translation_model
            status = self.check_ollama_status()
            
            if status['status'] == 'active':
                available_models = status['models']
                
                # Verificar modelo disponible
                if not any(model in available for available in available_models):
                    # Usar modelo alternativo
                    if any(self.fallback_model in available for available in available_models):
                        model = self.fallback_model
                    else:
                        # Usar primer modelo disponible
                        model = available_models[0] if available_models else None
                
                if model:
                    response = requests.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            'model': model,
                            'prompt': prompt,
                            'stream': False
                        },
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        translation = result.get('response', '').strip()
                        
                        if translation and translation != text:
                            self.translation_cache[cache_key] = translation
                            return translation
            
        except Exception as e:
            print(f"❌ Error en traducción Ollama: {e}")
        
        return None
    
    def analyze_geopolitical_context(self, title: str, content: str = "") -> Dict:
        """Analizar contexto geopolítico del artículo"""
        
        # Cache key
        text_for_analysis = f"{title} {content[:500]}"
        cache_key = hashlib.md5(text_for_analysis.encode()).hexdigest()
        
        if cache_key in self.geo_cache:
            return self.geo_cache[cache_key]
        
        # Prompt para análisis geopolítico
        prompt = f"""Analiza el siguiente artículo desde una perspectiva geopolítica y responde en formato JSON estricto.

Título: {title}
Contenido: {content[:1000]}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
    "is_geopolitical": true/false,
    "region": "nombre de la región (ej: Europa, Medio Oriente, Asia-Pacífico, América, África)",
    "country": "país principal mencionado",
    "conflict_type": "tipo de conflicto si aplica (militar, económico, diplomático, etc.)",
    "risk_level": "número del 1-10",
    "key_locations": ["ubicación1", "ubicación2"],
    "summary": "resumen breve del contexto geopolítico"
}}

Si no es geopolítico, usa is_geopolitical: false y null para los otros campos.

JSON:"""
        
        try:
            model = self.geo_analysis_model
            status = self.check_ollama_status()
            
            if status['status'] == 'active':
                available_models = status['models']
                
                # Verificar modelo disponible
                if not any(model in available for available in available_models):
                    if any(self.fallback_model in available for available in available_models):
                        model = self.fallback_model
                    else:
                        model = available_models[0] if available_models else None
                
                if model:
                    response = requests.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            'model': model,
                            'prompt': prompt,
                            'stream': False
                        },
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        analysis_text = result.get('response', '').strip()
                        
                        # Intentar parsear JSON
                        try:
                            analysis = json.loads(analysis_text)
                            # Validar y limpiar datos antes de cachear
                            analysis = self.validate_geopolitical_analysis(analysis)
                            self.geo_cache[cache_key] = analysis
                            return analysis
                        except json.JSONDecodeError:
                            # Intentar extraer JSON del texto
                            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                            if json_match:
                                try:
                                    analysis = json.loads(json_match.group())
                                    # Validar y limpiar datos antes de cachear
                                    analysis = self.validate_geopolitical_analysis(analysis)
                                    self.geo_cache[cache_key] = analysis
                                    return analysis
                                except json.JSONDecodeError:
                                    pass
            
        except Exception as e:
            print(f"❌ Error en análisis geopolítico: {e}")
        
        # Fallback - análisis básico por palabras clave
        return self.basic_geopolitical_analysis(title, content)
    
    def validate_geopolitical_analysis(self, analysis: Dict) -> Dict:
        """Validar y limpiar datos de análisis geopolítico para SQLite"""
        validated = {}
        
        # is_geopolitical - debe ser booleano
        validated['is_geopolitical'] = bool(analysis.get('is_geopolitical', False))
        
        # region - debe ser string o None
        region = analysis.get('region')
        if isinstance(region, list):
            validated['region'] = ', '.join(str(x) for x in region if x) if region else None
        elif region:
            validated['region'] = str(region)
        else:
            validated['region'] = None
            
        # country - debe ser string o None
        country = analysis.get('country')
        if isinstance(country, list):
            validated['country'] = ', '.join(str(x) for x in country if x) if country else None
        elif country:
            validated['country'] = str(country)
        else:
            validated['country'] = None
            
        # conflict_type - debe ser string o None
        conflict_type = analysis.get('conflict_type')
        if isinstance(conflict_type, list):
            validated['conflict_type'] = ', '.join(str(x) for x in conflict_type if x) if conflict_type else None
        elif conflict_type:
            validated['conflict_type'] = str(conflict_type)
        else:
            validated['conflict_type'] = None
            
        # risk_level - debe ser número entre 0-10
        risk_level = analysis.get('risk_level', 0)
        if isinstance(risk_level, list):
            risk_level = risk_level[0] if risk_level else 0
        try:
            validated['risk_level'] = max(0, min(10, float(risk_level)))
        except (ValueError, TypeError):
            validated['risk_level'] = 0
            
        # key_locations - convertir lista a string
        key_locations = analysis.get('key_locations', [])
        if isinstance(key_locations, list):
            validated['key_locations'] = [str(x) for x in key_locations if x]
        else:
            validated['key_locations'] = []
            
        # summary - debe ser string o None
        summary = analysis.get('summary')
        if isinstance(summary, list):
            validated['summary'] = ', '.join(str(x) for x in summary if x) if summary else None
        elif summary:
            validated['summary'] = str(summary)
        else:
            validated['summary'] = None
        
        return validated
    
    def basic_geopolitical_analysis(self, title: str, content: str) -> Dict:
        """Análisis geopolítico básico por palabras clave (fallback)"""
        
        text = f"{title} {content}".lower()
        
        # Detectar relevancia geopolítica
        geopolitical_keywords = [
            'war', 'guerra', 'conflict', 'conflicto', 'militar', 'military',
            'diplomacy', 'diplomacia', 'sanctions', 'sanciones', 'treaty', 'tratado',
            'government', 'gobierno', 'election', 'elecciones', 'president', 'presidente',
            'crisis', 'terror', 'security', 'seguridad', 'border', 'frontera'
        ]
        
        is_geopolitical = any(keyword in text for keyword in geopolitical_keywords)
        
        if not is_geopolitical:
            return {
                'is_geopolitical': False,
                'region': None,
                'country': None,
                'conflict_type': None,
                'risk_level': 0,
                'key_locations': [],
                'summary': None
            }
        
        # Detectar regiones
        regions_map = {
            'europa': ['europe', 'european', 'eu', 'nato', 'ukraine', 'russia', 'germany', 'france', 'italy', 'spain'],
            'medio oriente': ['middle east', 'israel', 'palestine', 'iran', 'iraq', 'syria', 'lebanon', 'yemen'],
            'asia-pacífico': ['china', 'japan', 'korea', 'taiwan', 'india', 'pakistan', 'afghanistan'],
            'américa': ['usa', 'united states', 'america', 'canada', 'mexico', 'brazil', 'venezuela', 'colombia'],
            'áfrica': ['africa', 'egypt', 'libya', 'sudan', 'ethiopia', 'somalia', 'nigeria']
        }
        
        detected_region = None
        for region, keywords in regions_map.items():
            if any(keyword in text for keyword in keywords):
                detected_region = region
                break
        
        # Calcular nivel de riesgo básico
        risk_indicators = ['war', 'guerra', 'terror', 'crisis', 'conflict', 'militar']
        risk_count = sum(1 for indicator in risk_indicators if indicator in text)
        risk_level = min(risk_count * 2 + 3, 10)
        
        return {
            'is_geopolitical': True,
            'region': detected_region,
            'country': None,  # Requeriría análisis más sofisticado
            'conflict_type': 'general',
            'risk_level': risk_level,
            'key_locations': [],
            'summary': 'Análisis básico por palabras clave'
        }
    
    def process_article(self, article_data: Dict) -> Dict:
        """Procesar artículo completo: traducción + análisis geopolítico"""
        
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        
        # 1. Detectar idioma
        detected_lang = self.detect_language(title)
        
        # 2. Traducir si es necesario
        translated_title = title
        if detected_lang == 'en':
            translation = self.translate_with_ollama(title, 'es')
            if translation:
                translated_title = translation
        
        # 3. Análisis geopolítico
        geo_analysis = self.analyze_geopolitical_context(title, content)
        
        # 4. Preparar resultado
        return {
            'original_title': title,
            'translated_title': translated_title,
            'detected_language': detected_lang,
            'translation_needed': detected_lang == 'en',
            'translation_success': translated_title != title,
            'geopolitical_analysis': geo_analysis,
            'processed_at': datetime.now().isoformat()
        }
    
    def batch_process_database(self, limit: int = 100) -> Dict:
        """Procesar artículos de la base de datos en lotes"""
        
        try:
            with sqlite3.connect('data/geopolitical_intel.db') as conn:
                cursor = conn.cursor()
                
                # Obtener artículos que necesitan procesamiento
                cursor.execute("""
                    SELECT id, title, content, summary
                    FROM unified_articles 
                    WHERE (title LIKE '%the %' OR title LIKE '%and %' OR title LIKE '%of %'
                           OR title LIKE '%in %' OR title LIKE '%to %')
                       OR region IS NULL OR region = '' OR region = 'Unknown'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                articles = cursor.fetchall()
                
                print(f"🔄 Procesando {len(articles)} artículos...")
                
                processed_count = 0
                translation_count = 0
                geo_updates = 0
                
                for article_id, title, content, summary in articles:
                    try:
                        # Procesar artículo
                        result = self.process_article({
                            'title': title,
                            'content': content or summary or ''
                        })
                        
                        # Actualizar base de datos
                        updates = []
                        params = []
                        
                        # Actualizar título traducido
                        if result['translation_success']:
                            updates.append("title = ?")
                            params.append(result['translated_title'])
                            translation_count += 1
                        
                        # Actualizar análisis geopolítico
                        geo = result['geopolitical_analysis']
                        if geo['is_geopolitical']:
                            # Convertir listas a strings si es necesario
                            if geo.get('region'):
                                region_value = geo['region']
                                if isinstance(region_value, list):
                                    region_value = ', '.join(str(x) for x in region_value)
                                updates.append("region = ?")
                                params.append(str(region_value))
                                
                            if geo.get('country'):
                                country_value = geo['country']
                                if isinstance(country_value, list):
                                    country_value = ', '.join(str(x) for x in country_value)
                                updates.append("country = ?") 
                                params.append(str(country_value))
                                
                            if geo.get('risk_level'):
                                risk_value = geo['risk_level']
                                # Asegurar que risk_level sea un número
                                if isinstance(risk_value, list):
                                    risk_value = risk_value[0] if risk_value else 0
                                try:
                                    risk_value = float(risk_value)
                                except (ValueError, TypeError):
                                    risk_value = 0
                                updates.append("risk_level = ?")
                                params.append(risk_value)
                            
                            updates.append("geopolitical_relevance = ?")
                            params.append(1)
                            geo_updates += 1
                        
                        # Ejecutar actualización
                        if updates:
                            params.append(article_id)
                            sql = f"UPDATE unified_articles SET {', '.join(updates)} WHERE id = ?"
                            cursor.execute(sql, params)
                        
                        processed_count += 1
                        
                        if processed_count % 10 == 0:
                            print(f"  ✅ Procesados {processed_count}/{len(articles)}")
                            conn.commit()  # Guardar progreso
                    
                    except Exception as e:
                        print(f"  ❌ Error procesando artículo {article_id}: {e}")
                        continue
                
                conn.commit()
                
                return {
                    'status': 'completed',
                    'total_processed': processed_count,
                    'translations': translation_count,
                    'geopolitical_updates': geo_updates,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Función principal para testing"""
    system = EnhancedTranslationGeoSystem()
    
    print("🔍 SISTEMA MEJORADO DE TRADUCCIÓN Y ANÁLISIS GEOPOLÍTICO")
    print("=" * 70)
    
    # Verificar estado
    status = system.check_ollama_status()
    print(f"\n📊 Estado de Ollama: {status['status']}")
    
    if status['status'] == 'active':
        print(f"✅ Modelos disponibles: {len(status['models'])}")
        
        # Verificar modelos recomendados
        recommended = status['recommended_available']
        print(f"🔤 Modelo de traducción: {'✅' if recommended['translation'] else '❌'}")
        print(f"🌍 Modelo geopolítico: {'✅' if recommended['geopolitical'] else '❌'}")
        print(f"🚀 Modelo fallback: {'✅' if recommended['fallback'] else '❌'}")
        
        if not all(recommended.values()):
            print("\n🔧 Instalando modelos faltantes...")
            install_result = system.install_recommended_models()
            print(f"📦 Resultado de instalación: {install_result}")
        
        # Test de procesamiento
        print("\n🧪 PRUEBA DE PROCESAMIENTO:")
        test_article = {
            'title': "Russia gives Ukrainian kids military training and reeducation",
            'content': "Russian forces are conducting military training programs for Ukrainian children in occupied territories, according to Yale researchers."
        }
        
        result = system.process_article(test_article)
        print(f"📄 Artículo original: {result['original_title']}")
        print(f"🔤 Idioma detectado: {result['detected_language']}")
        print(f"📝 Título traducido: {result['translated_title']}")
        print(f"🌍 Es geopolítico: {result['geopolitical_analysis']['is_geopolitical']}")
        print(f"📍 Región: {result['geopolitical_analysis'].get('region', 'N/A')}")
        print(f"⚠️ Nivel de riesgo: {result['geopolitical_analysis'].get('risk_level', 0)}")
        
    else:
        print(f"❌ Ollama no está disponible: {status.get('error', 'Desconocido')}")
        print("\n💡 Para resolver:")
        print("1. Instalar Ollama: https://ollama.ai/download")
        print("2. Ejecutar: ollama serve")
        print("3. Instalar modelos: ollama pull qwen2.5:7b-instruct")

if __name__ == "__main__":
    main()