"""Simple news collection test"""
import sys
import os
import sqlite3
sys.path.append(os.path.dirname(__file__))

from src.utils.config import config

# Test simple recolección
print("=== TESTING SIMPLE COLLECTION ===")

# Ejecutar main.py con recolección en inglés
import subprocess
result = subprocess.run([
    sys.executable, "main.py", "--collect", "--languages", "en"
], capture_output=True, text=True, cwd=".")

print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print(f"Return code: {result.returncode}")

# Verificar base de datos
print("\n=== DATABASE CHECK ===")
try:
    conn = sqlite3.connect(config.get_database_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language;")
    by_language = cursor.fetchall()
    print(f"Articles by language: {dict(by_language)}")
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-1 hour');")
    recent_count = cursor.fetchone()[0]
    print(f"Recent articles (last hour): {recent_count}")
    
    conn.close()
    
except Exception as e:
    print(f"Database error: {e}")
