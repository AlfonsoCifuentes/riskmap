import sqlite3
import logging
import re
import torch

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedNLPAnalyzer:
    def __init__(self, db_path):
        # --- DEFERRED IMPORT ---
        # Import transformers here to avoid issues with multiprocessing/reloading
        from transformers import pipeline

        self.db_path = db_path
        self.conn = self._get_db_connection()
        
        # --- Modelos de NLP ---
        # Modelo para clasificación de riesgo (ejemplo, ajustar al modelo real)
        try:
            logger.info("Cargando modelo de clasificación de riesgo...")
            self.risk_classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                return_all_scores=True
            )
            logger.info("Modelo de clasificación de riesgo cargado.")
        except Exception as e:
            logger.error(f"No se pudo cargar el modelo de clasificación: {e}")
            self.risk_classifier = None

        # Modelo para reconocimiento de entidades (NER) para geolocalización
        try:
            logger.info("Cargando modelo NER...")
            self.ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
            logger.info("Modelo NER cargado.")
        except Exception as e:
            logger.error(f"No se pudo cargar el modelo NER: {e}")
            self.ner_pipeline = None

    def _get_db_connection(self):
        """Establece la conexión con la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error de base de datos al conectar: {e}")
            return None

    def analyze_unprocessed_articles(self, limit=100):
        """Analiza artículos no procesados para calcular riesgo y extraer ubicaciones."""
        if not self.conn:
            logger.error("No hay conexión a la base de datos. Abortando análisis.")
            return 0
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, content FROM articles WHERE processed = 0 LIMIT ?", (limit,))
        articles = cursor.fetchall()

        if not articles:
            logger.info("No hay artículos nuevos para procesar.")
            return 0

        processed_count = 0
        for article in articles:
            try:
                text_to_analyze = f"{article['title']}. {article['content']}"
                
                # 1. Calcular Puntuación de Riesgo
                risk_score = self._calculate_risk(text_to_analyze)
                
                # 2. Extraer Ubicación Geográfica
                latitude, longitude = self._extract_geolocation(text_to_analyze)

                # 3. Actualizar la base de datos
                cursor.execute("""
                    UPDATE articles
                    SET risk_score = ?, latitude = ?, longitude = ?, processed = 1
                    WHERE id = ?
                """, (risk_score, latitude, longitude, article['id']))
                
                self.conn.commit()
                processed_count += 1
                logger.info(f"Artículo ID {article['id']} procesado. Riesgo: {risk_score}, Lat: {latitude}, Lon: {longitude}")

            except Exception as e:
                logger.error(f"Error procesando artículo ID {article['id']}: {e}")
                # Marcar como procesado para no reintentar indefinidamente si hay un error persistente
                cursor.execute("UPDATE articles SET processed = -1 WHERE id = ?", (article['id'],))
                self.conn.commit()

        logger.info(f"Proceso de análisis completado. {processed_count} artículos procesados.")
        return processed_count

    def _calculate_risk(self, text):
        """Calcula el riesgo usando el modelo de clasificación."""
        if not self.risk_classifier:
            return 50.0 # Valor por defecto si el modelo no está disponible

        try:
            # Truncar texto para que se ajuste al modelo
            max_length = self.risk_classifier.model.config.max_position_embeddings
            truncated_text = text[:max_length]
            
            scores = self.risk_classifier(truncated_text)[0]
            # Lógica para convertir la salida del modelo a una puntuación de 0-100
            # Esto es un ejemplo y debe ser ajustado al modelo específico
            positive_score = next((item['score'] for item in scores if item['label'] == 'POSITIVE'), 0)
            negative_score = next((item['score'] for item in scores if item['label'] == 'NEGATIVE'), 0)
            
            # Ejemplo: riesgo basado en la probabilidad de sentimiento negativo
            risk = negative_score * 100
            return round(risk, 2)
        except Exception as e:
            logger.error(f"Error en cálculo de riesgo: {e}")
            return 50.0 # Fallback

    def _extract_geolocation(self, text):
        """Extrae la ubicación más probable y la convierte a coordenadas (simulado)."""
        if not self.ner_pipeline:
            return None, None

        try:
            entities = self.ner_pipeline(text)
            locations = [entity['word'] for entity in entities if entity['entity'] == 'I-LOC']
            
            if not locations:
                return None, None

            # Lógica de geocodificación (aquí simulada)
            # En un caso real, usarías un servicio como Geopy con Nominatim, Google Maps, etc.
            most_likely_location = locations[0].replace(" ", "") # Tomar la primera ubicación encontrada
            
            # Simulación de coordenadas
            # Esto debería ser reemplazado por una llamada a una API de geocodificación
            if "paris" in most_likely_location.lower(): return 48.85, 2.35
            if "london" in most_likely_location.lower(): return 51.50, -0.12
            if "tokyo" in most_likely_location.lower(): return 35.68, 139.69
            
            return None, None # Si no se encuentra una ubicación conocida
        except Exception as e:
            logger.error(f"Error en extracción de geolocalización: {e}")
            return None, None

    def close_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()
            logger.info("Conexión a la base de datos cerrada.")

def run_analysis_process(db_path):
    """Función independiente para ejecutar el proceso de análisis NLP."""
    analyzer = EnhancedNLPAnalyzer(db_path)
    count = analyzer.analyze_unprocessed_articles()
    analyzer.close_connection()
    return count
