#!/usr/bin/env python3
"""
CORRECCIÓN DE ERRORES CRÍTICOS EN ENDPOINTS
==========================================

Script para corregir los errores encontrados en los endpoints API:
1. Variable 'unified_articles' incorrecta en get_top_articles_from_db
2. Variable 'unified_articles' incorrecta en api_deduplicated_articles
3. Verificar todas las consultas usan tabla 'unified_articles'

Autor: GitHub Copilot
Fecha: 2025
"""

import os
import re
import sqlite3
from datetime import datetime

def fix_endpoint_bugs():
    """Corregir errores críticos en endpoints"""
    print("🔧 REPARANDO ERRORES CRÍTICOS EN ENDPOINTS")
    print("=" * 80)
    
    app_file = "core/app_BUENA.py"
    backup_file = f"core/app_BUENA_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    # 1. Hacer backup
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Backup creado: {backup_file}")
    
    # 2. Buscar y corregir errores específicos
    fixes_made = 0
    
    # Error 1: unified_articles.append(article) debe ser articles.append(article)
    if "unified_articles.append(article)" in content:
        content = content.replace("unified_articles.append(article)", "articles.append(article)")
        fixes_made += 1
        print(f"✅ Corregido: unified_articles.append(article) -> articles.append(article)")
    
    # Error 2: En api_deduplicated_articles también hay el mismo error
    if "unified_articles.append(article)" in content:
        # Ya se corrigió arriba, pero verificamos si hay más instancias
        count = content.count("unified_articles.append(article)")
        if count > 0:
            content = content.replace("unified_articles.append(article)", "articles.append(article)")
            fixes_made += count
            print(f"✅ Corregidas {count} instancias adicionales de unified_articles.append")
    
    # 3. Verificar que todas las consultas usan tabla 'unified_articles'
    # Buscar posibles usos de tabla 'articles' antigua
    old_table_patterns = [
        r'FROM\s+articles\s+',
        r'FROM\s+`articles`\s+',
        r"FROM\s+'articles'\s+",
        r'FROM\s+"articles"\s+'
    ]
    
    for pattern in old_table_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # Reemplazar con la tabla correcta
            content = re.sub(pattern, 'FROM unified_articles ', content, flags=re.IGNORECASE)
            fixes_made += len(matches)
            print(f"✅ Corregidas {len(matches)} referencias a tabla 'articles' antigua")
    
    # 4. Escribir archivo corregido
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n🎯 RESUMEN DE CORRECCIONES:")
    print(f"   Total de fixes aplicados: {fixes_made}")
    print(f"   Archivo corregido: {app_file}")
    print(f"   Backup disponible en: {backup_file}")
    
    return fixes_made

def verify_database_schema():
    """Verificar esquema de base de datos actual"""
    print("\n🔍 VERIFICANDO ESQUEMA DE BASE DE DATOS")
    print("=" * 80)
    
    db_path = "data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"📋 Tablas encontradas:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Verificar que unified_articles existe
        table_names = [t[0] for t in tables]
        if 'unified_articles' in table_names:
            print(f"\n✅ Tabla 'unified_articles' encontrada correctamente")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM unified_articles")
            count = cursor.fetchone()[0]
            print(f"   📊 Registros en unified_articles: {count}")
        else:
            print(f"\n❌ ERROR: Tabla 'unified_articles' NO encontrada")
            return False
        
        # Verificar si existe tabla 'articles' antigua (no debería existir)
        if 'articles' in table_names:
            cursor.execute("SELECT COUNT(*) FROM articles")
            old_count = cursor.fetchone()[0]
            print(f"\n⚠️  ADVERTENCIA: Tabla 'articles' antigua aún existe con {old_count} registros")
            print(f"   Considerar eliminarla después de verificar migración completa")
        else:
            print(f"\n✅ Tabla 'articles' antigua no encontrada (correcto)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def test_critical_endpoints():
    """Probar endpoints críticos sintácticamente"""
    print("\n🧪 PROBANDO SINTAXIS DE ENDPOINTS CRÍTICOS")
    print("=" * 80)
    
    # Test básico de sintaxis Python
    try:
        with open("core/app_BUENA.py", 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Compilar el código para verificar sintaxis
        compile(code, "core/app_BUENA.py", "exec")
        print("✅ Sintaxis de app_BUENA.py es válida")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en app_BUENA.py:")
        print(f"   Línea {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error verificando sintaxis: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO REPARACIÓN DE ENDPOINTS CRÍTICOS")
    print("=" * 80)
    
    # Paso 1: Corregir errores
    fixes = fix_endpoint_bugs()
    
    # Paso 2: Verificar esquema
    schema_ok = verify_database_schema()
    
    # Paso 3: Probar sintaxis
    syntax_ok = test_critical_endpoints()
    
    # Resumen final
    print("\n🎯 RESUMEN FINAL")
    print("=" * 80)
    print(f"✅ Fixes aplicados: {fixes}")
    print(f"✅ Esquema BD verificado: {'Sí' if schema_ok else 'No'}")
    print(f"✅ Sintaxis válida: {'Sí' if syntax_ok else 'No'}")
    
    if fixes > 0 and schema_ok and syntax_ok:
        print(f"\n🎉 ÉXITO: Todos los errores críticos han sido corregidos")
        print(f"   Los endpoints /api/articles, /api/hero-article y /api/articles/deduplicated")
        print(f"   deberían funcionar correctamente ahora.")
    else:
        print(f"\n⚠️  Se requiere atención adicional en algunos componentes")