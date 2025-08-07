#!/usr/bin/env python3
"""
Script para corregir todos los problemas identificados en el análisis NLP y filtrado
"""

import sqlite3
import os
import json
import re

def fix_all_issues():
    """Corregir todos los problemas identificados"""
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    print("🔧 INICIANDO CORRECCIÓN COMPLETA DE PROBLEMAS")
    print("=" * 60)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. AÑADIR COLUMNAS DE COORDENADAS
        print("📍 PASO 1: Añadiendo columnas de coordenadas...")
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN latitude REAL")
            print("   ✅ Columna latitude añadida")
        except sqlite3.OperationalError:
            print("   ℹ️ Columna latitude ya existe")
        
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN longitude REAL")
            print("   ✅ Columna longitude añadida")
        except sqlite3.OperationalError:
            print("   ℹ️ Columna longitude ya existe")
        
        # 2. CORREGIR LÓGICA DE RISK_LEVEL
        print("\\n⚖️ PASO 2: Corrigiendo lógica de risk_level...")
        
        # Reclasificar basado en risk_score
        cursor.execute("""
            UPDATE articles 
            SET risk_level = CASE 
                WHEN risk_score >= 0.7 THEN 'high'
                WHEN risk_score >= 0.4 THEN 'medium'
                ELSE 'low'
            END
            WHERE risk_score IS NOT NULL
        """)
        
        # Contar cambios
        cursor.execute("SELECT risk_level, COUNT(*) FROM articles GROUP BY risk_level")
        new_distribution = cursor.fetchall()
        print("   📊 Nueva distribución:")
        for level, count in new_distribution:
            print(f"   - {level}: {count} artículos")
        
        # 3. ELIMINAR ARTÍCULOS NO GEOPOLÍTICOS
        print("\\n🌍 PASO 3: Eliminando artículos no geopolíticos...")
        
        # Marcar artículos de deportes para exclusión
        cursor.execute("""
            UPDATE articles 
            SET is_excluded = 1, excluded_reason = 'sports_content'
            WHERE category = 'sports' 
               OR LOWER(title) LIKE '%deporte%'
               OR LOWER(title) LIKE '%sport%'
               OR LOWER(title) LIKE '%football%'
               OR LOWER(title) LIKE '%basketball%'
               OR LOWER(title) LIKE '%tennis%'
               OR LOWER(title) LIKE '%golf%'
               OR LOWER(title) LIKE '%soccer%'
        """)
        
        excluded_count = cursor.rowcount
        print(f"   ✅ {excluded_count} artículos de deportes marcados como excluidos")
        
        # Marcar otros contenidos no geopolíticos
        cursor.execute("""
            UPDATE articles 
            SET is_excluded = 1, excluded_reason = 'non_geopolitical'
            WHERE category IN ('entertainment', 'lifestyle', 'health', 'technology')
               OR LOWER(title) LIKE '%celebrity%'
               OR LOWER(title) LIKE '%entretenimiento%'
               OR LOWER(title) LIKE '%videojuego%'
               OR LOWER(title) LIKE '%música%'
               OR LOWER(title) LIKE '%diet%'
               OR LOWER(title) LIKE '%fitness%'
        """)
        
        excluded_count2 = cursor.rowcount
        print(f"   ✅ {excluded_count2} artículos adicionales no geopolíticos marcados como excluidos")
        
        # 4. GEOCODIFICAR PAÍSES
        print("\\n📍 PASO 4: Geocodificando países...")
        
        # Diccionario de coordenadas para países principales
        country_coords = {
            'Israel': {'latitude': 31.0461, 'longitude': 34.8516},
            'Estados Unidos': {'latitude': 39.8283, 'longitude': -98.5795},
            'United States': {'latitude': 39.8283, 'longitude': -98.5795},
            'EE. UU.': {'latitude': 39.8283, 'longitude': -98.5795},
            'Ukraine': {'latitude': 48.3794, 'longitude': 31.1656},
            'Ucrania': {'latitude': 48.3794, 'longitude': 31.1656},
            'China': {'latitude': 35.8617, 'longitude': 104.1954},
            'India': {'latitude': 20.5937, 'longitude': 78.9629},
            'Russia': {'latitude': 61.5240, 'longitude': 105.3188},
            'Rusia': {'latitude': 61.5240, 'longitude': 105.3188},
            'Pakistan': {'latitude': 30.3753, 'longitude': 69.3451},
            'United Kingdom': {'latitude': 55.3781, 'longitude': -3.4360},
            'Iran': {'latitude': 32.4279, 'longitude': 53.6880},
            'France': {'latitude': 46.2276, 'longitude': 2.2137},
            'Germany': {'latitude': 51.1657, 'longitude': 10.4515},
            'Turkey': {'latitude': 38.9637, 'longitude': 35.2433},
            'Syria': {'latitude': 34.8021, 'longitude': 38.9968},
            'Lebanon': {'latitude': 33.8547, 'longitude': 35.8623},
            'Iraq': {'latitude': 33.2232, 'longitude': 43.6793},
            'Afghanistan': {'latitude': 33.9391, 'longitude': 67.7100},
            'Yemen': {'latitude': 15.5527, 'longitude': 48.5164},
            'Saudi Arabia': {'latitude': 23.8859, 'longitude': 45.0792},
            'Egypt': {'latitude': 26.0975, 'longitude': 30.0444},
            'Libya': {'latitude': 26.3351, 'longitude': 17.2283},
            'Sudan': {'latitude': 12.8628, 'longitude': 30.2176},
            'Ethiopia': {'latitude': 9.1450, 'longitude': 40.4897},
            'Somalia': {'latitude': 5.1521, 'longitude': 46.1996},
            'Nigeria': {'latitude': 9.0820, 'longitude': 8.6753},
            'South Korea': {'latitude': 35.9078, 'longitude': 127.7669},
            'North Korea': {'latitude': 40.3399, 'longitude': 127.5101},
            'Japan': {'latitude': 36.2048, 'longitude': 138.2529},
            'Taiwan': {'latitude': 23.6978, 'longitude': 120.9605},
            'Philippines': {'latitude': 12.8797, 'longitude': 121.7740},
            'Vietnam': {'latitude': 14.0583, 'longitude': 108.2772},
            'Thailand': {'latitude': 15.8700, 'longitude': 100.9925},
            'Myanmar': {'latitude': 21.9162, 'longitude': 95.9560},
            'Bangladesh': {'latitude': 23.6850, 'longitude': 90.3563},
            'Nepal': {'latitude': 28.3949, 'longitude': 84.1240},
            'Sri Lanka': {'latitude': 7.8731, 'longitude': 80.7718},
            'Indonesia': {'latitude': -0.7893, 'longitude': 113.9213},
            'Malaysia': {'latitude': 4.2105, 'longitude': 101.9758},
            'Singapore': {'latitude': 1.3521, 'longitude': 103.8198},
            'Australia': {'latitude': -25.2744, 'longitude': 133.7751},
            'New Zealand': {'latitude': -40.9006, 'longitude': 174.8860},
            'Canada': {'latitude': 56.1304, 'longitude': -106.3468},
            'Mexico': {'latitude': 23.6345, 'longitude': -102.5528},
            'Brazil': {'latitude': -14.2350, 'longitude': -51.9253},
            'Argentina': {'latitude': -38.4161, 'longitude': -63.6167},
            'Chile': {'latitude': -35.6751, 'longitude': -71.5430},
            'Colombia': {'latitude': 4.5709, 'longitude': -74.2973},
            'Venezuela': {'latitude': 6.4238, 'longitude': -66.5897},
            'Peru': {'latitude': -9.1900, 'longitude': -75.0152},
            'Ecuador': {'latitude': -1.8312, 'longitude': -78.1834},
            'Bolivia': {'latitude': -16.2902, 'longitude': -63.5887},
            'Paraguay': {'latitude': -23.4425, 'longitude': -58.4438},
            'Uruguay': {'latitude': -32.5228, 'longitude': -55.7658},
            'Spain': {'latitude': 40.4637, 'longitude': -3.7492},
            'Italy': {'latitude': 41.8719, 'longitude': 12.5674},
            'Portugal': {'latitude': 39.3999, 'longitude': -8.2245},
            'Greece': {'latitude': 39.0742, 'longitude': 21.8243},
            'Poland': {'latitude': 51.9194, 'longitude': 19.1451},
            'Czech Republic': {'latitude': 49.8175, 'longitude': 15.4730},
            'Hungary': {'latitude': 47.1625, 'longitude': 19.5033},
            'Romania': {'latitude': 45.9432, 'longitude': 24.9668},
            'Bulgaria': {'latitude': 42.7339, 'longitude': 25.4858},
            'Serbia': {'latitude': 44.0165, 'longitude': 21.0059},
            'Croatia': {'latitude': 45.1000, 'longitude': 15.2000},
            'Slovenia': {'latitude': 46.1512, 'longitude': 14.9955},
            'Slovakia': {'latitude': 48.6690, 'longitude': 19.6990},
            'Austria': {'latitude': 47.5162, 'longitude': 14.5501},
            'Switzerland': {'latitude': 46.8182, 'longitude': 8.2275},
            'Belgium': {'latitude': 50.5039, 'longitude': 4.4699},
            'Netherlands': {'latitude': 52.1326, 'longitude': 5.2913},
            'Denmark': {'latitude': 56.2639, 'longitude': 9.5018},
            'Sweden': {'latitude': 60.1282, 'longitude': 18.6435},
            'Norway': {'latitude': 60.4720, 'longitude': 8.4689},
            'Finland': {'latitude': 61.9241, 'longitude': 25.7482},
            'Iceland': {'latitude': 64.9631, 'longitude': -19.0208},
            'Ireland': {'latitude': 53.4129, 'longitude': -8.2439},
            'Morocco': {'latitude': 31.7917, 'longitude': -7.0926},
            'Algeria': {'latitude': 28.0339, 'longitude': 1.6596},
            'Tunisia': {'latitude': 33.8869, 'longitude': 9.5375},
            'Kenya': {'latitude': -0.0236, 'longitude': 37.9062},
            'Tanzania': {'latitude': -6.3690, 'longitude': 34.8888},
            'Uganda': {'latitude': 1.3733, 'longitude': 32.2903},
            'Rwanda': {'latitude': -1.9403, 'longitude': 29.8739},
            'Burundi': {'latitude': -3.3731, 'longitude': 29.9189},
            'Democratic Republic of Congo': {'latitude': -4.0383, 'longitude': 21.7587},
            'Central African Republic': {'latitude': 6.6111, 'longitude': 20.9394},
            'Chad': {'latitude': 15.4542, 'longitude': 18.7322},
            'Niger': {'latitude': 17.6078, 'longitude': 8.0817},
            'Mali': {'latitude': 17.5707, 'longitude': -3.9962},
            'Burkina Faso': {'latitude': 12.2383, 'longitude': -1.5616},
            'Ghana': {'latitude': 7.9465, 'longitude': -1.0232},
            'Ivory Coast': {'latitude': 7.5400, 'longitude': -5.5471},
            'Guinea': {'latitude': 9.9456, 'longitude': -9.6966},
            'Sierra Leone': {'latitude': 8.4606, 'longitude': -11.7799},
            'Liberia': {'latitude': 6.4281, 'longitude': -9.4295},
            'Senegal': {'latitude': 14.4974, 'longitude': -14.4524},
            'Gambia': {'latitude': 13.4432, 'longitude': -15.3101},
            'Guinea-Bissau': {'latitude': 11.8037, 'longitude': -15.1804},
            'Cape Verde': {'latitude': 16.5388, 'longitude': -24.0132},
            'Mauritania': {'latitude': 21.0079, 'longitude': -10.9408},
            'South Africa': {'latitude': -30.5595, 'longitude': 22.9375},
            'Namibia': {'latitude': -22.9576, 'longitude': 18.4904},
            'Botswana': {'latitude': -22.3285, 'longitude': 24.6849},
            'Zimbabwe': {'latitude': -19.0154, 'longitude': 29.1549},
            'Zambia': {'latitude': -13.1339, 'longitude': 27.8493},
            'Malawi': {'latitude': -13.2543, 'longitude': 34.3015},
            'Mozambique': {'latitude': -18.6657, 'longitude': 35.5296},
            'Madagascar': {'latitude': -18.7669, 'longitude': 46.8691},
            'Mauritius': {'latitude': -20.3484, 'longitude': 57.5522},
            'Seychelles': {'latitude': -4.6796, 'longitude': 55.4920},
            'Comoros': {'latitude': -11.6455, 'longitude': 43.3333},
        }
        
        geocoded_count = 0
        for country, coords in country_coords.items():
            cursor.execute("""
                UPDATE articles 
                SET latitude = ?, longitude = ?
                WHERE country = ? AND latitude IS NULL
            """, (coords['latitude'], coords['longitude'], country))
            
            if cursor.rowcount > 0:
                geocoded_count += cursor.rowcount
                print(f"   ✅ {country}: {cursor.rowcount} artículos geocodificados")
        
        print(f"   📊 Total geocodificado: {geocoded_count} artículos")
        
        # 5. MEJORAR ANÁLISIS DE CONFLICTOS DE ALTO RIESGO
        print("\\n⚔️ PASO 5: Mejorando detección de conflictos de alto riesgo...")
        
        # Palabras clave que indican conflictos de alto riesgo
        high_risk_keywords = [
            'war', 'guerra', 'militar', 'military', 'attack', 'ataque', 
            'bombing', 'bombardeo', 'invasion', 'invasión', 'conflict', 'conflicto',
            'crisis', 'tension', 'tensión', 'threat', 'amenaza', 'nuclear',
            'sanctions', 'sanciones', 'embargo', 'cease-fire', 'alto el fuego',
            'combat', 'combate', 'battle', 'batalla', 'siege', 'sitio',
            'troops', 'tropas', 'deployment', 'despliegue', 'strike', 'ataque aéreo'
        ]
        
        # Construir consulta para actualizar artículos con palabras clave de alto riesgo
        keyword_conditions = " OR ".join([f"LOWER(title) LIKE '%{keyword}%'" for keyword in high_risk_keywords])
        
        cursor.execute(f"""
            UPDATE articles 
            SET risk_level = 'high', risk_score = CASE 
                WHEN risk_score < 0.8 THEN 0.8 
                ELSE risk_score 
            END
            WHERE ({keyword_conditions})
            AND is_excluded != 1
        """)
        
        high_risk_updated = cursor.rowcount
        print(f"   ✅ {high_risk_updated} artículos reclasificados como alto riesgo por palabras clave")
        
        # 6. CREAR ZONAS DE CONFLICTO REALES
        print("\\n🎯 PASO 6: Creando zonas de conflicto reales...")
        
        # Crear tabla para zonas de conflicto si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflict_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_name TEXT UNIQUE,
                latitude REAL,
                longitude REAL,
                conflict_count INTEGER DEFAULT 0,
                avg_risk_score REAL DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Generar zonas de conflicto basadas en artículos de alto riesgo
        cursor.execute("""
            INSERT OR REPLACE INTO conflict_zones (zone_name, latitude, longitude, conflict_count, avg_risk_score)
            SELECT 
                country,
                AVG(latitude),
                AVG(longitude),
                COUNT(*),
                AVG(risk_score)
            FROM articles 
            WHERE risk_level = 'high' 
              AND latitude IS NOT NULL 
              AND longitude IS NOT NULL
              AND is_excluded != 1
              AND country IS NOT NULL
            GROUP BY country
            HAVING COUNT(*) >= 3
        """)
        
        zones_created = cursor.rowcount
        print(f"   ✅ {zones_created} zonas de conflicto creadas")
        
        # 7. ESTADÍSTICAS FINALES
        print("\\n📊 PASO 7: Estadísticas finales...")
        
        cursor.execute("SELECT risk_level, COUNT(*) FROM articles WHERE is_excluded != 1 GROUP BY risk_level")
        final_distribution = cursor.fetchall()
        print("   ⚖️ Distribución final de risk_level (solo artículos geopolíticos):")
        for level, count in final_distribution:
            print(f"   - {level}: {count} artículos")
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        geocoded_total = cursor.fetchone()[0]
        print(f"   📍 Total artículos con coordenadas: {geocoded_total}")
        
        cursor.execute("SELECT COUNT(*) FROM conflict_zones")
        zones_total = cursor.fetchone()[0]
        print(f"   🎯 Total zonas de conflicto: {zones_total}")
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_excluded = 1")
        excluded_total = cursor.fetchone()[0]
        print(f"   🚫 Total artículos excluidos: {excluded_total}")
        
        conn.commit()
        print("\\n✅ CORRECCIÓN COMPLETA FINALIZADA")
        print("🔄 Reinicia el servidor para ver los cambios")

if __name__ == "__main__":
    fix_all_issues()
