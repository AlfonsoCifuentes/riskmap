#!/usr/bin/env python3
"""
Análisis y limpieza de archivos no utilizados en el proyecto RiskMap
"""

import os
import re
import ast
from pathlib import Path
from typing import Set, List, Dict
import json

def extract_imports_from_file(filepath: str) -> Set[str]:
    """Extrae todos los imports de un archivo Python"""
    imports = set()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse AST to get imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except:
            # Fallback to regex if AST parsing fails
            import_pattern = r'^(?:from\s+([\w\.]+)|import\s+([\w\.]+))'
            matches = re.findall(import_pattern, content, re.MULTILINE)
            for match in matches:
                module = match[0] if match[0] else match[1]
                if module:
                    imports.add(module.split('.')[0])
                    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return imports

def get_local_modules(imports: Set[str]) -> Set[str]:
    """Filtra solo los módulos locales (no librerías estándar)"""
    standard_libs = {
        'typing', 'datetime', 'pathlib', 'json', 'signal', 'atexit', 
        'urllib', 'urllib3', 'bs4', 'hashlib', 'flask', 'dash', 
        'requests', 'sqlite3', 'asyncio', 'threading', 'time', 'sys', 
        'os', 'warnings', 'logging', 'numpy', 'ml_dtypes', 'ssl', 
        'dotenv', 'collections', 're', 'functools', 'contextlib', 
        'traceback', 'random', 'concurrent', 'dataclasses', 'flask_cors',
        'flask_socketio', 'dash_bootstrap_components', 'werkzeug',
        'pandas', 'plotly', 'scipy', 'sklearn', 'tensorflow', 'torch',
        'transformers', 'sentence_transformers', 'nltk', 'spacy',
        'cv2', 'PIL', 'matplotlib', 'seaborn', 'beautifulsoup4'
    }
    
    return {imp for imp in imports if imp not in standard_libs}

def find_used_files() -> Dict[str, Set[str]]:
    """Encuentra todos los archivos que son realmente utilizados"""
    used_files = {
        'RISKMAP.py': set(),  # Main app
        'start_riskmap.py': set(),  # Launcher
    }
    
    # Analyze main executables
    for main_file in ['RISKMAP.py', 'start_riskmap.py']:
        if os.path.exists(main_file):
            imports = extract_imports_from_file(main_file)
            local_modules = get_local_modules(imports)
            
            # Map modules to files
            for module in local_modules:
                # Check if it's a direct .py file
                if os.path.exists(f"{module}.py"):
                    used_files[f"{module}.py"] = set()
                # Check if it's a package
                elif os.path.exists(module) and os.path.isdir(module):
                    used_files[module] = set()
                    
    # Now recursively check imported files
    to_check = list(used_files.keys())
    checked = set()
    
    while to_check:
        current = to_check.pop(0)
        if current in checked:
            continue
        checked.add(current)
        
        if current.endswith('.py') and os.path.exists(current):
            imports = extract_imports_from_file(current)
            local_modules = get_local_modules(imports)
            
            for module in local_modules:
                if os.path.exists(f"{module}.py"):
                    if f"{module}.py" not in used_files:
                        used_files[f"{module}.py"] = set()
                        to_check.append(f"{module}.py")
                        
    return used_files

