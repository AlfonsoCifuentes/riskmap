#!/usr/bin/env python3
"""
Re-análisis BERT simplificado y funcional
"""

import sqlite3
import os
import json
import time
from datetime import datetime
from typing import Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_keyword_risk_score(text: str) -> float:
    """Calcular score de riesgo basado en palabras clave"""
    
    text = text.lower()
    
    # Palabras clave de alto riesgo con pesos
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
        'hostage': 2.7, 'rehén': 2.7, 'genocide': 3.0, 'genocidio': 3.0,
        'drone': 2.0, 'strike': 2.2, 'bombardment': 2.8, 'bombardeo': 2.8
    }
    
    # Palabras clave de riesgo medio
    medium_risk_keywords = {
        'political': 1.5, 'político': 1.5, 'election': 1.3, 'elección': 1.3,
        'government': 1.4, 'gobierno': 1.4, 'protest': 1.8, 'protesta': 1.8,
        'diplomatic': 1.6, 'diplomático': 1.6, 'economic': 1.7, 'económico': 1.7,
        'trade': 1.4, 'comercio': 1.4, 'negotiation': 1.2, 'negociación': 1.2,
        'agreement': 1.1, 'acuerdo': 1.1, 'treaty': 1.3, 'tratado': 1.3,
        'corruption': 1.6, 'corrupción': 1.6, 'investigation': 1.4, 'investigación': 1.4,
        'scandal': 1.5, 'escándalo': 1.5, 'reform': 1.2, 'reforma': 1.2,
        'tariffs': 1.8, 'aranceles': 1.8, 'recession': 1.9, 'recesión': 1.9
    }
    
    # Palabras clave de bajo riesgo
    low_risk_keywords = {
        'sports': -1.0, 'deportes': -1.0, 'entertainment': -0.8, 'entretenimiento': -0.8,
        'culture': -0.6, 'cultura': -0.6, 'technology': -0.5, 'tecnología': -0.5,
        'science': -0.4, 'ciencia': -0.4, 'health': -0.3, 'salud': -0.3,
        'education': -0.5, 'educación': -0.5, 'tourism': -0.7, 'turismo': -0.7,
        'festival': -0.8, 'art': -0.6, 'arte': -0.6,
        'music': -0.7, 'música': -0.7, 'movie': -0.8, 'película': -0.8,
        'celebrity': -0.9, 'celebridad': -0.9, 'fashion': -0.9, 'moda': -0.9,
        'iphone': -0.8, 'apple': -0.6, 'android': -0.7, 'netflix': -0.8
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
    if len(words) > 0:
        normalized_score = total_score / len(words) * 100
    else:
        normalized_score = 0.0
    
    # Convertir a rango 0-1
    final_score = max(0.0, min(1.0, (normalized_score + 5) / 10))
    
    return final_score

def analyze_risk_level(title: str, content: str) -> Dict[str, Any]:
    """Analizar nivel de riesgo mejorado"""
    
    # Combinar título y contenido
    full_text = f"{title}. {content}" if content else title or ""
    
    # Calcular score de palabras clave
    keyword_score = calculate_keyword_risk_score(full_text)
    
    # Análisis adicional por contexto geopolítico
    geopolitical_multiplier = 1.0
    text_lower = full_text.lower()
    
    # Países y regiones de alto riesgo
    high_risk_regions = ['ukraine', 'ucrania', 'russia', 'rusia', 'china', 'iran', 'israel', 'gaza', 'syria', 'siria', 'afghanistan', 'afganistán']
    for region in high_risk_regions:
        if region in text_lower:
            geopolitical_multiplier *= 1.3
            break
    
    # Palabras que indican urgencia o gravedad
    urgency_words = ['breaking', 'urgent', 'urgente', 'immediate', 'inmediato', 'emergency', 'emergencia']
    for word in urgency_words:
        if word in text_lower:
            geopolitical_multiplier *= 1.2
            break
    
    # Score final
    final_score = keyword_score * geopolitical_multiplier
    final_score = min(1.0, final_score)  # Cap at 1.0
    
    # Determinar nivel de riesgo
    if final_score >= 0.7:
        risk_level = 'high'
    elif final_score >= 0.35:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    return {
        'risk_level': risk_level,
        'risk_score': final_score,
        'keyword_score': keyword_score,
        'geopolitical_multiplier': geopolitical_multiplier,
        'analysis_method': 'enhanced_keyword_nlp'
    }

def reanalyze_all_articles():
    """Re-analizar todas las noticias en la base de datos"""
    
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
        risk_changes = {'high': 0, 'medium': 0, 'low': 0}
        
        for i, (article_id, title, content, current_risk, created_at) in enumerate(articles):
            try:
                print(f"\n📰 [{i+1}/{len(articles)}] Analizando artículo {article_id}")
                title_display = (title[:60] + "...") if title and len(title) > 60 else title or "Sin título"
                print(f"   Título: {title_display}")
                print(f"   Riesgo actual: {current_risk}")
                
                # Analizar con algoritmo mejorado
                analysis_result = analyze_risk_level(title or "", content or "")
                new_risk_level = analysis_result['risk_level']
                new_risk_score = analysis_result['risk_score']
                
                # Actualizar en la base de datos
                cursor.execute("""
                    UPDATE articles 
                    SET risk_level = ?, 
                        risk_score = ?,
                        enrichment_status = 'completed',
                        last_enriched = ?,
                        enrichment_version = COALESCE(enrichment_version, 0) + 1
                    WHERE id = ?
                """, (new_risk_level, new_risk_score, datetime.now().isoformat(), article_id))
                
                if new_risk_level != current_risk:
                    print(f"   ✅ ACTUALIZADO: {current_risk} → {new_risk_level} (score: {new_risk_score:.3f})")
                    updated_count += 1
                    risk_changes[new_risk_level] += 1
                else:
                    print(f"   ➡️ Sin cambios: {current_risk} (score: {new_risk_score:.3f})")
                
                # Commit cada 20 artículos
                if (i + 1) % 20 == 0:
                    conn.commit()
                    print(f"   💾 Guardados {i+1} análisis...")
                
                # Pausa breve
                time.sleep(0.05)
                
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
            ORDER BY 
                CASE risk_level 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                    ELSE 4 
                END
        """)
        
        final_distribution = cursor.fetchall()
        
        print("\n" + "=" * 60)
        print("✅ RE-ANÁLISIS COMPLETADO")
        print(f"📊 Artículos procesados: {len(articles)}")
        print(f"🔄 Artículos actualizados: {updated_count}")
        print(f"❌ Errores: {error_count}")
        
        print("\n📈 Nueva distribución de riesgos:")
        for risk, count in final_distribution:
            percentage = (count / len(articles)) * 100
            print(f"   {risk.upper()}: {count} artículos ({percentage:.1f}%)")
        
        print("\n🔄 Cambios realizados:")
        for risk_level, count in risk_changes.items():
            if count > 0:
                print(f"   Cambiados a {risk_level.upper()}: {count} artículos")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en re-análisis: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Enhanced NLP Re-Analysis Tool")
    print("Re-analizando todas las noticias con algoritmo mejorado...")
    print("=" * 60)
    
    success = reanalyze_all_articles()
    
    if success:
        print("\n🎉 Re-análisis completado exitosamente")
        print("🔄 Reinicia el servidor para ver los cambios")
    else:
        print("\n💥 Re-análisis falló")
