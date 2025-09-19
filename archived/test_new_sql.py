#!/usr/bin/env python3
"""
Test del endpoint después de permitir artículos con placeholder válido
"""
import sqlite3
import requests
import json
import time

def test_new_sql_logic():
    """Probar la nueva lógica SQL que permite todos los artículos"""
    print("🔍 Probando nueva lógica SQL (permite todos los artículos)...")
    
    try:
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
                CASE 
                    WHEN image_url IS NOT NULL AND image_url != '' AND image_url NOT LIKE '%via.placeholder%' THEN 
                        image_url
                    ELSE 
                        'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=200&fit=crop'
                END as image_url,
                ai_importance
            FROM articles 
            WHERE 
                -- Campos básicos requeridos
                title IS NOT NULL AND title != '' AND
                content IS NOT NULL AND content != '' AND
                
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
            
        print(f"✅ Encontrados {len(articles)} artículos")
        
        # Verificar contenido de los primeros artículos
        think_count = 0
        placeholder_count = 0
        
        for i, article in enumerate(articles[:5]):
            print(f"\n📰 Artículo {i+1}:")
            print(f"  ID: {article['id']}")
            print(f"  Título: {article['title'][:80]}...")
            
            summary = article['summary']
            image_url = article['image_url']
            
            # Verificar <think>
            if '<think>' in summary:
                think_count += 1
                print(f"  ⚠️  CONTIENE <think> EN SUMMARY")
            
            # Verificar placeholder
            if 'via.placeholder' in image_url:
                placeholder_count += 1
                print(f"  ⚠️  USA VIA.PLACEHOLDER")
            elif 'unsplash' in image_url:
                print(f"  ✅ Usando Unsplash (placeholder válido)")
            
            print(f"  Summary: {summary[:100]}...")
            print(f"  Imagen: {image_url}")
            print(f"  Risk: {article['risk_score']}")
        
        print(f"\n📊 Verificaciones:")
        print(f"- Total artículos: {len(articles)}")
        print(f"- Con texto <think>: {think_count}")
        print(f"- Con via.placeholder: {placeholder_count}")
        
        return len(articles) > 0 and think_count == 0
        
    except Exception as e:
        print(f"❌ Error en consulta SQL: {e}")
        return False

def test_unsplash_url():
    """Verificar que la URL de Unsplash carga correctamente"""
    print("\n🖼️  Probando URL de Unsplash...")
    
    try:
        url = "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=200&fit=crop"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ URL de Unsplash funciona correctamente")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Content-Length: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Unsplash devolvió {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error con Unsplash: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🧪 TESTING: Nuevo SQL con placeholder válido")
    print("=" * 60)
    
    # Prueba 1: Nueva lógica SQL
    sql_ok = test_new_sql_logic()
    
    # Prueba 2: URL de Unsplash
    unsplash_ok = test_unsplash_url()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print(f"- SQL Logic: {'✅ OK' if sql_ok else '❌ FALLO'}")
    print(f"- Unsplash URL: {'✅ OK' if unsplash_ok else '❌ FALLO'}")
    
    if sql_ok and unsplash_ok:
        print("\n🎉 LISTO PARA PROBAR EL FRONTEND")
        print("💡 Siguiente: iniciar app_BUENA.py y probar /api/articles")
    else:
        print("\n⚠️  REVISAR ERRORES ANTES DE CONTINUAR")

if __name__ == "__main__":
    main()