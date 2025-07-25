#!/usr/bin/env python3
"""
Script avanzado para detectar fuentes de noticias usando IA (Groq, OpenAI, etc.)
"""

import sqlite3
import sys
import os
import json
import requests
from pathlib import Path
from urllib.parse import urlparse

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.config import config, logger

class AISourceDetector:
    def __init__(self):
        """Inicializar el detector de fuentes con IA"""
        
        # Obtener API keys
        self.groq_key = config.get_groq_key()
        self.openai_key = config.get_openai_key()
        self.deepseek_key = config.get_deepseek_key()
        
        # Mapeo de dominios conocidos (fallback)
        self.domain_sources = {
            'reuters.com': 'Reuters',
            'bbc.com': 'BBC News',
            'bbc.co.uk': 'BBC News',
            'cnn.com': 'CNN',
            'nytimes.com': 'The New York Times',
            'washingtonpost.com': 'The Washington Post',
            'theguardian.com': 'The Guardian',
            'ft.com': 'Financial Times',
            'wsj.com': 'Wall Street Journal',
            'bloomberg.com': 'Bloomberg',
            'ap.org': 'Associated Press',
            'apnews.com': 'Associated Press',
            'aljazeera.com': 'Al Jazeera',
            'aljazeera.net': 'Al Jazeera',
            'elpais.com': 'El País',
            'elmundo.es': 'El Mundo',
            'abc.es': 'ABC',
            'lavanguardia.com': 'La Vanguardia',
            'lemonde.fr': 'Le Monde',
            'lefigaro.fr': 'Le Figaro',
            'spiegel.de': 'Der Spiegel',
            'zeit.de': 'Die Zeit',
            'corriere.it': 'Corriere della Sera',
            'repubblica.it': 'La Repubblica',
            'rt.com': 'RT News',
            'sputniknews.com': 'Sputnik News',
            'tass.com': 'TASS',
            'tass.ru': 'TASS',
            'xinhuanet.com': 'Xinhua News',
            'scmp.com': 'South China Morning Post',
            'japantimes.co.jp': 'The Japan Times',
            'straitstimes.com': 'The Straits Times',
            'clarin.com': 'Clarín',
            'lanacion.com.ar': 'La Nación',
            'folha.uol.com.br': 'Folha de S.Paulo',
            'globo.com': 'O Globo',
            'dawn.com': 'Dawn',
            'hindustantimes.com': 'Hindustan Times',
            'dw.com': 'Deutsche Welle',
            'euronews.com': 'Euronews',
            'france24.com': 'France 24',
            'skynews.com': 'Sky News',
            'foxnews.com': 'Fox News',
            'cnbc.com': 'CNBC',
            'npr.org': 'NPR',
            'independent.co.uk': 'The Independent',
            'telegraph.co.uk': 'The Telegraph',
            'economist.com': 'The Economist',
            'politico.com': 'Politico',
            'efe.com': 'Agencia EFE',
            'afp.com': 'AFP'
        }
        
        # Lista de fuentes conocidas para validación
        self.known_sources = [
            'Reuters', 'BBC News', 'CNN', 'The New York Times', 'The Washington Post',
            'The Guardian', 'Financial Times', 'Wall Street Journal', 'Bloomberg',
            'Associated Press', 'Al Jazeera', 'El País', 'El Mundo', 'ABC',
            'La Vanguardia', 'Le Monde', 'Le Figaro', 'Der Spiegel', 'Die Zeit',
            'Corriere della Sera', 'La Repubblica', 'RT News', 'Sputnik News',
            'TASS', 'Xinhua News', 'South China Morning Post', 'The Japan Times',
            'The Straits Times', 'Clarín', 'La Nación', 'Folha de S.Paulo',
            'O Globo', 'Dawn', 'Hindustan Times', 'Deutsche Welle', 'Euronews',
            'France 24', 'Sky News', 'Fox News', 'CNBC', 'NPR', 'The Independent',
            'The Telegraph', 'The Economist', 'Politico', 'Agencia EFE', 'AFP',
            'USA Today', 'Los Angeles Times', 'Chicago Tribune', 'The Boston Globe',
            'Axios', 'Vox', 'HuffPost', 'PBS NewsHour', 'Libération'
        ]
    
    def extract_domain_from_url(self, url):
        """Extraer dominio de URL"""
        try:
            if not url:
                return None
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return None
    
    def detect_source_from_url(self, url):
        """Detectar fuente desde URL usando mapeo de dominios"""
        domain = self.extract_domain_from_url(url)
        if domain and domain in self.domain_sources:
            return self.domain_sources[domain]
        return None
    
    def analyze_with_groq(self, title, content, url):
        """Analizar artículo usando Groq API"""
        if not self.groq_key:
            return None
        
        try:
            # Preparar el prompt
            text_to_analyze = f"Título: {title or ''}\nContenido: {(content or '')[:1000]}\nURL: {url or ''}"
            
            prompt = f"""Analiza el siguiente artículo de noticias y determina cuál es la fuente original (medio de comunicación) que lo publicó.

{text_to_analyze}

Instrucciones:
1. Identifica la fuente original del artículo basándote en el contenido, estilo, URL y cualquier mención explícita
2. Responde ÚNICAMENTE con el nombre de la fuente de noticias (ej: "Reuters", "BBC News", "El País", etc.)
3. Si no puedes determinar la fuente con certeza, responde "DESCONOCIDA"
4. Usa nombres estándar de medios reconocidos internacionalmente

Fuente detectada:"""

            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un experto en medios de comunicación que puede identificar fuentes de noticias con alta precisión."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 50
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                detected_source = result['choices'][0]['message']['content'].strip()
                
                # Limpiar la respuesta
                detected_source = detected_source.replace("Fuente detectada:", "").strip()
                detected_source = detected_source.replace("**", "").strip()
                
                # Validar que sea una fuente conocida
                if detected_source in self.known_sources:
                    return detected_source
                elif detected_source != "DESCONOCIDA":
                    # Buscar coincidencias parciales
                    for known_source in self.known_sources:
                        if detected_source.lower() in known_source.lower() or known_source.lower() in detected_source.lower():
                            return known_source
                
                return None
            else:
                logger.error(f"Error en Groq API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error en análisis con Groq: {e}")
            return None
    
    def analyze_with_openai(self, title, content, url):
        """Analizar artículo usando OpenAI API"""
        if not self.openai_key:
            return None
        
        try:
            import openai
            
            text_to_analyze = f"Título: {title or ''}\nContenido: {(content or '')[:1000]}\nURL: {url or ''}"
            
            prompt = f"""Analiza este artículo y determina la fuente original de noticias:

{text_to_analyze}

Responde solo con el nombre del medio (ej: Reuters, BBC News, El País). Si no estás seguro, responde "DESCONOCIDA"."""

            try:
                # Try new OpenAI client
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un experto en identificación de fuentes de noticias."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=50
                )
                detected_source = response.choices[0].message.content.strip()
            except ImportError:
                # Fallback to old interface
                openai.api_key = self.openai_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un experto en identificación de fuentes de noticias."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=50
                )
                detected_source = response.choices[0].message.content.strip()
            
            # Validar respuesta
            if detected_source in self.known_sources:
                return detected_source
            elif detected_source != "DESCONOCIDA":
                for known_source in self.known_sources:
                    if detected_source.lower() in known_source.lower() or known_source.lower() in detected_source.lower():
                        return known_source
            
            return None
            
        except Exception as e:
            logger.error(f"Error en análisis con OpenAI: {e}")
            return None
    
    def analyze_with_deepseek(self, title, content, url):
        """Analizar artículo usando DeepSeek API"""
        if not self.deepseek_key:
            return None
        
        try:
            text_to_analyze = f"Título: {title or ''}\nContenido: {(content or '')[:1000]}\nURL: {url or ''}"
            
            prompt = f"""Identifica la fuente original de este artículo de noticias:

{text_to_analyze}

Responde únicamente con el nombre del medio de comunicación. Si no puedes determinarlo, responde "DESCONOCIDA"."""

            headers = {
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Eres un experto en medios de comunicación."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 50
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                detected_source = result['choices'][0]['message']['content'].strip()
                
                # Validar respuesta
                if detected_source in self.known_sources:
                    return detected_source
                elif detected_source != "DESCONOCIDA":
                    for known_source in self.known_sources:
                        if detected_source.lower() in known_source.lower() or known_source.lower() in detected_source.lower():
                            return known_source
                
                return None
            else:
                logger.error(f"Error en DeepSeek API: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error en análisis con DeepSeek: {e}")
            return None
    
    def analyze_article(self, title, content, url):
        """Analizar artículo usando múltiples métodos"""
        
        # 1. Primero intentar con URL (más rápido y confiable)
        if url:
            source = self.detect_source_from_url(url)
            if source:
                return source, "URL"
        
        # 2. Intentar con Groq (más rápido)
        if self.groq_key:
            source = self.analyze_with_groq(title, content, url)
            if source:
                return source, "Groq"
        
        # 3. Intentar con OpenAI
        if self.openai_key:
            source = self.analyze_with_openai(title, content, url)
            if source:
                return source, "OpenAI"
        
        # 4. Intentar con DeepSeek
        if self.deepseek_key:
            source = self.analyze_with_deepseek(title, content, url)
            if source:
                return source, "DeepSeek"
        
        return None, "No detectado"

def update_rss_sources_with_ai(limit=None, dry_run=False):
    """Actualizar fuentes RSS usando IA"""
    
    # Conectar a la base de datos
    db_path = Path(__file__).parent / 'data' / 'geopolitical_intel.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    detector = AISourceDetector()
    
    try:
        # Verificar APIs disponibles
        available_apis = []
        if detector.groq_key:
            available_apis.append("Groq")
        if detector.openai_key:
            available_apis.append("OpenAI")
        if detector.deepseek_key:
            available_apis.append("DeepSeek")
        
        if not available_apis:
            print("❌ No hay APIs de IA configuradas. Verifica las claves en config.")
            return
        
        print(f"🤖 APIs disponibles: {', '.join(available_apis)}")
        
        # Obtener artículos con fuente "RSS Feed"
        query = """
            SELECT id, title, content, url, source 
            FROM articles 
            WHERE source = 'RSS Feed' OR source = 'RSS' OR source = 'Feed'
            ORDER BY created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        articles = cursor.fetchall()
        
        if not articles:
            print("✅ No se encontraron artículos con fuente 'RSS Feed' para procesar")
            return
        
        print(f"🔍 Encontrados {len(articles)} artículos con fuente RSS para procesar")
        
        updated_count = 0
        failed_count = 0
        method_stats = {}
        
        for i, (article_id, title, content, url, current_source) in enumerate(articles, 1):
            try:
                print(f"\n📰 Procesando artículo {i}/{len(articles)}: {(title or '')[:60]}...")
                
                # Analizar con IA
                detected_source, method = detector.analyze_article(title, content, url)
                
                # Estadísticas de métodos
                if method not in method_stats:
                    method_stats[method] = 0
                method_stats[method] += 1
                
                # Solo actualizar si se detectó una fuente válida
                if detected_source and detected_source != current_source:
                    print(f"   🎯 Fuente detectada: {detected_source} (método: {method})")
                    
                    if not dry_run:
                        # Actualizar en la base de datos
                        cursor.execute(
                            "UPDATE articles SET source = ? WHERE id = ?",
                            (detected_source, article_id)
                        )
                        updated_count += 1
                        print(f"   ✅ Actualizado: {current_source} → {detected_source}")
                    else:
                        print(f"   🔄 [DRY RUN] Cambiaría: {current_source} → {detected_source}")
                        updated_count += 1
                else:
                    print(f"   ⚠️  No se pudo detectar fuente específica (método: {method})")
                    failed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error procesando artículo {article_id}: {e}")
                failed_count += 1
                continue
        
        if not dry_run:
            # Confirmar cambios
            conn.commit()
            print(f"\n✅ Proceso completado:")
            print(f"   📊 Artículos actualizados: {updated_count}")
            print(f"   ❌ Artículos fallidos: {failed_count}")
        else:
            print(f"\n🔄 [DRY RUN] Resumen:")
            print(f"   📊 Artículos que se actualizarían: {updated_count}")
            print(f"   ❌ Artículos que fallarían: {failed_count}")
        
        # Estadísticas de métodos
        print(f"\n📈 Estadísticas de métodos de detección:")
        for method, count in method_stats.items():
            print(f"   {method}: {count} artículos")
        
        # Mostrar estadísticas de fuentes después del procesamiento
        print(f"\n📈 Estadísticas de fuentes actualizadas:")
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM articles 
            WHERE source IS NOT NULL 
            GROUP BY source 
            ORDER BY count DESC 
            LIMIT 15
        """)
        
        for source, count in cursor.fetchall():
            print(f"   {source}: {count} artículos")
            
    except Exception as e:
        logger.error(f"Error en update_rss_sources_with_ai: {e}")
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def show_api_status():
    """Mostrar estado de las APIs disponibles"""
    detector = AISourceDetector()
    
    print("🤖 Estado de APIs de IA:")
    print(f"   Groq: {'✅ Configurada' if detector.groq_key else '❌ No configurada'}")
    print(f"   OpenAI: {'✅ Configurada' if detector.openai_key else '❌ No configurada'}")
    print(f"   DeepSeek: {'✅ Configurada' if detector.deepseek_key else '❌ No configurada'}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Actualizar fuentes RSS usando IA")
    parser.add_argument("--limit", type=int, help="Número máximo de artículos a procesar")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar cambios sin aplicarlos")
    parser.add_argument("--status", action="store_true", help="Mostrar estado de APIs")
    
    args = parser.parse_args()
    
    if args.status:
        show_api_status()
    else:
        print("🚀 Iniciando actualización de fuentes RSS con IA...")
        update_rss_sources_with_ai(limit=args.limit, dry_run=args.dry_run)