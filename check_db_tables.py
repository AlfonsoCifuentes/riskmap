#!/usr/bin/env python3
import sqlite3
import os

db_path = 'data/geopolitical_intel.db'
print(f'DB exists: {os.path.exists(db_path)}')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f'Tables found: {len(tables)}')
    for table in tables:
        table_name = table[0]
        print(f'\n--- Table: {table_name} ---')
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print('Columns:')
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f'Rows: {count}')
        
        # Show sample data if available
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_rows = cursor.fetchall()
            print('Sample data:')
            for row in sample_rows:
                print(f'  {row}')
    
    conn.close()
else:
    print('Database file not found!')
