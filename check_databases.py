import sqlite3
import os

# Verificar todas las bases de datos
db_files = ['articles.db', 'geopolitical_intel.db', 'geopolitical_intelligence.db', 'news_database.db', 'osint_data.db']

for db_file in db_files:
    db_path = f'data/{db_file}'
    if os.path.exists(db_path):
        print(f"\n=== {db_file} ===")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tablas: {tables}")
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {table_name}: {count} registros")
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"{db_file}: No existe")
