import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('./data/geopolitical_intel.db')
cursor = conn.cursor()

# Buscar los textos problemáticos específicos
problematic_texts = [
    'aplicación gratuita',
    'UE advirtió',
    'akistán',
    'gratuita'
]

print("Verificando textos problemáticos específicos:")
print("=" * 50)

for text in problematic_texts:
    query = f"SELECT id, title FROM articles WHERE title LIKE '%{text}%'"
    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        print(f"\nEncontrado '{text}' en {len(results)} artículo(s):")
        for row in results:
            print(f"ID: {row[0]}, Title: {row[1][:150]}...")
    else:
        print(f"\n'{text}' - NO ENCONTRADO en títulos")

# Verificar si hay artículos con títulos muy largos que aún queden
cursor.execute("SELECT COUNT(*) FROM articles WHERE length(title) > 100")
long_titles_count = cursor.fetchone()[0]
print(f"\nArtículos con títulos > 100 caracteres: {long_titles_count}")

conn.close()