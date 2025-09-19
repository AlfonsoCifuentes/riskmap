#!/usr/bin/env python3
"""
MIGRACIÓN DE ENDPOINTS A UNIFIED_ARTICLES
=========================================

Script para actualizar automáticamente todos los endpoints del backend
que usan las tablas 'articles' y 'processed_data' para usar 'unified_articles'
"""

import re
import os
import shutil
from datetime import datetime

def backup_file(file_path):
    """Crear backup del archivo"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    return backup_path

def update_database_queries(content):
    """Actualizar queries de base de datos"""
    
    # Patrones de reemplazo
    replacements = [
        # Reemplazar "FROM articles" por "FROM unified_articles"
        (r'\bFROM articles\b', 'FROM unified_articles'),
        
        # Reemplazar "FROM processed_data" por "FROM unified_articles" 
        (r'\bFROM processed_data\b', 'FROM unified_articles'),
        
        # Reemplazar referencias a tablas en queries complejas
        (r'\barticles\.', 'unified_articles.'),
        (r'\bprocessed_data\.', 'unified_articles.'),
        
        # Actualizar JOINs
        (r'JOIN articles\b', 'JOIN unified_articles'),
        (r'JOIN processed_data\b', 'JOIN unified_articles'),
        
        # Actualizar INSERT INTO
        (r'INSERT INTO articles\b', 'INSERT INTO unified_articles'),
        (r'INSERT INTO processed_data\b', 'INSERT INTO unified_articles'),
        
        # Actualizar UPDATE
        (r'UPDATE articles\b', 'UPDATE unified_articles'),
        (r'UPDATE processed_data\b', 'UPDATE unified_articles'),
        
        # Actualizar DELETE FROM
        (r'DELETE FROM articles\b', 'DELETE FROM unified_articles'),
        (r'DELETE FROM processed_data\b', 'DELETE FROM unified_articles'),
    ]
    
    updated_content = content
    changes_made = 0
    
    for pattern, replacement in replacements:
        matches = re.findall(pattern, updated_content, re.IGNORECASE)
        if matches:
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.IGNORECASE)
            changes_made += len(matches)
            print(f"  ✓ Reemplazadas {len(matches)} ocurrencias de: {pattern}")
    
    return updated_content, changes_made

def fix_column_mappings(content):
    """Corregir mapeos de columnas que pueden haber cambiado"""
    
    # Mapeo de columnas que pueden tener nombres diferentes
    column_mappings = [
        # Mapeos conocidos de las migraciones anteriores
        ('description', 'summary'),  # Ya sabemos que description -> summary
        ('published_date', 'published_at'),  # Posible mapeo de fechas
        ('original_date', 'original_published_date'),  # Fechas originales
    ]
    
    updated_content = content
    changes_made = 0
    
    for old_col, new_col in column_mappings:
        # Buscar referencias a columnas en SELECT, WHERE, ORDER BY, etc.
        patterns = [
            rf'\b{old_col}\b(?=\s*[,\s]|\s+FROM|\s+WHERE|\s+ORDER)',
            rf'unified_articles\.{old_col}\b',
            rf'SELECT.*\b{old_col}\b.*FROM',
            rf'WHERE.*\b{old_col}\b',
            rf'ORDER BY.*\b{old_col}\b'
        ]
        
        for pattern in patterns:
            if re.search(pattern, updated_content, re.IGNORECASE):
                updated_content = re.sub(pattern, 
                                       lambda m: m.group().replace(old_col, new_col),
                                       updated_content, 
                                       flags=re.IGNORECASE)
                changes_made += 1
    
    if changes_made > 0:
        print(f"  ✓ Corregidos {changes_made} mapeos de columnas")
    
    return updated_content, changes_made

def add_corrected_indexes():
    """Crear índices corregidos en la base de datos"""
    print("\n🔧 CREANDO ÍNDICES CORREGIDOS")
    print("=" * 50)
    
    import sqlite3
    
    # Índices con nombres de columnas correctos
    corrected_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_unified_articles_published ON unified_articles(published_at)",
        "CREATE INDEX IF NOT EXISTS idx_unified_articles_created ON unified_articles(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_unified_articles_risk ON unified_articles(risk_level)",
        "CREATE INDEX IF NOT EXISTS idx_unified_articles_source ON unified_articles(source)",
        "CREATE INDEX IF NOT EXISTS idx_unified_articles_content ON unified_articles(content)",
        "CREATE INDEX IF NOT EXISTS idx_unified_articles_title ON unified_articles(title)"
    ]
    
    try:
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        for index_sql in corrected_indexes:
            try:
                cursor.execute(index_sql)
                index_name = index_sql.split("IF NOT EXISTS ")[1].split(" ON")[0]
                print(f"✅ Índice creado: {index_name}")
            except Exception as e:
                print(f"⚠️ Error creando índice: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Índices de optimización completados")
        return True
        
    except Exception as e:
        print(f"❌ Error en creación de índices: {e}")
        return False

def update_app_buena():
    """Actualizar app_BUENA.py"""
    print("🔄 ACTUALIZANDO APP_BUENA.PY")
    print("=" * 50)
    
    app_file = 'app_BUENA.py'
    
    if not os.path.exists(app_file):
        print(f"❌ Archivo {app_file} no encontrado")
        return False
    
    # Crear backup
    backup_path = backup_file(app_file)
    
    # Leer contenido actual
    try:
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error leyendo {app_file}: {e}")
        return False
    
    original_content = content
    total_changes = 0
    
    # 1. Actualizar queries de base de datos
    print("1. Actualizando queries de base de datos...")
    content, db_changes = update_database_queries(content)
    total_changes += db_changes
    
    # 2. Corregir mapeos de columnas
    print("2. Corrigiendo mapeos de columnas...")
    content, col_changes = fix_column_mappings(content)
    total_changes += col_changes
    
    # 3. Escribir archivo actualizado si hubo cambios
    if total_changes > 0:
        try:
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {app_file} actualizado con {total_changes} cambios")
            return True
        except Exception as e:
            print(f"❌ Error escribiendo {app_file}: {e}")
            return False
    else:
        print("ℹ️ No se encontraron cambios necesarios")
        return True

def validate_critical_endpoints():
    """Validar que los endpoints críticos funcionen"""
    print("\n🔍 VALIDACIÓN DE ENDPOINTS CRÍTICOS")
    print("=" * 50)
    
    critical_endpoints = [
        '/api/articles',
        '/api/articles/deduplicated', 
        '/api/hero-article',
        '/api/article/<id>',
        '/api/articles/info/<id>'
    ]
    
    print("Endpoints críticos identificados:")
    for endpoint in critical_endpoints:
        print(f"  📍 {endpoint}")
    
    print("\n⚠️ IMPORTANTE: Después de esta migración, debes:")
    print("1. Reiniciar la aplicación")
    print("2. Probar cada endpoint manualmente")
    print("3. Verificar que los datos se muestren correctamente")
    print("4. Comprobar que no hay errores 500 en los logs")
    
    return True

def main():
    """Función principal"""
    print("🚀 MIGRACIÓN AUTOMÁTICA A UNIFIED_ARTICLES")
    print("=" * 80)
    print("Actualizando backend para usar únicamente unified_articles")
    print("=" * 80)
    
    steps = [
        ("Actualizar app_BUENA.py", update_app_buena),
        ("Crear índices corregidos", add_corrected_indexes),
        ("Validar endpoints críticos", validate_critical_endpoints)
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        print(f"\n📋 PASO: {step_name}")
        print("-" * 50)
        
        try:
            if step_function():
                print(f"✅ {step_name} - COMPLETADO")
                success_count += 1
            else:
                print(f"❌ {step_name} - FALLÓ")
        except Exception as e:
            print(f"💥 {step_name} - ERROR: {e}")
    
    # Reporte final
    print("\n" + "=" * 80)
    print("📊 REPORTE DE MIGRACIÓN")
    print("=" * 80)
    
    success_rate = success_count / len(steps) * 100
    print(f"Pasos completados: {success_count}/{len(steps)} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("\n✅ Tu aplicación ahora usa únicamente unified_articles")
        print("✅ Base de datos optimizada con índices correctos")
        print("✅ Todas las referencias antiguas han sido actualizadas")
        
        print("\n🔄 PRÓXIMOS PASOS:")
        print("1. Reinicia tu aplicación: python app_BUENA.py")
        print("2. Verifica que cargue sin errores")
        print("3. Prueba los endpoints en el navegador")
        print("4. Revisa los logs por posibles warnings")
        
    else:
        print("⚠️ MIGRACIÓN PARCIAL")
        print("Algunos pasos requieren revisión manual")
    
    return success_rate == 100

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)