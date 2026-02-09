#!/usr/bin/env python3
"""
Debug script to check database structure and identify satellite API issues
"""

import sqlite3
import os
import sys

def check_database_structure():
    """Check database tables and identify missing tables causing 500 errors"""
    
    db_path = './data/geopolitical_intel.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"📊 Checking database structure: {db_path}")
    print("="*60)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"📋 Found {len(tables)} tables:")
            for table in tables:
                print(f"  ✓ {table}")
            
            print("\n🔍 Checking satellite-related tables:")
            satellite_tables = [
                'satellite_alerts',
                'satellite_analysis_new', 
                'satellite_images',
                'computer_vision_results_new',
                'computer_vision_results'
            ]
            
            missing_tables = []
            existing_tables = []
            
            for table in satellite_tables:
                if table in tables:
                    existing_tables.append(table)
                    print(f"  ✅ {table} - EXISTS")
                    
                    # Check structure
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    print(f"     Columns ({len(columns)}): {', '.join([col[1] for col in columns])}")
                    
                    # Check row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"     Rows: {count}")
                    
                else:
                    missing_tables.append(table)
                    print(f"  ❌ {table} - MISSING")
            
            print(f"\n📊 Summary:")
            print(f"  ✅ Existing satellite tables: {len(existing_tables)}")
            print(f"  ❌ Missing satellite tables: {len(missing_tables)}")
            
            if missing_tables:
                print(f"\n🚨 PROBLEM IDENTIFIED:")
                print(f"The satellite API endpoints are failing because these tables don't exist:")
                for table in missing_tables:
                    print(f"  - {table}")
                
                print(f"\n💡 SOLUTION:")
                print(f"Create missing tables or modify API endpoints to use existing tables")
                
                # Check what similar tables exist
                print(f"\n🔍 Similar tables that might be used instead:")
                for table in tables:
                    if any(keyword in table.lower() for keyword in ['satellite', 'alert', 'image', 'vision', 'analysis']):
                        if table not in satellite_tables:
                            print(f"  📋 {table}")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database_structure()