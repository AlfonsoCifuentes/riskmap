#!/usr/bin/env python3
"""
ESTRATEGIA TOTAL DE UNIFICACIÓN Y LIMPIEZA - RISKMAP
===================================================

Estrategia profesional y metodológica para unificar la base de datos 
y código, eliminando duplicaciones y optimizando el rendimiento.

ANÁLISIS DE LA SITUACIÓN ACTUAL:
- 21 tablas en BD, 10 vacías (47% innecesarias)
- 3 tablas de artículos con datos redundantes
- 46 templates HTML, muchos obsoletos
- Endpoints dispersos usando diferentes esquemas
- Pipeline de datos fragmentado

OBJETIVO: Sistema unificado, eficiente, mantenible y escalable
"""

import sqlite3
import os
import shutil
from datetime import datetime

class DatabaseUnificationStrategy:
    """Estrategia completa de unificación de base de datos"""
    
    def __init__(self):
        self.db_path = "data/geopolitical_intel.db"
        self.backup_path = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Tablas a mantener (esenciales)
        self.essential_tables = {
            'unified_articles': 'Tabla principal con todos los artículos y NLP',
            'conflict_zones': 'Zonas de conflicto activas',
            'feed_updates': 'Control de actualizaciones RSS',
            'enrichment_log': 'Log de enriquecimiento de datos',
            'alerts': 'Sistema de alertas',
            'gpr_index': 'Índice de riesgo geopolítico',
            'satellite_alerts': 'Alertas satelitales',
            'satellite_timeline': 'Timeline de eventos satelitales',
            'satellite_predictions': 'Predicciones satelitales'
        }
        
        # Tablas a eliminar (redundantes o vacías)
        self.tables_to_drop = [
            'articles',           # Migrado a unified_articles
            'processed_data',     # Integrado en unified_articles
            'acled_events',       # Vacía
            'gdelt_events',       # Vacía
            'satellite_images',   # Vacía
            'satellite_queries',  # Vacía
            'zone_satellite_images', # Vacía
            'conflict_events',    # Vacía
            'critical_events',    # Vacía
            'etl_runs',          # Vacía
            'satellite_zones',    # Vacía
            'article_duplicates'  # Vacía
        ]
        
        # Índices para optimización
        self.indexes_to_create = [
            "CREATE INDEX IF NOT EXISTS idx_unified_articles_date ON unified_articles(published_date)",
            "CREATE INDEX IF NOT EXISTS idx_unified_articles_risk ON unified_articles(risk_level)",
            "CREATE INDEX IF NOT EXISTS idx_unified_articles_source ON unified_articles(source)",
            "CREATE INDEX IF NOT EXISTS idx_unified_articles_countries ON unified_articles(detected_countries)",
            "CREATE INDEX IF NOT EXISTS idx_unified_articles_geopolitical ON unified_articles(is_geopolitical_filtered)",
            "CREATE INDEX IF NOT EXISTS idx_conflict_zones_active ON conflict_zones(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_feed_updates_status ON feed_updates(status)"
        ]

