#!/usr/bin/env python3
"""
Check existing table schemas to understand how to fix satellite API queries
"""

import sqlite3
import os

def check_table_schemas():
    """Check schemas of existing satellite tables"""
    
    db_path = './data/geopolitical_intel.db'
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check satellite_timeline table (might replace satellite_analysis_new)
            print("🔍 satellite_timeline table:")
            cursor.execute("PRAGMA table_info(satellite_timeline)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            print("\n📊 Sample data:")
            cursor.execute("SELECT * FROM satellite_timeline LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")
            
            print("\n" + "="*50)
            
            # Check image_analysis table (might replace computer_vision_results)
            print("🔍 image_analysis table:")
            cursor.execute("PRAGMA table_info(image_analysis)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            print("\n📊 Sample data:")
            cursor.execute("SELECT * FROM image_analysis LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")
            
            print("\n" + "="*50)
            
            # Check satellite_predictions table
            print("🔍 satellite_predictions table:")
            cursor.execute("PRAGMA table_info(satellite_predictions)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            print("\n📊 Sample data:")
            cursor.execute("SELECT * FROM satellite_predictions LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_table_schemas()