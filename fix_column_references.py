#!/usr/bin/env python3
"""
Script para corregir todas las referencias a source_url por url
"""

import re
from pathlib import Path

# Leer el archivo
app_file = Path("src/dashboard/app_modern.py")
content = app_file.read_text(encoding='utf-8')

print("🔧 Corrigiendo referencias de columnas...")

# Reemplazar todas las referencias en las consultas SQL
content = re.sub(
    r'SELECT title, content, created_at, country, risk_level, source_url, source, language',
    'SELECT title, content, created_at, country, risk_level, url, source, language',
    content
)

# Reemplazar las referencias en los diccionarios
content = re.sub(
    r"'source_url': row\['source_url'\]",
    "'source_url': row['url']",
    content
)

content = re.sub(
    r"'url': row\['source_url'\]",
    "'url': row['url']",
    content
)

# Escribir el archivo corregido
app_file.write_text(content, encoding='utf-8')

print("✅ Referencias corregidas en app_modern.py")

# Verificar que no queden referencias incorrectas
remaining_refs = content.count("row['source_url']")
if remaining_refs == 0:
    print("✅ Todas las referencias han sido corregidas")
else:
    print(f"⚠️ Quedan {remaining_refs} referencias por corregir")

print("🚀 Archivo listo para usar")