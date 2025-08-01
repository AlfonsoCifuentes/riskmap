import sqlite3
import pandas as pd

# Conectar a la base de datos
db_path = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
conn = sqlite3.connect(db_path)

# Obtener todas las tablas
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tablas en la base de datos:")
for table in tables:
    print(f"- {table[0]}")

# Examinar la estructura de cada tabla
for table in tables:
    table_name = table[0]
    print(f"\n=== Estructura de la tabla '{table_name}' ===")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Mostrar algunos registros de ejemplo
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    print(f"  Total de registros: {count}")
    
    if count > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        rows = cursor.fetchall()
        print(f"  Primeros 3 registros:")
        for row in rows:
            print(f"    {row}")

conn.close()
