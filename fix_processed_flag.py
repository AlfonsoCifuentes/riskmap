#!/usr/bin/env python3
"""
Script to fix the processed flag inconsistency in the database
"""
import sqlite3

# Database path
db_path = "./data/geopolitical_intel.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== FIXING PROCESSED FLAG INCONSISTENCY ===\n")
    
    # Check current status
    cursor.execute("SELECT COUNT(*) as count FROM articles WHERE processed = 0")
    unprocessed_count = cursor.fetchone()[0]
    print(f"📊 Current unprocessed articles: {unprocessed_count}")
    
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM articles a 
        INNER JOIN processed_data pd ON a.id = pd.article_id 
        WHERE a.processed = 0
    """)
    inconsistent_count = cursor.fetchone()[0]
    print(f"📊 Articles with processed_data but processed=0: {inconsistent_count}")
    
    if inconsistent_count > 0:
        print(f"\n🔧 Updating {inconsistent_count} articles to processed=1...")
        
        # Update articles that have processed_data to set processed=1
        cursor.execute("""
            UPDATE articles 
            SET processed = 1 
            WHERE id IN (
                SELECT a.id 
                FROM articles a 
                INNER JOIN processed_data pd ON a.id = pd.article_id 
                WHERE a.processed = 0
            )
        """)
        
        updated_rows = cursor.rowcount
        conn.commit()
        
        print(f"✅ Updated {updated_rows} articles to processed=1")
        
        # Verify the fix
        cursor.execute("SELECT processed, COUNT(*) as count FROM articles GROUP BY processed")
        processed_stats = cursor.fetchall()
        
        print("\n📊 Updated status:")
        for row in processed_stats:
            status_text = "Unprocessed" if row[0] == 0 else "Processed" if row[0] == 1 else "Error"
            print(f"   {status_text} (processed={row[0]}): {row[1]} articles")
    else:
        print("\n✅ No inconsistency found - database is already optimized!")
    
    conn.close()
    print("\n✅ Database optimization complete!")

except Exception as e:
    print(f"❌ Error fixing database: {e}")
    import traceback
    traceback.print_exc()