#!/usr/bin/env python3
"""
News Deduplication and Risk Assessment with Ollama
Sistema para evitar noticias duplicadas y evaluar correctamente el nivel de riesgo
"""

import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import requests
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsDeduplicator:
    def __init__(self, db_path: str, ollama_base_url: str = "http://localhost:11434"):
        self.db_path = db_path
        self.ollama_base_url = ollama_base_url
        
    def call_ollama(self, model: str, prompt: str, timeout: int = 30) -> Optional[str]:
        """Llamar a Ollama con un modelo específico"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 512
                    }
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"Ollama error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Ollama {model}: {e}")
            return None
    
    def are_articles_duplicate(self, article1: Dict, article2: Dict) -> bool:
        """Determinar si dos artículos son duplicados usando Ollama"""
        
        # Prompt para detectar duplicados
        prompt = f"""
Analiza si estos dos artículos de noticias son sobre el mismo evento o noticia:

ARTÍCULO 1:
Título: {article1.get('title', '')[:200]}
Ubicación: {article1.get('location', '')}
Contenido: {article1.get('content', '')[:300]}

ARTÍCULO 2:
Título: {article2.get('title', '')[:200]}
Ubicación: {article2.get('location', '')}
Contenido: {article2.get('content', '')[:300]}

Responde SOLO con:
- "DUPLICADO" si son sobre el mismo evento/noticia
- "DIFERENTE" si son sobre eventos/noticias diferentes

Respuesta:"""

        # Intentar con diferentes modelos en orden de preferencia
        models = ['llama3.1:8b', 'llama3:8b', 'mistral:7b', 'gemma:7b']
        
        for model in models:
            result = self.call_ollama(model, prompt, timeout=20)
            if result:
                response = result.upper()
                if 'DUPLICADO' in response:
                    return True
                elif 'DIFERENTE' in response:
                    return False
        
        # Fallback: comparación simple por texto
        title1 = article1.get('title', '').lower()
        title2 = article2.get('title', '').lower()
        
        # Si los títulos comparten más del 70% de palabras, considerarlos duplicados
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if len(words1) > 0 and len(words2) > 0:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            similarity = intersection / union
            return similarity > 0.7
        
        return False
    
    def assess_risk_level(self, article: Dict) -> str:
        """Evaluar el nivel de riesgo de un artículo usando Ollama"""
        
        prompt = f"""
Analiza el nivel de riesgo geopolítico de esta noticia:

Título: {article.get('title', '')}
Ubicación: {article.get('location', '')}
Contenido: {article.get('content', '')[:500]}

Criterios de riesgo:
- ALTO: Conflictos armados, terrorismo, crisis económicas graves, tensiones nucleares, golpes de estado
- MEDIO: Protestas, tensiones diplomáticas, problemas económicos moderados, elecciones controvertidas
- BAJO: Noticias políticas rutinarias, eventos culturales, deportes, economía estable

Responde SOLO con una de estas palabras:
ALTO, MEDIO, BAJO

