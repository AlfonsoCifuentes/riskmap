import sqlite3
import os

# Crear directorio si no existe
os.makedirs("./data", exist_ok=True)

# Conectar a la base de datos
conn = sqlite3.connect("./data/geopolitical_intel.db")
cursor = conn.cursor()

# Crear tabla processed_data
cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        url TEXT,
        source TEXT,
        published_date TEXT,
        processed_date TEXT DEFAULT CURRENT_TIMESTAMP,
        category TEXT,
        sentiment REAL,
        risk_score REAL,
        geolocation TEXT,
        language TEXT DEFAULT 'en',
        raw_data TEXT
    )
""")

# Crear tabla satellite_zones con columnas correctas
cursor.execute("""
    CREATE TABLE IF NOT EXISTS satellite_zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        bbox_coords TEXT,
        priority INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        active INTEGER DEFAULT 1
    )
""")

conn.commit()
conn.close()
print("Tablas creadas correctamente")