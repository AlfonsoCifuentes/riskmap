#!/usr/bin/env python3
"""
Database structure checker and importance_score column fixer
"""

import sqlite3
import sys

def check_and_fix_database():
    """Check database structure and add missing importance_score column"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📊 Available tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check articles table for importance_score column
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        
        print(f"\n📋 Articles table has {len(columns)} columns")
        
        if 'importance_score' not in column_names:
            print("❌ Missing 'importance_score' column in articles table")
            print("🔧 Adding importance_score column...")
            
            # Add the missing column
            cursor.execute("ALTER TABLE articles ADD COLUMN importance_score REAL DEFAULT 0.5")
            
            # Update existing records with calculated importance scores
            cursor.execute("""
                UPDATE articles 
                SET importance_score = CASE 
                    WHEN risk_score > 0.7 THEN 0.9
                    WHEN risk_score > 0.5 THEN 0.7
                    WHEN risk_score > 0.3 THEN 0.5
                    ELSE 0.3
                END
                WHERE importance_score IS NULL OR importance_score = 0.5
            """)
            
            conn.commit()
            print("✅ importance_score column added and populated")
        else:
            print("✅ importance_score column already exists")
        
        # Check if there are any other related conflict tables that might need the column
        conflict_related_tables = ['conflict_events', 'conflict_data', 'conflicts']
        
        for table_name in conflict_related_tables:
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                table_columns = cursor.fetchall()
                if table_columns:  # Table exists
                    table_column_names = [col[1] for col in table_columns]
                    print(f"\n📋 {table_name} table found with {len(table_columns)} columns")
                    
                    if 'importance_score' not in table_column_names:
                        print(f"🔧 Adding importance_score column to {table_name}...")
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN importance_score REAL DEFAULT 0.5")
                        conn.commit()
                        print(f"✅ importance_score column added to {table_name}")
                    else:
                        print(f"✅ importance_score column already exists in {table_name}")
            except sqlite3.OperationalError as e:
                if "no such table" not in str(e):
                    print(f"⚠️ Error checking table {table_name}: {e}")
        
        # Verify the fix
        cursor.execute("SELECT COUNT(*) FROM articles WHERE importance_score IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"\n🎯 Articles with importance_score: {count}")
        
        # Test the query that was failing
        try:
            cursor.execute("SELECT id, title, importance_score FROM articles LIMIT 5")
            results = cursor.fetchall()
            print("\n✅ Test query successful - sample results:")
            for row in results:
                print(f"  ID: {row[0]}, Title: {row[1][:50]}..., Importance: {row[2]}")
        except Exception as e:
            print(f"❌ Test query failed: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Checking and fixing database structure...")
    success = check_and_fix_database()
    
    if success:
        print("\n✅ Database structure check and fix completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Database structure check failed")
        sys.exit(1)