def categorize_files() -> Dict[str, List[str]]:
    """Categoriza todos los archivos del proyecto"""
    categories = {
        'core_files': [],  # Archivos principales
        'src_modules': [],  # Módulos en src/
        'config_files': [],  # Archivos de configuración
        'data_files': [],  # Archivos de datos
        'test_files': [],  # Archivos de prueba
        'utility_scripts': [],  # Scripts de utilidad
        'cleanup_candidates': []  # Candidatos para eliminar
    }
    
    # Get all Python files in root
    root_files = [f for f in os.listdir('.') if f.endswith('.py')]
    
    # Core files that should never be deleted
    core_files = {
        'RISKMAP.py', 'start_riskmap.py', 
        'enhanced_translation_geo_system.py',
        'yolo_permanent_patch.py', 'fix_tf_warnings.py',
        'advanced_image_extractor.py', 'ultra_hd_satellite_system.py',
        'satellite_integration.py', 'ml_dtypes_patch.py'
    }
    
    # Config and important files
    config_files = {
        'requirements.txt', 'pyproject.toml', '.env.example',
        'docker-compose.yml', 'Dockerfile', 'README.md',
        '.gitignore', '.flake8', 'mypy.ini'
    }
    
    # Test and diagnostic files (can be cleaned)
    test_patterns = [
        r'^test_', r'^quick_test', r'^diagnose', r'^debug_',
        r'^check_', r'^verify_', r'^validate_', r'^examine_',
        r'^explore_', r'^investigate_', r'^find_', r'^scan_',
        r'^document_', r'^analyze_', r'^extract_'
    ]
    
    # Cleanup and fix files (can be cleaned)
    cleanup_patterns = [
        r'^cleanup_', r'^fix_', r'^repair_', r'^patch_',
        r'^migrate_', r'^reset_', r'^restore_', r'^reprocess_',
        r'^optimize_', r'^improve_', r'^enhance_'
    ]
    
    # Temporary and backup files (should be cleaned)
    temp_patterns = [
        r'\.backup', r'_backup', r'_old', r'_temp',
        r'^tmp_', r'^temp_', r'^prueba_', r'^final_'
    ]
    
    used_files = find_used_files()
    
    for file in root_files:
        if file in core_files:
            categories['core_files'].append(file)
        elif file in used_files:
            categories['core_files'].append(file)
        elif any(re.match(pattern, file) for pattern in test_patterns):
            categories['test_files'].append(file)
        elif any(re.match(pattern, file) for pattern in cleanup_patterns):
            categories['utility_scripts'].append(file)
        elif any(re.search(pattern, file) for pattern in temp_patterns):
            categories['cleanup_candidates'].append(file)
        else:
            # Check if it's imported anywhere
            is_imported = False
            for check_file in ['RISKMAP.py', 'start_riskmap.py']:
                if os.path.exists(check_file):
                    with open(check_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        module_name = file[:-3]  # Remove .py
                        if module_name in content:
                            is_imported = True
                            break
            
            if not is_imported:
                categories['cleanup_candidates'].append(file)
            else:
                categories['utility_scripts'].append(file)
    
    return categories

def main():
    """Análisis principal y generación de reporte"""
    print("=" * 80)
    print("ANÁLISIS DE ARCHIVOS DEL PROYECTO RISKMAP")
    print("=" * 80)
    
    # Categorize files
    categories = categorize_files()
    
    # Generate report
    print("\n📊 RESUMEN DE ARCHIVOS:")
    print("-" * 40)
    
    total_files = sum(len(files) for files in categories.values())
    print(f"Total de archivos Python: {total_files}")
    
    print(f"\n✅ Archivos principales (NO BORRAR): {len(categories['core_files'])}")
    for file in sorted(categories['core_files'])[:10]:
        print(f"   - {file}")
    if len(categories['core_files']) > 10:
        print(f"   ... y {len(categories['core_files']) - 10} más")
    
    print(f"\n🧪 Archivos de prueba: {len(categories['test_files'])}")
    for file in sorted(categories['test_files'])[:5]:
        print(f"   - {file}")
    if len(categories['test_files']) > 5:
        print(f"   ... y {len(categories['test_files']) - 5} más")
    
    print(f"\n🔧 Scripts de utilidad: {len(categories['utility_scripts'])}")
    for file in sorted(categories['utility_scripts'])[:5]:
        print(f"   - {file}")
    if len(categories['utility_scripts']) > 5:
        print(f"   ... y {len(categories['utility_scripts']) - 5} más")
    
    print(f"\n🗑️ CANDIDATOS PARA ELIMINAR: {len(categories['cleanup_candidates'])}")
    for file in sorted(categories['cleanup_candidates'])[:20]:
        size = os.path.getsize(file) / 1024  # KB
        print(f"   - {file} ({size:.1f} KB)")
    if len(categories['cleanup_candidates']) > 20:
        print(f"   ... y {len(categories['cleanup_candidates']) - 20} más")
    
    # Calculate space that would be freed
    total_size = sum(os.path.getsize(f) for f in categories['cleanup_candidates']) / (1024 * 1024)  # MB
    print(f"\n💾 Espacio que se liberaría: {total_size:.2f} MB")
    
    # Save detailed report
    report = {
        'timestamp': str(Path.cwd()),
        'summary': {
            'total_files': total_files,
            'core_files': len(categories['core_files']),
            'test_files': len(categories['test_files']),
            'utility_scripts': len(categories['utility_scripts']),
            'cleanup_candidates': len(categories['cleanup_candidates']),
            'space_to_free_mb': total_size
        },
        'categories': categories
    }
    
    with open('cleanup_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n📄 Reporte detallado guardado en: cleanup_report.json")
    
    # Ask for confirmation to delete
    print("\n" + "=" * 80)
    print("⚠️  IMPORTANTE: Se recomienda hacer un backup antes de eliminar archivos")
    print("=" * 80)
    
    if categories['cleanup_candidates']:
        response = input(f"\n¿Deseas eliminar los {len(categories['cleanup_candidates'])} archivos candidatos? (s/n): ")
        if response.lower() == 's':
            deleted_count = 0
            for file in categories['cleanup_candidates']:
                try:
                    os.remove(file)
                    deleted_count += 1
                    print(f"✅ Eliminado: {file}")
                except Exception as e:
                    print(f"❌ Error eliminando {file}: {e}")
            
            print(f"\n✅ Se eliminaron {deleted_count} archivos")
            print(f"💾 Espacio liberado: {total_size:.2f} MB")
        else:
            print("\n❌ Operación cancelada. No se eliminó ningún archivo.")
    else:
        print("\n✅ No hay archivos candidatos para eliminar. El proyecto está limpio.")

if __name__ == "__main__":
    main()