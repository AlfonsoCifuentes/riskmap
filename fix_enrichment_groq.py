#!/usr/bin/env python3
"""
Script para arreglar el enriquecimiento con Groq y análisis NLP
Este script va a procesar REALMENTE los artículos con Groq
"""

import os
import sys
import sqlite3
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'fix_enrichment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Importar Groq
try:
    from groq import Groq
    logger.info("✅ Groq importado correctamente")
except ImportError:
    logger.error("❌ Groq no está instalado. Instalando...")
    os.system("pip install groq")
    from groq import Groq

class GroqEnrichmentFixer:
    """Arregla el enriquecimiento usando Groq directamente"""
    
    def __init__(self):
        self.db_path = Path('data/geopolitical_intel.db')
        
        # Configurar Groq
        api_key = os.getenv('GROQ_API_KEY') or "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"
        if not api_key:
            raise ValueError("GROQ_API_KEY no encontrada")
        
        self.groq_client = Groq(api_key=api_key)
        self.processed_count = 0
        self.error_count = 0
        
    def analyze_article_with_groq(self, title: str, content: str) -> Dict[str, Any]:
        """Analiza un artículo con Groq para extraer entidades y personas"""
        
        prompt = f"""
Analiza el siguiente artículo de noticias geopolíticas y extrae la información en formato JSON:

TÍTULO: {title}
CONTENIDO: {content[:2000]}...

Responde SOLO con un JSON válido que contenga:
{{
    "key_persons": ["persona1", "persona2", ...],
    "key_locations": ["lugar1", "lugar2", ...],
    "extracted_entities": {{
        "persons": ["persona1", "persona2"],
        "locations": ["lugar1", "lugar2"],
        "organizations": ["org1", "org2"],
        "events": ["evento1", "evento2"]
    }},
    "conflict_probability": 0.0-1.0,
    "geopolitical_relevance": 0.0-1.0,
    "main_themes": ["tema1", "tema2"],
    "risk_indicators": ["indicador1", "indicador2"]
}}

Extrae solo entidades REALES y RELEVANTES. No inventes información.
"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Limpiar respuesta para obtener solo el JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parsear JSON
            result = json.loads(response_text)
            
            # Validar estructura mínima
            if not isinstance(result, dict):
                raise ValueError("Respuesta no es un diccionario")
                
            # Asegurar que los campos existen
            result.setdefault("key_persons", [])
            result.setdefault("key_locations", [])
            result.setdefault("extracted_entities", {})
            result.setdefault("conflict_probability", 0.0)
            result.setdefault("geopolitical_relevance", 0.0)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analizando con Groq: {e}")
            return {
                "key_persons": [],
                "key_locations": [],
                "extracted_entities": {},
                "conflict_probability": 0.0,
                "geopolitical_relevance": 0.0,
                "error": str(e)
            }

    def update_article_with_groq_analysis(self, article_id: int, analysis: Dict[str, Any]) -> bool:
        """Actualiza un artículo con el análisis de Groq"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Extraer datos del análisis
            key_persons = json.dumps(analysis.get("key_persons", []))
            key_locations = json.dumps(analysis.get("key_locations", []))
            extracted_entities_json = json.dumps(analysis.get("extracted_entities", {}))
            conflict_probability = analysis.get("conflict_probability", 0.0)
            geopolitical_relevance = analysis.get("geopolitical_relevance", 0.0)
            
            # Actualizar artículo
            cursor.execute("""
                UPDATE articles SET
                    key_persons = ?,
                    key_locations = ?,
                    extracted_entities_json = ?,
                    conflict_probability = ?,
                    geopolitical_relevance = ?,
                    groq_enhanced = 1,
                    nlp_processed = 1,
                    enhanced_date = ?,
                    processing_version = 'groq_fix_v1.0'
                WHERE id = ?
            """, (
                key_persons,
                key_locations, 
                extracted_entities_json,
                conflict_probability,
                geopolitical_relevance,
                datetime.now().isoformat(),
                article_id
            ))
            
            conn.commit()
            conn.close()
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando artículo {article_id}: {e}")
            self.error_count += 1
            return False

    def process_unprocessed_articles(self, limit: int = 50):
        """Procesa artículos que no han sido enriquecidos con Groq"""
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Obtener artículos sin procesar
        cursor.execute("""
            SELECT id, title, content 
            FROM articles 
            WHERE (groq_enhanced IS NULL OR groq_enhanced = 0)
            AND title IS NOT NULL 
            AND content IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        articles = cursor.fetchall()
        conn.close()
        
        logger.info(f"🚀 Procesando {len(articles)} artículos con Groq...")
        
        for i, (article_id, title, content) in enumerate(articles, 1):
            logger.info(f"📝 Procesando artículo {i}/{len(articles)}: ID {article_id}")
            logger.info(f"   Título: {title[:100]}...")
            
            # Analizar con Groq
            analysis = self.analyze_article_with_groq(title, content)
            
            if "error" not in analysis:
                # Actualizar artículo
                success = self.update_article_with_groq_analysis(article_id, analysis)
                
                if success:
                    logger.info(f"✅ Artículo {article_id} enriquecido exitosamente")
                    logger.info(f"   Personas: {len(analysis.get('key_persons', []))}")
                    logger.info(f"   Lugares: {len(analysis.get('key_locations', []))}")
                    logger.info(f"   Probabilidad conflicto: {analysis.get('conflict_probability', 0.0):.2f}")
                else:
                    logger.error(f"❌ Error actualizando artículo {article_id}")
            else:
                logger.error(f"❌ Error analizando artículo {article_id}: {analysis['error']}")
            
            # Pausa para evitar rate limiting
            time.sleep(2)
            
            # Progreso cada 10 artículos
            if i % 10 == 0:
                logger.info(f"📊 Progreso: {i}/{len(articles)} artículos procesados")

        logger.info("🏁 Procesamiento completado:")
        logger.info(f"   ✅ Exitosos: {self.processed_count}")
        logger.info(f"   ❌ Errores: {self.error_count}")
        logger.info(f"   📈 Tasa éxito: {(self.processed_count/(self.processed_count+self.error_count)*100):.1f}%")

def main():
    """Función principal"""
    logger.info("🔧 Iniciando corrección de enriquecimiento con Groq...")
    
    try:
        fixer = GroqEnrichmentFixer()
        
        # Procesar hasta 50 artículos no procesados
        fixer.process_unprocessed_articles(limit=50)
        
        logger.info("✅ Corrección completada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error en corrección: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
