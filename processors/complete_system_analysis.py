#!/usr/bin/env python3
"""
ANÁLISIS COMPLETO DEL SISTEMA RISKMAP
=====================================

Este script realiza un análisis exhaustivo de:
1. Base de datos y sus tablas
2. Código del backend (endpoints, pipelines)
3. Frontend (todas las páginas)
4. Pipeline de datos
5. Redundancias y optimizaciones

Objetivo: Crear estrategia de unificación y limpieza total
"""

import sqlite3
import os
import glob
import json
from pathlib import Path

def analyze_database_schema():
    """Analizar en detalle todas las tablas y sus relaciones"""
    print("🔍 ANÁLISIS DETALLADO DE BASE DE DATOS")
    print("=" * 80)
    
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    analysis = {
        'tables': {},
        'redundancies': [],
        'recommendations': []
    }
    
    for table in tables:
        if table == 'sqlite_sequence':
            continue
            
        # Información de la tabla
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # Obtener algunos datos de muestra
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            sample_data = cursor.fetchall()
        else:
            sample_data = []
        
        analysis['tables'][table] = {
            'columns': columns,
            'count': count,
            'sample_data': sample_data
        }
    
    conn.close()
    
    # Análisis de redundancias
    article_tables = ['articles', 'unified_articles', 'processed_data']
    for table in article_tables:
        if table in analysis['tables']:
            print(f"\n📊 TABLA: {table}")
            print(f"   Registros: {analysis['tables'][table]['count']:,}")
            print(f"   Columnas: {len(analysis['tables'][table]['columns'])}")
    
    return analysis

