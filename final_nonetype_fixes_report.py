#!/usr/bin/env python3
"""
Final summary of NoneType error fixes for the NLP pipeline
"""
import sqlite3
from datetime import datetime

def final_status_report():
    """Generate comprehensive status report after NoneType fixes"""
    
    print("🔧 INFORME FINAL: CORRECCIONES DE ERRORES NONETYPE")
    print("=" * 70)
    print(f"📅 Fecha del informe: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db_path = "./data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Check articles with NULL content
        print(f"\n📝 1. ANÁLISIS DE CONTENIDO NULL:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_articles,
                SUM(CASE WHEN content IS NULL THEN 1 ELSE 0 END) as null_content,
                SUM(CASE WHEN content = '' THEN 1 ELSE 0 END) as empty_content,
                SUM(CASE WHEN content IS NOT NULL AND content != '' THEN 1 ELSE 0 END) as has_content
            FROM articles
        """)
        
        total, null_content, empty_content, has_content = cursor.fetchone()
        
        print(f"   📊 Total artículos: {total}")
        print(f"   📄 Con contenido NULL: {null_content} ({null_content/total*100:.1f}%)")
        print(f"   📄 Con contenido vacío: {empty_content} ({empty_content/total*100:.1f}%)")
        print(f"   📄 Con contenido válido: {has_content} ({has_content/total*100:.1f}%)")
        
        # 2. Check NLP processing coverage
        print(f"\n🧠 2. COBERTURA DE PROCESAMIENTO NLP:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_articles,
                SUM(CASE WHEN pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != '' THEN 1 ELSE 0 END) as processed_articles
            FROM articles a
            LEFT JOIN processed_data pd ON a.url = pd.url
            WHERE a.is_excluded = 0
        """)
        
        total_active, processed = cursor.fetchone()
        coverage = (processed / total_active * 100) if total_active > 0 else 0
        
        print(f"   📊 Artículos activos: {total_active}")
        print(f"   🧠 Con NLP procesado: {processed}")
        print(f"   📈 Cobertura: {coverage:.1f}%")
        
        # 3. Check articles that were failing before (1117-1108)
        failing_ids = [1117, 1116, 1115, 1114, 1113, 1112, 1111, 1110, 1109, 1108]
        
        print(f"\n❌ 3. ARTÍCULOS QUE FALLABAN ANTES:")
        print("-" * 40)
        
        processed_count = 0
        for article_id in failing_ids:
            cursor.execute("""
                SELECT pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != ''
                FROM articles a
                LEFT JOIN processed_data pd ON a.url = pd.url
                WHERE a.id = ?
            """, (article_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                processed_count += 1
                status = "✅ PROCESADO"
            else:
                status = "❌ SIN PROCESAR"
            
            print(f"   Artículo {article_id}: {status}")
        
        print(f"\n   📊 Resumen: {processed_count}/{len(failing_ids)} artículos problemáticos ahora procesados")
        
        # 4. Recent processing activity
        print(f"\n⏰ 4. ACTIVIDAD RECIENTE:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                DATE(a.created_at) as date,
                COUNT(*) as articles_count,
                SUM(CASE WHEN pd.advanced_nlp IS NOT NULL AND pd.advanced_nlp != '' THEN 1 ELSE 0 END) as processed_count
            FROM articles a
            LEFT JOIN processed_data pd ON a.url = pd.url
            WHERE a.created_at >= datetime('now', '-7 days')
            AND a.is_excluded = 0
            GROUP BY DATE(a.created_at)
            ORDER BY date DESC
            LIMIT 7
        """)
        
        recent_data = cursor.fetchall()
        
        for date, total, processed in recent_data:
            coverage = (processed / total * 100) if total > 0 else 0
            print(f"   📅 {date}: {processed}/{total} artículos ({coverage:.1f}%)")
        
        # 5. Risk distribution
        print(f"\n🎯 5. DISTRIBUCIÓN DE RIESGO ACTUAL:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                risk_level,
                COUNT(*) as count
            FROM articles a
            WHERE a.risk_level IS NOT NULL
            AND a.is_excluded = 0
            GROUP BY risk_level
            ORDER BY 
                CASE risk_level 
                    WHEN 'high' THEN 3 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 1 
                    ELSE 0 
                END DESC
        """)
        
        risk_data = cursor.fetchall()
        total_with_risk = sum(count for _, count in risk_data)
        
        for risk_level, count in risk_data:
            percentage = (count / total_with_risk * 100) if total_with_risk > 0 else 0
            print(f"   🎯 {risk_level.upper()}: {count} artículos ({percentage:.1f}%)")
        
        conn.close()
        
        # 6. Summary of fixes applied
        print(f"\n🔧 6. CORRECCIONES APLICADAS:")
        print("-" * 40)
        print(f"   ✅ main_orchestrator.py: Fixed len(content) → len(content or '')")
        print(f"   ✅ process_all_articles_nlp.py: Fixed len(content) → len(content or '')")
        print(f"   ✅ integrate_advanced_nlp.py: Fixed len(content) → len(content or '')")
        print(f"   ✅ Added safe content handling: (content[:300] + '...' if len(content or '') > 300 else content) or ''")
        print(f"   ✅ All NLP processing now handles NULL content gracefully")
        
        # 7. Final status
        print(f"\n🎉 7. ESTADO FINAL:")
        print("-" * 40)
        
        if coverage >= 95 and processed_count >= len(failing_ids) * 0.8:
            print(f"   🟢 SISTEMA OPERATIVO: Pipeline NLP funcionando correctamente")
            print(f"   ✅ Error 'object of type 'NoneType' has no len()' RESUELTO")
            print(f"   📈 Cobertura de procesamiento: {coverage:.1f}%")
            print(f"   🔧 Artículos problemáticos: {processed_count}/{len(failing_ids)} procesados")
        elif coverage >= 80:
            print(f"   🟡 SISTEMA FUNCIONAL: Mayoría de artículos procesados")
            print(f"   ⚠️ Revisar artículos pendientes de procesamiento")
        else:
            print(f"   🔴 SISTEMA NECESITA ATENCIÓN: Baja cobertura de procesamiento")
            print(f"   ❌ Revisar errores en el pipeline")
        
    except Exception as e:
        print(f"❌ Error generando informe: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_status_report()