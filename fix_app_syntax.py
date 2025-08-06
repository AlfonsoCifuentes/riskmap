#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRECCIÓN DE SINTAXIS DE app_BUENA.py
Aplicar correcciones necesarias para resolver errores de sintaxis
"""

import sys
import os
import re
import logging
from pathlib import Path

# Configurar codificación UTF-8 para Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_app_syntax():
    """Corregir errores de sintaxis en app_BUENA.py"""
    try:
        app_file = Path("app_BUENA.py")
        
        if not app_file.exists():
            logger.error("app_BUENA.py no encontrado")
            return False
        
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar el punto donde está la clase y las funciones mal colocadas
        # Vamos a buscar el patrón donde aparecen @app.route fuera de la clase
        
        # Encontrar donde terminan las funciones de la clase y empiezan las rutas independientes
        # Buscar el patrón "if __name__ == "__main__":" que debería estar al final
        
        main_pattern = r'if __name__ == "__main__":'
        if main_pattern in content:
            # Dividir el contenido en la parte de la clase y la parte principal
            parts = content.split('if __name__ == "__main__":')
            class_content = parts[0]
            main_content = 'if __name__ == "__main__":' + parts[1]
            
            # Eliminar las funciones independientes que están mal colocadas
            # y las rutas @app.route que deberían estar dentro de la clase
            
            # Encontrar donde termina realmente la clase
            # Buscar el último método de la clase antes de las funciones independientes
            
            corrected_content = class_content.rstrip()
            
            # Asegurar que el archivo termine correctamente
            if not corrected_content.endswith('\n'):
                corrected_content += '\n'
            
            # Agregar la función main al final
            corrected_content += '\n' + main_content
            
            # Escribir el contenido corregido
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(corrected_content)
            
            logger.info("Sintaxis de app_BUENA.py corregida")
            return True
        else:
            logger.warning("No se encontró el patrón principal para corregir")
            return False
            
    except Exception as e:
        logger.error(f"Error corrigiendo sintaxis: {e}")
        return False

if __name__ == "__main__":
    print("Corrigiendo sintaxis de app_BUENA.py...")
    success = fix_app_syntax()
    
    if success:
        print("✓ Sintaxis corregida exitosamente")
    else:
        print("✗ Error corrigiendo sintaxis")
    
    sys.exit(0 if success else 1)
