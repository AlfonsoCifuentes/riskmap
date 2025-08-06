#!/usr/bin/env python3
"""
Script para investigar y solucionar el problema de niveles de riesgo
"""

import sqlite3
import os
import sys
from datetime import datetime

def check_risk_distribution():
    """Verificar la distribución de niveles de riesgo en la base de datos"""
    db_path = "data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Analizando distribución de niveles de riesgo...")
        print("=" * 60)
        
        # 1. Verificar distribución general
        cursor.execute("""
            SELECT risk_level, COUNT(*) 
            FROM articles 
            GROUP BY risk_level 
            ORDER BY COUNT(*) DESC
        """)
        
        distribution = cursor.fetchall()
        
        print("📊 Distribución total de niveles de riesgo:")
        total_articles = 0
        for risk, count in distribution:
            print(f"   {risk or 'NULL'}: {count} artículos")
            total_articles += count
        
        print(f"\n📈 Total de artículos: {total_articles}")
        
        # 2. Verificar artículos recientes (últimas 24 horas)
        cursor.execute("""
            SELECT risk_level, COUNT(*) 
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY risk_level 
            ORDER BY COUNT(*) DESC
        """)
        
        recent_distribution = cursor.fetchall()
        
        print("\n📊 Distribución últimas 24 horas:")
        recent_total = 0
        for risk, count in recent_distribution:
            print(f"   {risk or 'NULL'}: {count} artículos")
            recent_total += count
        
        print(f"\n📈 Total artículos recientes: {recent_total}")
        
        # 3. Verificar algunos artículos específicos con sus campos de riesgo
        cursor.execute("""
            SELECT id, title, risk_level, risk_score, created_at 
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        recent_articles = cursor.fetchall()
        
        print("\n📰 Últimos 10 artículos:")
        for id, title, risk_level, risk_score, created_at in recent_articles:
            title_short = title[:50] + "..." if title and len(title) > 50 else title or "Sin título"
            print(f"   ID {id}: [{risk_level or 'NULL'}] {title_short}")
            print(f"        Risk Score: {risk_score or 'NULL'} | Fecha: {created_at}")
        
        # 4. Verificar si hay campos de riesgo nulos
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(risk_level) as with_risk,
                COUNT(risk_score) as with_score
            FROM articles
        """)
        
        field_stats = cursor.fetchone()
        total, with_risk, with_score = field_stats
        
        print("\n📊 Estadísticas de campos:")
        print(f"   Total artículos: {total}")
        print(f"   Con risk_level: {with_risk} ({(with_risk/total*100):.1f}%)")
        print(f"   Con risk_score: {with_score} ({(with_score/total*100):.1f}%)")
        print(f"   Sin risk_level: {total - with_risk}")
        print(f"   Sin risk_score: {total - with_score}")
        
        conn.close()
        
        # Análisis del problema
        print("\n🔍 ANÁLISIS DEL PROBLEMA:")
        all_medium = all(risk == 'medium' for risk, count in distribution if risk)
        
        if all_medium:
            print("❌ PROBLEMA DETECTADO: Todos los artículos con risk_level están marcados como 'medium'")
            print("💡 POSIBLES CAUSAS:")
            print("   1. El sistema de evaluación de riesgo no está funcionando")
            print("   2. Valor por defecto está forzando 'medium' para todos")
            print("   3. Los modelos de IA no están asignando riesgo correctamente")
            return True
        else:
            print("✅ La distribución parece normal")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando distribución: {e}")
        return False

