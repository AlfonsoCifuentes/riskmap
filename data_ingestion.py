"""
Sistema de Ingesta de Datos para Análisis Geopolítico
====================================================
Este módulo maneja la recolección, procesamiento y almacenamiento de datos
de múltiples fuentes para el entrenamiento del modelo BERT.
"""

import sqlite3
import pandas as pd
import numpy as np
import requests
import feedparser
import json
import hashlib
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Web scraping
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Image processing
import cv2
from PIL import Image
import imagehash
import base64
import io

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArticleData:
    """Estructura de datos para artículos"""
    title: str
    content: str
    url: str
    source: str
    published_at: Optional[datetime]
    language: str
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    image_hash: Optional[str] = None
    extracted_text: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None

class GeopoliticalDataIngestion:
    """Sistema principal de ingesta de datos geopolíticos"""
    
    def __init__(self, db_path: str, trained_db_path: str = None):
        self.db_path = db_path
        self.trained_db_path = trained_db_path or db_path.replace('.db', '_trained_analysis.db')
        self.image_cache_dir = Path("data/image_cache")
        self.image_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar selenium
        self.setup_selenium()
        
        # Crear base de datos de entrenamiento
        self.setup_trained_database()
        
    def setup_selenium(self):
        """Configurar navegador para web scraping"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Selenium configurado correctamente")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo configurar Selenium: {e}")
            self.driver = None
    
    def setup_trained_database(self):
        """Crear la nueva base de datos para análisis entrenado"""
        conn = sqlite3.connect(self.trained_db_path)
        cursor = conn.cursor()
        
        # Tabla principal de artículos procesados
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trained_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_article_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            url TEXT UNIQUE,
            source TEXT,
            published_at DATETIME,
            language TEXT,
            
            -- Datos de imagen
            image_url TEXT,
            image_path TEXT,
            image_hash TEXT,
            image_description TEXT,
            
            -- Predicciones del modelo
            risk_level INTEGER,  -- 1-5 escala
            risk_score REAL,     -- 0-1 probabilidad
            topic TEXT,          -- Categoría del conflicto
            location TEXT,       -- Ubicación geográfica
            source_credibility REAL,  -- Confiabilidad de la fuente
            
            -- Factor de importancia
            importance_score REAL,
            recency_factor REAL,
            risk_factor REAL,
            
            -- Metadatos
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed_at DATETIME,
            model_version TEXT,
            confidence_score REAL,
            
            FOREIGN KEY (original_article_id) REFERENCES articles (id)
        )
        ''')
        
        # Tabla de etiquetas de entrenamiento
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            
            -- Etiquetas manuales para entrenamiento
            manual_risk_level INTEGER,  -- 1-5
            manual_topic TEXT,
            manual_location TEXT,
            manual_source_type TEXT,
            
            -- Información adicional
            labeled_by TEXT,
            labeled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            
            FOREIGN KEY (article_id) REFERENCES trained_articles (id)
        )
        ''')
        
        # Tabla de métricas de rendimiento
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_version TEXT,
            accuracy REAL,
            precision_risk REAL,
            recall_risk REAL,
            f1_score REAL,
            training_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            training_samples INTEGER,
            validation_samples INTEGER,
            notes TEXT
        )
        ''')
        
        # Tabla de fuentes RSS expandidas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rss_sources_expanded (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT UNIQUE,
            language TEXT,
            region TEXT,
            country TEXT,
            reliability_score REAL,  -- 0-1
            political_bias TEXT,     -- left, center, right
            topic_focus TEXT,        -- geopolitics, economics, etc.
            update_frequency INTEGER, -- minutos
            active BOOLEAN DEFAULT 1,
            last_checked DATETIME,
            error_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 1.0
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Base de datos de entrenamiento creada: {self.trained_db_path}")
    
    def get_existing_sources(self) -> List[Dict]:
        """Obtener fuentes RSS existentes de la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, url, language, region FROM sources WHERE active = 1")
        sources = [
            {
                'name': row[0],
                'url': row[1], 
                'language': row[2],
                'region': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return sources
    
    def add_premium_rss_sources(self):
        """Añadir fuentes RSS premium y especializadas"""
        premium_sources = [
            # Fuentes geopolíticas especializadas
            {
                'name': 'Foreign Affairs',
                'url': 'https://www.foreignaffairs.com/rss.xml',
                'language': 'en',
                'region': 'global',
                'country': 'US',
                'reliability_score': 0.95,
                'political_bias': 'center',
                'topic_focus': 'geopolitics'
            },
            {
                'name': 'International Crisis Group',
                'url': 'https://www.crisisgroup.org/rss.xml',
                'language': 'en', 
                'region': 'global',
                'country': 'International',
                'reliability_score': 0.98,
                'political_bias': 'center',
                'topic_focus': 'conflict_analysis'
            },
            {
                'name': 'Council on Foreign Relations',
                'url': 'https://www.cfr.org/rss-feeds',
                'language': 'en',
                'region': 'global', 
                'country': 'US',
                'reliability_score': 0.92,
                'political_bias': 'center',
                'topic_focus': 'international_relations'
            },
            {
                'name': 'Jane\'s Defence Weekly',
                'url': 'https://www.janes.com/feeds/defence-weekly',
                'language': 'en',
                'region': 'global',
                'country': 'UK',
                'reliability_score': 0.94,
                'political_bias': 'center',
                'topic_focus': 'defense_intelligence'
            },
            # Fuentes regionales importantes
            {
                'name': 'South China Morning Post',
                'url': 'https://www.scmp.com/rss',
                'language': 'en',
                'region': 'asia',
                'country': 'Hong Kong',
                'reliability_score': 0.88,
                'political_bias': 'center',
                'topic_focus': 'asia_geopolitics'
            },
            {
                'name': 'Al Jazeera English',
                'url': 'https://www.aljazeera.com/xml/rss/all.xml',
                'language': 'en',
                'region': 'middle_east',
                'country': 'Qatar',
                'reliability_score': 0.85,
                'political_bias': 'left',
                'topic_focus': 'middle_east_politics'
            },
            {
                'name': 'RT International',
                'url': 'https://www.rt.com/rss/',
                'language': 'en',
                'region': 'europe',
                'country': 'Russia',
                'reliability_score': 0.65,  # Menor por sesgo
                'political_bias': 'right',
                'topic_focus': 'russia_perspective'
            },
            {
                'name': 'Times of India',
                'url': 'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',
                'language': 'en',
                'region': 'asia',
                'country': 'India',
                'reliability_score': 0.82,
                'political_bias': 'center',
                'topic_focus': 'south_asia'
            },
            # Fuentes económicas con impacto geopolítico
            {
                'name': 'Financial Times',
                'url': 'https://www.ft.com/rss',
                'language': 'en',
                'region': 'global',
                'country': 'UK',
                'reliability_score': 0.93,
                'political_bias': 'center',
                'topic_focus': 'geopolitical_economics'
            },
            {
                'name': 'Nikkei Asia',
                'url': 'https://asia.nikkei.com/rss',
                'language': 'en',
                'region': 'asia',
                'country': 'Japan',
                'reliability_score': 0.90,
                'political_bias': 'center',
                'topic_focus': 'asia_economics'
            }
        ]
        
        conn = sqlite3.connect(self.trained_db_path)
        cursor = conn.cursor()
        
        for source in premium_sources:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO rss_sources_expanded 
                (name, url, language, region, country, reliability_score, 
                 political_bias, topic_focus, update_frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    source['name'], source['url'], source['language'],
                    source['region'], source['country'], source['reliability_score'],
                    source['political_bias'], source['topic_focus'], 30  # 30 minutos
                ))
                logger.info(f"✅ Fuente añadida: {source['name']}")
            except Exception as e:
                logger.error(f"❌ Error añadiendo fuente {source['name']}: {e}")
        
        conn.commit()
        conn.close()
    
    def fetch_rss_articles(self, source_url: str, source_name: str) -> List[ArticleData]:
        """Obtener artículos de una fuente RSS"""
        articles = []
        try:
            feed = feedparser.parse(source_url)
            
            for entry in feed.entries:
                # Extraer fecha de publicación
                published_at = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                
                # Extraer contenido
                content = ""
                if hasattr(entry, 'summary'):
                    content = entry.summary
                elif hasattr(entry, 'description'):
                    content = entry.description
                
                # Limpiar HTML
                content = BeautifulSoup(content, 'html.parser').get_text().strip()
                
                article = ArticleData(
                    title=entry.title,
                    content=content,
                    url=entry.link,
                    source=source_name,
                    published_at=published_at,
                    language='en'  # Asumir inglés por defecto
                )
                
                articles.append(article)
                
        except Exception as e:
            logger.error(f"❌ Error procesando RSS {source_name}: {e}")
        
        return articles
    
    def extract_article_content(self, url: str) -> Tuple[str, str, str]:
        """Extraer contenido completo, imagen y metadatos de un artículo"""
        full_content = ""
        image_url = ""
        image_description = ""
        
        try:
            # Método 1: Requests + BeautifulSoup
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer texto del artículo
            article_selectors = [
                'article', '.article-body', '.story-body', '.content',
                '.post-content', '.entry-content', '.article-content'
            ]
            
            for selector in article_selectors:
                article_element = soup.select_one(selector)
                if article_element:
                    # Remover elementos no deseados
                    for unwanted in article_element.find_all(['script', 'style', 'nav', 'footer']):
                        unwanted.decompose()
                    full_content = article_element.get_text().strip()
                    break
            
            # Extraer imagen principal
            img_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                '.hero-image img',
                '.featured-image img',
                'article img:first-of-type'
            ]
            
            for selector in img_selectors:
                img_element = soup.select_one(selector)
                if img_element:
                    if 'content' in img_element.attrs:
                        image_url = img_element['content']
                    elif 'src' in img_element.attrs:
                        image_url = img_element['src']
                    
                    # Convertir URL relativa a absoluta
                    if image_url and not image_url.startswith('http'):
                        image_url = urljoin(url, image_url)
                    
                    # Extraer descripción de la imagen
                    image_description = img_element.get('alt', '') or img_element.get('title', '')
                    break
            
            # Método 2: Selenium para contenido dinámico (fallback)
            if not full_content and self.driver:
                try:
                    self.driver.get(url)
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    full_content = self.driver.find_element(By.TAG_NAME, "body").text
                except Exception as e:
                    logger.warning(f"Selenium falló para {url}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo contenido de {url}: {e}")
        
        return full_content, image_url, image_description
    
    def download_and_process_image(self, image_url: str, article_url: str) -> Tuple[str, str, bytes]:
        """Descargar y procesar imagen del artículo"""
        if not image_url:
            return "", "", b""
        
        try:
            # Crear nombre de archivo único
            url_hash = hashlib.md5(article_url.encode()).hexdigest()[:8]
            image_ext = Path(urlparse(image_url).path).suffix or '.jpg'
            image_filename = f"{url_hash}_{int(time.time())}{image_ext}"
            image_path = self.image_cache_dir / image_filename
            
            # Descargar imagen
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Verificar que es una imagen válida
            image = Image.open(io.BytesIO(response.content))
            image_data = response.content
            
            # Calcular hash para detectar duplicados
            image_hash = str(imagehash.average_hash(image))
            
            # Guardar imagen
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"✅ Imagen descargada: {image_filename}")
            return str(image_path), image_hash, image_data
            
        except Exception as e:
            logger.error(f"❌ Error descargando imagen {image_url}: {e}")
            
            # Fallback: captura de pantalla con Selenium
            if self.driver:
                try:
                    return self.screenshot_article(article_url)
                except Exception as se:
                    logger.error(f"❌ Error con captura de pantalla: {se}")
            
            return "", "", b""
    
    def screenshot_article(self, url: str) -> Tuple[str, str, bytes]:
        """Tomar captura de pantalla de un artículo como fallback"""
        if not self.driver:
            return "", "", b""
        
        try:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            screenshot_filename = f"screenshot_{url_hash}_{int(time.time())}.png"
            screenshot_path = self.image_cache_dir / screenshot_filename
            
            self.driver.get(url)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Tomar captura de pantalla
            self.driver.save_screenshot(str(screenshot_path))
            
            # Leer y procesar la imagen
            with open(screenshot_path, 'rb') as f:
                image_data = f.read()
            
            image = Image.open(screenshot_path)
            image_hash = str(imagehash.average_hash(image))
            
            logger.info(f"✅ Captura de pantalla tomada: {screenshot_filename}")
            return str(screenshot_path), image_hash, image_data
            
        except Exception as e:
            logger.error(f"❌ Error en captura de pantalla para {url}: {e}")
            return "", "", b""
    
    def calculate_importance_score(self, risk_level: int, published_at: datetime) -> Dict[str, float]:
        """Calcular factor de importancia basado en riesgo y recencia"""
        if not published_at:
            published_at = datetime.now(timezone.utc)
        
        # Calcular antigüedad en horas
        now = datetime.now(timezone.utc)
        age_hours = (now - published_at).total_seconds() / 3600
        
        # Factor de recencia (decae exponencialmente)
        # Noticias de última hora (0-6h): factor 1.0
        # Noticias del día (6-24h): factor 0.8
        # Noticias de la semana (24-168h): factor 0.5
        # Noticias más antiguas: factor mínimo 0.1
        if age_hours <= 6:
            recency_factor = 1.0
        elif age_hours <= 24:
            recency_factor = 0.8
        elif age_hours <= 168:  # 1 semana
            recency_factor = 0.5 * (1 - (age_hours - 24) / (168 - 24)) + 0.1
        else:
            recency_factor = 0.1
        
        # Factor de riesgo (escala 1-5 normalizada)
        risk_factor = risk_level / 5.0
        
        # Fórmula de importancia: combina riesgo y recencia de forma no lineal
        # Riesgo alto + muy reciente = importancia muy alta
        # Riesgo bajo + antiguo = importancia muy baja
        importance_score = (risk_factor ** 1.5) * (recency_factor ** 0.8)
        
        # Bonus para riesgo muy alto y muy reciente
        if risk_level >= 4 and age_hours <= 6:
            importance_score *= 1.2
        
        return {
            'importance_score': min(importance_score, 1.0),
            'recency_factor': recency_factor,
            'risk_factor': risk_factor,
            'age_hours': age_hours
        }
    
    def store_article(self, article: ArticleData) -> int:
        """Almacenar artículo en la base de datos de entrenamiento"""
        conn = sqlite3.connect(self.trained_db_path)
        cursor = conn.cursor()
        
        try:
            # Verificar si el artículo ya existe
            cursor.execute("SELECT id FROM trained_articles WHERE url = ?", (article.url,))
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"📄 Artículo ya existe: {article.title[:50]}...")
                return existing[0]
            
            # Extraer contenido completo e imagen
            full_content, image_url, image_description = self.extract_article_content(article.url)
            if full_content:
                article.content = full_content
            
            # Procesar imagen
            image_path, image_hash, image_data = "", "", b""
            if image_url:
                image_path, image_hash, image_data = self.download_and_process_image(image_url, article.url)
            
            # Insertar artículo
            cursor.execute('''
            INSERT INTO trained_articles (
                title, content, url, source, published_at, language,
                image_url, image_path, image_hash, image_description,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.title, article.content, article.url, article.source,
                article.published_at, article.language,
                image_url, image_path, image_hash, image_description,
                datetime.now(timezone.utc)
            ))
            
            article_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"✅ Artículo almacenado: {article.title[:50]}... (ID: {article_id})")
            return article_id
            
        except Exception as e:
            logger.error(f"❌ Error almacenando artículo: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def run_ingestion(self, max_articles_per_source: int = 50):
        """Ejecutar proceso completo de ingesta de datos"""
        logger.info("🚀 Iniciando ingesta de datos geopolíticos...")
        
        # Añadir fuentes premium
        self.add_premium_rss_sources()
        
        # Obtener fuentes RSS
        all_sources = []
        
        # Fuentes existentes
        existing_sources = self.get_existing_sources()
        all_sources.extend(existing_sources)
        
        # Fuentes nuevas de la base de entrenamiento
        conn = sqlite3.connect(self.trained_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, url FROM rss_sources_expanded WHERE active = 1")
        new_sources = [{'name': row[0], 'url': row[1]} for row in cursor.fetchall()]
        conn.close()
        
        all_sources.extend(new_sources)
        
        total_articles = 0
        
        # Procesar cada fuente RSS
        for source in all_sources:
            logger.info(f"📡 Procesando fuente: {source['name']}")
            
            try:
                articles = self.fetch_rss_articles(source['url'], source['name'])
                
                # Limitar artículos por fuente
                articles = articles[:max_articles_per_source]
                
                # Procesar artículos en paralelo
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [
                        executor.submit(self.store_article, article)
                        for article in articles
                    ]
                    
                    for future in as_completed(futures):
                        try:
                            article_id = future.result()
                            if article_id > 0:
                                total_articles += 1
                        except Exception as e:
                            logger.error(f"❌ Error procesando artículo: {e}")
                
                # Pausa entre fuentes para evitar sobrecarga
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error procesando fuente {source['name']}: {e}")
        
        logger.info(f"✅ Ingesta completada. Total de artículos nuevos: {total_articles}")
        
        # Cerrar driver si existe
        if self.driver:
            self.driver.quit()
    
    def create_training_dataset(self, sample_size: int = 500) -> pd.DataFrame:
        """Crear conjunto de datos para etiquetado manual"""
        conn = sqlite3.connect(self.trained_db_path)
        
        # Obtener muestra estratificada
        query = '''
        SELECT id, title, content, source, published_at, url
        FROM trained_articles 
        WHERE length(content) > 200  -- Artículos con contenido suficiente
        ORDER BY RANDOM()
        LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(sample_size,))
        conn.close()
        
        # Añadir columnas para etiquetado manual
        df['manual_risk_level'] = None
        df['manual_topic'] = None  
        df['manual_location'] = None
        df['manual_source_type'] = None
        df['notes'] = None
        
        # Guardar como CSV para etiquetado
        output_path = f"training_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_path, index=False)
        
        logger.info(f"✅ Dataset de entrenamiento creado: {output_path}")
        logger.info("📋 Para etiquetar manualmente:")
        logger.info("  - manual_risk_level: 1 (muy bajo) a 5 (muy alto)")
        logger.info("  - manual_topic: 'armed_conflict', 'diplomatic_tension', 'economic_sanctions', etc.")
        logger.info("  - manual_location: país o región del conflicto")
        logger.info("  - manual_source_type: 'mainstream_media', 'government', 'think_tank', etc.")
        
        return df

def main():
    """Función principal para ejecutar la ingesta"""
    # Rutas de las bases de datos
    original_db = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    trained_db = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\trained_analysis.db"
    
    # Crear sistema de ingesta
    ingestion_system = GeopoliticalDataIngestion(
        db_path=original_db,
        trained_db_path=trained_db
    )
    
    # Ejecutar ingesta de datos
    ingestion_system.run_ingestion(max_articles_per_source=30)
    
    # Crear dataset de entrenamiento para etiquetado manual
    training_df = ingestion_system.create_training_dataset(sample_size=1000)
    
    print(f"\n✅ Sistema de ingesta completado!")
    print(f"📊 Dataset de entrenamiento: {training_df.shape[0]} artículos")
    print(f"🗄️ Base de datos de entrenamiento: {trained_db}")

if __name__ == "__main__":
    main()
