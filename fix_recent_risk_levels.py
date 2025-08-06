#!/usr/bin/env python3
"""
Script para corregir los niveles de riesgo de los artículos recientes
Analiza el contenido y asigna niveles de riesgo apropiados
"""

import sqlite3
import os
import time
import json
import re
from typing import Dict, Any

def analyze_risk_level(title: str, content: str) -> str:
    """
    Análisis simple pero efectivo de nivel de riesgo basado en palabras clave
    """
    text = f"{title} {content}".lower()
    
    # Palabras clave para alto riesgo
    high_risk_keywords = [
        'war', 'guerra', 'conflict', 'conflicto', 'attack', 'ataque', 'bombing', 'bomba',
        'terrorism', 'terrorismo', 'violence', 'violencia', 'crisis', 'emergency',
        'threat', 'amenaza', 'invasion', 'invasión', 'military', 'militar',
        'assassination', 'asesinato', 'coup', 'golpe', 'sanctions', 'sanciones',
        'nuclear', 'weapon', 'arma', 'missile', 'misil', 'explosion', 'explosión',
        'death', 'muerte', 'killed', 'killed', 'murdered', 'asesinado',
        'rebel', 'rebelde', 'insurgent', 'insurgente', 'hostage', 'rehén',
        'genocide', 'genocidio', 'civil war', 'guerra civil', 'uprising', 'levantamiento'
    ]
    
    # Palabras clave para riesgo medio
    medium_risk_keywords = [
        'political', 'político', 'election', 'elección', 'government', 'gobierno',
        'protest', 'protesta', 'demonstration', 'manifestación', 'diplomatic', 'diplomático',
        'economic', 'económico', 'trade', 'comercio', 'summit', 'cumbre',
        'negotiation', 'negociación', 'agreement', 'acuerdo', 'treaty', 'tratado',
        'policy', 'política', 'reform', 'reforma', 'corruption', 'corrupción',
        'investigation', 'investigación', 'scandal', 'escándalo', 'debate', 'debate'
    ]
    
    # Palabras clave para bajo riesgo
    low_risk_keywords = [
        'sports', 'deportes', 'entertainment', 'entretenimiento', 'culture', 'cultura',
        'technology', 'tecnología', 'science', 'ciencia', 'health', 'salud',
        'weather', 'clima', 'education', 'educación', 'tourism', 'turismo',
        'festival', 'festival', 'art', 'arte', 'music', 'música', 'movie', 'película',
        'celebrity', 'celebridad', 'fashion', 'moda', 'food', 'comida'
    ]
    
    # Contar matches
    high_count = sum(1 for keyword in high_risk_keywords if keyword in text)
    medium_count = sum(1 for keyword in medium_risk_keywords if keyword in text)
    low_count = sum(1 for keyword in low_risk_keywords if keyword in text)
    
    # Decisión basada en densidad de palabras clave
    total_words = len(text.split())
    
    # Calcular densidad (proporción de palabras clave por total de palabras)
    high_density = (high_count / total_words) * 100 if total_words > 0 else 0
    medium_density = (medium_count / total_words) * 100 if total_words > 0 else 0
    low_density = (low_count / total_words) * 100 if total_words > 0 else 0
    
    # Lógica de decisión
    if high_count >= 2 or high_density > 0.5:
        return 'high'
    elif low_count >= 3 or low_density > 1.0:
        return 'low'
    elif medium_count >= 1 or medium_density > 0.3:
        return 'medium'
    else:
        # Análisis adicional por contexto
        if any(word in text for word in ['trump', 'biden', 'ukraine', 'russia', 'china', 'iran', 'israel', 'gaza']):
            return 'medium'
        else:
            return 'low'

def calculate_risk_score(risk_level: str) -> float:
    """Calcular score numérico basado en el nivel de riesgo"""
    scores = {'low': 0.3, 'medium': 0.6, 'high': 0.9, 'critical': 1.0}
    return scores.get(risk_level, 0.5)

def fix_recent_risk_levels():
    """Corregir los niveles de riesgo de artículos recientes"""
    db_path = "data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Corrigiendo niveles de riesgo de artículos recientes...")
        print("=" * 60)
        
        # Obtener artículos recientes con risk_level = 'medium'
        cursor.execute("""
            SELECT id, title, content, risk_level 
            FROM articles 
            WHERE created_at > datetime('now', '-48 hours')
            AND risk_level = 'medium'
            ORDER BY created_at DESC
        """)
        
        articles_to_fix = cursor.fetchall()
        
        print(f"📊 Encontrados {len(articles_to_fix)} artículos 'medium' para re-analizar")
        
        updates = {'high': 0, 'medium': 0, 'low': 0}
        
        for id, title, content, current_risk in articles_to_fix:
            title_short = title[:60] + "..." if title and len(title) > 60 else title or "Sin título"
            
            # Analizar contenido completo
            full_content = f"{title} {content}" if content else title or ""
            new_risk_level = analyze_risk_level(title or "", content or "")
            new_risk_score = calculate_risk_score(new_risk_level)
            
            if new_risk_level != current_risk:
                # Actualizar en la base de datos
                cursor.execute("""
                    UPDATE articles 
                    SET risk_level = ?, risk_score = ?
                    WHERE id = ?
                """, (new_risk_level, new_risk_score, id))
                
                updates[new_risk_level] += 1
                print(f"   ✅ ID {id}: {current_risk} → {new_risk_level}")
                print(f"      {title_short}")
            else:
                print(f"   ➡️ ID {id}: {current_risk} (sin cambios)")
        
        conn.commit()
        
        print(f"\n📈 Resultados de la corrección:")
        print(f"   Alto riesgo: {updates['high']} artículos")
        print(f"   Riesgo medio: {updates['medium']} artículos")
        print(f"   Bajo riesgo: {updates['low']} artículos")
        
        # Verificar nueva distribución
        cursor.execute("""
            SELECT risk_level, COUNT(*) 
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY risk_level
            ORDER BY COUNT(*) DESC
        """)
        
        new_distribution = cursor.fetchall()
        
        print(f"\n📊 Nueva distribución (últimas 24h):")
        for risk, count in new_distribution:
            print(f"   {risk}: {count} artículos")
        
        conn.close()
        
        print(f"\n✅ Corrección completada. Reinicia el servidor para ver los cambios.")
        
    except Exception as e:
        print(f"❌ Error corrigiendo niveles de riesgo: {e}")

if __name__ == "__main__":
    fix_recent_risk_levels()
