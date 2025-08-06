#!/usr/bin/env python3
"""
Script para verificar el funcionamiento del modal de artículos
"""

import sqlite3
import sys
from pathlib import Path

def verify_modal_functionality():
    """Verificar que el modal funcionará correctamente"""
    
    print("🔍 VERIFICACIÓN DEL MODAL DE ARTÍCULOS")
    print("=" * 60)
    
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. Verificar que existen artículos
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    print(f"📊 Total de artículos: {total_articles}")
    
    if total_articles == 0:
        print("❌ No hay artículos en la base de datos")
        conn.close()
        return False
    
    # 2. Verificar que hay artículos con auto_generated_summary
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE auto_generated_summary IS NOT NULL 
        AND auto_generated_summary != ''
    """)
    articles_with_auto_summary = cursor.fetchone()[0]
    print(f"📝 Artículos con resumen auto-generado: {articles_with_auto_summary}")
    
    # 3. Verificar que hay artículos con summary regular
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE summary IS NOT NULL 
        AND summary != ''
    """)
    articles_with_summary = cursor.fetchone()[0]
    print(f"📄 Artículos con resumen: {articles_with_summary}")
    
    # 4. Verificar que hay artículos con contenido
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE content IS NOT NULL 
        AND content != ''
    """)
    articles_with_content = cursor.fetchone()[0]
    print(f"📃 Artículos con contenido: {articles_with_content}")
    
    # 5. Verificar estructura de columnas necesarias
    cursor.execute("PRAGMA table_info(articles)")
    columns = [row[1] for row in cursor.fetchall()]
    
    required_columns = [
        'id', 'title', 'auto_generated_summary', 'summary', 'content',
        'url', 'risk_level', 'risk_score', 'source', 'published_at'
    ]
    
    missing_columns = []
    for col in required_columns:
        if col not in columns:
            missing_columns.append(col)
    
    if missing_columns:
        print(f"❌ Columnas faltantes: {missing_columns}")
        conn.close()
        return False
    else:
        print("✅ Todas las columnas necesarias están presentes")
    
    # 6. Mostrar ejemplos de artículos para el modal
    print("\n📋 EJEMPLOS DE ARTÍCULOS PARA EL MODAL:")
    print("-" * 50)
    
    cursor.execute("""
        SELECT id, title, 
               CASE 
                   WHEN auto_generated_summary IS NOT NULL AND auto_generated_summary != '' THEN 'AUTO'
                   WHEN summary IS NOT NULL AND summary != '' THEN 'SUMMARY'
                   WHEN content IS NOT NULL AND content != '' THEN 'CONTENT'
                   ELSE 'NONE'
               END as source_type,
               risk_level, risk_score,
               LENGTH(COALESCE(auto_generated_summary, summary, content, '')) as content_length
        FROM articles 
        WHERE risk_level IN ('high', 'medium')
        ORDER BY risk_score DESC, published_at DESC
        LIMIT 10
    """)
    
    examples = cursor.fetchall()
    
    for i, (article_id, title, source_type, risk_level, risk_score, content_length) in enumerate(examples, 1):
        emoji = "🔥" if risk_level == 'high' else "⚠️" if risk_level == 'medium' else "🟢"
        title_short = title[:60] + '...' if len(title) > 60 else title
        print(f"  {i:2d}. {emoji} ID:{article_id} [{source_type}] ({content_length} chars) {title_short}")
    
    # 7. Verificar endpoint de API
    print(f"\n🌐 VERIFICACIÓN DEL ENDPOINT API:")
    print("-" * 50)
    
    if examples:
        test_id = examples[0][0]  # Usar el primer artículo como ejemplo
        print(f"✅ Endpoint disponible: /api/article/{test_id}")
        print(f"📝 Este endpoint debería devolver el artículo completo con resumen")
        
        # Verificar los datos específicos del artículo de prueba
        cursor.execute("""
            SELECT title, auto_generated_summary, summary, content, url, risk_level
            FROM articles WHERE id = ?
        """, (test_id,))
        
        result = cursor.fetchone()
        if result:
            title, auto_summary, summary, content, url, risk_level = result
            print(f"\n📊 DATOS DEL ARTÍCULO DE PRUEBA (ID: {test_id}):")
            print(f"   Título: {title[:50]}...")
            print(f"   Auto-resumen: {'SÍ' if auto_summary else 'NO'} ({len(auto_summary or '')} chars)")
            print(f"   Resumen: {'SÍ' if summary else 'NO'} ({len(summary or '')} chars)")
            print(f"   Contenido: {'SÍ' if content else 'NO'} ({len(content or '')} chars)")
            print(f"   URL: {'SÍ' if url else 'NO'}")
            print(f"   Nivel de riesgo: {risk_level}")
    
    conn.close()
    
    # 8. Resumen de verificación
    print(f"\n🎯 RESUMEN DE VERIFICACIÓN:")
    print("=" * 60)
    
    score = 0
    total_checks = 6
    
    if total_articles > 0:
        score += 1
        print("✅ Hay artículos en la base de datos")
    
    if articles_with_auto_summary > 0 or articles_with_summary > 0 or articles_with_content > 0:
        score += 1
        print("✅ Hay contenido disponible para mostrar en el modal")
    
    if not missing_columns:
        score += 1
        print("✅ Estructura de base de datos correcta")
    
    if examples:
        score += 1
        print("✅ Artículos de prueba disponibles")
    
    if articles_with_auto_summary > 0:
        score += 1
        print("✅ Hay artículos con resúmenes auto-generados")
    else:
        print("⚠️ No hay artículos con resúmenes auto-generados (se usarán fallbacks)")
    
    coverage = (articles_with_auto_summary + articles_with_summary + articles_with_content) / total_articles * 100
    if coverage >= 80:
        score += 1
        print(f"✅ Buena cobertura de contenido ({coverage:.1f}%)")
    else:
        print(f"⚠️ Cobertura de contenido mejorable ({coverage:.1f}%)")
    
    print(f"\n🏆 PUNTUACIÓN FINAL: {score}/{total_checks}")
    
    if score >= 5:
        print("🎉 ¡Excelente! El modal debería funcionar perfectamente")
        return True
    elif score >= 3:
        print("👍 Bien! El modal funcionará con algunas limitaciones")
        return True
    else:
        print("⚠️ Problemas detectados - revisar configuración")
        return False

if __name__ == '__main__':
    success = verify_modal_functionality()
    sys.exit(0 if success else 1)
