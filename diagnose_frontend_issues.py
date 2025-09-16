#!/usr/bin/env python3
"""
Análisis directo de la base de datos para identificar problemas
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta

def analyze_database():
    """Analizar directamente la base de datos"""
    print("🔍 ANÁLISIS DIRECTO DE LA BASE DE DATOS")
    print("=" * 60)
    
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabla articles
        print("\n📊 ANÁLISIS DE TABLA ARTICLES")
        print("-" * 40)
        
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        print(f"Total artículos: {total_articles}")
        
        if total_articles == 0:
            print("⚠️ No hay artículos en la base de datos")
            print("💡 Esto explica por qué el frontend no muestra contenido")
            return
        
        # Artículos con imágenes
        cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ''")
        with_images = cursor.fetchone()[0]
        print(f"Con imágenes: {with_images}")
        
        # Artículos recientes (últimas 24h)
        cutoff = datetime.now() - timedelta(hours=24)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT COUNT(*) FROM articles WHERE pub_date >= ?", (cutoff_str,))
        recent_articles = cursor.fetchone()[0]
        print(f"Recientes (24h): {recent_articles}")
        
        # Artículos recientes con imágenes
        cursor.execute("SELECT COUNT(*) FROM articles WHERE pub_date >= ? AND image_url IS NOT NULL AND image_url != ''", (cutoff_str,))
        recent_with_images = cursor.fetchone()[0]
        print(f"Recientes con imágenes: {recent_with_images}")
        
        # Mostrar algunos ejemplos
        print("\n📰 EJEMPLOS DE ARTÍCULOS RECIENTES:")
        print("-" * 40)
        cursor.execute("""
            SELECT title, source_name, pub_date, 
                   CASE WHEN image_url IS NULL OR image_url = '' THEN 'Sin imagen' ELSE 'Con imagen' END as image_status
            FROM articles 
            WHERE pub_date >= ? 
            ORDER BY pub_date DESC 
            LIMIT 5
        """, (cutoff_str,))
        
        for i, row in enumerate(cursor.fetchall(), 1):
            title, source, pub_date, image_status = row
            print(f"{i}. {title[:50]}...")
            print(f"   Fuente: {source}")
            print(f"   Fecha: {pub_date}")
            print(f"   Imagen: {image_status}")
            print()
        
        # Verificar esquema
        print("🔧 ESQUEMA DE LA TABLA:")
        print("-" * 40)
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"• {col[1]} ({col[2]})")
        
        # Estadísticas de fuentes
        print("\n📡 FUENTES DE ARTÍCULOS:")
        print("-" * 40)
        cursor.execute("""
            SELECT source_name, COUNT(*) as count 
            FROM articles 
            WHERE pub_date >= ? 
            GROUP BY source_name 
            ORDER BY count DESC 
            LIMIT 10
        """, (cutoff_str,))
        
        for source, count in cursor.fetchall():
            print(f"• {source}: {count} artículos")
        
        conn.close()
        
        # Diagnóstico final
        print("\n🎯 DIAGNÓSTICO:")
        print("-" * 40)
        
        if total_articles == 0:
            print("❌ PROBLEMA PRINCIPAL: No hay artículos")
            print("💡 Solución: Ejecutar el ingestion de datos")
        elif recent_articles == 0:
            print("⚠️ PROBLEMA: No hay artículos recientes")
            print("💡 Solución: Verificar el sistema de ingestion automática")
        elif recent_with_images == 0:
            print("⚠️ PROBLEMA: Los artículos recientes no tienen imágenes")
            print("💡 Esto puede hacer que el mosaico aparezca vacío")
            print("💡 El sistema debería usar imágenes por defecto")
        else:
            print("✅ Hay artículos recientes con imágenes")
            print("💡 El problema podría estar en la lógica de deduplicación")
            
    except Exception as e:
        print(f"❌ Error analizando base de datos: {e}")

def create_test_solution():
    """Crear solución para el problema"""
    print("\n🛠️ CREANDO SOLUCIÓN")
    print("=" * 60)
    
    solution = """
RESUMEN DEL PROBLEMA:
- Error 1: Favicon 404 (no existe archivo favicon.ico)
- Error 2: Frontend no puede cargar artículos deduplicados
- Error 3: El endpoint /api/articles/deduplicated retorna mosaico vacío

SOLUCIONES IMPLEMENTADAS:
1. ✅ Favicon creado automáticamente en app_DIAGNOSTIC.py
2. ✅ Endpoint simplificado que siempre retorna artículos
3. ✅ Lógica de fallback mejorada

PRÓXIMOS PASOS:
1. Verificar que hay artículos en la base de datos
2. Si no hay artículos, ejecutar ingestion de datos
3. Ajustar criterios de deduplicación en la app principal
4. Copiar el favicon al proyecto principal
"""
    
    print(solution)
    
    # Verificar si necesitamos ejecutar ingestion
    db_path = "./data/geopolitical_intel.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles WHERE pub_date >= ?", 
                      ((datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),))
        recent = cursor.fetchone()[0]
        conn.close()
        
        if recent < 5:
            print("\n🚨 ACCIÓN REQUERIDA:")
            print("Hay muy pocos artículos recientes.")
            print("Ejecuta uno de estos comandos para obtener datos:")
            print("• python -c \"from src.data.rss_ingestion import RSSIngestion; RSSIngestion().process_all_feeds()\"")
            print("• python automation_block_1.py")
            print("• Esperar a que el proceso automático se ejecute")

def main():
    """Función principal"""
    print("🚀 DIAGNÓSTICO COMPLETO DEL PROBLEMA FRONTEND")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    analyze_database()
    create_test_solution()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN EJECUTIVO:")
    print("• El problema principal es la falta de artículos que cumplan")
    print("  criterios específicos para deduplicación (imagen + idioma)")
    print("• La aplicación de diagnóstico resuelve esto simplificando")
    print("  los criterios y siempre retornando artículos")
    print("• El favicon se crea automáticamente")
    print("• Para la aplicación principal, necesitas:")
    print("  1. Copiar la lógica de fallback")
    print("  2. Crear static/favicon.ico")
    print("  3. Asegurar que hay artículos en la base de datos")

if __name__ == "__main__":
    main()