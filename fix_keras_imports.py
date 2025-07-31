"""
Script para corregir automáticamente las importaciones de tensorflow.keras a keras
En TensorFlow 2.13+, keras se separó de tensorflow
"""

import os
import re
from pathlib import Path

def fix_keras_imports_in_file(filepath):
    """Corrige las importaciones de keras en un archivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup original
        backup_path = str(filepath) + '.backup'
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Replace tensorflow.keras with keras
        original_content = content
        
        # Lista de reemplazos
        replacements = [
            ('from tensorflow.keras.models import', 'from keras.models import'),
            ('from tensorflow.keras.layers import', 'from keras.layers import'),
            ('from tensorflow.keras.optimizers import', 'from keras.optimizers import'),
            ('from tensorflow.keras.callbacks import', 'from keras.callbacks import'),
            ('from tensorflow.keras.regularizers import', 'from keras.regularizers import'),
            ('from tensorflow.keras import regularizers', 'from keras import regularizers'),
            ('from tensorflow.keras import', 'from keras import'),
            ('import tensorflow.keras as keras', 'import keras'),
            ('tensorflow.keras.', 'keras.'),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Solo escribir si hay cambios
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {filepath}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return False

def fix_all_keras_imports():
    """Corrige todas las importaciones de keras en el proyecto"""
    project_root = Path(__file__).parent
    python_files = list(project_root.rglob('*.py'))
    
    print("🔧 Corrigiendo importaciones de Keras...")
    print(f"📁 Directorio: {project_root}")
    print(f"📄 Archivos encontrados: {len(python_files)}")
    print()
    
    fixed_count = 0
    for py_file in python_files:
        # Skip backup files and this script
        if '.backup' in str(py_file) or py_file.name == 'fix_keras_imports.py':
            continue
            
        # Skip .venv directory
        if '.venv' in str(py_file):
            continue
            
        if fix_keras_imports_in_file(py_file):
            fixed_count += 1
    
    print()
    print(f"✅ Proceso completado!")
    print(f"📝 Archivos modificados: {fixed_count}")
    print()
    print("⚠️  Nota: Se crearon archivos .backup para cada archivo modificado")
    print("💡 Si algo sale mal, puedes restaurar con: mv archivo.py.backup archivo.py")

if __name__ == "__main__":
    fix_all_keras_imports()
