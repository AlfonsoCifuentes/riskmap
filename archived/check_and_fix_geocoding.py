#!/usr/bin/env python3
"""
Script para verificar y corregir la geocodificación
"""

import sqlite3
import os

def check_and_fix_geocoding():
    """Verificar el estado de geocodificación y corregir"""
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    print("🔍 VERIFICANDO ESTADO DE GEOCODIFICACIÓN")
    print("=" * 50)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Ver estructura de la tabla
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        print("📋 Columnas de la tabla articles:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # Verificar qué países tenemos
        cursor.execute("""
            SELECT country, COUNT(*) 
            FROM articles 
            WHERE country IS NOT NULL 
              AND (is_excluded IS NULL OR is_excluded != 1)
            GROUP BY country 
            ORDER BY COUNT(*) DESC 
            LIMIT 15
        """)
        
        print("\\n🌍 TOP 15 PAÍSES EN LA BD:")
        countries_found = cursor.fetchall()
        for country, count in countries_found:
            print(f"   {country}: {count} artículos")
        
        # Verificar coordenadas actuales
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """)
        coords_count = cursor.fetchone()[0]
        print(f"\\n📍 Artículos con coordenadas: {coords_count}")
        
        # Intentar geocodificar nuevamente con nombres más amplios
        print("\\n🔧 REINTENTANDO GEOCODIFICACIÓN...")
        
        # Diccionario de coordenadas expandido
        country_coords = {
            'Israel': {'lat': 31.0461, 'lng': 34.8516},
            'Palestine': {'lat': 31.9522, 'lng': 35.2332},
            'Palestina': {'lat': 31.9522, 'lng': 35.2332},
            'Gaza': {'lat': 31.3547, 'lng': 34.3088},
            'West Bank': {'lat': 31.9466, 'lng': 35.3027},
            'Estados Unidos': {'lat': 39.8283, 'lng': -98.5795},
            'United States': {'lat': 39.8283, 'lng': -98.5795},
            'EE.UU.': {'lat': 39.8283, 'lng': -98.5795},
            'EE. UU.': {'lat': 39.8283, 'lng': -98.5795},
            'EEUU': {'lat': 39.8283, 'lng': -98.5795},
            'Ukraine': {'lat': 48.3794, 'lng': 31.1656},
            'Ucrania': {'lat': 48.3794, 'lng': 31.1656},
            'China': {'lat': 35.8617, 'lng': 104.1954},
            'India': {'lat': 20.5937, 'lng': 78.9629},
            'Russia': {'lat': 61.5240, 'lng': 105.3188},
            'Rusia': {'lat': 61.5240, 'lng': 105.3188},
            'Pakistan': {'lat': 30.3753, 'lng': 69.3451},
            'United Kingdom': {'lat': 55.3781, 'lng': -3.4360},
            'Reino Unido': {'lat': 55.3781, 'lng': -3.4360},
            'Iran': {'lat': 32.4279, 'lng': 53.6880},
            'Irán': {'lat': 32.4279, 'lng': 53.6880},
            'France': {'lat': 46.2276, 'lng': 2.2137},
            'Francia': {'lat': 46.2276, 'lng': 2.2137},
            'Germany': {'lat': 51.1657, 'lng': 10.4515},
            'Alemania': {'lat': 51.1657, 'lng': 10.4515},
            'Turkey': {'lat': 38.9637, 'lng': 35.2433},
            'Turquía': {'lat': 38.9637, 'lng': 35.2433},
            'Syria': {'lat': 34.8021, 'lng': 38.9968},
            'Siria': {'lat': 34.8021, 'lng': 38.9968},
            'Lebanon': {'lat': 33.8547, 'lng': 35.8623},
            'Líbano': {'lat': 33.8547, 'lng': 35.8623},
            'Iraq': {'lat': 33.2232, 'lng': 43.6793},
            'Irak': {'lat': 33.2232, 'lng': 43.6793},
            'Afghanistan': {'lat': 33.9391, 'lng': 67.7100},
            'Afganistán': {'lat': 33.9391, 'lng': 67.7100},
            'Yemen': {'lat': 15.5527, 'lng': 48.5164},
            'Saudi Arabia': {'lat': 23.8859, 'lng': 45.0792},
            'Arabia Saudí': {'lat': 23.8859, 'lng': 45.0792},
            'Egypt': {'lat': 26.0975, 'lng': 30.0444},
            'Egipto': {'lat': 26.0975, 'lng': 30.0444},
            'Libya': {'lat': 26.3351, 'lng': 17.2283},
            'Libia': {'lat': 26.3351, 'lng': 17.2283},
            'Sudan': {'lat': 12.8628, 'lng': 30.2176},
            'Sudán': {'lat': 12.8628, 'lng': 30.2176},
            'Ethiopia': {'lat': 9.1450, 'lng': 40.4897},
            'Etiopía': {'lat': 9.1450, 'lng': 40.4897},
            'Somalia': {'lat': 5.1521, 'lng': 46.1996},
            'Nigeria': {'lat': 9.0820, 'lng': 8.6753},
            'South Korea': {'lat': 35.9078, 'lng': 127.7669},
            'Corea del Sur': {'lat': 35.9078, 'lng': 127.7669},
            'North Korea': {'lat': 40.3399, 'lng': 127.5101},
            'Corea del Norte': {'lat': 40.3399, 'lng': 127.5101},
            'Japan': {'lat': 36.2048, 'lng': 138.2529},
            'Japón': {'lat': 36.2048, 'lng': 138.2529},
            'Taiwan': {'lat': 23.6978, 'lng': 120.9605},
            'Taiwán': {'lat': 23.6978, 'lng': 120.9605},
            'Philippines': {'lat': 12.8797, 'lng': 121.7740},
            'Filipinas': {'lat': 12.8797, 'lng': 121.7740},
            'Vietnam': {'lat': 14.0583, 'lng': 108.2772},
            'Thailand': {'lat': 15.8700, 'lng': 100.9925},
            'Tailandia': {'lat': 15.8700, 'lng': 100.9925},
            'Myanmar': {'lat': 21.9162, 'lng': 95.9560},
            'Bangladesh': {'lat': 23.6850, 'lng': 90.3563},
            'Nepal': {'lat': 28.3949, 'lng': 84.1240},
            'Sri Lanka': {'lat': 7.8731, 'lng': 80.7718},
            'Indonesia': {'lat': -0.7893, 'lng': 113.9213},
            'Malaysia': {'lat': 4.2105, 'lng': 101.9758},
            'Malasia': {'lat': 4.2105, 'lng': 101.9758},
            'Singapore': {'lat': 1.3521, 'lng': 103.8198},
            'Singapur': {'lat': 1.3521, 'lng': 103.8198},
            'Australia': {'lat': -25.2744, 'lng': 133.7751},
            'New Zealand': {'lat': -40.9006, 'lng': 174.8860},
            'Nueva Zelanda': {'lat': -40.9006, 'lng': 174.8860},
            'Canada': {'lat': 56.1304, 'lng': -106.3468},
            'Canadá': {'lat': 56.1304, 'lng': -106.3468},
            'Mexico': {'lat': 23.6345, 'lng': -102.5528},
            'México': {'lat': 23.6345, 'lng': -102.5528},
            'Brazil': {'lat': -14.2350, 'lng': -51.9253},
            'Brasil': {'lat': -14.2350, 'lng': -51.9253},
            'Argentina': {'lat': -38.4161, 'lng': -63.6167},
            'Chile': {'lat': -35.6751, 'lng': -71.5430},
            'Colombia': {'lat': 4.5709, 'lng': -74.2973},
            'Venezuela': {'lat': 6.4238, 'lng': -66.5897},
            'Peru': {'lat': -9.1900, 'lng': -75.0152},
            'Perú': {'lat': -9.1900, 'lng': -75.0152},
            'Ecuador': {'lat': -1.8312, 'lng': -78.1834},
            'Bolivia': {'lat': -16.2902, 'lng': -63.5887},
            'Paraguay': {'lat': -23.4425, 'lng': -58.4438},
            'Uruguay': {'lat': -32.5228, 'lng': -55.7658},
            'Spain': {'lat': 40.4637, 'lng': -3.7492},
            'España': {'lat': 40.4637, 'lng': -3.7492},
            'Italy': {'lat': 41.8719, 'lng': 12.5674},
            'Italia': {'lat': 41.8719, 'lng': 12.5674},
            'Portugal': {'lat': 39.3999, 'lng': -8.2245},
            'Greece': {'lat': 39.0742, 'lng': 21.8243},
            'Grecia': {'lat': 39.0742, 'lng': 21.8243},
            'Poland': {'lat': 51.9194, 'lng': 19.1451},
            'Polonia': {'lat': 51.9194, 'lng': 19.1451},
            'Czech Republic': {'lat': 49.8175, 'lng': 15.4730},
            'Hungary': {'lat': 47.1625, 'lng': 19.5033},
            'Hungría': {'lat': 47.1625, 'lng': 19.5033},
            'Romania': {'lat': 45.9432, 'lng': 24.9668},
            'Rumania': {'lat': 45.9432, 'lng': 24.9668},
            'Bulgaria': {'lat': 42.7339, 'lng': 25.4858},
            'Serbia': {'lat': 44.0165, 'lng': 21.0059},
            'Croatia': {'lat': 45.1000, 'lng': 15.2000},
            'Croacia': {'lat': 45.1000, 'lng': 15.2000},
            'Slovenia': {'lat': 46.1512, 'lng': 14.9955},
            'Eslovenia': {'lat': 46.1512, 'lng': 14.9955},
            'Slovakia': {'lat': 48.6690, 'lng': 19.6990},
            'Eslovaquia': {'lat': 48.6690, 'lng': 19.6990},
            'Austria': {'lat': 47.5162, 'lng': 14.5501},
            'Switzerland': {'lat': 46.8182, 'lng': 8.2275},
            'Suiza': {'lat': 46.8182, 'lng': 8.2275},
            'Belgium': {'lat': 50.5039, 'lng': 4.4699},
            'Bélgica': {'lat': 50.5039, 'lng': 4.4699},
            'Netherlands': {'lat': 52.1326, 'lng': 5.2913},
            'Países Bajos': {'lat': 52.1326, 'lng': 5.2913},
            'Denmark': {'lat': 56.2639, 'lng': 9.5018},
            'Dinamarca': {'lat': 56.2639, 'lng': 9.5018},
            'Sweden': {'lat': 60.1282, 'lng': 18.6435},
            'Suecia': {'lat': 60.1282, 'lng': 18.6435},
            'Norway': {'lat': 60.4720, 'lng': 8.4689},
            'Noruega': {'lat': 60.4720, 'lng': 8.4689},
            'Finland': {'lat': 61.9241, 'lng': 25.7482},
            'Finlandia': {'lat': 61.9241, 'lng': 25.7482},
            'Iceland': {'lat': 64.9631, 'lng': -19.0208},
            'Islandia': {'lat': 64.9631, 'lng': -19.0208},
            'Ireland': {'lat': 53.4129, 'lng': -8.2439},
            'Irlanda': {'lat': 53.4129, 'lng': -8.2439},
            'Morocco': {'lat': 31.7917, 'lng': -7.0926},
            'Marruecos': {'lat': 31.7917, 'lng': -7.0926},
            'Algeria': {'lat': 28.0339, 'lng': 1.6596},
            'Argelia': {'lat': 28.0339, 'lng': 1.6596},
            'Tunisia': {'lat': 33.8869, 'lng': 9.5375},
            'Túnez': {'lat': 33.8869, 'lng': 9.5375},
            'Kenya': {'lat': -0.0236, 'lng': 37.9062},
            'Tanzania': {'lat': -6.3690, 'lng': 34.8888},
            'Uganda': {'lat': 1.3733, 'lng': 32.2903},
            'Rwanda': {'lat': -1.9403, 'lng': 29.8739},
            'Ruanda': {'lat': -1.9403, 'lng': 29.8739},
            'Burundi': {'lat': -3.3731, 'lng': 29.9189},
            'Democratic Republic of Congo': {'lat': -4.0383, 'lng': 21.7587},
            'República Democrática del Congo': {'lat': -4.0383, 'lng': 21.7587},
            'Central African Republic': {'lat': 6.6111, 'lng': 20.9394},
            'Chad': {'lat': 15.4542, 'lng': 18.7322},
            'Niger': {'lat': 17.6078, 'lng': 8.0817},
            'Níger': {'lat': 17.6078, 'lng': 8.0817},
            'Mali': {'lat': 17.5707, 'lng': -3.9962},
            'Malí': {'lat': 17.5707, 'lng': -3.9962},
            'Burkina Faso': {'lat': 12.2383, 'lng': -1.5616},
            'Ghana': {'lat': 7.9465, 'lng': -1.0232},
            'Ivory Coast': {'lat': 7.5400, 'lng': -5.5471},
            'Costa de Marfil': {'lat': 7.5400, 'lng': -5.5471},
            'Guinea': {'lat': 9.9456, 'lng': -9.6966},
            'Sierra Leone': {'lat': 8.4606, 'lng': -11.7799},
            'Liberia': {'lat': 6.4281, 'lng': -9.4295},
            'Senegal': {'lat': 14.4974, 'lng': -14.4524},
            'Gambia': {'lat': 13.4432, 'lng': -15.3101},
            'Guinea-Bissau': {'lat': 11.8037, 'lng': -15.1804},
            'Cape Verde': {'lat': 16.5388, 'lng': -24.0132},
            'Cabo Verde': {'lat': 16.5388, 'lng': -24.0132},
            'Mauritania': {'lat': 21.0079, 'lng': -10.9408},
            'South Africa': {'lat': -30.5595, 'lng': 22.9375},
            'Sudáfrica': {'lat': -30.5595, 'lng': 22.9375},
            'Namibia': {'lat': -22.9576, 'lng': 18.4904},
            'Botswana': {'lat': -22.3285, 'lng': 24.6849},
            'Zimbabwe': {'lat': -19.0154, 'lng': 29.1549},
            'Zambia': {'lat': -13.1339, 'lng': 27.8493},
            'Malawi': {'lat': -13.2543, 'lng': 34.3015},
            'Mozambique': {'lat': -18.6657, 'lng': 35.5296},
            'Madagascar': {'lat': -18.7669, 'lng': 46.8691},
            'Mauritius': {'lat': -20.3484, 'lng': 57.5522},
            'Seychelles': {'lat': -4.6796, 'lng': 55.4920},
            'Comoros': {'lat': -11.6455, 'lng': 43.3333},
        }
        
        geocoded_count = 0
        
        for country in countries_found:
            country_name = country[0]
            if country_name in country_coords:
                coords = country_coords[country_name]
                cursor.execute("""
                    UPDATE articles 
                    SET latitude = ?, longitude = ?
                    WHERE country = ? AND latitude IS NULL
                """, (coords['lat'], coords['lng'], country_name))
                
                if cursor.rowcount > 0:
                    geocoded_count += cursor.rowcount
                    print(f"   ✅ {country_name}: {cursor.rowcount} artículos geocodificados")
        
        print(f"\\n📊 Total geocodificado: {geocoded_count} artículos")
        
        # Verificar coordenadas después de la geocodificación
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
              AND (is_excluded IS NULL OR is_excluded != 1)
        """)
        final_coords_count = cursor.fetchone()[0]
        print(f"📍 Artículos geopolíticos con coordenadas: {final_coords_count}")
        
        conn.commit()
        print("\\n✅ GEOCODIFICACIÓN CORREGIDA")

if __name__ == "__main__":
    check_and_fix_geocoding()
