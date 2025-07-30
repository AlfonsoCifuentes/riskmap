#!/usr/bin/env python3
"""
Script de prueba para verificar el filtro de deportes
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.content_classifier import ContentClassifier
from data_ingestion.rss_fetcher import RSSFetcher
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_content_classifier():
    """Prueba el clasificador de contenido con ejemplos deportivos."""
    logger.info("=== PROBANDO CLASIFICADOR DE CONTENIDO ===")
    
    classifier = ContentClassifier()
    
    # Casos de prueba
    test_cases = [
        # Casos deportivos (deberían ser filtrados)
        {
            'title': 'Real Madrid vence al Barcelona en el Clásico',
            'content': 'El equipo merengue ganó 2-1 en el Santiago Bernabéu con goles de Benzema y Vinicius. El partido fue muy emocionante.',
            'expected': 'sports_entertainment'
        },
        {
            'title': 'NBA Finals: Lakers vs Warriors',
            'content': 'The basketball championship game will be played tonight at the Staples Center. LeBron James leads the Lakers.',
            'expected': 'sports_entertainment'
        },
        {
            'title': 'Olimpiadas de París 2024: Resultados de natación',
            'content': 'Los nadadores españoles consiguieron tres medallas en la piscina olímpica. Gran actuación del equipo nacional.',
            'expected': 'sports_entertainment'
        },
        {
            'title': 'Manchester United signs new player',
            'content': 'The football club announced the signing of a new midfielder for the upcoming season. The transfer fee was 50 million euros.',
            'expected': 'sports_entertainment'
        },
        
        # Casos geopolíticos (NO deberían ser filtrados)
        {
            'title': 'Tensiones militares en Europa Oriental',
            'content': 'Las fuerzas armadas de varios países han aumentado su presencia en la frontera. La situación diplomática se deteriora.',
            'expected': 'military_conflict'
        },
        {
            'title': 'Economic sanctions imposed on country',
            'content': 'The international community has decided to impose trade restrictions and financial sanctions following recent political developments.',
            'expected': 'economic_security'
        },
        {
            'title': 'Climate change summit in Geneva',
            'content': 'World leaders gather to discuss carbon emissions and environmental policies. New agreements on renewable energy expected.',
            'expected': 'climate_environment'
        },
        {
            'title': 'Cyber attack on government infrastructure',
            'content': 'Hackers targeted critical systems causing widespread disruption. Intelligence agencies investigate the security breach.',
            'expected': 'cyber_security'
        },
        
        # Casos ambiguos
        {
            'title': 'Política deportiva del gobierno',
            'content': 'El ministro anunció nuevas políticas para el deporte nacional y la inversión en infraestructura deportiva.',
            'expected': 'general_news'  # Podría ser política o deportes
        }
    ]
    
    print(f"\nProbando {len(test_cases)} casos de prueba:")
    print("-" * 80)
    
    correct = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        title = case['title']
        content = case['content']
        expected = case['expected']
        
        # Clasificar
        result = classifier.classify(f"{title} {content}")
        
        # Verificar si es deportivo
        is_sports = classifier._is_sports_entertainment(f"{title} {content}".lower())
        
        # Mostrar resultado
        status = "✅" if result == expected else "❌"
        sports_flag = "🏈" if is_sports else "📰"
        
        print(f"{status} {sports_flag} Caso {i}:")
        print(f"   Título: {title}")
        print(f"   Clasificación: {result} (esperado: {expected})")
        print(f"   Es deportivo: {is_sports}")
        
        if result == expected:
            correct += 1
        
        print()
    
    accuracy = (correct / total) * 100
    print(f"Precisión: {correct}/{total} ({accuracy:.1f}%)")
    
    return accuracy

def test_rss_filter():
    """Prueba el filtro RSS con ejemplos."""
    logger.info("=== PROBANDO FILTRO RSS ===")
    
    # Crear fetcher (sin base de datos real)
    try:
        fetcher = RSSFetcher(':memory:')  # Base de datos en memoria para pruebas
        
        # Casos de prueba para el filtro geopolítico
        test_articles = [
            {
                'title': 'Barcelona defeats Real Madrid 3-1',
                'content': 'The football match was exciting with goals from Messi and Suarez. The stadium was packed with fans.',
                'language': 'en',
                'should_pass': False
            },
            {
                'title': 'Military tensions rise in Eastern Europe',
                'content': 'Armed forces have been deployed to the border region amid diplomatic crisis. International observers express concern.',
                'language': 'en',
                'should_pass': True
            },
            {
                'title': 'Nuevo récord mundial en natación',
                'content': 'El nadador estableció un nuevo récord en los 100 metros libres durante el campeonato mundial de natación.',
                'language': 'es',
                'should_pass': False
            },
            {
                'title': 'Sanciones económicas contra país',
                'content': 'La comunidad internacional impone restricciones comerciales debido a violaciones de derechos humanos.',
                'language': 'es',
                'should_pass': True
            }
        ]
        
        print(f"\nProbando filtro geopolítico con {len(test_articles)} artículos:")
        print("-" * 80)
        
        correct = 0
        total = len(test_articles)
        
        for i, article in enumerate(test_articles, 1):
            title = article['title']
            content = article['content']
            language = article['language']
            should_pass = article['should_pass']
            
            # Probar filtro geopolítico
            passes_filter = fetcher.is_geopolitical_content(title, content, language)
            
            # Probar clasificador adicional
            text_for_classification = f"{title} {content}"
            category = fetcher.content_classifier.classify(text_for_classification)
            is_sports = category == 'sports_entertainment'
            
            # Determinar si pasaría el filtro completo
            would_be_saved = passes_filter and not is_sports
            
            # Verificar resultado
            status = "✅" if would_be_saved == should_pass else "❌"
            filter_flag = "📰" if passes_filter else "🚫"
            sports_flag = "🏈" if is_sports else "📄"
            
            print(f"{status} Artículo {i}:")
            print(f"   Título: {title}")
            print(f"   {filter_flag} Pasa filtro geopolítico: {passes_filter}")
            print(f"   {sports_flag} Categoría: {category}")
            print(f"   Sería guardado: {would_be_saved} (esperado: {should_pass})")
            
            if would_be_saved == should_pass:
                correct += 1
            
            print()
        
        accuracy = (correct / total) * 100
        print(f"Precisión del filtro: {correct}/{total} ({accuracy:.1f}%)")
        
        return accuracy
        
    except Exception as e:
        logger.error(f"Error en prueba de filtro RSS: {e}")
        return 0

def test_sports_patterns():
    """Prueba patrones específicos de deportes."""
    logger.info("=== PROBANDO PATRONES DEPORTIVOS ===")
    
    classifier = ContentClassifier()
    
    # Patrones deportivos específicos
    sports_patterns = [
        "El Real Madrid ganó el partido",
        "NBA championship finals tonight",
        "Olimpiadas de Tokio 2024",
        "Manchester United transfers",
        "Copa del Mundo FIFA",
        "Champions League final",
        "Wimbledon tennis tournament",
        "Formula 1 Grand Prix",
        "Super Bowl halftime show",
        "Premier League standings"
    ]
    
    # Patrones geopolíticos
    geopolitical_patterns = [
        "Military conflict in Ukraine",
        "Economic sanctions imposed",
        "Diplomatic summit in Geneva",
        "Cyber attack on infrastructure",
        "Climate change negotiations",
        "Refugee crisis at border",
        "Nuclear weapons program",
        "Trade war escalation",
        "Terrorism threat level raised",
        "International peace treaty"
    ]
    
    print("\nPatrones deportivos (deberían ser identificados como deportes):")
    sports_correct = 0
    for pattern in sports_patterns:
        is_sports = classifier._is_sports_entertainment(pattern.lower())
        category = classifier.classify(pattern)
        status = "✅" if is_sports else "❌"
        print(f"  {status} '{pattern}' -> Deportivo: {is_sports}, Categoría: {category}")
        if is_sports:
            sports_correct += 1
    
    print(f"\nPrecisión deportes: {sports_correct}/{len(sports_patterns)} ({(sports_correct/len(sports_patterns)*100):.1f}%)")
    
    print("\nPatrones geopolíticos (NO deberían ser identificados como deportes):")
    geo_correct = 0
    for pattern in geopolitical_patterns:
        is_sports = classifier._is_sports_entertainment(pattern.lower())
        category = classifier.classify(pattern)
        status = "✅" if not is_sports else "❌"
        print(f"  {status} '{pattern}' -> Deportivo: {is_sports}, Categoría: {category}")
        if not is_sports:
            geo_correct += 1
    
    print(f"\nPrecisión geopolítica: {geo_correct}/{len(geopolitical_patterns)} ({(geo_correct/len(geopolitical_patterns)*100):.1f}%)")
    
    total_correct = sports_correct + geo_correct
    total_patterns = len(sports_patterns) + len(geopolitical_patterns)
    overall_accuracy = (total_correct / total_patterns) * 100
    
    return overall_accuracy

def main():
    """Función principal de pruebas."""
    print("🔍 PRUEBAS DEL FILTRO DE DEPORTES")
    print("=" * 50)
    
    try:
        # Prueba 1: Clasificador de contenido
        accuracy1 = test_content_classifier()
        
        # Prueba 2: Filtro RSS
        accuracy2 = test_rss_filter()
        
        # Prueba 3: Patrones específicos
        accuracy3 = test_sports_patterns()
        
        # Resumen final
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE RESULTADOS")
        print("=" * 50)
        print(f"Clasificador de contenido: {accuracy1:.1f}%")
        print(f"Filtro RSS completo: {accuracy2:.1f}%")
        print(f"Patrones específicos: {accuracy3:.1f}%")
        
        average_accuracy = (accuracy1 + accuracy2 + accuracy3) / 3
        print(f"\nPrecisión promedio: {average_accuracy:.1f}%")
        
        if average_accuracy >= 80:
            print("✅ El filtro de deportes funciona correctamente")
        elif average_accuracy >= 60:
            print("⚠️  El filtro de deportes necesita mejoras")
        else:
            print("❌ El filtro de deportes requiere revisión")
        
    except Exception as e:
        logger.error(f"Error en las pruebas: {e}")
        print("❌ Error ejecutando las pruebas")

if __name__ == "__main__":
    main()