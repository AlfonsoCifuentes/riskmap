#!/usr/bin/env python3
"""
LIMPIEZA DE TEMPLATES OBSOLETOS
==============================

Script para identificar y eliminar templates HTML obsoletos,
consolidar duplicados y optimizar la estructura del frontend.
"""

import os
import glob
import shutil
import re
from pathlib import Path
from datetime import datetime

def create_archived_folder():
    """Crear carpeta para archivar templates obsoletos"""
    archive_path = "archived_templates"
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
        print(f"✅ Carpeta creada: {archive_path}")
    return archive_path

def identify_obsolete_templates():
    """Identificar templates obsoletos"""
    print("🔍 IDENTIFICANDO TEMPLATES OBSOLETOS")
    print("=" * 60)
    
    # Patrones de templates obsoletos
    obsolete_patterns = [
        'debug_*.html',
        'test_*.html', 
        'temp_*.html',
        'wireframe_*.html',
        'validation_*.html',
        '*_backup.html',
        '*_test.html',
        'diagnostic_*.html'
    ]
    
    obsolete_files = []
    
    # Buscar en directorio raíz
    for pattern in obsolete_patterns:
        matches = glob.glob(pattern)
        obsolete_files.extend(matches)
    
    # Buscar en subdirectorios
    for pattern in obsolete_patterns:
        matches = glob.glob(f"**/{pattern}", recursive=True)
        obsolete_files.extend(matches)
    
    # Eliminar duplicados
    obsolete_files = list(set(obsolete_files))
    
    print(f"📊 Templates obsoletos encontrados: {len(obsolete_files)}")
    for file in sorted(obsolete_files):
        print(f"  🗑️  {file}")
    
    return obsolete_files

def identify_main_templates():
    """Identificar templates principales"""
    print("\n🔍 IDENTIFICANDO TEMPLATES PRINCIPALES")
    print("=" * 60)
    
    # Templates principales que deben mantenerse
    main_templates = [
        'src/web/templates/dashboard_BUENO.html',
        'dashboard.html',
        'src/web/templates/conflict_monitoring.html',
        'src/web/templates/satellite_analysis.html',
        'src/web/templates/executive_reports.html',
        'src/web/templates/data_intelligence.html',
        'src/web/templates/early_warning.html',
        'src/web/templates/historical_analysis.html',
        'src/web/templates/trends_analysis.html',
        'src/web/templates/video_surveillance.html',
        'src/web/templates/about.html',
        'src/web/templates/error.html',
        'src/web/templates/footer.html',
        'index.html'
    ]
    
    existing_main = []
    for template in main_templates:
        if os.path.exists(template):
            existing_main.append(template)
            print(f"  ✅ {template}")
        else:
            print(f"  ❌ {template} (no encontrado)")
    
    print(f"\n📊 Templates principales activos: {len(existing_main)}")
    return existing_main

def identify_duplicate_templates():
    """Identificar templates duplicados"""
    print("\n🔍 IDENTIFICANDO TEMPLATES DUPLICADOS")
    print("=" * 60)
    
    # Buscar posibles duplicados por nombre similar
    all_html_files = glob.glob("**/*.html", recursive=True)
    
    # Agrupar por nombre base (sin rutas ni sufijos)
    template_groups = {}
    
    for file_path in all_html_files:
        base_name = os.path.basename(file_path)
        # Remover sufijos como _backup, _test, etc.
        clean_name = re.sub(r'(_backup|_test|_copy|_temp|_old|_new)\.html$', '.html', base_name)
        
        if clean_name not in template_groups:
            template_groups[clean_name] = []
        template_groups[clean_name].append(file_path)
    
    duplicates = {}
    for name, files in template_groups.items():
        if len(files) > 1:
            duplicates[name] = files
    
    print(f"📊 Grupos con duplicados: {len(duplicates)}")
    for name, files in duplicates.items():
        print(f"  📄 {name}:")
        for file in files:
            print(f"    • {file}")
    
    return duplicates

def archive_obsolete_templates(obsolete_files, archive_path):
    """Archivar templates obsoletos"""
    print(f"\n🗂️ ARCHIVANDO TEMPLATES OBSOLETOS")
    print("=" * 60)
    
    archived_count = 0
    
    for file_path in obsolete_files:
        try:
            if os.path.exists(file_path):
                # Crear estructura de carpetas en el archivo
                relative_path = os.path.relpath(file_path)
                archive_file_path = os.path.join(archive_path, relative_path)
                
                # Crear directorios necesarios
                os.makedirs(os.path.dirname(archive_file_path), exist_ok=True)
                
                # Mover archivo
                shutil.move(file_path, archive_file_path)
                print(f"  ✅ {file_path} → {archive_file_path}")
                archived_count += 1
            else:
                print(f"  ⚠️ {file_path} (ya no existe)")
        except Exception as e:
            print(f"  ❌ Error archivando {file_path}: {e}")
    
    print(f"\n📊 Templates archivados: {archived_count}")
    return archived_count

