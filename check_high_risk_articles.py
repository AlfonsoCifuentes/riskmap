#!/usr/bin/env python3
"""
Script para verificar artículos de alto riesgo disponibles para análisis optimizado
"""

import sqlite3
from datetime import datetime, timedelta

def check_high_risk_articles():
    """Verificar disponibilidad de artículos de alto riesgo"""
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Verificar últimas 72 horas
        cutoff_72h = datetime.now() - timedelta(hours=72)
        cutoff_24h = datetime.now() - timedelta(hours=24)
        
        print("🔍 VERIFICACIÓN DE ARTÍCULOS DE ALTO RIESGO")
        print("=" * 50)
        
        # Artículos de alto riesgo últimas 72h
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_risk,
                   COUNT(CASE WHEN risk_level = 'very_high' THEN 1 END) as very_high_risk,
                   COUNT(CASE WHEN risk_score >= 0.7 THEN 1 END) as high_score
            FROM articles 
            WHERE published_at >= ? 
            AND (content IS NOT NULL AND LENGTH(content) > 100)
            AND (title IS NOT NULL AND LENGTH(title) > 10)
        """, (cutoff_72h.strftime('%Y-%m-%d %H:%M:%S'),))
        
        stats_72h = cursor.fetchone()
        
        print(f"📊 ÚLTIMAS 72 HORAS:")
        print(f"   Total artículos: {stats_72h[0]}")
        print(f"   Alto riesgo (high): {stats_72h[1]}")
        print(f"   Muy alto riesgo (very_high): {stats_72h[2]}")
        print(f"   Score >= 0.7: {stats_72h[3]}")
        
        # Artículos de alto riesgo últimas 24h
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_risk,
                   COUNT(CASE WHEN risk_level = 'very_high' THEN 1 END) as very_high_risk,
                   COUNT(CASE WHEN risk_score >= 0.7 THEN 1 END) as high_score
            FROM articles 
            WHERE published_at >= ? 
            AND (content IS NOT NULL AND LENGTH(content) > 100)
            AND (title IS NOT NULL AND LENGTH(title) > 10)
        """, (cutoff_24h.strftime('%Y-%m-%d %H:%M:%S'),))
        
        stats_24h = cursor.fetchone()
        
        print(f"\n📊 ÚLTIMAS 24 HORAS:")
        print(f"   Total artículos: {stats_24h[0]}")
        print(f"   Alto riesgo (high): {stats_24h[1]}")
        print(f"   Muy alto riesgo (very_high): {stats_24h[2]}")
        print(f"   Score >= 0.7: {stats_24h[3]}")
        
        # Obtener ejemplos de artículos de alto riesgo
        cursor.execute("""
            SELECT id, title, risk_level, risk_score, published_at, country
            FROM articles 
            WHERE published_at >= ? 
            AND (risk_level = 'high' OR risk_level = 'very_high' OR risk_score >= 0.7)
            AND (content IS NOT NULL AND LENGTH(content) > 100)
            ORDER BY published_at DESC
            LIMIT 5
        """, (cutoff_72h.strftime('%Y-%m-%d %H:%M:%S'),))
        
        examples = cursor.fetchall()
        
        if examples:
            print(f"\n📰 EJEMPLOS DE ARTÍCULOS DE ALTO RIESGO:")
            for i, (id, title, risk_level, risk_score, published_at, country) in enumerate(examples, 1):
                print(f"   {i}. [{id}] {title[:60]}...")
                print(f"      Riesgo: {risk_level} | Score: {risk_score:.2f} | País: {country}")
                print(f"      Fecha: {published_at}")
                print()
        else:
            print("\n⚠️ NO SE ENCONTRARON ARTÍCULOS DE ALTO RIESGO RECIENTES")
            print("💡 Esto significa que el análisis optimizado podría no encontrar conflictos")
            
            # Buscar artículos de riesgo medio como alternativa
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM articles 
                WHERE published_at >= ? 
                AND (risk_level = 'medium' OR risk_score >= 0.4)
                AND (content IS NOT NULL AND LENGTH(content) > 100)
            """, (cutoff_72h.strftime('%Y-%m-%d %H:%M:%S'),))
            
            medium_count = cursor.fetchone()[0]
            print(f"📊 Artículos de riesgo medio disponibles: {medium_count}")
        
        # Verificar distribución general de riesgo
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM articles 
            WHERE published_at >= ?
            GROUP BY risk_level
            ORDER BY count DESC
        """, (cutoff_72h.strftime('%Y-%m-%d %H:%M:%S'),))
        
        risk_distribution = cursor.fetchall()
        
        print(f"\n📈 DISTRIBUCIÓN DE RIESGO (72h):")
        for risk_level, count in risk_distribution:
            print(f"   {risk_level}: {count} artículos")
        
        conn.close()
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        total_high_risk = stats_72h[1] + stats_72h[2] + stats_72h[3]
        if total_high_risk >= 5:
            print("✅ Suficientes artículos de alto riesgo para análisis optimizado")
        elif total_high_risk >= 1:
            print("⚠️ Pocos artículos de alto riesgo. El análisis será rápido pero con pocos resultados")
        else:
            print("❌ Sin artículos de alto riesgo. El análisis usará artículos de riesgo medio")
            print("🔧 Considera ejecutar el analizador BERT para re-evaluar riesgos")
        
    except Exception as e:
        print(f"❌ Error verificando artículos: {e}")

if __name__ == "__main__":
    check_high_risk_articles()
