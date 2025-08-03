#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Inteligente de Enriquecimiento de Datos
Integra BERT, Computer Vision, Groq y técnicas avanzadas de la conversación ChatGPT
para mantener la base de datos rica, limpia y completa automáticamente
"""

import os
import sqlite3
import logging
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Configurar logging
logger = logging.getLogger(__name__)

# Importaciones de IA - con fallbacks robustos
try:
    from transformers import (
        AutoTokenizer, AutoModelForSequenceClassification, 
        AutoModelForTokenClassification, pipeline
    )
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
    logger.info("✅ Transformers (BERT/NLP) available")
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    logger.warning(f"⚠️ Transformers not available: {e}")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("⚠️ PyTorch not available")

try:
    from ultralytics import YOLO
    import cv2
    import numpy as np
    from PIL import Image
    COMPUTER_VISION_AVAILABLE = True
    logger.info("✅ Computer Vision (YOLO/OpenCV) available")
except ImportError as e:
    COMPUTER_VISION_AVAILABLE = False
    logger.warning(f"⚠️ Computer Vision not available: {e}")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
    logger.info("✅ Groq API available")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("⚠️ Groq API not available")

try:
    import sqlite_vss
    VECTOR_SEARCH_AVAILABLE = True
    logger.info("✅ Vector Search (sqlite-vss) available")
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    logger.warning("⚠️ Vector Search not available")

@dataclass
class EnrichmentResult:
    """Resultado del enriquecimiento de un artículo"""
    article_id: int
    fields_updated: List[str]
    success: bool
    error: Optional[str] = None
    processing_time: float = 0.0
    confidence_scores: Dict[str, float] = None

@dataclass
class EnrichmentConfig:
    """Configuración del sistema de enriquecimiento"""
    bert_model_name: str = "dslim/bert-base-NER"
    sentiment_model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    embedding_model_name: str = "thenlper/gte-small"
    yolo_model_path: str = "yolov8n.pt"
    groq_model: str = "llama-3.1-8b-instant"
    
    # Configuración de procesamiento
    batch_size: int = 10
    max_workers: int = 4
    confidence_threshold: float = 0.7
    vector_dimension: int = 384
    
    # Intervalos de procesamiento
    auto_enrich_interval_hours: int = 6
    priority_processing_interval_hours: int = 2

class IntelligentDataEnrichment:
    """
    Sistema principal de enriquecimiento inteligente de datos
    Combina BERT, Computer Vision, Groq y búsqueda vectorial
    """
    
    def __init__(self, db_path: str = None, config: EnrichmentConfig = None):
        self.db_path = db_path or self._get_database_path()
        self.config = config or EnrichmentConfig()
        
        # Modelos de IA
        self.models = {}
        self.groq_client = None
        
        # Estado del sistema
        self.running = False
        self.processing_stats = {
            'articles_processed': 0,
            'fields_enriched': 0,
            'errors': 0,
            'last_run': None
        }
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.stop_event = threading.Event()
        
        # Inicializar sistema
        self._initialize_models()
        self._ensure_enrichment_tables()
        
        logger.info(f"IntelligentDataEnrichment initialized with DB: {self.db_path}")

    def _get_database_path(self) -> str:
        """Obtener ruta de la base de datos"""
        try:
            from src.utils.config import get_database_path
            return get_database_path()
        except ImportError:
            db_path = os.getenv('DATABASE_PATH', './data/geopolitical_intel.db')
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            return db_path

    def _initialize_models(self):
        """Inicializar todos los modelos de IA disponibles"""
        logger.info("🤖 Initializing AI models...")
        
        # BERT para análisis de entidades y sentimientos
        if TRANSFORMERS_AVAILABLE:
            try:
                # Modelo NER para entidades
                self.models['ner'] = pipeline(
                    "ner",
                    model=self.config.bert_model_name,
                    tokenizer=self.config.bert_model_name,
                    aggregation_strategy="simple",
                    device=0 if TORCH_AVAILABLE and torch.cuda.is_available() else -1
                )
                logger.info("✅ NER model loaded")
                
                # Modelo de sentimientos
                self.models['sentiment'] = pipeline(
                    "sentiment-analysis",
                    model=self.config.sentiment_model_name,
                    device=0 if TORCH_AVAILABLE and torch.cuda.is_available() else -1
                )
                logger.info("✅ Sentiment model loaded")
                
                # Modelo de embeddings para búsqueda vectorial
                if VECTOR_SEARCH_AVAILABLE:
                    self.models['embeddings'] = SentenceTransformer(self.config.embedding_model_name)
                    logger.info("✅ Embedding model loaded")
                    
            except Exception as e:
                logger.error(f"Error loading BERT models: {e}")
        
        # YOLO para análisis de imágenes
        if COMPUTER_VISION_AVAILABLE:
            try:
                self.models['yolo'] = YOLO(self.config.yolo_model_path)
                logger.info("✅ YOLO model loaded")
            except Exception as e:
                logger.error(f"Error loading YOLO model: {e}")
        
        # Groq para análisis avanzado
        if GROQ_AVAILABLE:
            try:
                groq_api_key = os.getenv('GROQ_API_KEY')
                if groq_api_key:
                    self.groq_client = Groq(api_key=groq_api_key)
                    logger.info("✅ Groq client initialized")
                else:
                    logger.warning("⚠️ GROQ_API_KEY not found")
            except Exception as e:
                logger.error(f"Error initializing Groq: {e}")

    def _ensure_enrichment_tables(self):
        """Crear tablas necesarias para el enriquecimiento"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de vectores para búsqueda semántica (siguiendo ChatGPT)
                if VECTOR_SEARCH_AVAILABLE:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS article_embeddings (
                            article_id INTEGER PRIMARY KEY,
                            title_embedding BLOB,
                            content_embedding BLOB,
                            combined_embedding BLOB,
                            embedding_model TEXT,
                            created_at TEXT DEFAULT (datetime('now')),
                            updated_at TEXT DEFAULT (datetime('now')),
                            FOREIGN KEY (article_id) REFERENCES articles (id)
                        )
                    """)
                
                # Tabla de procesamiento de enriquecimiento
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS enrichment_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id INTEGER,
                        processing_type TEXT, -- 'auto', 'manual', 'trigger'
                        fields_processed TEXT, -- JSON array
                        success INTEGER,
                        error_message TEXT,
                        processing_time REAL,
                        confidence_scores TEXT, -- JSON
                        created_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
                # Tabla de duplicados detectados (ChatGPT approach)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS article_duplicates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id_1 INTEGER,
                        article_id_2 INTEGER,
                        similarity_score REAL,
                        duplicate_type TEXT, -- 'exact', 'semantic', 'fuzzy'
                        status TEXT DEFAULT 'pending', -- 'pending', 'merged', 'ignored'
                        detected_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (article_id_1) REFERENCES articles (id),
                        FOREIGN KEY (article_id_2) REFERENCES articles (id)
                    )
                """)
                
                # Extender tabla articles si es necesario
                cursor.execute("PRAGMA table_info(articles)")
                existing_columns = [row[1] for row in cursor.fetchall()]
                
                new_columns = [
                    ("enrichment_status", "TEXT DEFAULT 'pending'"),
                    ("enrichment_version", "INTEGER DEFAULT 1"),
                    ("last_enriched", "TEXT"),
                    ("enrichment_confidence", "REAL"),
                    ("semantic_hash", "TEXT"),  # Para deduplicación
                    ("auto_generated_summary", "TEXT"),
                    ("extracted_entities_json", "TEXT"),
                    ("conflict_probability", "REAL"),
                    ("geopolitical_relevance", "REAL")
                ]
                
                for col_name, col_def in new_columns:
                    if col_name not in existing_columns:
                        cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_def}")
                        logger.info(f"Added column: {col_name}")
                
                # Índices para optimización
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrichment_status ON articles (enrichment_status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_enriched ON articles (last_enriched)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_semantic_hash ON articles (semantic_hash)")
                
                conn.commit()
                logger.info("✅ Enrichment tables ensured")
                
        except Exception as e:
            logger.error(f"Error creating enrichment tables: {e}")

    def _generate_semantic_hash(self, title: str, content: str) -> str:
        """Generar hash semántico para detección de duplicados"""
        # Normalizar texto
        normalized = f"{title} {content}".lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Crear hash MD5
        return hashlib.md5(normalized.encode()).hexdigest()

    def extract_entities_with_bert(self, text: str) -> Dict[str, List[str]]:
        """Extraer entidades usando BERT NER"""
        if not self.models.get('ner'):
            return {}
            
        try:
            entities = self.models['ner'](text)
            
            # Agrupar por tipo de entidad
            grouped_entities = {}
            for entity in entities:
                entity_type = entity['entity_group']
                entity_text = entity['word']
                
                if entity_type not in grouped_entities:
                    grouped_entities[entity_type] = []
                
                if entity_text not in grouped_entities[entity_type]:
                    grouped_entities[entity_type].append(entity_text)
            
            return grouped_entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}

    def analyze_sentiment_with_bert(self, text: str) -> Tuple[float, str]:
        """Analizar sentimiento usando BERT"""
        if not self.models.get('sentiment'):
            return 0.0, 'neutral'
            
        try:
            result = self.models['sentiment'](text)[0]
            
            # Mapear a scores numéricos
            label_mapping = {
                'POSITIVE': 1.0,
                'NEGATIVE': -1.0,
                'NEUTRAL': 0.0
            }
            
            score = label_mapping.get(result['label'], 0.0) * result['score']
            sentiment_label = result['label'].lower()
            
            return score, sentiment_label
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.0, 'neutral'

    def analyze_image_with_yolo(self, image_path: str) -> Dict[str, Any]:
        """Analizar imagen usando YOLO"""
        if not self.models.get('yolo') or not Path(image_path).exists():
            return {}
            
        try:
            results = self.models['yolo'](image_path)
            
            detected_objects = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        detected_objects.append({
                            'class': result.names[int(box.cls)],
                            'confidence': float(box.conf),
                            'bbox': box.xyxy[0].tolist()
                        })
            
            # Análisis adicional de la imagen
            image = cv2.imread(image_path)
            if image is not None:
                height, width, channels = image.shape
                
                # Detectar personas/vehículos/armas para análisis de conflicto
                conflict_indicators = []
                for obj in detected_objects:
                    if obj['class'] in ['person', 'car', 'truck', 'military vehicle', 'weapon']:
                        conflict_indicators.append(obj['class'])
                
                return {
                    'detected_objects': detected_objects,
                    'conflict_indicators': conflict_indicators,
                    'image_dimensions': [width, height],
                    'has_people': 'person' in [obj['class'] for obj in detected_objects],
                    'vehicles_count': len([obj for obj in detected_objects if 'car' in obj['class'] or 'truck' in obj['class']]),
                    'analysis_confidence': sum([obj['confidence'] for obj in detected_objects]) / len(detected_objects) if detected_objects else 0
                }
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            
        return {}

    def enhance_with_groq(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquecer artículo usando Groq con fallback inteligente a Ollama"""
        try:
            # Intentar con servicio unificado (maneja fallback automáticamente)
            from src.ai.unified_ai_service import unified_ai_service
            
            title = article_data.get('title', '')
            content = article_data.get('content', '')
            
            # Usar el servicio unificado para análisis geopolítico
            response = asyncio.run(unified_ai_service.analyze_geopolitical_content(
                content=f"TÍTULO: {title}\nCONTENIDO: {content}",
                prefer_local=True  # Priorizar Ollama para evitar rate limits
            ))
            
            if response.success and response.metadata:
                # Convertir respuesta del servicio unificado a formato esperado
                metadata = response.metadata
                return {
                    "published_date": metadata.get('published_date'),
                    "country": metadata.get('country', '').split(',')[0] if metadata.get('country') else '',
                    "region": metadata.get('region', ''),
                    "conflict_type": metadata.get('conflict_type'),
                    "summary": metadata.get('summary', ''),
                    "key_persons": metadata.get('key_persons', []),
                    "key_locations": metadata.get('key_locations', []),
                    "geopolitical_relevance": metadata.get('geopolitical_relevance', 0.5),
                    "risk_assessment": metadata.get('risk_level', 'medium')
                }
            
            # Fallback manual a Groq directo si el servicio unificado falla
            if not self.groq_client:
                logger.warning("🔄 Servicio unificado falló y Groq no disponible")
                return self._fallback_to_ollama_direct(title, content)
                
            return self._enhance_with_groq_direct(title, content)
            
        except Exception as e:
            logger.error(f"Error enhancing with AI: {e}")
            
            # Fallback directo a Ollama en caso de cualquier error
            try:
                return self._fallback_to_ollama_direct(
                    article_data.get('title', ''), 
                    article_data.get('content', '')
                )
            except Exception as fallback_error:
                logger.error(f"Error en fallback Ollama: {fallback_error}")
                return {}
                
    def _enhance_with_groq_direct(self, title: str, content: str) -> Dict[str, Any]:
        """Método directo con Groq (preservado para compatibilidad)"""
        try:
            # Prompt estructurado para extraer información faltante
            prompt = f"""
Analiza el siguiente artículo de noticias y extrae la información solicitada en formato JSON:

TÍTULO: {title}
CONTENIDO: {content[:2000]}...

Extrae y devuelve SOLO un JSON válido con esta estructura:
{{
    "published_date": "YYYY-MM-DD o null si no se puede determinar",
    "country": "País principal mencionado en la noticia",
    "region": "Región geográfica o continente",
    "conflict_type": "tipo de conflicto (war, terrorism, civil_unrest, diplomatic, economic, etc.) o null",
    "summary": "Resumen ejecutivo en 2-3 líneas",
    "key_persons": ["Lista de personas importantes mencionadas"],
    "key_locations": ["Lista de lugares específicos mencionados"],
    "geopolitical_relevance": 0.8,
    "risk_assessment": "high/medium/low"
}}

JSON:
"""
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres un analista geopolítico experto. Responde SOLO con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                model=self.config.groq_model,
                max_tokens=1000,
                temperature=0.1
            )
            
            # Extraer y parsear JSON
            response_text = response.choices[0].message.content.strip()
            
            # Limpiar respuesta para extraer solo el JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
                
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                logger.warning(f"🔄 Rate limit detectado, usando Ollama directo...")
                return self._fallback_to_ollama_direct(title, content)
            else:
                raise e
                
        return {}
        
    def _fallback_to_ollama_direct(self, title: str, content: str) -> Dict[str, Any]:
        """Fallback directo a Ollama para enriquecimiento"""
        try:
            from src.ai.ollama_service import ollama_service, OllamaModel
            
            if not ollama_service.check_ollama_status():
                logger.warning("⚠️ Ollama no disponible para fallback")
                return {}
                
            # Usar DeepSeek para análisis profundo
            analysis = ollama_service.analyze_geopolitical_content(
                content=f"TÍTULO: {title}\nCONTENIDO: {content}",
                model=OllamaModel.DEEPSEEK_R1_7B
            )
            
            if analysis:
                logger.info("✅ Análisis completado con Ollama DeepSeek")
                return {
                    "published_date": analysis.get('published_date'),
                    "country": analysis.get('country', ''),
                    "region": analysis.get('region', ''),
                    "conflict_type": analysis.get('conflict_type'),
                    "summary": analysis.get('summary', ''),
                    "key_persons": analysis.get('key_persons', []),
                    "key_locations": analysis.get('key_locations', []),
                    "geopolitical_relevance": analysis.get('geopolitical_relevance', 0.5),
                    "risk_assessment": analysis.get('risk_level', 'medium')
                }
                
        except Exception as e:
            logger.error(f"Error en fallback Ollama directo: {e}")
            
        return {}

    def generate_embedding(self, text: str) -> Optional[bytes]:
        """Generar embedding vectorial para búsqueda semántica"""
        if not self.models.get('embeddings'):
            return None
            
        try:
            embedding = self.models['embeddings'].encode(text)
            return embedding.tobytes()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def enrich_single_article(self, article_id: int) -> EnrichmentResult:
        """Enriquecer un artículo individual con todas las técnicas disponibles"""
        start_time = time.time()
        fields_updated = []
        confidence_scores = {}
        
        try:
            # Obtener datos del artículo
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, content, url, source, published_at, country, region, 
                           conflict_type, sentiment_score, summary, image_url, key_persons, 
                           key_locations, risk_level, enrichment_status
                    FROM articles WHERE id = ?
                """, (article_id,))
                
                row = cursor.fetchone()
                if not row:
                    return EnrichmentResult(article_id, [], False, "Article not found")
                
                columns = [desc[0] for desc in cursor.description]
                article_data = dict(zip(columns, row))
            
            # Preparar updates
            updates = {}
            
            # 1. Análisis NLP con BERT
            if article_data.get('title') and article_data.get('content'):
                full_text = f"{article_data['title']} {article_data['content']}"
                
                # Extraer entidades
                entities = self.extract_entities_with_bert(full_text)
                if entities:
                    updates['extracted_entities_json'] = json.dumps(entities)
                    
                    # Actualizar campos específicos si están vacíos
                    if not article_data.get('key_persons') and 'PER' in entities:
                        updates['key_persons'] = ', '.join(entities['PER'][:5])
                        fields_updated.append('key_persons')
                    
                    if not article_data.get('key_locations') and 'LOC' in entities:
                        updates['key_locations'] = ', '.join(entities['LOC'][:5])
                        fields_updated.append('key_locations')
                    
                    confidence_scores['entities'] = 0.85
                
                # Análisis de sentimiento
                if not article_data.get('sentiment_score'):
                    sentiment_score, sentiment_label = self.analyze_sentiment_with_bert(full_text)
                    updates['sentiment_score'] = sentiment_score
                    updates['sentiment_label'] = sentiment_label
                    fields_updated.append('sentiment_score')
                    confidence_scores['sentiment'] = 0.9
                
                # Generar hash semántico para deduplicación
                semantic_hash = self._generate_semantic_hash(article_data['title'], article_data['content'])
                updates['semantic_hash'] = semantic_hash
                
                # Generar embeddings para búsqueda vectorial
                if VECTOR_SEARCH_AVAILABLE:
                    title_embedding = self.generate_embedding(article_data['title'])
                    content_embedding = self.generate_embedding(article_data['content'][:500])
                    combined_embedding = self.generate_embedding(full_text[:1000])
                    
                    if title_embedding and content_embedding:
                        # Guardar embeddings en tabla separada
                        with sqlite3.connect(self.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT OR REPLACE INTO article_embeddings 
                                (article_id, title_embedding, content_embedding, combined_embedding, embedding_model, updated_at)
                                VALUES (?, ?, ?, ?, ?, datetime('now'))
                            """, (article_id, title_embedding, content_embedding, combined_embedding, self.config.embedding_model_name))
                            conn.commit()
                        
                        fields_updated.append('embeddings')
                        confidence_scores['embeddings'] = 0.95
            
            # 2. Análisis de imagen con YOLO
            if article_data.get('image_url') and Path(article_data['image_url']).exists():
                image_analysis = self.analyze_image_with_yolo(article_data['image_url'])
                if image_analysis:
                    updates['detected_objects'] = json.dumps(image_analysis.get('detected_objects', []))
                    updates['has_faces'] = image_analysis.get('has_people', False)
                    updates['visual_analysis_json'] = json.dumps(image_analysis)
                    updates['visual_analysis_timestamp'] = datetime.now().isoformat()
                    
                    # Calcular probabilidad de conflicto basada en objetos detectados
                    conflict_prob = len(image_analysis.get('conflict_indicators', [])) * 0.2
                    updates['conflict_probability'] = min(conflict_prob, 1.0)
                    
                    fields_updated.extend(['detected_objects', 'visual_analysis', 'conflict_probability'])
                    confidence_scores['computer_vision'] = image_analysis.get('analysis_confidence', 0.8)
            
            # 3. Enriquecimiento con Groq para campos complejos
            groq_enhancements = self.enhance_with_groq(article_data)
            if groq_enhancements:
                # Actualizar solo campos faltantes
                if not article_data.get('published_at') and groq_enhancements.get('published_date'):
                    updates['published_at'] = groq_enhancements['published_date']
                    fields_updated.append('published_at')
                
                if not article_data.get('country') and groq_enhancements.get('country'):
                    updates['country'] = groq_enhancements['country']
                    fields_updated.append('country')
                
                if not article_data.get('region') and groq_enhancements.get('region'):
                    updates['region'] = groq_enhancements['region']
                    fields_updated.append('region')
                
                if not article_data.get('conflict_type') and groq_enhancements.get('conflict_type'):
                    updates['conflict_type'] = groq_enhancements['conflict_type']
                    fields_updated.append('conflict_type')
                
                if not article_data.get('summary') and groq_enhancements.get('summary'):
                    updates['auto_generated_summary'] = groq_enhancements['summary']
                    fields_updated.append('summary')
                
                if groq_enhancements.get('geopolitical_relevance'):
                    updates['geopolitical_relevance'] = groq_enhancements['geopolitical_relevance']
                    fields_updated.append('geopolitical_relevance')
                
                if groq_enhancements.get('risk_assessment'):
                    updates['risk_level'] = groq_enhancements['risk_assessment']
                    fields_updated.append('risk_level')
                
                confidence_scores['groq_analysis'] = 0.85
            
            # Actualizar metadatos de enriquecimiento
            if updates:
                avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.8
                updates['enrichment_status'] = 'completed'
                updates['last_enriched'] = datetime.now().isoformat()
                updates['enrichment_confidence'] = avg_confidence
                updates['enrichment_version'] = (article_data.get('enrichment_version') or 0) + 1
                
                # Aplicar updates a la base de datos
                if updates:
                    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
                    values = list(updates.values()) + [article_id]
                    
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(f"UPDATE articles SET {set_clause} WHERE id = ?", values)
                        conn.commit()
            
            processing_time = time.time() - start_time
            
            # Registrar en log
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO enrichment_log 
                    (article_id, processing_type, fields_processed, success, processing_time, confidence_scores)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    article_id, 'auto', json.dumps(fields_updated), 
                    1, processing_time, json.dumps(confidence_scores)
                ))
                conn.commit()
            
            logger.info(f"✅ Enriched article {article_id}: {len(fields_updated)} fields updated in {processing_time:.2f}s")
            
            return EnrichmentResult(
                article_id=article_id,
                fields_updated=fields_updated,
                success=True,
                processing_time=processing_time,
                confidence_scores=confidence_scores
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            # Registrar error
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO enrichment_log 
                    (article_id, processing_type, fields_processed, success, error_message, processing_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (article_id, 'auto', json.dumps([]), 0, error_msg, processing_time))
                conn.commit()
            
            logger.error(f"❌ Error enriching article {article_id}: {error_msg}")
            
            return EnrichmentResult(
                article_id=article_id,
                fields_updated=[],
                success=False,
                error=error_msg,
                processing_time=processing_time
            )

    def detect_and_merge_duplicates(self) -> Dict[str, int]:
        """Detectar y marcar artículos duplicados usando hashes semánticos y embeddings"""
        if not VECTOR_SEARCH_AVAILABLE:
            logger.warning("Vector search not available for duplicate detection")
            return {'detected': 0, 'merged': 0}
        
        try:
            duplicates_detected = 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Detectar duplicados exactos por hash semántico
                cursor.execute("""
                    SELECT semantic_hash, GROUP_CONCAT(id) as article_ids, COUNT(*) as count
                    FROM articles 
                    WHERE semantic_hash IS NOT NULL
                    GROUP BY semantic_hash
                    HAVING COUNT(*) > 1
                """)
                
                hash_duplicates = cursor.fetchall()
                
                for semantic_hash, article_ids_str, count in hash_duplicates:
                    article_ids = [int(x) for x in article_ids_str.split(',')]
                    
                    # Marcar como duplicados (mantener el más reciente)
                    for i in range(len(article_ids) - 1):
                        cursor.execute("""
                            INSERT OR IGNORE INTO article_duplicates 
                            (article_id_1, article_id_2, similarity_score, duplicate_type)
                            VALUES (?, ?, ?, ?)
                        """, (article_ids[0], article_ids[i+1], 1.0, 'exact'))
                        duplicates_detected += 1
                
                conn.commit()
                
            logger.info(f"✅ Duplicate detection completed: {duplicates_detected} duplicates found")
            return {'detected': duplicates_detected, 'merged': 0}
            
        except Exception as e:
            logger.error(f"Error detecting duplicates: {e}")
            return {'detected': 0, 'merged': 0}

    def enrich_batch_articles(self, article_ids: List[int] = None, limit: int = None) -> Dict[str, Any]:
        """Enriquecer un lote de artículos"""
        start_time = time.time()
        
        if not article_ids:
            # Obtener artículos que necesitan enriquecimiento
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM articles 
                    WHERE enrichment_status IS NULL OR enrichment_status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit or self.config.batch_size,))
                
                article_ids = [row[0] for row in cursor.fetchall()]
        
        if not article_ids:
            logger.info("No articles need enrichment")
            return {'processed': 0, 'success': 0, 'errors': 0}
        
        logger.info(f"🚀 Starting batch enrichment of {len(article_ids)} articles")
        
        results = []
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_id = {
                executor.submit(self.enrich_single_article, aid): aid 
                for aid in article_ids
            }
            
            for future in future_to_id:
                try:
                    result = future.result(timeout=300)  # 5 min timeout
                    results.append(result)
                except Exception as e:
                    article_id = future_to_id[future]
                    logger.error(f"Timeout/error processing article {article_id}: {e}")
                    results.append(EnrichmentResult(article_id, [], False, str(e)))
        
        # Estadísticas
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        error_count = len(results) - success_count
        total_fields = sum(len(r.fields_updated) for r in results)
        
        # Actualizar stats del sistema
        self.processing_stats['articles_processed'] += len(results)
        self.processing_stats['fields_enriched'] += total_fields
        self.processing_stats['errors'] += error_count
        self.processing_stats['last_run'] = datetime.now().isoformat()
        
        logger.info(f"✅ Batch enrichment completed: {success_count}/{len(results)} success, {total_fields} fields enriched in {total_time:.2f}s")
        
        return {
            'processed': len(results),
            'success': success_count,
            'errors': error_count,
            'fields_enriched': total_fields,
            'processing_time': total_time,
            'average_time_per_article': total_time / len(results) if results else 0
        }

    def setup_automatic_enrichment_triggers(self):
        """Configurar triggers de base de datos para enriquecimiento automático"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Trigger para marcar nuevos artículos para enriquecimiento
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS auto_enrich_new_articles
                    AFTER INSERT ON articles
                    BEGIN
                        UPDATE articles 
                        SET enrichment_status = 'pending',
                            semantic_hash = NULL
                        WHERE id = NEW.id;
                    END;
                """)
                
                # Trigger para re-enriquecer cuando se actualiza contenido
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS auto_enrich_updated_articles
                    AFTER UPDATE OF title, content ON articles
                    WHEN OLD.title != NEW.title OR OLD.content != NEW.content
                    BEGIN
                        UPDATE articles 
                        SET enrichment_status = 'pending',
                            semantic_hash = NULL,
                            last_enriched = NULL
                        WHERE id = NEW.id;
                    END;
                """)
                
                conn.commit()
                logger.info("✅ Automatic enrichment triggers configured")
                
        except Exception as e:
            logger.error(f"Error setting up triggers: {e}")

    def start_automatic_enrichment(self):
        """Iniciar procesamiento automático continuo"""
        if self.running:
            logger.warning("Automatic enrichment already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        # Configurar triggers
        self.setup_automatic_enrichment_triggers()
        
        def enrichment_loop():
            """Loop principal de enriquecimiento automático"""
            while not self.stop_event.is_set():
                try:
                    # Procesar artículos pendientes
                    stats = self.enrich_batch_articles()
                    
                    if stats['processed'] > 0:
                        logger.info(f"Automatic enrichment cycle: {stats}")
                    
                    # Ejecutar detección de duplicados periódicamente
                    if self.processing_stats['articles_processed'] % 100 == 0:
                        duplicate_stats = self.detect_and_merge_duplicates()
                        logger.info(f"Duplicate detection: {duplicate_stats}")
                    
                    # Esperar antes del siguiente ciclo
                    if self.stop_event.wait(timeout=self.config.auto_enrich_interval_hours * 3600):
                        break
                        
                except Exception as e:
                    logger.error(f"Error in enrichment loop: {e}")
                    self.stop_event.wait(300)  # Esperar 5 min antes de reintentar
        
        # Iniciar en thread separado
        thread = threading.Thread(target=enrichment_loop, daemon=True, name="EnrichmentLoop")
        thread.start()
        
        logger.info("🚀 Automatic enrichment started")

    def stop_automatic_enrichment(self):
        """Detener procesamiento automático"""
        if not self.running:
            return
        
        self.running = False
        self.stop_event.set()
        logger.info("🛑 Automatic enrichment stopped")

    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de enriquecimiento"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas generales
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_articles = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM articles WHERE enrichment_status = 'completed'")
                enriched_articles = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM articles WHERE enrichment_status = 'pending'")
                pending_articles = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM article_duplicates WHERE status = 'pending'")
                pending_duplicates = cursor.fetchone()[0]
                
                # Campos completados
                field_stats = {}
                for field in ['published_at', 'country', 'region', 'conflict_type', 'sentiment_score', 'summary']:
                    cursor.execute(f"SELECT COUNT(*) FROM articles WHERE {field} IS NOT NULL AND {field} != ''")
                    field_stats[field] = cursor.fetchone()[0]
                
                return {
                    'total_articles': total_articles,
                    'enriched_articles': enriched_articles,
                    'pending_articles': pending_articles,
                    'completion_rate': (enriched_articles / total_articles * 100) if total_articles > 0 else 0,
                    'pending_duplicates': pending_duplicates,
                    'field_completion': field_stats,
                    'processing_stats': self.processing_stats,
                    'models_loaded': list(self.models.keys()),
                    'running': self.running,
                    'last_update': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting enrichment statistics: {e}")
            return {'error': str(e)}

# Función de conveniencia para integración con app_BUENA.py
def create_enrichment_system(db_path: str = None, config: EnrichmentConfig = None) -> IntelligentDataEnrichment:
    """Factory function para crear el sistema de enriquecimiento"""
    return IntelligentDataEnrichment(db_path=db_path, config=config)

if __name__ == "__main__":
    # Ejemplo de uso directo
    enrichment = IntelligentDataEnrichment()
    
    try:
        # Configurar triggers automáticos
        enrichment.setup_automatic_enrichment_triggers()
        
        # Ejecutar enriquecimiento en lote
        stats = enrichment.enrich_batch_articles(limit=50)
        print(f"Batch enrichment stats: {stats}")
        
        # Detectar duplicados
        duplicate_stats = enrichment.detect_and_merge_duplicates()
        print(f"Duplicate detection: {duplicate_stats}")
        
        # Mostrar estadísticas
        enrichment_stats = enrichment.get_enrichment_statistics()
        print(f"Enrichment stats: {enrichment_stats}")
        
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
