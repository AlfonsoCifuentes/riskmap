#!/usr/bin/env python3
"""
Script para comprobar el número de artículos en la base de datos RiskMap
"""

import sqlite3
import os
from datetime import datetime

def check_article_count():
    """Comprueba cuántos artículos hay en la base de datos"""
    
    # Ruta de la base de datos
    db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verificando estructura de la base de datos...")
        
        # Verificar qué tablas existen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%article%'")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No se encontraron tablas de artículos")
            return
        
        print(f"📊 Tablas de artículos encontradas: {[table[0] for table in tables]}")
        
        total_articles = 0
        
        for table in tables:
            table_name = table[0]
            try:
                # Contar artículos en cada tabla
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   📰 Tabla '{table_name}': {count:,} artículos")
                total_articles += count
                
                # Obtener información adicional si es la tabla principal
                if 'article' in table_name.lower():
                    # Fecha del artículo más antiguo
                    cursor.execute(f"SELECT MIN(published_at), MAX(published_at) FROM {table_name} WHERE published_at IS NOT NULL")
                    date_range = cursor.fetchone()
                    
                    if date_range[0] and date_range[1]:
                        print(f"      📅 Rango de fechas: {date_range[0]} → {date_range[1]}")
                    
                    # Contar por estado de procesamiento si existe la columna
                    try:
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [column[1] for column in cursor.fetchall()]
                        
                        if 'processed' in columns:
                            cursor.execute(f"SELECT processed, COUNT(*) FROM {table_name} GROUP BY processed")
                            processed_stats = cursor.fetchall()
                            for processed, count in processed_stats:
                                status = "✅ Procesados" if processed else "⏳ Pendientes"
                                print(f"      {status}: {count:,}")
                        
                        if 'sentiment_score' in columns:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE sentiment_score IS NOT NULL")
                            sentiment_count = cursor.fetchone()[0]
                            print(f"      🤖 Con análisis de sentimiento: {sentiment_count:,}")
                        
                        if 'importance_score' in columns:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE importance_score IS NOT NULL")
                            importance_count = cursor.fetchone()[0]
                            print(f"      ⭐ Con puntuación de importancia: {importance_count:,}")
                    
                    except sqlite3.Error as e:
                        print(f"      ⚠️ No se pudo obtener estadísticas detalladas: {e}")
                
            except sqlite3.Error as e:
                print(f"   ❌ Error al consultar tabla '{table_name}': {e}")
        
        print(f"\n📈 TOTAL DE ARTÍCULOS EN LA BASE DE DATOS: {total_articles:,}")
        
        # Información adicional del archivo de base de datos
        db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        db_modified = datetime.fromtimestamp(os.path.getmtime(db_path))
        
        print(f"💾 Tamaño de la base de datos: {db_size:.2f} MB")
        print(f"🕒 Última modificación: {db_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except sqlite3.Error as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("✅ Conexión cerrada")

if __name__ == "__main__":
    print("🔍 Comprobando artículos en la base de datos RiskMap...")
    print("=" * 60)
    check_article_count()
