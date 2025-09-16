import sqlite3

try:
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Verificar columnas de la tabla articles
    cursor.execute('PRAGMA table_info(articles)')
    columns = cursor.fetchall()
    
    print("Columnas de la tabla articles:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")
    
    # También verificar si hay datos
    cursor.execute('SELECT COUNT(*) FROM articles')
    count = cursor.fetchone()[0]
    print(f"\nTotal de artículos: {count}")
    
    # Si hay artículos, mostrar algunas columnas de muestra
    if count > 0:
        cursor.execute('SELECT * FROM articles LIMIT 1')
        sample = cursor.fetchone()
        print(f"\nMuestra de datos: {sample}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    if conn:
        conn.close()
