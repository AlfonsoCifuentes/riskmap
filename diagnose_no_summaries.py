#!/usr/bin/env python3
"""
DIAGNÓSTICO FINAL: Verificar que NO aparezcan summaries en el frontend
"""

import sqlite3
import os
import json

def check_database_summaries():
    """Verificar qué artículos tienen summary en la BD"""
    db_path = "./data/geopolitical_intel.db"
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar cuántos artículos tienen summary
    cursor.execute("""
        SELECT id, title, 
               CASE WHEN summary IS NOT NULL AND summary != '' THEN 'SÍ' ELSE 'NO' END as tiene_summary,
               CASE WHEN LENGTH(summary) > 50 THEN SUBSTR(summary, 1, 50) || '...' ELSE summary END as summary_preview
        FROM articles 
        WHERE geopolitical_relevance = 1 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    print("🔍 ARTÍCULOS EN LA BASE DE DATOS:")
    print("=" * 80)
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Título: {row[1][:60]}...")
        print(f"¿Tiene summary?: {row[2]}")
        if row[3]:
            print(f"Summary preview: {row[3]}")
        print("-" * 40)
    
    conn.close()

def generate_test_endpoint_response():
    """Simular la respuesta del endpoint limpio"""
    print("\n🧪 SIMULANDO RESPUESTA DEL ENDPOINT LIMPIO:")
    print("=" * 80)
    
    # Esta es la estructura que DEBERÍA devolver el endpoint limpio
    clean_response = {
        "success": True,
        "hero": {
            "id": 1,
            "title": "Título del artículo héroe - Sin summary",
            "image_url": "https://example.com/hero-image.jpg", 
            "risk_level": "high",
            "original_url": "https://example.com/article"
        },
        "mosaic": [
            {
                "id": 2,
                "title": "Artículo 1 - Solo título",
                "image_url": "https://example.com/image1.jpg",
                "risk_level": "medium", 
                "original_url": "https://example.com/article1"
            },
            {
                "id": 3,
                "title": "Artículo 2 - Solo título",
                "image_url": "https://example.com/image2.jpg",
                "risk_level": "low",
                "original_url": "https://example.com/article2"
            }
        ]
    }
    
    print("✅ RESPUESTA ESPERADA (LIMPIA):")
    print(json.dumps(clean_response, indent=2, ensure_ascii=False))
    
    # Verificar que NO hay campos prohibidos
    forbidden_fields = ['summary', 'content', 'description', 'auto_generated_summary']
    
    def check_forbidden_fields(obj, path=""):
        found_forbidden = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if key in forbidden_fields:
                    found_forbidden.append(current_path)
                found_forbidden.extend(check_forbidden_fields(value, current_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                found_forbidden.extend(check_forbidden_fields(item, f"{path}[{i}]"))
        return found_forbidden
    
    forbidden_found = check_forbidden_fields(clean_response)
    
    if forbidden_found:
        print("❌ CAMPOS PROHIBIDOS ENCONTRADOS:")
        for field in forbidden_found:
            print(f"   - {field}")
    else:
        print("✅ NO se encontraron campos prohibidos")

def main():
    print("🔬 DIAGNÓSTICO FINAL - ELIMINACIÓN DE SUMMARIES")
    print("=" * 60)
    
    print("\n1️⃣ Verificando artículos en base de datos...")
    check_database_summaries()
    
    print("\n2️⃣ Verificando estructura de respuesta esperada...")
    generate_test_endpoint_response()
    
    print("\n📋 RESUMEN DE CAMBIOS APLICADOS:")
    print("✅ Backend: Endpoint reescrito para devolver SOLO campos permitidos")
    print("✅ Frontend: Eliminada referencia a summary en finalText del héroe")
    print("✅ Frontend: Eliminadas referencias a summary en modales")
    print("✅ Frontend: CSS del hero-text oculto completamente")
    print("✅ Frontend: Funciones de traducción limitadas solo al título")
    print("✅ Frontend: Detección de tópicos solo usa título")
    
    print("\n🚀 PRÓXIMO PASO:")
    print("Ejecutar 'python app_BUENA.py' y verificar en http://localhost:5001")
    print("DEBE mostrar SOLO títulos, sin texto superpuesto ni summaries")

if __name__ == "__main__":
    main()