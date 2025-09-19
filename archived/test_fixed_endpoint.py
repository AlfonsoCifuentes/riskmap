#!/usr/bin/env python3
"""
Test del endpoint de artículos después de aplicar filtros de imágenes reales
"""
import sqlite3
import requests
import json
import time
from datetime import datetime

def test_database_articles():
    """Probar directamente la base de datos con los nuevos filtros"""
    print("🔍 Probando consulta SQL con filtros de imágenes reales...")
    
    try:
        # Usar la misma lógica que app_BUENA.py
        db_path = "./data/geopolitical_intel.db"
        
        query = """
            SELECT 
                id, title, 
                CASE 
                    WHEN summary IS NOT NULL AND summary != '' AND summary NOT LIKE '%<think>%' THEN 
                        summary
                    WHEN auto_generated_summary IS NOT NULL AND auto_generated_summary != '' AND auto_generated_summary NOT LIKE '%<think>%' THEN 
                        auto_generated_summary
                    WHEN content IS NOT NULL AND content != '' AND content NOT LIKE '%<think>%' THEN 
                        SUBSTR(content, 1, 300) || '...'
                    ELSE 
                        'Análisis de contenido geopolítico disponible para revisión.'
                END as summary,
                url, source, published_at, country, region, risk_level, 
                conflict_type, sentiment_score, risk_score,
                image_url,
                ai_importance
            FROM articles 
            WHERE 
                -- Campos básicos requeridos
                title IS NOT NULL AND title != '' AND
                content IS NOT NULL AND content != '' AND
                
                -- Solo artículos con imágenes reales (no placeholders)
                image_url IS NOT NULL AND image_url != '' AND
                image_url NOT LIKE '%placeholder%' AND
                image_url NOT LIKE '%picsum.photos%' AND
                image_url NOT LIKE '%via.placeholder%' AND
                
                -- Riesgo válido
                risk_score >= 0.0 AND
                
                -- Excluir artículos HERO (solo para mosaic)
                (content NOT LIKE '%HERO ARTICLE%' OR content IS NULL) AND
                (title NOT LIKE '%HERO%' OR title IS NULL)
            ORDER BY ai_importance DESC, published_at DESC
            LIMIT 10
        """
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            articles = [dict(row) for row in cursor.fetchall()]
            
        print(f"✅ Encontrados {len(articles)} artículos con imágenes reales")
        
        for article in articles[:3]:  # Mostrar solo 3 primeros
            print(f"- ID: {article['id']}")
            print(f"  Título: {article['title'][:80]}...")
            print(f"  Imagen: {article['image_url']}")
            print(f"  Summary: {article['summary'][:100]}...")
            print(f"  Risk Score: {article['risk_score']}")
            print()
            
        return len(articles) > 0
        
    except Exception as e:
        print(f"❌ Error en consulta SQL: {e}")
        return False

def test_api_endpoint():
    """Probar el endpoint /api/articles"""
    print("\n🌐 Probando endpoint /api/articles...")
    
    try:
        url = "http://localhost:5001/api/articles?limit=10"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"✅ Endpoint funcionando: {len(articles)} artículos retornados")
            
            # Verificar que no hay placeholders
            placeholder_count = 0
            think_count = 0
            
            for article in articles[:3]:  # Verificar primeros 3
                image_url = article.get('image', '') or article.get('image_url', '')
                summary = article.get('summary', '')
                content = article.get('content', '')
                
                print(f"- ID: {article.get('id')}")
                print(f"  Título: {article.get('title', '')[:80]}...")
                print(f"  Imagen: {image_url}")
                
                # Verificar placeholders
                if any(x in image_url.lower() for x in ['placeholder', 'picsum', 'via.placeholder']):
                    placeholder_count += 1
                    print(f"  ⚠️  PLACEHOLDER DETECTADO")
                
                # Verificar <think>
                if '<think>' in summary or '<think>' in content:
                    think_count += 1
                    print(f"  ⚠️  <THINK> DETECTADO")
                
                print(f"  Summary: {summary[:100]}...")
                print(f"  Risk Score: {article.get('risk_score', 0)}")
                print()
            
            print(f"\n📊 Resultados:")
            print(f"- Total artículos: {len(articles)}")
            print(f"- Placeholders encontrados: {placeholder_count}")
            print(f"- Texto <think> encontrado: {think_count}")
            
            return len(articles) > 0 and placeholder_count == 0 and think_count == 0
            
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en endpoint: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🧪 TESTING: Endpoint corregido con filtros de imágenes reales")
    print("=" * 60)
    
    # Prueba 1: Base de datos directa
    db_ok = test_database_articles()
    
    # Prueba 2: API endpoint  
    api_ok = test_api_endpoint()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS:")
    print(f"- Consulta SQL: {'✅ OK' if db_ok else '❌ FALLO'}")
    print(f"- API Endpoint: {'✅ OK' if api_ok else '❌ FALLO'}")
    
    if db_ok and api_ok:
        print("\n🎉 TODAS LAS PRUEBAS EXITOSAS: Solo artículos con imágenes reales")
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON: Revisar filtros")

if __name__ == "__main__":
    main()