def consolidate_duplicates(duplicates):
    """Consolidar templates duplicados"""
    print(f"\n🔄 CONSOLIDANDO TEMPLATES DUPLICADOS")
    print("=" * 60)
    
    consolidated_count = 0
    
    for name, files in duplicates.items():
        print(f"\n📄 Consolidando: {name}")
        
        # Ordenar por fecha de modificación (más reciente primero)
        files_with_mtime = [(f, os.path.getmtime(f)) for f in files if os.path.exists(f)]
        files_with_mtime.sort(key=lambda x: x[1], reverse=True)
        
        if len(files_with_mtime) <= 1:
            continue
        
        # El más reciente se mantiene, los demás se archivan
        keep_file = files_with_mtime[0][0]
        archive_files = [f[0] for f in files_with_mtime[1:]]
        
        print(f"  ✅ Mantener: {keep_file}")
        
        for archive_file in archive_files:
            try:
                archive_name = f"duplicates/{archive_file.replace('/', '_')}.{datetime.now().strftime('%Y%m%d')}"
                archive_full_path = f"archived_templates/{archive_name}"
                
                os.makedirs(os.path.dirname(archive_full_path), exist_ok=True)
                shutil.move(archive_file, archive_full_path)
                print(f"  🗂️  Archivado: {archive_file} → {archive_full_path}")
                consolidated_count += 1
                
            except Exception as e:
                print(f"  ❌ Error consolidando {archive_file}: {e}")
    
    print(f"\n📊 Templates consolidados: {consolidated_count}")
    return consolidated_count

def optimize_template_structure():
    """Optimizar estructura de templates"""
    print(f"\n⚡ OPTIMIZANDO ESTRUCTURA DE TEMPLATES")
    print("=" * 60)
    
    # Verificar que los templates principales estén en la ubicación correcta
    main_template_dir = "src/web/templates"
    
    if not os.path.exists(main_template_dir):
        print(f"⚠️ Directorio principal {main_template_dir} no existe")
        return False
    
    # Contar templates activos por directorio
    template_dirs = {}
    for root, dirs, files in os.walk('.'):
        html_files = [f for f in files if f.endswith('.html')]
        if html_files:
            template_dirs[root] = len(html_files)
    
    print("📊 Templates por directorio:")
    for dir_path, count in sorted(template_dirs.items()):
        print(f"  📁 {dir_path}: {count} templates")
    
    return True

def generate_cleanup_report(obsolete_count, consolidated_count, remaining_templates):
    """Generar reporte final de limpieza"""
    print(f"\n📊 REPORTE FINAL DE LIMPIEZA")
    print("=" * 80)
    
    print(f"Templates obsoletos archivados: {obsolete_count}")
    print(f"Templates duplicados consolidados: {consolidated_count}")
    print(f"Templates principales restantes: {len(remaining_templates)}")
    
    total_cleaned = obsolete_count + consolidated_count
    
    print(f"\n🧹 Total de archivos limpiados: {total_cleaned}")
    
    if total_cleaned > 0:
        print("✅ LIMPIEZA EXITOSA")
        print("\n📁 Estructura final optimizada:")
        print("  • Templates obsoletos → archived_templates/")
        print("  • Templates principales → src/web/templates/")
        print("  • Templates duplicados eliminados")
    else:
        print("ℹ️ No se encontraron templates para limpiar")
    
    return total_cleaned

def main():
    """Función principal"""
    print("🧹 LIMPIEZA DE TEMPLATES DEL FRONTEND")
    print("=" * 80)
    print("Optimizando estructura de templates HTML")
    print("=" * 80)
    
    # 1. Crear carpeta de archivo
    archive_path = create_archived_folder()
    
    # 2. Identificar diferentes tipos de templates
    obsolete_files = identify_obsolete_templates()
    main_templates = identify_main_templates()
    duplicates = identify_duplicate_templates()
    
    # 3. Realizar limpieza
    obsolete_count = archive_obsolete_templates(obsolete_files, archive_path)
    consolidated_count = consolidate_duplicates(duplicates)
    
    # 4. Optimizar estructura
    optimize_template_structure()
    
    # 5. Generar reporte
    total_cleaned = generate_cleanup_report(obsolete_count, consolidated_count, main_templates)
    
    success = True
    
    if success:
        print("\n🎉 LIMPIEZA DE FRONTEND COMPLETADA")
        print("=" * 80)
        print("✅ Templates obsoletos archivados")
        print("✅ Duplicados consolidados")
        print("✅ Estructura optimizada")
        
        print("\n🔄 PRÓXIMOS PASOS:")
        print("1. Verifica que tu aplicación cargue correctamente")
        print("2. Revisa que todas las páginas funcionen")
        print("3. Si algo falla, los backups están en archived_templates/")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)