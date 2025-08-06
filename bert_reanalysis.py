#!/usr/bin/env python3
"""
Re-análisis completo de todas las noticias usando BERT NLP
Corrige niveles de riesgo incorrectos y asegura consistencia
"""

import sqlite3
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers library available")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("❌ Transformers library not available. Install with: pip install transformers torch")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BertRiskAnalyzer:
    """Analizador de riesgo usando BERT para clasificación de texto"""
    
    def __init__(self):
        self.sentiment_analyzer = None
        self.classifier = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Usando dispositivo: {self.device}")
        
    def initialize_models(self):
        """Inicializar modelos BERT"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library not available")
            
        try:
            print("🚀 Inicializando modelos BERT...")
            
            # Modelo para análisis de sentimiento
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                device=0 if self.device == "cuda" else -1
            )
            
            # Modelo para clasificación de texto (usando un modelo pre-entrenado general)
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if self.device == "cuda" else -1
            )
            
            print("✅ Modelos BERT inicializados correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando modelos BERT: {e}")
            return False
    
    def analyze_risk_level(self, title: str, content: str) -> Dict[str, Any]:
        """
        Analizar nivel de riesgo usando BERT y lógica avanzada
        """
        try:
            # Combinar título y contenido para análisis
            full_text = f"{title}. {content}" if content else title
            
            # Truncar si es muy largo (BERT tiene límites)
            if len(full_text) > 512:
                full_text = full_text[:512]
            
            # Análisis de sentimiento con BERT
            sentiment_result = self.sentiment_analyzer(full_text)
            sentiment_score = sentiment_result[0]['score'] if sentiment_result else 0.5
            sentiment_label = sentiment_result[0]['label'] if sentiment_result else 'NEUTRAL'
            
            # Clasificación de contenido usando zero-shot classification
            risk_categories = [
                "guerra y conflictos armados",
                "terrorismo y violencia",
                "crisis económica y financiera", 
                "política y diplomacia",
                "tecnología y ciencia",
                "entretenimiento y deportes",
                "salud y medicina",
                "medio ambiente"
            ]
            
            classification_result = self.classifier(full_text, risk_categories)
            top_category = classification_result['labels'][0]
            top_score = classification_result['scores'][0]
            
            # Análisis de palabras clave críticas
            risk_score = self._calculate_keyword_risk_score(full_text.lower())
            
            # Determinar nivel de riesgo final
            final_risk_level = self._determine_final_risk_level(
                sentiment_score, sentiment_label, top_category, top_score, risk_score
            )
            
            return {
                'risk_level': final_risk_level,
                'risk_score': self._convert_risk_to_score(final_risk_level),
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'top_category': top_category,
                'category_confidence': top_score,
                'keyword_risk_score': risk_score,
                'analysis_method': 'bert_nlp'
            }
            
        except Exception as e:
            logger.error(f"Error en análisis BERT: {e}")
            # Fallback a análisis por palabras clave
            return self._fallback_keyword_analysis(title, content)
    
    def _calculate_keyword_risk_score(self, text: str) -> float:
        """Calcular score de riesgo basado en palabras clave"""
        
        # Palabras clave de alto riesgo
        high_risk_keywords = {
            'guerra': 3.0, 'war': 3.0, 'conflict': 2.5, 'conflicto': 2.5,
            'attack': 2.8, 'ataque': 2.8, 'bombing': 3.0, 'bomba': 3.0,
            'terrorism': 3.0, 'terrorismo': 3.0, 'terrorist': 3.0, 'terrorista': 3.0,
            'violence': 2.5, 'violencia': 2.5, 'crisis': 2.0, 'emergency': 2.2,
            'threat': 2.3, 'amenaza': 2.3, 'invasion': 3.0, 'invasión': 3.0,
            'military': 2.0, 'militar': 2.0, 'assassination': 3.0, 'asesinato': 3.0,
            'coup': 2.8, 'golpe': 2.8, 'sanctions': 2.2, 'sanciones': 2.2,
            'nuclear': 2.8, 'weapon': 2.5, 'arma': 2.5, 'missile': 2.7, 'misil': 2.7,
            'explosion': 2.6, 'explosión': 2.6, 'death': 2.0, 'muerte': 2.0,
            'killed': 2.3, 'muerto': 2.3, 'murdered': 2.8, 'asesinado': 2.8,
            'hostage': 2.7, 'rehén': 2.7, 'genocide': 3.0, 'genocidio': 3.0
        }
        
        # Palabras clave de riesgo medio
        medium_risk_keywords = {
            'political': 1.5, 'político': 1.5, 'election': 1.3, 'elección': 1.3,
            'government': 1.4, 'gobierno': 1.4, 'protest': 1.8, 'protesta': 1.8,
            'diplomatic': 1.6, 'diplomático': 1.6, 'economic': 1.7, 'económico': 1.7,
            'trade': 1.4, 'comercio': 1.4, 'negotiation': 1.2, 'negociación': 1.2,
            'agreement': 1.1, 'acuerdo': 1.1, 'treaty': 1.3, 'tratado': 1.3,
            'corruption': 1.6, 'corrupción': 1.6, 'investigation': 1.4, 'investigación': 1.4,
            'scandal': 1.5, 'escándalo': 1.5, 'reform': 1.2, 'reforma': 1.2
        }
        
        # Palabras clave de bajo riesgo
        low_risk_keywords = {
            'sports': -1.0, 'deportes': -1.0, 'entertainment': -0.8, 'entretenimiento': -0.8,
            'culture': -0.6, 'cultura': -0.6, 'technology': -0.5, 'tecnología': -0.5,
            'science': -0.4, 'ciencia': -0.4, 'health': -0.3, 'salud': -0.3,
            'education': -0.5, 'educación': -0.5, 'tourism': -0.7, 'turismo': -0.7,
            'festival': -0.8, 'festival': -0.8, 'art': -0.6, 'arte': -0.6,
            'music': -0.7, 'música': -0.7, 'movie': -0.8, 'película': -0.8,
            'celebrity': -0.9, 'celebridad': -0.9, 'fashion': -0.9, 'moda': -0.9
        }
        
        # Calcular score total
        total_score = 0.0
        word_count = 0
        
        words = text.split()
        
        for word in words:
            if word in high_risk_keywords:
                total_score += high_risk_keywords[word]
                word_count += 1
            elif word in medium_risk_keywords:
                total_score += medium_risk_keywords[word]
                word_count += 1
            elif word in low_risk_keywords:
                total_score += low_risk_keywords[word]
                word_count += 1
        
        # Normalizar score
        if word_count > 0:
            normalized_score = total_score / len(words) * 100  # Convertir a porcentaje
        else:
            normalized_score = 0.0
        
        # Asegurar que esté en rango 0-1
        return max(0.0, min(1.0, (normalized_score + 5) / 10))  # +5 para offset, /10 para normalizar
    
    def _determine_final_risk_level(self, sentiment_score: float, sentiment_label: str, 
                                   top_category: str, category_confidence: float, 
                                   keyword_risk_score: float) -> str:
        """Determinar nivel de riesgo final combinando todos los factores"""
        
        # Mapeo de categorías a riesgo base
        category_risk_mapping = {
            "guerra y conflictos armados": 0.9,
            "terrorismo y violencia": 0.95,
            "crisis económica y financiera": 0.7,
            "política y diplomacia": 0.5,
            "tecnología y ciencia": 0.2,
            "entretenimiento y deportes": 0.1,
            "salud y medicina": 0.3,
            "medio ambiente": 0.4
        }
        
        # Score base según categoría
        category_risk = category_risk_mapping.get(top_category, 0.5)
        
        # Ajustar según confianza en la categoría
        category_risk *= category_confidence
        
        # Ajustar según sentimiento (sentimiento muy negativo = más riesgo)
        sentiment_multiplier = 1.0
        if sentiment_label in ['NEGATIVE', '1 star', '2 stars']:
            sentiment_multiplier = 1.3
        elif sentiment_label in ['POSITIVE', '4 stars', '5 stars']:
            sentiment_multiplier = 0.8
        
        # Combinar todos los factores
        final_score = (category_risk * 0.4 + keyword_risk_score * 0.6) * sentiment_multiplier
        
        # Determinar nivel final
        if final_score >= 0.7:
            return 'high'
        elif final_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _convert_risk_to_score(self, risk_level: str) -> float:
        """Convertir nivel de riesgo a score numérico"""
        mapping = {'low': 0.25, 'medium': 0.6, 'high': 0.9, 'critical': 1.0}
        return mapping.get(risk_level, 0.5)
    
    def _fallback_keyword_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """Análisis de fallback usando solo palabras clave"""
        text = f"{title} {content}".lower()
        risk_score = self._calculate_keyword_risk_score(text)
        
        if risk_score >= 0.7:
            risk_level = 'high'
        elif risk_score >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'risk_score': self._convert_risk_to_score(risk_level),
            'sentiment_score': 0.5,
            'sentiment_label': 'UNKNOWN',
            'analysis_method': 'keyword_fallback'
        }

def reanalyze_all_articles():
    """Re-analizar todas las noticias en la base de datos"""
    
    if not TRANSFORMERS_AVAILABLE:
        print("❌ No se puede ejecutar sin la librería transformers")
        print("Instala con: pip install transformers torch")
        return False
    
    # Inicializar analizador BERT
    analyzer = BertRiskAnalyzer()
    if not analyzer.initialize_models():
        print("❌ No se pudieron inicializar los modelos BERT")
        return False
    
    db_path = "data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todas las noticias
        cursor.execute("""
            SELECT id, title, content, risk_level, created_at 
            FROM articles 
            ORDER BY created_at DESC
        """)
        
        articles = cursor.fetchall()
        
        print(f"🔍 Encontradas {len(articles)} noticias para re-analizar")
        print("=" * 60)
        
        updated_count = 0
        error_count = 0
        
        for i, (article_id, title, content, current_risk, created_at) in enumerate(articles):
            try:
                print(f"\n📰 [{i+1}/{len(articles)}] Analizando artículo {article_id}")
                print(f"   Título: {title[:60]}...")
                print(f"   Riesgo actual: {current_risk}")
                
                # Analizar con BERT
                analysis_result = analyzer.analyze_risk_level(title or "", content or "")
                new_risk_level = analysis_result['risk_level']
                new_risk_score = analysis_result['risk_score']
                
                # Actualizar en la base de datos
                cursor.execute("""
                    UPDATE articles 
                    SET risk_level = ?, 
                        risk_score = ?,
                        enrichment_status = 'completed',
                        last_enriched = ?,
                        enrichment_version = enrichment_version + 1
                    WHERE id = ?
                """, (new_risk_level, new_risk_score, datetime.now().isoformat(), article_id))
                
                if new_risk_level != current_risk:
                    print(f"   ✅ ACTUALIZADO: {current_risk} → {new_risk_level} (score: {new_risk_score:.2f})")
                    updated_count += 1
                else:
                    print(f"   ➡️ Sin cambios: {current_risk}")
                
                # Commit cada 10 artículos para evitar pérdida de datos
                if (i + 1) % 10 == 0:
                    conn.commit()
                    print(f"   💾 Guardados {i+1} análisis...")
                
                # Pausa breve para evitar sobrecarga
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Error analizando artículo {article_id}: {e}")
                error_count += 1
                continue
        
        # Commit final
        conn.commit()
        
        # Estadísticas finales
        cursor.execute("""
            SELECT risk_level, COUNT(*) 
            FROM articles 
            GROUP BY risk_level 
            ORDER BY COUNT(*) DESC
        """)
        
        final_distribution = cursor.fetchall()
        
        print(f"\n" + "=" * 60)
        print(f"✅ RE-ANÁLISIS COMPLETADO")
        print(f"📊 Artículos procesados: {len(articles)}")
        print(f"🔄 Artículos actualizados: {updated_count}")
        print(f"❌ Errores: {error_count}")
        print(f"\n📈 Nueva distribución de riesgos:")
        for risk, count in final_distribution:
            print(f"   {risk}: {count} artículos")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en re-análisis: {e}")
        return False

if __name__ == "__main__":
    print("🔬 BERT NLP Re-Analysis Tool")
    print("Analizando todas las noticias con modelos BERT...")
    print("=" * 60)
    
    success = reanalyze_all_articles()
    
    if success:
        print(f"\n🎉 Re-análisis completado exitosamente")
        print(f"🔄 Reinicia el servidor para ver los cambios")
    else:
        print(f"\n💥 Re-análisis falló")
