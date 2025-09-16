#!/usr/bin/env python3
"""
Script para probar el endpoint /api/articles después de las correcciones
"""

import sqlite3
import requests
from pathlib import Path
import json
import time

def test_database_direct():
    """Test directo de la base de datos"""
    print("🔍 Testing base de datos directamente...")
    
    db_path = Path("./data/geopolitical_intel.db")
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return False
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            # Test el mismo SQL que usa el endpoint
            query = """
                SELECT id, title, 
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
                    CASE 
                        WHEN image_url IS NOT NULL AND image_url != '' THEN image_url
                        ELSE 'https://picsum.photos/400/200?random=1'
                    END as image_url,
                    ai_importance
                FROM articles 
                WHERE 
                    title IS NOT NULL AND title != '' AND
                    published_at IS NOT NULL
                ORDER BY published_at DESC 
                LIMIT 5
            """
            
            cursor = conn.execute(query)
            results = cursor.fetchall()
            
            print(f"✅ Base de datos retorna {len(results)} artículos")
            
            for i, row in enumerate(results[:3]):
                title = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
                summary = row[2][:50] + "..." if len(row[2]) > 50 else row[2]
                image_url = row[12]
                
                print(f"📰 Artículo {i+1}:")
                print(f"  - Título: {title}")
                print(f"  - Summary: {summary}")
                print(f"  - Image: {image_url}")
                
                # Check for problematic content
                if '<think>' in row[2]:
                    print(f"  ❌ PROBLEMA: Summary contiene <think>")
                else:
                    print(f"  ✅ Summary limpio")
                    
                if 'via.placeholder.com' in row[12]:
                    print(f"  ❌ PROBLEMA: Usando URL de placeholder problemática")
                elif 'picsum.photos' in row[12]:
                    print(f"  ✅ Usando placeholder corregido")
                else:
                    print(f"  ✅ Imagen real")
                    
                print()
            
            return len(results) > 0
    
    except Exception as e:
        print(f"❌ Error en test de BD: {e}")
        return False

def test_api_endpoint():
    """Test del endpoint de API"""
    print("🌐 Testing endpoint /api/articles...")
    
    try:
        response = requests.get('http://localhost:5001/api/articles', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"✅ API retorna {len(articles)} artículos")
            
            for i, article in enumerate(articles[:3]):
                title = article.get('title', '')[:50] + "..." if len(article.get('title', '')) > 50 else article.get('title', '')
                summary = article.get('summary', '')[:50] + "..." if len(article.get('summary', '')) > 50 else article.get('summary', '')
                image_url = article.get('image_url', '')
                
                print(f"📰 Artículo {i+1}:")
                print(f"  - Título: {title}")
                print(f"  - Summary: {summary}")
                print(f"  - Image: {image_url}")
                
                # Check for problematic content
                if '<think>' in summary:
                    print(f"  ❌ PROBLEMA: Summary contiene <think>")
                else:
                    print(f"  ✅ Summary limpio")
                    
                if 'via.placeholder.com' in image_url:
                    print(f"  ❌ PROBLEMA: Usando URL de placeholder problemática")
                elif 'picsum.photos' in image_url:
                    print(f"  ✅ Usando placeholder corregido")
                else:
                    print(f"  ✅ Imagen real")
                    
                print()
            
            return len(articles) > 0
            
        else:
            print(f"❌ API retorna status code {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
    
    except requests.ConnectionError:
        print("❌ No se puede conectar al servidor (¿está corriendo?)")
        return False
    except Exception as e:
        print(f"❌ Error en test de API: {e}")
        return False

def main():
    """Test principal"""
    print("🧪 TESTING CORRECCIONES DE CONTENIDO Y API")
    print("=" * 50)
    
    # Test BD
    db_ok = test_database_direct()
    print()
    
    # Test API
    print("Esperando que el servidor esté listo...")
    time.sleep(2)
    api_ok = test_api_endpoint()
    print()
    
    # Resumen
    print("📋 RESUMEN:")
    print(f"  Base de datos: {'✅' if db_ok else '❌'}")
    print(f"  API endpoint: {'✅' if api_ok else '❌'}")
    
    if db_ok and api_ok:
        print("\n🎉 ¡TODAS LAS CORRECCIONES FUNCIONANDO!")
        print("✅ El frontend debería cargar correctamente")
        print("✅ Las imágenes placeholder deberían funcionar")
        print("✅ Los summaries deberían estar limpios")
    else:
        print("\n⚠️  Hay problemas que requieren atención")

if __name__ == "__main__":
    main()