import sqlite3
import os

# Verificar las bases de datos disponibles
databases = [
    'data/geopolitical_intel.db',
    'data/riskmap.db', 
    'geopolitical_intel.db'
]

main_db = None
for db_path in databases:
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si tiene tabla articles
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
            if cursor.fetchone():
                # Contar artículos
                cursor.execute("SELECT COUNT(*) FROM articles")
                count = cursor.fetchone()[0]
                print(f"✅ {db_path}: {count} artículos")
                if count > 0:
                    main_db = db_path
                    
                    # Mostrar algunos ejemplos
                    cursor.execute("SELECT id, title, image_url FROM articles LIMIT 3")
                    for row in cursor.fetchall():
                        print(f"   - ID {row[0]}: {row[1][:50]}... (img: {row[2] is not None})")
            else:
                print(f"❌ {db_path}: No tiene tabla 'articles'")
            
            conn.close()
        except Exception as e:
            print(f"❌ {db_path}: Error - {e}")
    else:
        print(f"❌ {db_path}: No existe")

if main_db:
    print(f"\n🎯 Base de datos principal: {main_db}")
else:
    print("\n❌ No se encontró base de datos con artículos")
