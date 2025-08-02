import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('geopolitical_intel.db')
cursor = conn.cursor()

# Obtener las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tablas en la base de datos:")
for table in tables:
    print(f"- {table[0]}")

# Si hay tablas, mostrar la estructura de la primera
if tables:
    table_name = tables[0][0]
    print(f"\nEstructura de la tabla '{table_name}':")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Contar registros
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\nTotal de registros: {count}")

conn.close()
