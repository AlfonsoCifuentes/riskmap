"""
Script to unify all databases into one single database.
This will merge all data from different databases into geopolitical_intel.db
"""

import sqlite3
import os
from pathlib import Path

def get_table_schema(conn, table_name):
    """Get the CREATE TABLE statement for a table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = cursor.fetchone()
    return result[0] if result else None

def get_all_tables(conn):
    """Get all table names from a database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]

def merge_table_data(source_conn, target_conn, table_name):
    """Merge data from source table to target table."""
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    # Get column names
    source_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in source_cursor.fetchall()]
    
    # Check which columns exist in target
    target_cursor.execute(f"PRAGMA table_info({table_name})")
    target_columns = [col[1] for col in target_cursor.fetchall()]
    
    # Use only common columns
    common_columns = [col for col in columns if col in target_columns]
    
    if not common_columns:
        print(f"  No common columns found for table {table_name}")
        return 0
    
    columns_str = ', '.join(common_columns)
    placeholders = ', '.join(['?' for _ in common_columns])
    
    # Get data from source
    source_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
    rows = source_cursor.fetchall()
    
    # Insert into target
    inserted = 0
    for row in rows:
        try:
            target_cursor.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", row)
            inserted += 1
        except sqlite3.IntegrityError:
            # Skip duplicates
            pass
        except Exception as e:
            print(f"  Error inserting row: {e}")
    
    target_conn.commit()
    return inserted

def main():
    # Define the main database
    main_db = 'data/geopolitical_intel.db'
    
    # List of other databases to merge
    other_dbs = [
        'data/riskmap.db',
        'data/geopolitical_intelligence.db',
        'data/articles.db',
        'data/news_database.db',
        'data/osint_data.db'
    ]
    
    print(f"Unifying all databases into: {main_db}")
    print("=" * 60)
    
    # Connect to main database
    main_conn = sqlite3.connect(main_db)
    
    # Process each database
    for db_path in other_dbs:
        if not os.path.exists(db_path):
            print(f"\nSkipping {db_path} - file not found")
            continue
            
        # Check if it's empty
        if os.path.getsize(db_path) == 0:
            print(f"\nSkipping {db_path} - empty file")
            continue
            
        print(f"\nProcessing {db_path}...")
        
        try:
            # Connect to source database
            source_conn = sqlite3.connect(db_path)
            
            # Get all tables
            tables = get_all_tables(source_conn)
            print(f"  Found {len(tables)} tables: {', '.join(tables)}")
            
            for table in tables:
                # Check if table exists in main database
                main_cursor = main_conn.cursor()
                main_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                
                if not main_cursor.fetchone():
                    # Create table in main database
                    schema = get_table_schema(source_conn, table)
                    if schema:
                        print(f"  Creating table {table} in main database")
                        main_conn.execute(schema)
                        main_conn.commit()
                
                # Merge data
                inserted = merge_table_data(source_conn, main_conn, table)
                if inserted > 0:
                    print(f"  Merged {inserted} rows from table {table}")
            
            source_conn.close()
            
        except Exception as e:
            print(f"  Error processing {db_path}: {e}")
    
    # Show final statistics
    print("\n" + "=" * 60)
    print("Final database statistics:")
    
    cursor = main_conn.cursor()
    tables = get_all_tables(main_conn)
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    
    main_conn.close()
    
    # Ask user before deleting other databases
    print("\n" + "=" * 60)
    response = input("Do you want to delete the other database files? (y/N): ")
    
    if response.lower() == 'y':
        for db_path in other_dbs:
            if os.path.exists(db_path) and db_path != main_db:
                try:
                    os.remove(db_path)
                    print(f"Deleted {db_path}")
                except Exception as e:
                    print(f"Error deleting {db_path}: {e}")
        print("\nDatabase unification complete!")
    else:
        print("\nDatabase files kept. You can delete them manually later.")

if __name__ == "__main__":
    main()