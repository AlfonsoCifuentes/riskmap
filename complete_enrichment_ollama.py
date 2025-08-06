#!/usr/bin/env python3
"""
Enriquecimiento masivo COMPLETO usando modelos locales de Ollama
Procesa TODA la base de datos sin límites
"""

import sqlite3
import json
import requests
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import re
import os
from urllib.parse import urlparse, urljoin
import hashlib
from bs4 import BeautifulSoup

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'ollama_enrichment_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class CompleteOllamaEnricher:
    """Enriquecedor completo usando modelos locales de Ollama"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.models = {
            'primary': 'deepseek-r1:7b',     # Modelo principal para análisis complejo
            'fast': 'gemma2:2b',             # Modelo rápido para extracciones simples
            'backup': 'llama3:latest'        # Modelo de respaldo
        }
        self.db_path = Path('data/geopolitical_intel.db')
        self.images_dir = Path('data/images')
        self.images_dir.mkdir(exist_ok=True)
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def test_ollama_connection(self):
        """Verificar que Ollama esté funcionando"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                logger.info(f"✅ Ollama conectado. Modelos disponibles: {models}")
                return True
            else:
                logger.error(f"❌ Ollama responde pero con error: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ No se puede conectar a Ollama: {e}")
            return False
    
    def query_ollama(self, prompt: str, model: str = None, max_retries: int = 3) -> Optional[str]:
        """Hacer consulta a Ollama con reintentos"""
        if not model:
            model = self.models['primary']
            
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 500
            }
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🤖 Consultando {model} (intento {attempt + 1})")
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()
                else:
                    logger.warning(f"⚠️ Error {response.status_code} en intento {attempt + 1}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Error de conexión en intento {attempt + 1}: {e}")
                
            # Esperar antes del siguiente intento
            if attempt < max_retries - 1:
                time.sleep(3 ** attempt)
        
        logger.error(f"❌ Falló después de {max_retries} intentos con {model}")
        return None
    
    def extract_entities(self, title: str, content: str) -> Dict[str, Any]:
        """Extraer entidades usando Ollama"""
        
        text_to_analyze = f"{title}. {content[:500] if content else ''}"
        
        prompt = f"""Analyze this news article and extract key geopolitical information. Respond ONLY with a valid JSON object:

Text: {text_to_analyze}

Extract these fields exactly:
{{
    "key_persons": ["list of important people mentioned"],
    "key_locations": ["list of countries, cities, regions mentioned"],
    "geopolitical_relevance": (score from 0-10),
    "risk_level": "low", "medium", or "high",
    "summary": "Brief 2-sentence summary",
    "main_topics": ["list of main topics discussed"]
}}

Respond only with the JSON object, no additional text."""

        response = self.query_ollama(prompt, self.models['primary'])
        
        if response:
            try:
                # Limpiar respuesta y extraer JSON
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response.replace('```json', '').replace('```', '')
                
                # Buscar JSON en la respuesta
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                    
                    # Validar estructura mínima
                    required_fields = ['key_persons', 'key_locations', 'geopolitical_relevance']
                    if all(field in result for field in required_fields):
                        logger.info("✅ Análisis NLP exitoso")
                        return result
                    
                logger.warning("⚠️ JSON no tiene la estructura esperada")
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Error parseando JSON: {e}")
                
        # Fallback: análisis básico
        logger.info("📝 Usando análisis de fallback")
        return self.fallback_analysis(title, content)
    
    def fallback_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """Análisis básico cuando falla el análisis principal"""
        
        text = f"{title} {content or ''}".lower()
        
        # Buscar países comunes
        countries = [
            'ukraine', 'russia', 'china', 'usa', 'iran', 'israel', 'palestine', 
            'syria', 'afghanistan', 'north korea', 'south korea', 'india', 
            'pakistan', 'turkey', 'egypt', 'saudi arabia', 'europe', 'america'
        ]
        
        found_locations = [country.title() for country in countries if country in text]
        
        # Buscar palabras clave geopolíticas
        geopolitical_keywords = [
            'war', 'conflict', 'military', 'sanctions', 'treaty', 'diplomacy', 
            'election', 'government', 'president', 'minister', 'crisis', 
            'protest', 'terrorism', 'peace', 'security'
        ]
        
        relevance_score = sum(2 if keyword in text else 0 for keyword in geopolitical_keywords)
        relevance_score = min(relevance_score, 10)
        
        # Determinar nivel de riesgo
        if relevance_score >= 8:
            risk_level = "high"
        elif relevance_score >= 4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "key_persons": [],
            "key_locations": found_locations[:5],
            "geopolitical_relevance": relevance_score,
            "risk_level": risk_level,
            "summary": f"Article about {', '.join(found_locations[:2]) if found_locations else 'various topics'}.",
            "main_topics": geopolitical_keywords[:3] if relevance_score > 0 else ["general_news"]
        }
    
    def download_image_from_url(self, image_url: str, article_id: int) -> Optional[str]:
        """Descargar imagen desde URL"""
        try:
            response = requests.get(image_url, headers=self.headers, timeout=15, stream=True)
            if response.status_code == 200:
                # Generar nombre único
                url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
                extension = '.jpg'
                
                content_type = response.headers.get('content-type', '')
                if 'png' in content_type:
                    extension = '.png'
                elif 'gif' in content_type:
                    extension = '.gif'
                elif 'webp' in content_type:
                    extension = '.webp'
                
                filename = f"article_{article_id}_{url_hash}{extension}"
                filepath = self.images_dir / filename
                
                # Descargar imagen
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verificar que se descargó correctamente
                if filepath.exists() and filepath.stat().st_size > 1000:  # Al menos 1KB
                    logger.info(f"✅ Imagen descargada: {filename}")
                    return str(filepath)
                else:
                    filepath.unlink(missing_ok=True)
                    
        except Exception as e:
            logger.warning(f"⚠️ Error descargando imagen {image_url}: {e}")
        
        return None
    
    def extract_image_from_article(self, url: str, article_id: int) -> Optional[str]:
        """Extraer imagen principal del artículo"""
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar meta tags de imagen primero
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image['content']
                if self.is_valid_image_url(image_url, url):
                    result = self.download_image_from_url(image_url, article_id)
                    if result:
                        return result
            
            # Buscar Twitter card
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                image_url = twitter_image['content']
                if self.is_valid_image_url(image_url, url):
                    result = self.download_image_from_url(image_url, article_id)
                    if result:
                        return result
            
            # Buscar imágenes en el contenido
            img_selectors = [
                'img[class*="featured"]',
                'img[class*="hero"]',
                'img[class*="main"]',
                'article img',
                '.article img',
                '.content img'
            ]
            
            for selector in img_selectors:
                img = soup.select_one(selector)
                if img and img.get('src'):
                    image_url = img['src']
                    if self.is_valid_image_url(image_url, url):
                        result = self.download_image_from_url(image_url, article_id)
                        if result:
                            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo imagen de {url}: {e}")
        
        return None
    
    def is_valid_image_url(self, image_url: str, base_url: str) -> bool:
        """Validar y normalizar URL de imagen"""
        if not image_url:
            return False
            
        # Normalizar URL
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            base_netloc = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
            image_url = urljoin(base_netloc, image_url)
        
        # Verificar que sea una URL válida de imagen
        if not image_url.startswith('http'):
            return False
            
        # Verificar extensión
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        url_lower = image_url.lower()
        
        return any(ext in url_lower for ext in valid_extensions) or 'image' in url_lower
    
    def analyze_image_basic(self, image_path: str) -> Dict[str, Any]:
        """Análisis básico de imagen"""
        try:
            file_size = os.path.getsize(image_path)
            filename = os.path.basename(image_path)
            
            return {
                "has_image": True,
                "image_file": filename,
                "file_size_kb": round(file_size / 1024, 2),
                "detected_objects": json.dumps(["news_image"]),
                "visual_analysis_json": json.dumps({
                    "type": "news_article_image",
                    "confidence": 0.8,
                    "description": "Image associated with news article",
                    "timestamp": datetime.now().isoformat()
                }),
                "has_faces": 0
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error analizando imagen {image_path}: {e}")
            return {
                "has_image": False,
                "detected_objects": "",
                "visual_analysis_json": "",
                "has_faces": 0
            }
    
    def enrich_article(self, article_id: int, title: str, content: str, url: str = None) -> bool:
        """Enriquecer un artículo completo"""
        
        logger.info(f"🔍 Enriqueciendo artículo {article_id}: {title[:50]}...")
        
        # 1. Análisis NLP
        analysis = self.extract_entities(title, content or title)
        if not analysis:
            logger.warning(f"⚠️ No se pudo analizar artículo {article_id}")
            return False
        
        # 2. Procesamiento de imagen
        image_data = {}
        local_image_path = None
        
        if url and url.startswith('http'):
            logger.info(f"🖼️ Buscando imagen para artículo {article_id}")
            local_image_path = self.extract_image_from_article(url, article_id)
            
            if local_image_path:
                image_analysis = self.analyze_image_basic(local_image_path)
                image_data.update(image_analysis)
                image_data['image_url'] = local_image_path
            else:
                logger.info(f"📷 No se encontró imagen válida para artículo {article_id}")
        
        # 3. Preparar actualización
        updates = {
            'key_persons': json.dumps(analysis.get('key_persons', [])),
            'key_locations': json.dumps(analysis.get('key_locations', [])),
            'extracted_entities_json': json.dumps(analysis),
            'summary': analysis.get('summary', ''),
            'geopolitical_relevance': analysis.get('geopolitical_relevance', 5),
            'risk_level': analysis.get('risk_level', 'medium'),
            'groq_enhanced': 1,
            'last_enrichment': datetime.now().isoformat()
        }
        
        # Añadir datos de imagen si existen
        if image_data:
            updates.update({
                'image_url': image_data.get('image_url', ''),
                'detected_objects': image_data.get('detected_objects', ''),
                'visual_analysis_json': image_data.get('visual_analysis_json', ''),
                'has_faces': image_data.get('has_faces', 0)
            })
        
        # 4. Actualizar base de datos
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
            query = f"UPDATE articles SET {set_clause} WHERE id = ?"
            values = list(updates.values()) + [article_id]
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            success_msg = f"✅ Artículo {article_id} enriquecido"
            if local_image_path:
                success_msg += f" (con imagen)"
            logger.info(success_msg)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando artículo {article_id}: {e}")
            return False
    
    def run_complete_enrichment(self):
        """Ejecutar enriquecimiento completo de TODA la base de datos"""
        
        logger.info("🚀 Iniciando enriquecimiento COMPLETO con Ollama")
        
        # Verificar conexión
        if not self.test_ollama_connection():
            logger.error("❌ No se puede conectar a Ollama")
            return
        
        # Conectar a base de datos
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Obtener TODOS los artículos sin enriquecer
        query = """
        SELECT id, title, content, url 
        FROM articles 
        WHERE (groq_enhanced IS NULL OR groq_enhanced = 0)
        AND title IS NOT NULL
        ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        articles = cursor.fetchall()
        total_count = len(articles)
        
        logger.info(f"📊 Encontrados {total_count} artículos para enriquecer (TODOS)")
        
        if total_count == 0:
            logger.info("✅ No hay artículos pendientes")
            conn.close()
            return 0, 0
        
        # Procesar todos los artículos
        success_count = 0
        start_time = time.time()
        
        for i, (article_id, title, content, url) in enumerate(articles, 1):
            logger.info(f"📝 [{i}/{total_count}] ID {article_id}")
            
            if self.enrich_article(article_id, title, content, url):
                success_count += 1
            
            # Pausa para no sobrecargar
            time.sleep(3)
            
            # Progreso cada 10 artículos
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed * 60  # artículos por minuto
                logger.info(f"📈 Progreso: {i}/{total_count} ({success_count} exitosos) - {rate:.1f} art/min")
                
            # Pausa larga cada 50 artículos
            if i % 50 == 0:
                logger.info("⏸️ Pausa para limpieza...")
                time.sleep(10)
        
        conn.close()
        
        # Reporte final
        elapsed_total = time.time() - start_time
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        logger.info(f"🎯 ENRIQUECIMIENTO COMPLETO TERMINADO:")
        logger.info(f"   - Exitosos: {success_count}/{total_count} ({success_rate:.1f}%)")
        logger.info(f"   - Tiempo total: {elapsed_total/60:.1f} minutos")
        logger.info(f"   - Velocidad promedio: {total_count/(elapsed_total/60):.1f} artículos/minuto")
        
        return success_count, total_count

def main():
    """Función principal"""
    enricher = CompleteOllamaEnricher()
    
    print("🤖 ENRIQUECIMIENTO MASIVO COMPLETO CON OLLAMA")
    print("=" * 70)
    print("📊 Procesando TODA la base de datos sin límites")
    print("🧠 Análisis NLP completo con modelos locales")
    print("🖼️ Descarga y análisis de imágenes de artículos")
    print("🔄 Procesamiento continuo hasta completar TODO")
    print("=" * 70)
    
    # Confirmar antes de proceder
    try:
        confirm = input("\n¿Continuar con el enriquecimiento completo? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Cancelado por el usuario")
            return
    except KeyboardInterrupt:
        print("\n❌ Cancelado por el usuario")
        return
    
    # Ejecutar enriquecimiento completo
    success, total = enricher.run_complete_enrichment()
    
    print("\n" + "=" * 70)
    print("✅ PROCESAMIENTO COMPLETADO:")
    print(f"   - Artículos procesados exitosamente: {success}")
    print(f"   - Total de artículos: {total}")
    if total > 0:
        print(f"   - Tasa de éxito final: {success/total*100:.1f}%")
    print("=" * 70)

if __name__ == '__main__':
    main()
