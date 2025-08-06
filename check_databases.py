#!/usr/bin/env python3
import sqlite3
import os

db_files = [
    "data/geopolitical_data.db",
    "data/geopolitical_intel.db", 
    "data/riskmap.db"
]

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"\n=== {db_file} ===")
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Tablas: {tables}")
            
            if 'articles' in tables:
                cursor.execute("SELECT COUNT(*) FROM articles")
                count = cursor.fetchone()[0]
                print(f"Artículos: {count}")
                
                cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language")
                langs = cursor.fetchall()
                print(f"Por idioma: {langs}")
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"{db_file}: No existe")