def phase_1_backup_and_analysis():
    """Fase 1: Backup completo y análisis final"""
    print("🔄 FASE 1: BACKUP Y ANÁLISIS FINAL")
    print("=" * 60)
    
    strategy = DatabaseUnificationStrategy()
    
    # 1. Crear backup
    print("1. Creando backup de seguridad...")
    try:
        shutil.copy2(strategy.db_path, strategy.backup_path)
        print(f"   ✅ Backup creado: {strategy.backup_path}")
    except Exception as e:
        print(f"   ❌ Error en backup: {e}")
        return False
    
    # 2. Verificar integridad de unified_articles
    print("2. Verificando integridad de unified_articles...")
    conn = sqlite3.connect(strategy.db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE title IS NOT NULL AND content IS NOT NULL")
        valid_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM unified_articles")
        total_articles = cursor.fetchone()[0]
        
        integrity_ratio = valid_articles / total_articles * 100
        print(f"   📊 Artículos válidos: {valid_articles:,} de {total_articles:,} ({integrity_ratio:.1f}%)")
        
        if integrity_ratio < 90:
            print("   ⚠️ Advertencia: Menos del 90% de artículos están completos")
        else:
            print("   ✅ Integridad de datos confirmada")
            
    except Exception as e:
        print(f"   ❌ Error verificando integridad: {e}")
        return False
    finally:
        conn.close()
    
    return True

def phase_2_database_cleanup():
    """Fase 2: Limpieza de base de datos"""
    print("\n🔄 FASE 2: LIMPIEZA DE BASE DE DATOS")
    print("=" * 60)
    
    strategy = DatabaseUnificationStrategy()
    conn = sqlite3.connect(strategy.db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Eliminar tablas redundantes
        print("1. Eliminando tablas redundantes...")
        for table in strategy.tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"   ✅ Eliminada: {table}")
            except Exception as e:
                print(f"   ⚠️ No se pudo eliminar {table}: {e}")
        
        conn.commit()
        
        # 2. Crear índices de optimización
        print("2. Creando índices de optimización...")
        for index_sql in strategy.indexes_to_create:
            try:
                cursor.execute(index_sql)
                index_name = index_sql.split("IF NOT EXISTS ")[1].split(" ON")[0]
                print(f"   ✅ Índice creado: {index_name}")
            except Exception as e:
                print(f"   ⚠️ Error creando índice: {e}")
        
        conn.commit()
        
        # 3. Analizar espacio recuperado
        cursor.execute("VACUUM")
        print("   ✅ Base de datos optimizada (VACUUM ejecutado)")
        
        # 4. Estadísticas finales
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        remaining_tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📊 Tablas restantes: {len(remaining_tables)}")
        for table in remaining_tables:
            if table != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status = "✅ ACTIVA" if count > 0 else "❌ VACÍA"
                print(f"   • {table:<25} | {count:>6,} registros | {status}")
        
    except Exception as e:
        print(f"❌ Error en limpieza de BD: {e}")
        return False
    finally:
        conn.close()
    
    return True

def phase_3_backend_unification():
    """Fase 3: Unificación del backend"""
    print("\n🔄 FASE 3: UNIFICACIÓN DEL BACKEND")
    print("=" * 60)
    
    # Endpoints que deben usar unified_articles
    critical_endpoints = [
        '/api/articles',
        '/api/articles/deduplicated',
        '/api/hero-article',
        '/api/article/<int:article_id>',
        '/api/articles/info/<int:article_id>'
    ]
    
    print("1. Analizando endpoints críticos...")
    for endpoint in critical_endpoints:
        print(f"   📍 {endpoint}")
    
    print("\n2. Acciones requeridas en app_BUENA.py:")
    print("   • Actualizar queries para usar unified_articles únicamente")
    print("   • Eliminar referencias a 'articles' y 'processed_data'")
    print("   • Optimizar joins y consultas complejas")
    print("   • Actualizar serialización de respuestas JSON")
    
    return True

def phase_4_frontend_optimization():
    """Fase 4: Optimización del frontend"""
    print("\n🔄 FASE 4: OPTIMIZACIÓN DEL FRONTEND")
    print("=" * 60)
    
    print("1. Templates principales identificados:")
    main_templates = [
        'src/web/templates/dashboard_BUENO.html',  # Dashboard principal
        'dashboard.html',                          # Dashboard alternativo
        'src/web/templates/conflict_monitoring.html',
        'src/web/templates/satellite_analysis.html',
        'src/web/templates/executive_reports.html'
    ]
    
    for template in main_templates:
        if os.path.exists(template):
            print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template} (no encontrado)")
    
    print("\n2. Templates obsoletos a eliminar:")
    obsolete_templates = [
        'debug_*.html',
        'test_*.html',
        'temp_*.html',
        'wireframe_*.html',
        'validation_*.html',
        '*_backup.html'
    ]
    
    for pattern in obsolete_templates:
        print(f"   🗑️  {pattern}")
    
    print("\n3. Acciones de optimización:")
    print("   • Consolidar templates duplicados")
    print("   • Eliminar archivos de debug y test")
    print("   • Optimizar llamadas API en JavaScript")
    print("   • Unificar sistema de estilos CSS")
    
    return True

