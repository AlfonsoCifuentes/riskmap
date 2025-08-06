#!/usr/bin/env python3
"""
Script para verificar y optimizar el sistema de enriquecimiento automático
Muestra cuántos artículos están pendientes y optimiza el procesamiento
"""

import sqlite3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_enrichment_status():
    """Verificar el estado del sistema de enriquecimiento"""
    db_path = "data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    print("🔍 VERIFICANDO ESTADO DEL SISTEMA DE ENRIQUECIMIENTO")
    print("=" * 60)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Total de artículos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        print(f"📰 Total artículos en la base de datos: {total_articles}")
        
        # Artículos pendientes de enriquecimiento (TODOS)
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE enrichment_status IS NULL OR enrichment_status = 'pending'
        """)
        total_pending = cursor.fetchone()[0]
        print(f"⏳ Total artículos pendientes de enriquecimiento: {total_pending}")
        
        # Artículos NUEVOS pendientes (últimas 48 horas)
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE (enrichment_status IS NULL OR enrichment_status = 'pending')
            AND created_at >= datetime('now', '-48 hours')
        """)
        new_pending = cursor.fetchone()[0]
        print(f"🆕 Artículos NUEVOS pendientes (48h): {new_pending}")
        
        # Artículos antiguos pendientes (más de 48 horas)
        old_pending = total_pending - new_pending
        print(f"🗄️ Artículos ANTIGUOS pendientes (>48h): {old_pending}")
        
        # Artículos ya enriquecidos
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE enrichment_status = 'completed'
        """)
        completed = cursor.fetchone()[0]
        print(f"✅ Artículos ya enriquecidos: {completed}")
        
        # Artículos con errores
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE enrichment_status = 'error'
        """)
        errors = cursor.fetchone()[0]
        print(f"❌ Artículos con errores de enriquecimiento: {errors}")
        
        print("\n" + "=" * 60)
        
        # Estadísticas por tiempo
        print("📊 DISTRIBUCIÓN TEMPORAL:")
        
        # Últimas 24 horas
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE created_at >= datetime('now', '-24 hours')
        """)
        last_24h = cursor.fetchone()[0]
        print(f"   📅 Últimas 24 horas: {last_24h} artículos")
        
        # Última semana
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE created_at >= datetime('now', '-7 days')
        """)
        last_week = cursor.fetchone()[0]
        print(f"   📅 Última semana: {last_week} artículos")
        
        # Último mes
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE created_at >= datetime('now', '-30 days')
        """)
        last_month = cursor.fetchone()[0]
        print(f"   📅 Último mes: {last_month} artículos")
        
        print("\n" + "=" * 60)
        print("🎯 ANÁLISIS Y RECOMENDACIONES:")
        
        if new_pending > 0:
            print(f"✅ PRIORIDAD: {new_pending} artículos nuevos necesitan enriquecimiento")
            print("   → El sistema se enfocará en estos primero")
        else:
            print("✅ No hay artículos nuevos pendientes")
        
        if old_pending > 100:
            print(f"⚠️ CUIDADO: {old_pending} artículos antiguos pendientes")
            print("   → El sistema procesará máximo 10 por ciclo para evitar sobrecarga")
        elif old_pending > 0:
            print(f"ℹ️ {old_pending} artículos antiguos pendientes (procesamiento limitado)")
        else:
            print("✅ No hay artículos antiguos pendientes")
        
        percentage_complete = (completed / total_articles * 100) if total_articles > 0 else 0
        print(f"📈 Progreso general: {percentage_complete:.1f}% completado")
        
        if percentage_complete < 50:
            print("🚀 OPTIMIZACIÓN ACTIVADA: Procesamiento acelerado para artículos nuevos")
        else:
            print("✅ Sistema funcionando eficientemente")

def optimize_enrichment():
    """Optimizar artículos muy antiguos marcándolos como omitidos"""
    db_path = "data/geopolitical_intel.db"
    
    print("\n🔧 OPTIMIZANDO SISTEMA DE ENRIQUECIMIENTO...")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Marcar artículos muy antiguos (más de 30 días) como 'skipped' para evitar procesamiento
        cursor.execute("""
            UPDATE articles 
            SET enrichment_status = 'skipped'
            WHERE (enrichment_status IS NULL OR enrichment_status = 'pending')
            AND created_at < datetime('now', '-30 days')
        """)
        
        skipped_count = cursor.rowcount
        conn.commit()
        
        if skipped_count > 0:
            print(f"⚡ Optimización: {skipped_count} artículos antiguos marcados como 'skipped'")
            print("   → Esto acelera el procesamiento enfocándose en contenido reciente")
        else:
            print("✅ No hay artículos antiguos que optimizar")

def reset_error_articles():
    """Reintentar artículos que tuvieron errores"""
    db_path = "data/geopolitical_intel.db"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Reintentar artículos con errores que sean recientes (últimas 7 días)
        cursor.execute("""
            UPDATE articles 
            SET enrichment_status = 'pending'
            WHERE enrichment_status = 'error'
            AND created_at >= datetime('now', '-7 days')
        """)
        
        retry_count = cursor.rowcount
        conn.commit()
        
        if retry_count > 0:
            print(f"🔄 Reintentando {retry_count} artículos recientes que tuvieron errores")
        else:
            print("✅ No hay artículos recientes con errores para reintentar")

if __name__ == "__main__":
    print("🤖 OPTIMIZADOR DEL SISTEMA DE ENRIQUECIMIENTO AUTOMÁTICO")
    print("=" * 60)
    print(f"⏰ Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar estado actual
    check_enrichment_status()
    
    # Optimizar sistema
    optimize_enrichment()
    
    # Reintentar errores recientes
    reset_error_articles()
    
    print("\n" + "=" * 60)
    print("✅ OPTIMIZACIÓN COMPLETADA")
    print("🚀 El sistema ahora se enfocará en artículos nuevos (últimas 48 horas)")
    print("📊 Artículos antiguos se procesan de forma limitada (máx 10 por ciclo)")
    print("⚡ Intervalo optimizado: 1-2 horas para nuevos, 6 horas para mantenimiento")
