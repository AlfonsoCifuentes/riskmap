#!/usr/bin/env python3
"""
Script detallado para analizar la base de datos geopolitical_intel.db
"""

import sqlite3
import os
from datetime import datetime

def analyze_geopolitical_db():
    """Análisis detallado de la base de datos geopolitical_intel.db"""
    
    db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 ANÁLISIS DETALLADO DE LA BASE DE DATOS GEOPOLITICAL_INTEL")
        print("=" * 70)
        
        # Obtener información de la tabla articles
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        
        print("\n🏗️ ESTRUCTURA DE LA TABLA 'articles':")
        for col in columns:
            print(f"   • {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # Contar total de artículos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_count = cursor.fetchone()[0]
        print(f"\n📰 TOTAL DE ARTÍCULOS: {total_count:,}")
        
        # Estadísticas por columnas disponibles
        column_names = [col[1] for col in columns]
        
        if 'date' in column_names:
            print("\n📅 ESTADÍSTICAS POR FECHA:")
            cursor.execute("SELECT MIN(date), MAX(date) FROM articles WHERE date IS NOT NULL")
            date_range = cursor.fetchone()
            if date_range[0] and date_range[1]:
                print(f"   • Rango: {date_range[0]} → {date_range[1]}")
            
            cursor.execute("SELECT date, COUNT(*) FROM articles WHERE date IS NOT NULL GROUP BY date ORDER BY COUNT(*) DESC LIMIT 10")
            top_dates = cursor.fetchall()
            if top_dates:
                print("   • Top 10 fechas con más artículos:")
                for date, count in top_dates:
                    print(f"     - {date}: {count:,} artículos")
        
        if 'source' in column_names:
            print("\n📰 ESTADÍSTICAS POR FUENTE:")
            cursor.execute("SELECT source, COUNT(*) FROM articles WHERE source IS NOT NULL GROUP BY source ORDER BY COUNT(*) DESC LIMIT 10")
            top_sources = cursor.fetchall()
            if top_sources:
                for source, count in top_sources:
                    print(f"   • {source}: {count:,} artículos")
        
        if 'country' in column_names:
            print("\n🌍 ESTADÍSTICAS POR PAÍS:")
            cursor.execute("SELECT country, COUNT(*) FROM articles WHERE country IS NOT NULL GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10")
            top_countries = cursor.fetchall()
            if top_countries:
                for country, count in top_countries:
                    print(f"   • {country}: {count:,} artículos")
        
        if 'risk_level' in column_names:
            print("\n⚠️ ESTADÍSTICAS POR NIVEL DE RIESGO:")
            cursor.execute("SELECT risk_level, COUNT(*) FROM articles WHERE risk_level IS NOT NULL GROUP BY risk_level ORDER BY COUNT(*) DESC")
            risk_levels = cursor.fetchall()
            if risk_levels:
                for level, count in risk_levels:
                    print(f"   • {level}: {count:,} artículos")
        
        if 'sentiment_label' in column_names:
            print("\n😊 ESTADÍSTICAS DE SENTIMIENTO:")
            cursor.execute("SELECT sentiment_label, COUNT(*) FROM articles WHERE sentiment_label IS NOT NULL GROUP BY sentiment_label ORDER BY COUNT(*) DESC")
            sentiments = cursor.fetchall()
            if sentiments:
                for sentiment, count in sentiments:
                    print(f"   • {sentiment}: {count:,} artículos")
        
        if 'processed' in column_names:
            print("\n🔄 ESTADO DE PROCESAMIENTO:")
            cursor.execute("SELECT processed, COUNT(*) FROM articles GROUP BY processed")
            processed_stats = cursor.fetchall()
            for processed, count in processed_stats:
                status = "✅ Procesados" if processed else "⏳ Pendientes"
                print(f"   • {status}: {count:,} artículos")
        
        # Estadísticas de contenido
        print("\n📝 ESTADÍSTICAS DE CONTENIDO:")
        if 'title' in column_names:
            cursor.execute("SELECT COUNT(*) FROM articles WHERE title IS NOT NULL AND title != ''")
            titles_count = cursor.fetchone()[0]
            print(f"   • Artículos con título: {titles_count:,}")
        
        if 'content' in column_names:
            cursor.execute("SELECT COUNT(*) FROM articles WHERE content IS NOT NULL AND content != ''")
            content_count = cursor.fetchone()[0]
            print(f"   • Artículos con contenido: {content_count:,}")
        
        if 'summary' in column_names:
            cursor.execute("SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary != ''")
            summary_count = cursor.fetchone()[0]
            print(f"   • Artículos con resumen: {summary_count:,}")
        
        # Información del archivo
        db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        db_modified = datetime.fromtimestamp(os.path.getmtime(db_path))
        
        print(f"\n💾 INFORMACIÓN DEL ARCHIVO:")
        print(f"   • Tamaño: {db_size:.2f} MB")
        print(f"   • Última modificación: {db_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except sqlite3.Error as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("\n✅ Análisis completado")

if __name__ == "__main__":
    analyze_geopolitical_db()
