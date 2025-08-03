#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación del estado actual de la base de datos
Muestra estadísticas de enriquecimiento
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar función de base de datos
from app_BUENA import get_database_path

def check_database_status():
    """Verificar el estado actual de la base de datos"""
    
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    print(f"📍 Base de datos: {db_path}")
    print(f"📁 Tamaño: {os.path.getsize(db_path) / 1024 / 1024:.1f} MB")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabla processed_data
        cursor.execute("SELECT COUNT(*) FROM processed_data")
        total_articles = cursor.fetchone()[0]
        print(f"📰 Total de artículos: {total_articles:,}")
        
        if total_articles == 0:
            print("⚠️ No hay artículos en la base de datos")
            conn.close()
            return
        
        # Artículos con resumen de AI
        cursor.execute("""
            SELECT COUNT(*) FROM processed_data 
            WHERE ai_summary IS NOT NULL 
            AND ai_summary != '' 
            AND ai_summary != 'N/A'
        """)
        with_summary = cursor.fetchone()[0]
        
        # Artículos con análisis geopolítico
        cursor.execute("""
            SELECT COUNT(*) FROM processed_data 
            WHERE geopolitical_analysis IS NOT NULL 
            AND geopolitical_analysis != '' 
            AND geopolitical_analysis != 'N/A'
        """)
        with_geopolitical = cursor.fetchone()[0]
        
        # Artículos con probabilidad de conflicto
        cursor.execute("""
            SELECT COUNT(*) FROM processed_data 
            WHERE conflict_probability IS NOT NULL 
            AND conflict_probability > 0
        """)
        with_conflict_prob = cursor.fetchone()[0]
        
        # Artículos completamente enriquecidos
        cursor.execute("""
            SELECT COUNT(*) FROM processed_data 
            WHERE (ai_summary IS NOT NULL AND ai_summary != '' AND ai_summary != 'N/A')
            AND (geopolitical_analysis IS NOT NULL AND geopolitical_analysis != '' AND geopolitical_analysis != 'N/A')
            AND (conflict_probability IS NOT NULL AND conflict_probability > 0)
        """)
        fully_enriched = cursor.fetchone()[0]
        
        # Estadísticas de enriquecimiento
        print("📊 ESTADO DE ENRIQUECIMIENTO:")
        print(f"  📝 Con resumen de AI: {with_summary:,} ({with_summary/total_articles*100:.1f}%)")
        print(f"  🌍 Con análisis geopolítico: {with_geopolitical:,} ({with_geopolitical/total_articles*100:.1f}%)")
        print(f"  ⚡ Con probabilidad de conflicto: {with_conflict_prob:,} ({with_conflict_prob/total_articles*100:.1f}%)")
        print(f"  ✅ Completamente enriquecidos: {fully_enriched:,} ({fully_enriched/total_articles*100:.1f}%)")
        
        # Artículos que necesitan enriquecimiento
        pending = total_articles - fully_enriched
        print(f"  🔄 Pendientes de enriquecer: {pending:,} ({pending/total_articles*100:.1f}%)")
        
        print()
        
        # Últimas actualizaciones
        cursor.execute("""
            SELECT MAX(last_updated) FROM processed_data 
            WHERE ai_summary IS NOT NULL AND ai_summary != '' AND ai_summary != 'N/A'
        """)
        last_enrichment = cursor.fetchone()[0]
        if last_enrichment:
            print(f"📅 Último enriquecimiento: {last_enrichment}")
        
        # Distribución por fuente
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM processed_data 
            GROUP BY source 
            ORDER BY count DESC 
            LIMIT 10
        """)
        sources = cursor.fetchall()
        
        if sources:
            print("\n📡 DISTRIBUCIÓN POR FUENTE:")
            for source, count in sources:
                source_name = source if source else "Sin fuente"
                print(f"  {source_name}: {count:,} artículos")
        
        # Distribución por nivel de riesgo
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM processed_data 
            WHERE risk_level IS NOT NULL
            GROUP BY risk_level 
            ORDER BY risk_level DESC
        """)
        risk_levels = cursor.fetchall()
        
        if risk_levels:
            print("\n⚠️ DISTRIBUCIÓN POR NIVEL DE RIESGO:")
            for risk_level, count in risk_levels:
                print(f"  Nivel {risk_level}: {count:,} artículos")
        
        # Artículos recientes sin enriquecer
        cursor.execute("""
            SELECT id, title, published_date 
            FROM processed_data 
            WHERE (ai_summary IS NULL OR ai_summary = '' OR ai_summary = 'N/A')
               OR (geopolitical_analysis IS NULL OR geopolitical_analysis = '' OR geopolitical_analysis = 'N/A')
               OR (conflict_probability IS NULL OR conflict_probability = 0)
            ORDER BY published_date DESC 
            LIMIT 5
        """)
        recent_pending = cursor.fetchall()
        
        if recent_pending:
            print("\n🔍 ÚLTIMOS ARTÍCULOS SIN ENRIQUECER:")
            for article_id, title, pub_date in recent_pending:
                title_short = title[:60] + "..." if len(title) > 60 else title
                print(f"  [{article_id}] {title_short} ({pub_date})")
        
        conn.close()
        
        # Recomendaciones
        print("\n💡 RECOMENDACIONES:")
        if pending > 0:
            print(f"  🔄 Ejecutar enriquecimiento masivo para {pending:,} artículos pendientes")
            print("  📋 Comando: python enriquecimiento_masivo.py")
        else:
            print("  ✅ Todos los artículos están enriquecidos")
        
        if pending > 100:
            print("  ⚡ Para testing: python test_enriquecimiento_rapido.py")
        
    except Exception as e:
        logger.error(f"❌ Error verificando base de datos: {e}")
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN DEL ESTADO DE LA BASE DE DATOS")
    print("=" * 50)
    
    try:
        check_database_status()
    except KeyboardInterrupt:
        print("\n⏹️ Verificación interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