def analyze_backend_code():
    """Analizar código del backend"""
    print("\n🔍 ANÁLISIS DEL BACKEND")
    print("=" * 80)
    
    backend_analysis = {
        'endpoints': [],
        'data_models': [],
        'pipeline_scripts': []
    }
    
    # Buscar archivos Python principales
    python_files = [
        'app_BUENA.py',
        'main.py',
        'activate_agent.py'
    ]
    
    for file_path in python_files:
        if os.path.exists(file_path):
            print(f"📄 Analizando: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Buscar endpoints
                endpoints = []
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '@app.route(' in line or '@app.get(' in line or '@app.post(' in line:
                        endpoints.append({
                            'line': i + 1,
                            'route': line.strip(),
                            'file': file_path
                        })
                
                backend_analysis['endpoints'].extend(endpoints)
                print(f"   ✅ Encontrados {len(endpoints)} endpoints")
                
            except Exception as e:
                print(f"   ❌ Error leyendo {file_path}: {e}")
    
    return backend_analysis

def analyze_frontend_pages():
    """Analizar todas las páginas del frontend"""
    print("\n🔍 ANÁLISIS DEL FRONTEND")
    print("=" * 80)
    
    frontend_analysis = {
        'templates': [],
        'javascript_functions': [],
        'data_usage': []
    }
    
    # Buscar templates HTML
    template_patterns = ['*.html', 'src/web/templates/*.html', 'templates/*.html']
    
    for pattern in template_patterns:
        for html_file in glob.glob(pattern, recursive=True):
            if os.path.exists(html_file):
                print(f"📄 Analizando template: {html_file}")
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Buscar endpoints llamados desde JavaScript
                    api_calls = []
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'fetch(' in line or '$.get(' in line or '$.post(' in line:
                            api_calls.append({
                                'line': i + 1,
                                'call': line.strip(),
                                'file': html_file
                            })
                    
                    frontend_analysis['templates'].append({
                        'file': html_file,
                        'api_calls': api_calls,
                        'size': len(lines)
                    })
                    
                    print(f"   ✅ {len(api_calls)} llamadas API encontradas")
                    
                except Exception as e:
                    print(f"   ❌ Error leyendo {html_file}: {e}")
    
    return frontend_analysis

def analyze_data_pipeline():
    """Analizar pipeline de datos"""
    print("\n🔍 ANÁLISIS DEL PIPELINE DE DATOS")
    print("=" * 80)
    
    pipeline_files = []
    
    # Buscar archivos relacionados con procesamiento de datos
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and any(keyword in file.lower() for keyword in 
                ['process', 'enrich', 'nlp', 'automation', 'feed', 'etl']):
                pipeline_files.append(os.path.join(root, file))
    
    pipeline_analysis = {
        'scripts': [],
        'data_flow': [],
        'redundant_processes': []
    }
    
    for script in pipeline_files[:20]:  # Limitar para no sobrecargar
        if os.path.exists(script):
            print(f"📄 Analizando script: {script}")
            pipeline_analysis['scripts'].append(script)
    
    return pipeline_analysis

def identify_redundancies_and_optimizations(db_analysis, backend_analysis, frontend_analysis):
    """Identificar redundancias y oportunidades de optimización"""
    print("\n🔍 IDENTIFICACIÓN DE REDUNDANCIAS")
    print("=" * 80)
    
    redundancies = []
    optimizations = []
    
    # 1. Redundancia de tablas de artículos
    article_tables = ['articles', 'unified_articles', 'processed_data']
    existing_article_tables = [t for t in article_tables if t in db_analysis['tables']]
    
    if len(existing_article_tables) > 1:
        redundancies.append({
            'type': 'database',
            'issue': f'Múltiples tablas de artículos: {existing_article_tables}',
            'impact': 'Alto - Duplicación de datos y complejidad innecesaria',
            'solution': 'Consolidar en una sola tabla optimizada'
        })
    
    # 2. Tablas vacías
    empty_tables = [t for t, info in db_analysis['tables'].items() if info['count'] == 0]
    if empty_tables:
        redundancies.append({
            'type': 'database',
            'issue': f'Tablas vacías: {empty_tables}',
            'impact': 'Medio - Complejidad innecesaria del esquema',
            'solution': 'Eliminar tablas no utilizadas o poblarlas'
        })
    
    # 3. Endpoints duplicados o no utilizados
    endpoint_paths = [ep['route'] for ep in backend_analysis['endpoints']]
    unique_paths = set()
    duplicate_endpoints = []
    
    for path in endpoint_paths:
        if path in unique_paths:
            duplicate_endpoints.append(path)
        unique_paths.add(path)
    
    if duplicate_endpoints:
        redundancies.append({
            'type': 'backend',
            'issue': f'Endpoints duplicados: {duplicate_endpoints}',
            'impact': 'Medio - Confusión y mantenimiento complejo',
            'solution': 'Consolidar endpoints duplicados'
        })
    
    return redundancies, optimizations

def create_optimization_strategy(redundancies, db_analysis):
    """Crear estrategia de optimización"""
    print("\n🎯 ESTRATEGIA DE OPTIMIZACIÓN")
    print("=" * 80)
    
    strategy = {
        'database_consolidation': [],
        'code_cleanup': [],
        'performance_improvements': [],
        'implementation_plan': []
    }
    
    # 1. Plan de consolidación de base de datos
    if 'unified_articles' in db_analysis['tables']:
        strategy['database_consolidation'].append({
            'action': 'Mantener unified_articles como tabla principal',
            'details': 'Es la más completa con 79 columnas y datos procesados',
            'priority': 'Alta'
        })
        
        if 'articles' in db_analysis['tables']:
            strategy['database_consolidation'].append({
                'action': 'Eliminar tabla articles',
                'details': 'Datos ya migrados a unified_articles',
                'priority': 'Alta'
            })
        
        if 'processed_data' in db_analysis['tables']:
            strategy['database_consolidation'].append({
                'action': 'Eliminar tabla processed_data',
                'details': 'Datos NLP ya integrados en unified_articles',
                'priority': 'Alta'
            })
    
    # 2. Plan de limpieza de código
    strategy['code_cleanup'].append({
        'action': 'Actualizar todos los endpoints para usar unified_articles',
        'details': 'Modificar queries en app_BUENA.py',
        'priority': 'Alta'
    })
    
    # 3. Plan de implementación
    strategy['implementation_plan'] = [
        '1. Backup completo de la base de datos',
        '2. Verificar integridad de unified_articles',
        '3. Actualizar endpoints backend',
        '4. Probar todos los endpoints',
        '5. Eliminar tablas redundantes',
        '6. Optimizar índices de unified_articles',
        '7. Validación final del sistema'
    ]
    
    return strategy

def main():
    """Función principal de análisis"""
    print("🚀 INICIANDO ANÁLISIS COMPLETO DEL SISTEMA RISKMAP")
    print("=" * 80)
    print("Objetivo: Estrategia de unificación y limpieza total")
    print("=" * 80)
    
    # 1. Análisis de base de datos
    db_analysis = analyze_database_schema()
    
    # 2. Análisis del backend
    backend_analysis = analyze_backend_code()
    
    # 3. Análisis del frontend
    frontend_analysis = analyze_frontend_pages()
    
    # 4. Análisis del pipeline
    pipeline_analysis = analyze_data_pipeline()
    
    # 5. Identificar redundancias
    redundancies, optimizations = identify_redundancies_and_optimizations(
        db_analysis, backend_analysis, frontend_analysis
    )
    
    # 6. Crear estrategia
    strategy = create_optimization_strategy(redundancies, db_analysis)
    
    # 7. Reporte final
    print("\n📊 REPORTE FINAL")
    print("=" * 80)
    
    print(f"\n🗄️  TABLAS EN BASE DE DATOS: {len(db_analysis['tables'])}")
    for table, info in db_analysis['tables'].items():
        status = "✅ ACTIVA" if info['count'] > 0 else "❌ VACÍA"
        print(f"   • {table:<25} | {info['count']:>6,} registros | {status}")
    
    print(f"\n🔗 ENDPOINTS ENCONTRADOS: {len(backend_analysis['endpoints'])}")
    for endpoint in backend_analysis['endpoints'][:10]:  # Primeros 10
        print(f"   • {endpoint['route']}")
    
    print(f"\n🌐 TEMPLATES ANALIZADOS: {len(frontend_analysis['templates'])}")
    for template in frontend_analysis['templates']:
        print(f"   • {template['file']} | {len(template['api_calls'])} llamadas API")
    
    print(f"\n⚠️  REDUNDANCIAS IDENTIFICADAS: {len(redundancies)}")
    for i, redundancy in enumerate(redundancies, 1):
        print(f"   {i}. {redundancy['issue']}")
        print(f"      Impacto: {redundancy['impact']}")
        print(f"      Solución: {redundancy['solution']}")
    
    print(f"\n🎯 ESTRATEGIA DE OPTIMIZACIÓN:")
    print("\n   CONSOLIDACIÓN DE BASE DE DATOS:")
    for action in strategy['database_consolidation']:
        print(f"   • {action['action']} ({action['priority']})")
        print(f"     → {action['details']}")
    
    print("\n   PLAN DE IMPLEMENTACIÓN:")
    for step in strategy['implementation_plan']:
        print(f"   {step}")
    
    print("\n✅ ANÁLISIS COMPLETADO")
    print("=" * 80)
    
    return {
        'database': db_analysis,
        'backend': backend_analysis,
        'frontend': frontend_analysis,
        'pipeline': pipeline_analysis,
        'redundancies': redundancies,
        'strategy': strategy
    }

if __name__ == "__main__":
    analysis_result = main()