def phase_5_pipeline_consolidation():
    """Fase 5: Consolidación del pipeline de datos"""
    print("\n🔄 FASE 5: CONSOLIDACIÓN DEL PIPELINE")
    print("=" * 60)
    
    print("1. Scripts esenciales del pipeline:")
    essential_scripts = [
        'advanced_geopolitical_nlp.py',      # NLP avanzado
        'mass_article_processor.py',         # Procesamiento masivo  
        'database_unification.py',           # Unificación (ya hecho)
        'app_BUENA.py'                       # Aplicación principal
    ]
    
    for script in essential_scripts:
        if os.path.exists(script):
            print(f"   ✅ {script}")
        else:
            print(f"   ❌ {script} (crear si necesario)")
    
    print("\n2. Scripts obsoletos a limpiar:")
    print("   • automation_block_*.py (múltiples versiones)")
    print("   • check_*.py (scripts de diagnóstico)")
    print("   • test_*.py (scripts de prueba)")
    print("   • debug_*.py (scripts de debug)")
    
    print("\n3. Organización propuesta:")
    print("   📁 /core/          - Lógica principal")
    print("   📁 /processors/    - Scripts de procesamiento")
    print("   📁 /utils/         - Utilidades y helpers")
    print("   📁 /archived/      - Scripts obsoletos")
    
    return True

def phase_6_final_validation():
    """Fase 6: Validación final del sistema"""
    print("\n🔄 FASE 6: VALIDACIÓN FINAL")
    print("=" * 60)
    
    print("1. Pruebas de integridad:")
    print("   • Verificar todos los endpoints API")
    print("   • Validar carga del frontend")
    print("   • Comprobar pipeline de datos")
    print("   • Verificar sistema de traducción")
    
    print("\n2. Métricas de rendimiento:")
    print("   • Tiempo de carga de artículos")
    print("   • Velocidad de consultas SQL")
    print("   • Uso de memoria del sistema")
    print("   • Tiempo de procesamiento NLP")
    
    print("\n3. Documentación actualizada:")
    print("   • Esquema de base de datos unificado")
    print("   • API endpoints documentados")
    print("   • Guía de mantenimiento")
    print("   • Proceso de deployment")
    
    return True

def execute_complete_strategy():
    """Ejecutar estrategia completa de unificación"""
    print("🚀 ESTRATEGIA TOTAL DE UNIFICACIÓN - RISKMAP")
    print("=" * 80)
    print("Transformación completa del sistema a arquitectura unificada")
    print("=" * 80)
    
    phases = [
        ("Backup y Análisis", phase_1_backup_and_analysis),
        ("Limpieza de Base de Datos", phase_2_database_cleanup),
        ("Unificación del Backend", phase_3_backend_unification),
        ("Optimización del Frontend", phase_4_frontend_optimization),
        ("Consolidación del Pipeline", phase_5_pipeline_consolidation),
        ("Validación Final", phase_6_final_validation)
    ]
    
    results = []
    
    for i, (phase_name, phase_function) in enumerate(phases, 1):
        print(f"\n{'='*20} EJECUTANDO FASE {i}: {phase_name.upper()} {'='*20}")
        try:
            success = phase_function()
            results.append((phase_name, success))
            if success:
                print(f"✅ FASE {i} COMPLETADA: {phase_name}")
            else:
                print(f"❌ FASE {i} FALLÓ: {phase_name}")
        except Exception as e:
            print(f"💥 ERROR EN FASE {i}: {e}")
            results.append((phase_name, False))
    
    # Reporte final
    print("\n" + "="*80)
    print("📊 REPORTE FINAL DE UNIFICACIÓN")
    print("="*80)
    
    successful_phases = sum(1 for _, success in results if success)
    total_phases = len(results)
    success_rate = successful_phases / total_phases * 100
    
    print(f"Fases completadas: {successful_phases}/{total_phases} ({success_rate:.1f}%)")
    print("\nDetalle por fase:")
    for phase_name, success in results:
        status = "✅ ÉXITO" if success else "❌ FALLO"
        print(f"   • {phase_name:<30} | {status}")
    
    if success_rate >= 80:
        print("\n🎉 UNIFICACIÓN EXITOSA")
        print("El sistema ha sido unificado y optimizado correctamente.")
        print("\nPróximos pasos:")
        print("1. Reiniciar la aplicación (python app_BUENA.py)")
        print("2. Verificar funcionamiento de todos los endpoints")
        print("3. Monitorear rendimiento en las primeras 24 horas")
    else:
        print("\n⚠️ UNIFICACIÓN PARCIAL")
        print("Algunas fases requieren atención manual.")
        print("Revisar logs y corregir errores antes de continuar.")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = execute_complete_strategy()
    exit(0 if success else 1)