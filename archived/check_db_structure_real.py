#!/usr/bin/env python3
"""
Verificar estructura real de la base de datos
============================================
"""

import sqlite3

def check_table_structure():
    """Verificar la estructura real de las tablas"""
    try:
        conn = sqlite3.connect('./data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Verificar estructura de articles
        print("📋 ESTRUCTURA DE LA TABLA 'articles':")
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Verificar estructura de ai_detected_conflicts
        print("\n📋 ESTRUCTURA DE LA TABLA 'ai_detected_conflicts':")
        cursor.execute("PRAGMA table_info(ai_detected_conflicts)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Verificar algunos artículos de ejemplo
        print("\n📊 MUESTRA DE ARTÍCULOS:")
        cursor.execute("SELECT id, title, risk_level, risk_score FROM articles LIMIT 5")
        articles = cursor.fetchall()
        for article in articles:
            print(f"  ID {article[0]}: {article[1][:50]}... - Riesgo: {article[2]} (Score: {article[3]})")
        
        # Verificar conflictos existentes
        print("\n🔥 CONFLICTOS EXISTENTES:")
        cursor.execute("SELECT COUNT(*) FROM ai_detected_conflicts")
        count = cursor.fetchone()[0]
        print(f"  Total: {count} conflictos")
        
        if count > 0:
            cursor.execute("SELECT location, risk_level, confidence FROM ai_detected_conflicts LIMIT 3")
            conflicts = cursor.fetchall()
            for conflict in conflicts:
                print(f"  📍 {conflict[0]} - {conflict[1]} ({conflict[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_table_structure()
