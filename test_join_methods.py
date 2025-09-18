#!/usr/bin/env python3
"""
Test different JOIN methods for processed_data
"""
import sqlite3

def test_join_methods():
    db_path = "./data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 PROBANDO MÉTODOS DE JOIN")
        print("=" * 40)
        
        # Method 1: JOIN by URL
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles a 
            INNER JOIN processed_data pd ON a.url = pd.url 
            WHERE pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != ''
        """)
        url_join_count = cursor.fetchone()[0]
        print(f"📊 JOIN por URL: {url_join_count} artículos")
        
        # Method 2: JOIN by article_id
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles a 
            INNER JOIN processed_data pd ON a.id = pd.article_id 
            WHERE pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != ''
        """)
        id_join_count = cursor.fetchone()[0]
        print(f"📊 JOIN por article_id: {id_join_count} artículos")
        
        # Check sample problematic articles with both methods
        test_ids = [1117, 1116, 1115, 1114, 1113]
        
        print(f"\n🔬 PRUEBA CON ARTÍCULOS PROBLEMÁTICOS:")
        for article_id in test_ids:
            # URL JOIN
            cursor.execute("""
                SELECT pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != ''
                FROM articles a 
                LEFT JOIN processed_data pd ON a.url = pd.url 
                WHERE a.id = ?
            """, (article_id,))
            url_result = cursor.fetchone()
            url_status = "✅" if url_result and url_result[0] else "❌"
            
            # ID JOIN  
            cursor.execute("""
                SELECT pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != ''
                FROM articles a 
                LEFT JOIN processed_data pd ON a.id = pd.article_id 
                WHERE a.id = ?
            """, (article_id,))
            id_result = cursor.fetchone()
            id_status = "✅" if id_result and id_result[0] else "❌"
            
            print(f"   Artículo {article_id}: URL JOIN {url_status} | ID JOIN {id_status}")
        
        # Check if processed_data has the right article_ids
        print(f"\n📋 VERIFICACIÓN DE processed_data:")
        cursor.execute("""
            SELECT article_id, COUNT(*) as count
            FROM processed_data 
            WHERE article_id IN (1117, 1116, 1115, 1114, 1113)
            AND advanced_nlp IS NOT NULL AND advanced_nlp != ''
            GROUP BY article_id
            ORDER BY article_id DESC
        """)
        
        processed_records = cursor.fetchall()
        if processed_records:
            print(f"   Registros encontrados en processed_data:")
            for article_id, count in processed_records:
                print(f"     - Artículo {article_id}: {count} registros")
        else:
            print(f"   ❌ No se encontraron registros para artículos problemáticos")
        
        conn.close()
        
        print(f"\n💡 CONCLUSIÓN:")
        if id_join_count > url_join_count:
            print(f"   🎯 Usar JOIN por article_id es más efectivo")
            print(f"   🔧 Actualizar consultas para usar a.id = pd.article_id")
        elif url_join_count > id_join_count:
            print(f"   🎯 Usar JOIN por URL es más efectivo")
        else:
            print(f"   ⚠️ Ambos métodos dan el mismo resultado")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_join_methods()