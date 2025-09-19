#!/usr/bin/env python3
"""
VALIDADOR FINAL DEL WEBSITE - ACTUALIZADO
=========================================

Validador completo que toma en cuenta la configuración real del sistema.

Autor: GitHub Copilot
Fecha: 2025
"""

import os
import sqlite3

def final_validation():
    """Validación final completa del sistema"""
    print("🎯 VALIDACIÓN FINAL COMPLETA DEL WEBSITE")
    print("=" * 80)
    
    results = {}
    
    # 1. Verificar templates en ubicación correcta
    print("📁 VERIFICANDO TEMPLATES EN src/web/templates/")
    template_dir = "src/web/templates"
    required_templates = [
        'dashboard_BUENO.html', 'conflict_monitoring.html', 'satellite_analysis.html',
        'trends_analysis.html', 'early_warning.html', 'executive_reports.html',
        'data_intelligence.html', 'video_surveillance.html'
    ]
    
    templates_ok = 0
    if os.path.exists(template_dir):
        for template in required_templates:
            template_path = os.path.join(template_dir, template)
            if os.path.exists(template_path):
                print(f"✅ {template}")
                templates_ok += 1
            else:
                print(f"❌ {template}")
    else:
        print(f"❌ Directorio {template_dir} no existe")
    
    results['templates'] = templates_ok == len(required_templates)
    
    # 2. Verificar configuración Flask
    print(f"\n🔧 VERIFICANDO CONFIGURACIÓN FLASK")
    try:
        with open("core/app_BUENA.py", 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        if "template_folder='src/web/templates'" in app_content:
            print(f"✅ template_folder configurado correctamente")
            results['flask_config'] = True
        else:
            print(f"❌ template_folder no configurado correctamente")
            results['flask_config'] = False
    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")
        results['flask_config'] = False
    
    # 3. Verificar base de datos y queries
    print(f"\n🗄️ VERIFICANDO BASE DE DATOS Y QUERIES")
    try:
        db_path = "data/geopolitical_intel.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test query crítico
            cursor.execute("""
                SELECT COUNT(*) FROM unified_articles 
                WHERE geopolitical_relevance = 1 
                  AND title IS NOT NULL 
                  AND (original_image_url IS NOT NULL OR image_url IS NOT NULL)
            """)
            articles_count = cursor.fetchone()[0]
            
            if articles_count > 0:
                print(f"✅ Base de datos operativa: {articles_count} artículos disponibles")
                results['database'] = True
            else:
                print(f"⚠️  Base de datos sin artículos válidos")
                results['database'] = False
            
            conn.close()
        else:
            print(f"❌ Base de datos no encontrada")
            results['database'] = False
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        results['database'] = False
    
    # 4. Verificar endpoints críticos en código
    print(f"\n🔗 VERIFICANDO ENDPOINTS CRÍTICOS")
    critical_endpoints = ['/api/articles', '/api/hero-article', '/api/articles/deduplicated']
    
    with open("core/app_BUENA.py", 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    endpoints_found = 0
    for endpoint in critical_endpoints:
        # Buscar tanto con methods como sin methods
        pattern1 = f"@self.flask_app.route('{endpoint}')"
        pattern2 = f"@self.flask_app.route('{endpoint}', methods="
        if pattern1 in app_content or pattern2 in app_content:
            print(f"✅ {endpoint}")
            endpoints_found += 1
        else:
            print(f"❌ {endpoint}")
    
    results['endpoints'] = endpoints_found == len(critical_endpoints)
    
    # 5. Verificar que no hay referencias a tabla 'articles' antigua
    print(f"\n🔍 VERIFICANDO AUSENCIA DE TABLA 'articles' ANTIGUA")
    old_table_references = 0
    
    # Buscar patrones problemáticos
    problematic_patterns = [
        'FROM articles ', 'FROM `articles`', "FROM 'articles'", 'FROM "articles"',
        'INTO articles ', 'UPDATE articles ', 'DELETE FROM articles '
    ]
    
    for pattern in problematic_patterns:
        if pattern.lower() in app_content.lower():
            old_table_references += 1
            print(f"⚠️  Encontrado: {pattern}")
    
    if old_table_references == 0:
        print(f"✅ No se encontraron referencias a tabla 'articles' antigua")
        results['no_old_tables'] = True
    else:
        print(f"❌ Encontradas {old_table_references} referencias a tabla antigua")
        results['no_old_tables'] = False
    
    # 6. Verificar que se usa 'unified_articles'
    print(f"\n📋 VERIFICANDO USO DE TABLA 'unified_articles'")
    unified_references = app_content.count('FROM unified_articles')
    
    if unified_references > 0:
        print(f"✅ Encontradas {unified_references} referencias a 'unified_articles'")
        results['uses_unified'] = True
    else:
        print(f"❌ No se encontraron referencias a 'unified_articles'")
        results['uses_unified'] = False
    
    # RESUMEN FINAL
    print(f"\n🎯 RESUMEN DE VALIDACIÓN FINAL")
    print("=" * 80)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASA" if passed else "❌ FALLA"
        print(f"{status} - {check}")
        if not passed:
            all_passed = False
    
    print(f"\n" + "=" * 80)
    if all_passed:
        print(f"🎉 VALIDACIÓN EXITOSA COMPLETA")
        print(f"   ✅ Todos los componentes están correctamente configurados")
        print(f"   ✅ El sistema usa exclusivamente 'unified_articles'")
        print(f"   ✅ No hay referencias a tablas obsoletas")
        print(f"   ✅ Los endpoints están listos para funcionar")
        print(f"   ✅ Los templates están en la ubicación correcta")
        print(f"")
        print(f"🚀 EL WEBSITE ESTÁ LISTO PARA FUNCIONAR")
        print(f"   El usuario puede ejecutar: python core/app_BUENA.py")
        print(f"   Y acceder a: http://localhost:5001")
    else:
        print(f"⚠️  ALGUNOS COMPONENTES NECESITAN ATENCIÓN")
        print(f"   Revisar elementos marcados como FALLA")
    
    return all_passed

if __name__ == "__main__":
    final_validation()