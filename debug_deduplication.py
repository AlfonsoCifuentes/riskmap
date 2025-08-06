#!/usr/bin/env python3
"""
Script para diagnosticar problemas de deduplicación
"""

import sys
import os
import requests
import json
from datetime import datetime

def test_deduplication_endpoint():
    """Test the deduplication endpoint directly"""
    base_url = "http://localhost:8050"
    
    print("🔍 Diagnosticando sistema de deduplicación...")
    print("=" * 60)
    
    # 1. Probar endpoint de deduplicación
    print("\n1. 📞 Probando endpoint /api/articles/deduplicated...")
    try:
        response = requests.get(f"{base_url}/api/articles/deduplicated?hours=24", timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Respuesta exitosa:")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Hero articles: {1 if data.get('hero') else 0}")
            print(f"   - Mosaic articles: {len(data.get('mosaic', []))}")
            
            stats = data.get('stats', {})
            print(f"   - Total procesados: {stats.get('total_processed', 0)}")
            print(f"   - Duplicados removidos: {stats.get('duplicates_removed', 0)}")
            print(f"   - Artículos únicos: {stats.get('unique_articles', 0)}")
            
            # Mostrar títulos de mosaico para verificar duplicados
            if data.get('mosaic'):
                print(f"\n   📰 Títulos en mosaico:")
                for i, article in enumerate(data.get('mosaic', [])[:10], 1):
                    title = article.get('title', 'Sin título')[:80]
                    risk = article.get('risk_level', 'unknown')
                    print(f"   {i:2d}. [{risk:6s}] {title}")
                    
        else:
            print(f"   ❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ No se puede conectar al servidor en 8050")
        print("   💡 Asegúrate de que el servidor esté ejecutándose")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # 2. Comparar con endpoint regular
    print("\n2. 📞 Comparando con endpoint regular /api/articles...")
    try:
        response = requests.get(f"{base_url}/api/articles?limit=10", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Artículos regulares: {len(data.get('articles', []))}")
            
            if data.get('articles'):
                print(f"   📰 Títulos de artículos regulares:")
                for i, article in enumerate(data.get('articles', [])[:10], 1):
                    title = article.get('title', 'Sin título')[:80]
                    risk = article.get('risk_level', 'unknown')
                    print(f"   {i:2d}. [{risk:6s}] {title}")
        else:
            print(f"   ❌ Error con endpoint regular: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error con endpoint regular: {e}")
    
    # 3. Verificar estado del sistema
    print("\n3. 🔧 Verificando estado del sistema...")
    try:
        response = requests.get(f"{base_url}/api/system-status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ Estado del sistema:")
            print(f"   - Servidor activo: {status.get('server_running', 'Unknown')}")
            if 'components' in status:
                components = status['components']
                print(f"   - Base de datos: {components.get('database', 'Unknown')}")
                print(f"   - Deduplicación: {components.get('news_deduplication_initialized', 'Unknown')}")
        else:
            print(f"   ⚠️ No se puede verificar estado del sistema")
    except Exception as e:
        print(f"   ⚠️ Error verificando estado: {e}")
    
    return True

def check_database_duplicates():
    """Verificar duplicados directamente en la base de datos"""
    print("\n4. 🗃️ Verificando duplicados en la base de datos...")
    
    try:
        import sqlite3
        db_path = "data/geopolitical_intel.db"
        
        if not os.path.exists(db_path):
            print(f"   ❌ Base de datos no encontrada en: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Buscar títulos similares
        cursor.execute("""
            SELECT title, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY title 
            HAVING count > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"   ⚠️ Encontrados {len(duplicates)} títulos duplicados exactos:")
            for title, count, ids in duplicates:
                print(f"   - ({count}x) {title[:70]}... [IDs: {ids}]")
        else:
            print(f"   ✅ No se encontraron títulos duplicados exactos")
        
        # Verificar artículos recientes
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   COUNT(DISTINCT title) as unique_titles,
                   MIN(created_at) as oldest,
                   MAX(created_at) as newest
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
        """)
        
        stats = cursor.fetchone()
        if stats:
            total, unique_titles, oldest, newest = stats
            duplicates_found = total - unique_titles
            print(f"   📊 Estadísticas (últimas 24h):")
            print(f"   - Total artículos: {total}")
            print(f"   - Títulos únicos: {unique_titles}")
            print(f"   - Posibles duplicados: {duplicates_found}")
            print(f"   - Período: {oldest} → {newest}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error verificando base de datos: {e}")

if __name__ == "__main__":
    print("🔍 Diagnóstico del Sistema de Deduplicación")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar diagnósticos
    server_ok = test_deduplication_endpoint()
    
    if server_ok:
        check_database_duplicates()
    
    print("\n" + "=" * 60)
    print("✅ Diagnóstico completado")