Respuesta:"""

        models = ['llama3.1:8b', 'llama3:8b', 'mistral:7b']
        
        for model in models:
            result = self.call_ollama(model, prompt, timeout=15)
            if result:
                response = result.upper().strip()
                if 'ALTO' in response:
                    return 'high'
                elif 'MEDIO' in response:
                    return 'medium'
                elif 'BAJO' in response:
                    return 'low'
        
        # Fallback: análisis por palabras clave
        content_lower = (article.get('title', '') + ' ' + article.get('content', '')).lower()
        
        high_risk_keywords = [
            'guerra', 'conflicto', 'ataque', 'bomba', 'terrorismo', 'crisis', 'golpe',
            'invasion', 'militar', 'ejercito', 'amenaza', 'tension', 'nuclear'
        ]
        
        medium_risk_keywords = [
            'protesta', 'manifestacion', 'elecciones', 'politico', 'gobierno',
            'economia', 'mercado', 'inflacion', 'desempleo'
        ]
        
        high_count = sum(1 for keyword in high_risk_keywords if keyword in content_lower)
        medium_count = sum(1 for keyword in medium_risk_keywords if keyword in content_lower)
        
        if high_count >= 2:
            return 'high'
        elif high_count >= 1 or medium_count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def detect_duplicate_images(self, articles: List[Dict]) -> Dict[str, List[int]]:
        """Detectar imágenes duplicadas por hash"""
        image_hashes = {}
        
        for article in articles:
            image_url = article.get('image')
            if image_url:
                # Crear hash simple de la URL de imagen
                image_hash = hashlib.md5(image_url.encode()).hexdigest()
                
                if image_hash not in image_hashes:
                    image_hashes[image_hash] = []
                image_hashes[image_hash].append(article.get('id'))
        
        # Retornar solo los hashes que tienen duplicados
        duplicates = {hash_val: ids for hash_val, ids in image_hashes.items() if len(ids) > 1}
        return duplicates
    
    def get_recent_articles(self, hours: int = 24, limit: int = 50) -> List[Dict]:
        """Obtener artículos recientes de la base de datos"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()
            
            # Calcular timestamp de hace X horas
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT id, title, content, country, risk_level, 
                       image_url, url, published_at, auto_generated_summary
                FROM articles 
                WHERE published_at > ? 
                ORDER BY published_at DESC 
                LIMIT ?
            """, (cutoff_time.isoformat(), limit))
            
            columns = [desc[0] for desc in cursor.description]
            articles = []
            
            for row in cursor.fetchall():
                article = dict(zip(columns, row))
                # Mapear columnas a nombres esperados
                article['location'] = article.get('country', 'Unknown')
                article['image'] = article.get('image_url', '')
                article['original_url'] = article.get('url', '')
                articles.append(article)
            
            db.close()
            return articles
            
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []
    
    def process_articles_for_display(self, hours: int = 24) -> Dict:
        """Procesar artículos para mostrar: deduplicar, evaluar riesgo, seleccionar hero"""
        logger.info("🔍 Iniciando procesamiento de artículos para display...")
        
        # Obtener artículos recientes
        articles = self.get_recent_articles(hours)
        logger.info(f"📰 Obtenidos {len(articles)} artículos recientes")
        
        if not articles:
            return {'hero': None, 'mosaic': [], 'duplicates_removed': 0}
        
        # 1. Detectar y remover duplicados
        unique_articles = []
        removed_duplicates = 0
        
        for article in articles:
            is_duplicate = False
            
            for unique_article in unique_articles:
                if self.are_articles_duplicate(article, unique_article):
                    logger.info(f"🔄 Duplicado detectado: '{article.get('title', '')[:50]}...'")
                    is_duplicate = True
                    removed_duplicates += 1
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
        
        logger.info(f"✅ {removed_duplicates} duplicados removidos, {len(unique_articles)} artículos únicos")
        
        # 2. Reevaluar niveles de riesgo
        for article in unique_articles:
            new_risk = self.assess_risk_level(article)
            if new_risk != article.get('risk_level'):
                logger.info(f"📊 Riesgo actualizado para '{article.get('title', '')[:50]}...': {article.get('risk_level')} → {new_risk}")
                article['risk_level'] = new_risk
        
        # 3. Detectar imágenes duplicadas
        duplicate_images = self.detect_duplicate_images(unique_articles)
        
        # Remover artículos con imágenes duplicadas (mantener el de mayor riesgo)
        if duplicate_images:
            articles_to_remove = set()
            
            for image_hash, article_ids in duplicate_images.items():
                if len(article_ids) > 1:
                    # Encontrar artículos con esta imagen
                    duplicate_articles = [a for a in unique_articles if a.get('id') in article_ids]
                    
                    # Ordenar por riesgo (high > medium > low) y mantener solo el primero
                    risk_order = {'high': 3, 'medium': 2, 'low': 1}
                    duplicate_articles.sort(key=lambda x: risk_order.get(x.get('risk_level', 'low'), 1), reverse=True)
                    
                    # Marcar los demás para remoción
                    for article in duplicate_articles[1:]:
                        articles_to_remove.add(article.get('id'))
                        logger.info(f"🖼️ Imagen duplicada removida: '{article.get('title', '')[:50]}...'")
            
            # Remover artículos con imágenes duplicadas
            unique_articles = [a for a in unique_articles if a.get('id') not in articles_to_remove]
        
        # 4. Seleccionar hero (artículo de mayor riesgo más reciente)
        hero_article = None
        high_risk_articles = [a for a in unique_articles if a.get('risk_level') == 'high']
        
        if high_risk_articles:
            # Ordenar por fecha más reciente
            high_risk_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            hero_article = high_risk_articles[0]
        elif unique_articles:
            # Si no hay de alto riesgo, tomar el más reciente
            unique_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            hero_article = unique_articles[0]
        
        # 5. Preparar mosaico (excluir hero y ordenar por riesgo)
        mosaic_articles = [a for a in unique_articles if a.get('id') != hero_article.get('id')] if hero_article else unique_articles
        
        # Ordenar mosaico por riesgo y luego por fecha
        risk_order = {'high': 3, 'medium': 2, 'low': 1}
        mosaic_articles.sort(
            key=lambda x: (
                risk_order.get(x.get('risk_level', 'low'), 1),
                x.get('published_at', '')
            ),
            reverse=True
        )
        
        logger.info(f"🏆 Hero seleccionado: '{hero_article.get('title', '')[:50]}...' (riesgo: {hero_article.get('risk_level')})")
        logger.info(f"🎯 Mosaico preparado con {len(mosaic_articles)} artículos")
        
        return {
            'hero': hero_article,
            'mosaic': mosaic_articles,
            'duplicates_removed': removed_duplicates,
            'total_processed': len(articles),
            'unique_articles': len(unique_articles)
        }

if __name__ == "__main__":
    # Ruta a la base de datos
    db_path = "data/geopolitical_intel.db"
    
    # Crear instancia del deduplicador
    deduplicator = NewsDeduplicator(db_path)
    
    # Procesar artículos
    result = deduplicator.process_articles_for_display()
    
    print("\n" + "="*50)
    print("RESULTADO DEL PROCESAMIENTO")
    print("="*50)
    print(f"📊 Artículos procesados: {result.get('total_processed', 0)}")
    print(f"🔄 Duplicados removidos: {result.get('duplicates_removed', 0)}")
    print(f"✅ Artículos únicos: {result.get('unique_articles', 0)}")
    
    if result.get('hero'):
        print(f"\n🏆 HERO ARTICLE:")
        print(f"   Título: {result['hero']['title']}")
        print(f"   Riesgo: {result['hero']['risk_level']}")
        print(f"   Ubicación: {result['hero']['location']}")
    
    print(f"\n🎯 MOSAICO ({len(result.get('mosaic', []))} artículos):")
    for i, article in enumerate(result.get('mosaic', [])[:10]):  # Mostrar solo los primeros 10
        print(f"   {i+1}. [{article['risk_level'].upper()}] {article['title'][:60]}...")
