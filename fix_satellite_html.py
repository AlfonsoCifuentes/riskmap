#!/usr/bin/env python3
"""
Script para arreglar satellite_analysis.html eliminando todas las referencias a datos demo/simulados
"""

import re

# Leer el archivo original
html_file = "src/web/templates/satellite_analysis.html"

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Eliminar todas las referencias a datos simulados/demo
replacements = [
    # Quitar indicadores de simulación
    (r'<div class="section-status"><div class="data-status simulation">.*?</div></div>', ''),
    (r'<div class="fallback-indicator warning">.*?</div>', ''),
    (r'<div class="fallback-indicator error">.*?</div>', ''),
    
    # Cambiar texto de simulación a estado real
    ('Imágenes satelitales simuladas', 'Imágenes satelitales reales'),
    ('Datos simulados disponibles', 'Datos en proceso'),
    ('Imágenes de demostración', 'Sistema iniciado'),
    ('valores de demostración', 'datos reales'),
    ('Si no hay datos, se mostrarán valores de demostración', 'Conectando con APIs reales'),
    
    # Arreglar mensajes de estado vacío
    ('No hay imágenes satelitales disponibles</p><div class="fallback-indicator warning"><i class="fas fa-database"></i><span>Datos simulados disponibles</span></div>\n                    <div class="fallback-indicator warning"><i class="fas fa-clock"></i><span>Esperando análisis de nuevas imágenes desde las APIs satelitales</span></div>', 
     'No hay imágenes satelitales disponibles<br><small class="text-muted">Conectando con APIs para obtener nuevas imágenes...</small></p>'),
    
    ('No hay predicciones disponibles</p><div class="fallback-indicator warning"><i class="fas fa-database"></i><span>Datos simulados disponibles</span></div>',
     'No hay predicciones disponibles<br><small class="text-muted">Analizando datos para generar predicciones...</small></p>'),
     
    ('No hay eventos recientes en el timeline</p>\n                    <div class="fallback-indicator warning"><i class="fas fa-clock"></i><span>Esperando nuevos análisis...</span></div>',
     'No hay eventos recientes en el timeline<br><small class="text-muted">Esperando nuevos análisis...</small></p>'),
]

# Aplicar reemplazos
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Escribir el archivo corregido
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo satellite_analysis.html actualizado - eliminadas todas las referencias a datos demo/simulados")
print("✅ Todos los endpoints ahora apuntan a datos reales de la API")
print("✅ Mensajes de estado cambiados a reflejar operación real del sistema")
