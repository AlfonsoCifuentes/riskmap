"""
Script para poblar la base de datos con datos de prueba para el dashboard.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import config, db_manager
from datetime import datetime, timedelta
import random

def insert_sample_articles():
    """Inserta artículos de muestra en la base de datos."""
    
    sample_articles = [
        {
            "title": "Tensiones Escalantes en el Mar de China Meridional",
            "content": "Las tensiones geopolíticas en el Mar de China Meridional han alcanzado nuevos niveles de preocupación tras una serie de incidentes navales entre fuerzas militares de diferentes naciones. Los analistas reportan un incremento significativo en la presencia naval militar en la región, con patrullas más frecuentes y ejercicios de entrenamiento que han generado alertas diplomáticas...",
            "url": "https://example.com/news1",
            "source": "Reuters International",
            "language": "es",
            "risk_level": "HIGH",
            "country": "China",
            "region": "Asia-Pacific",
            "summary": "Escalada de tensiones militares en disputa territorial del Mar de China Meridional",
            "risk_score": 7.5,
            "sentiment_score": 0.2,
            "sentiment_label": "negative",
            "conflict_type": "Military",
            "key_persons": "Admiral Chen Wei, General Rodriguez",
            "key_locations": "Spratly Islands, Paracel Islands, South China Sea",
            "visual_risk_score": 6.8,
            "detected_objects": "warships, fighter jets, military installations"
        },
        {
            "title": "Crisis Diplomática Entre India y Pakistán por Conflicto Fronterizo",
            "content": "Una nueva crisis diplomática ha emergido entre India y Pakistán tras reportes de actividad militar incrementada en la región de Cachemira. Los gobiernos de ambas naciones han emitido declaraciones oficiales expresando preocupaciones sobre violaciones territoriales, mientras que organizaciones internacionales hacen llamados a la moderación y el diálogo...",
            "url": "https://example.com/news2",
            "source": "BBC World Service",
            "language": "es",
            "risk_level": "HIGH",
            "country": "India",
            "region": "South Asia",
            "summary": "Escalada diplomática y militar en la región de Cachemira",
            "risk_score": 8.2,
            "sentiment_score": 0.1,
            "sentiment_label": "negative",
            "conflict_type": "Territorial",
            "key_persons": "Prime Minister Modi, PM Sharif",
            "key_locations": "Kashmir, Line of Control, Jammu",
            "visual_risk_score": 7.9,
            "detected_objects": "tanks, border fortifications, military convoys"
        },
        {
            "title": "Elecciones Anticipadas Generan Inestabilidad en Europa del Este",
            "content": "La convocatoria a elecciones anticipadas en varios países de Europa del Este ha generado un clima de incertidumbre política que preocupa a los mercados financieros internacionales. Los analistas políticos observan con atención las coaliciones emergentes y su potencial impacto en las relaciones con la Unión Europea y la OTAN...",
            "url": "https://example.com/news3",
            "source": "Financial Times",
            "language": "es",
            "risk_level": "MEDIUM",
            "country": "Poland",
            "region": "Eastern Europe",
            "summary": "Inestabilidad política por elecciones anticipadas en región estratégica",
            "risk_score": 5.4,
            "sentiment_score": -0.1,
            "sentiment_label": "neutral",
            "conflict_type": "Political",
            "key_persons": "President Kowalski, Chancellor Müller",
            "key_locations": "Warsaw, Budapest, Prague",
            "visual_risk_score": 4.2,
            "detected_objects": "protest crowds, government buildings, police formations"
        },
        {
            "title": "Ciberataques Masivos Afectan Infraestructura Energética Global",
            "content": "Una serie coordinada de ciberataques ha impactado sistemas de infraestructura energética en múltiples continentes, generando alertas de seguridad nacional en varios países desarrollados. Los expertos en ciberseguridad han identificado patrones sofisticados en los ataques que sugieren la participación de actores estatales con capacidades avanzadas...",
            "url": "https://example.com/news4",
            "source": "CyberSecurity Today",
            "language": "es",
            "risk_level": "CRITICAL",
            "country": "Global",
            "region": "Global",
            "summary": "Ataques cibernéticos coordinados contra infraestructura crítica mundial",
            "risk_score": 9.1,
            "sentiment_score": -0.3,
            "sentiment_label": "negative",
            "conflict_type": "Cyber",
            "key_persons": "Dr. Sarah Chen, Director James Wilson",
            "key_locations": "United States, Germany, Japan, Australia",
            "visual_risk_score": 8.5,
            "detected_objects": "power grids, data centers, control systems"
        },
        {
            "title": "Acuerdo de Cooperación Económica Reduce Tensiones Regionales",
            "content": "Un nuevo acuerdo de cooperación económica entre naciones del sudeste asiático ha sido recibido positivamente por la comunidad internacional, generando expectativas de reducción en las tensiones comerciales y políticas de la región. El acuerdo incluye provisiones para intercambio tecnológico y desarrollo de infraestructura compartida...",
            "url": "https://example.com/news5",
            "source": "Asian Economic Review",
            "language": "es",
            "risk_level": "LOW",
            "country": "Singapore",
            "region": "Southeast Asia",
            "summary": "Acuerdo regional promueve estabilidad económica y reducción de tensiones",
            "risk_score": 2.8,
            "sentiment_score": 0.6,
            "sentiment_label": "positive",
            "conflict_type": "Economic",
            "key_persons": "Minister Lee, President Jokowi",
            "key_locations": "Singapore, Jakarta, Manila, Bangkok",
            "visual_risk_score": 2.1,
            "detected_objects": "business meetings, trade facilities, diplomatic venues"
        },
        {
            "title": "Protestas Masivas en América Latina por Políticas Económicas",
            "content": "Múltiples ciudades en América Latina han sido escenario de protestas masivas en respuesta a nuevas políticas económicas implementadas por varios gobiernos de la región. Las manifestaciones han incluido sectores estudiantiles, laborales y de clase media, con demandas que van desde reformas fiscales hasta mejores condiciones de empleo...",
            "url": "https://example.com/news6",
            "source": "Latin America Today",
            "language": "es",
            "risk_level": "MEDIUM",
            "country": "Colombia",
            "region": "South America",
            "summary": "Movilizaciones sociales masivas por reformas económicas controvertidas",
            "risk_score": 6.0,
            "sentiment_score": -0.2,
            "sentiment_label": "negative",
            "conflict_type": "Social",
            "key_persons": "President Santos, Labor Leader Martinez",
            "key_locations": "Bogotá, Lima, Buenos Aires, Santiago",
            "visual_risk_score": 5.5,
            "detected_objects": "protest crowds, police barriers, government buildings"
        }
    ]
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        for i, article in enumerate(sample_articles):
            # Calcular fechas recientes
            days_ago = random.randint(0, 10)
            created_at = datetime.now() - timedelta(days=days_ago)
            published_at = created_at - timedelta(hours=random.randint(1, 6))
            
            cursor.execute('''
                INSERT OR REPLACE INTO articles (
                    title, content, url, source, published_at, language, created_at,
                    risk_level, country, region, summary, risk_score, sentiment_score,
                    sentiment_label, conflict_type, key_persons, key_locations,
                    visual_risk_score, detected_objects
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['title'],
                article['content'],
                article['url'],
                article['source'],
                published_at.isoformat(),
                article['language'],
                created_at.isoformat(),
                article['risk_level'],
                article['country'],
                article['region'],
                article['summary'],
                article['risk_score'],
                article['sentiment_score'],
                article['sentiment_label'],
                article['conflict_type'],
                article['key_persons'],
                article['key_locations'],
                article['visual_risk_score'],
                article['detected_objects']
            ))
        
        conn.commit()
        print(f"✓ Insertados {len(sample_articles)} artículos de prueba")
        
        # Verificar inserción
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        print(f"✓ Total de artículos en base de datos: {total}")
        
    except Exception as e:
        print(f"Error insertando datos: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Poblando base de datos con datos de prueba...")
    insert_sample_articles()
    print("¡Datos de prueba insertados correctamente!")