def update_risk_levels_based_on_content():
    """Actualizar niveles de riesgo basado en análisis de contenido"""
    db_path = "data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔧 Actualizando niveles de riesgo basado en contenido...")
        
        # Obtener artículos para reclasificar
        cursor.execute("""
            SELECT id, title, content, summary, auto_generated_summary 
            FROM articles 
            WHERE risk_level = 'medium' OR risk_level IS NULL
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        articles = cursor.fetchall()
        print(f"📋 Procesando {len(articles)} artículos...")
        
        high_risk_keywords = [
            'guerra', 'war', 'conflicto', 'conflict', 'ataque', 'attack', 'bomba', 'bomb',
            'crisis', 'emergency', 'emergencia', 'militar', 'military', 'muerte', 'death',
            'terrorista', 'terrorist', 'violencia', 'violence', 'asesinato', 'murder',
            'explosión', 'explosion', 'invasión', 'invasion', 'batalla', 'battle',
            'nuclear', 'missile', 'misil', 'sanción', 'sanction'
        ]
        
        medium_risk_keywords = [
            'tensión', 'tension', 'disputa', 'dispute', 'negociación', 'negotiation',
            'diplomacia', 'diplomacy', 'elección', 'election', 'política', 'politics',
            'economía', 'economy', 'comercio', 'trade', 'inflación', 'inflation'
        ]
        
        low_risk_keywords = [
            'acuerdo', 'agreement', 'cooperación', 'cooperation', 'paz', 'peace',
            'desarrollo', 'development', 'crecimiento', 'growth', 'inversión', 'investment',
            'cultura', 'culture', 'deporte', 'sports', 'tecnología', 'technology'
        ]
        
        updates_made = 0
        
        for id, title, content, summary, auto_summary in articles:
            # Combinar texto para análisis
            text_to_analyze = ""
            if title:
                text_to_analyze += title.lower() + " "
            if content:
                text_to_analyze += content.lower() + " "
            if summary:
                text_to_analyze += summary.lower() + " "
            if auto_summary:
                text_to_analyze += auto_summary.lower() + " "
            
            if not text_to_analyze.strip():
                continue
            
            # Contar palabras clave por categoría
            high_score = sum(1 for keyword in high_risk_keywords if keyword in text_to_analyze)
            medium_score = sum(1 for keyword in medium_risk_keywords if keyword in text_to_analyze)
            low_score = sum(1 for keyword in low_risk_keywords if keyword in text_to_analyze)
            
            # Determinar nivel de riesgo
            new_risk_level = 'medium'  # default
            
            if high_score >= 2:
                new_risk_level = 'high'
            elif high_score >= 4:
                new_risk_level = 'critical'
            elif low_score > high_score and low_score > medium_score:
                new_risk_level = 'low'
            elif medium_score > 0:
                new_risk_level = 'medium'
            
            # Calcular risk_score
            risk_score = high_score * 2 + medium_score + low_score * 0.5
            
            # Actualizar en la base de datos
            cursor.execute("""
                UPDATE articles 
                SET risk_level = ?, 
                    risk_score = ?
                WHERE id = ?
            """, (new_risk_level, risk_score, id))
            
            updates_made += 1
            
            title_short = title[:40] + "..." if title and len(title) > 40 else title or "Sin título"
            print(f"   ID {id}: {new_risk_level.upper()} | {title_short}")
            print(f"        Scores - Alto:{high_score}, Medio:{medium_score}, Bajo:{low_score}")
        
        conn.commit()
        print(f"\n✅ Se actualizaron {updates_made} artículos")
        
        # Verificar nueva distribución
        cursor.execute("""
            SELECT risk_level, COUNT(*) 
            FROM articles 
            GROUP BY risk_level 
            ORDER BY COUNT(*) DESC
        """)
        
        new_distribution = cursor.fetchall()
        
        print("\n📊 Nueva distribución de riesgo:")
        for risk, count in new_distribution:
            print(f"   {risk or 'NULL'}: {count} artículos")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando niveles de riesgo: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Investigación y Solución de Niveles de Riesgo")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Paso 1: Verificar el problema
    problem_detected = check_risk_distribution()
    
    if problem_detected:
        print("\n" + "="*60)
        response = input("¿Quieres que actualice los niveles de riesgo automáticamente? (s/n): ")
        
        if response.lower() in ['s', 'y', 'si', 'yes']:
            # Paso 2: Solucionarlo
            success = update_risk_levels_based_on_content()
            
            if success:
                print("\n✅ Problema solucionado. Ejecuta de nuevo para verificar.")
            else:
                print("\n❌ Error solucionando el problema.")
        else:
            print("\n💡 Para solucionar manualmente, revisa el código de evaluación de riesgo.")
    
    print("\n" + "="*60)
    print("✅ Análisis completado")
