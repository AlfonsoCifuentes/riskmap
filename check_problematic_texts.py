import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('./data/geopolitical_intel.db')
cursor = conn.cursor()

# Buscar artículos con textos problemáticos
problematic_texts = [
    'aplicación',
    'gratuita',
    'UE advirtió',
    'akistán'
]

print('Buscando artículos con textos problemáticos...')
for text in problematic_texts:
    query = f"SELECT id, title FROM articles WHERE title LIKE '%{text}%' LIMIT 5"
    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        print(f'\nArtículos encontrados con "{text}":')
        for row in results:
            print(f'ID: {row[0]}, Title: {row[1][:200]}...')

# También buscar en el contenido
print('\n\nBuscando en el contenido de los artículos...')
for text in problematic_texts:
    query = f"SELECT id, title, content FROM articles WHERE content LIKE '%{text}%' LIMIT 3"
    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        print(f'\nArtículos con "{text}" en el contenido:')
        for row in results:
            print(f'ID: {row[0]}')
            print(f'Title: {row[1][:100]}...')
            print(f'Content preview: {row[2][:200]}...')
            print('---')

conn.close()