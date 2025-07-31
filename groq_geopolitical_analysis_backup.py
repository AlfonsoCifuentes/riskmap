"""
BACKUP - Análisis Geopolítico Avanzado por IA con Groq
========================================================

Este archivo contiene toda la lógica del análisis geopolítico que usa Groq AI
para generar artículos periodísticos profesionales basados en noticias actuales.

Funcionalidades incluidas:
1. Generación de análisis con Groq API
2. Análisis de respaldo (fallback)
3. Obtención de artículos mock/reales
4. Endpoint Flask completo
5. Manejo robusto de errores

Creado: 31 de Julio, 2025
Autor: Sistema de IA Dashboard
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import request, jsonify

# Configurar logging
logger = logging.getLogger(__name__)

# =====================================================
# FUNCIONES PRINCIPALES DE ANÁLISIS GROQ
# =====================================================

def generate_groq_geopolitical_analysis(articles):
    """
    Genera un análisis geopolítico usando Groq API
    
    Args:
        articles (list): Lista de artículos para analizar
        
    Returns:
        dict: Análisis geopolítico estructurado
    """
    try:
        from groq import Groq
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            logger.warning("GROQ_API_KEY no encontrada. Usando análisis de respaldo.")
            return generate_fallback_analysis(articles)
        
        client = Groq(api_key=groq_api_key)
        
        articles_context = "\n\n".join([
            f"ARTÍCULO {i+1}:\nTítulo: {article.get('title', 'N/A')}\nContenido: {article.get('content', 'N/A')[:500]}...\nUbicación: {article.get('location', 'N/A')}"
            for i, article in enumerate(articles[:20])
        ])
        
        prompt = f"""
        Eres un periodista experto en geopolítica con 25 años de experiencia, escribiendo para un periódico de renombre mundial. Tu estilo es incisivo, humano y riguroso. No temes nombrar líderes, países o conflictos, y ofreces predicciones fundamentadas pero humildes.

        Analiza los siguientes {len(articles)} artículos de noticias y genera un análisis geopolítico en formato HTML.

        ARTÍCULOS DE CONTEXTO:
        {articles_context}

        INSTRUCCIONES CLAVE:
        1.  **Estilo Periodístico Humano**: Escribe con una voz personal y experta, no como una IA. Usa un lenguaje rico y evocador.
        2.  **Nombres Propios**: Menciona líderes (Putin, Xi Jinping, Biden, Zelensky), países y regiones relevantes.
        3.  **Análisis Profundo**: Conecta los puntos entre diferentes conflictos y tendencias. No te limites a resumir.
        4.  **Opinión Fundamentada**: Expresa tu opinión y proyecciones, pero siempre desde la humildad y el rigor analítico.
        5.  **Formato HTML Específico**:
            *   El `content` debe ser una cadena de texto HTML.
            *   Usa párrafos `<p>` para el cuerpo del texto.
            *   **No uses** `<h1>`, `<h2>`, etc., dentro del `content`. El título y subtítulo van en sus propios campos.
            *   Puedes usar `<strong>` para enfatizar conceptos clave.

        RESPONDE ÚNICAMENTE CON UN OBJETO JSON VÁLIDO con la siguiente estructura:
        {{
          "title": "Un titular principal, impactante y profesional",
          "subtitle": "Un subtítulo que resuma la esencia del análisis",
          "content": "El cuerpo completo del artículo en HTML, usando solo <p> y <strong>.",
          "sources_count": {len(articles)}
        }}
        """

        logger.info("🤖 Generando análisis con Groq AI...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analista geopolítico de élite. Tu única salida es un objeto JSON válido que sigue estrictamente la estructura solicitada."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.75,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        response_content = chat_completion.choices[0].message.content
        logger.info("✅ Análisis Groq generado exitosamente.")
        
        try:
            analysis_data = json.loads(response_content)
            # Validar campos requeridos
            if 'title' in analysis_data and 'subtitle' in analysis_data and 'content' in analysis_data:
                return analysis_data
            else:
                logger.error("JSON de Groq incompleto. Faltan campos requeridos.")
                return generate_fallback_analysis(articles)
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar JSON de Groq. Contenido: {response_content[:500]}...")
            return generate_fallback_analysis(articles)
            
    except ImportError:
        logger.error("Librería Groq no instalada. Ejecuta: pip install groq")
        return generate_fallback_analysis(articles)
    except Exception as e:
        logger.error(f"Error en la llamada a la API de Groq: {e}")
        return generate_fallback_analysis(articles)

def generate_fallback_analysis(articles):
    """
    Genera análisis de respaldo cuando Groq no está disponible
    
    Args:
        articles (list): Lista de artículos para el contexto
        
    Returns:
        dict: Análisis geopolítico de respaldo
    """
    current_date = datetime.now().strftime("%d de %B de %Y")
    
    return {
        "title": "El Tablero Geopolítico se Reconfigura en Tiempo Real",
        "subtitle": "Tensiones globales y nuevas alianzas redefinen el orden mundial mientras la incertidumbre marca el rumbo internacional",
        "content": f"""
            <p>El panorama geopolítico mundial atraviesa uno de sus momentos más complejos de las últimas décadas. Las tensiones que se extienden desde Europa Oriental hasta el Pacífico están redibujando las alianzas internacionales y poniendo a prueba el orden establecido tras la Guerra Fría.</p>
            
            <p>En Europa, el conflicto en Ucrania ha consolidado la posición de la OTAN como un actor determinante en la seguridad continental. La respuesta occidental, liderada por Estados Unidos y respaldada firmemente por Reino Unido y Polonia, ha demostrado una cohesión que pocos predecían. Sin embargo, las fisuras emergen cuando se analiza la dependencia energética europea, particularmente de Alemania, que se ve obligada a reconsiderar décadas de política energética.</p>

            <p>El presidente <strong>Volodymyr Zelensky</strong> ha logrado mantener el apoyo internacional, aunque las elecciones en Estados Unidos podrían alterar significativamente este respaldo. La fatiga bélica en algunos sectores de la opinión pública occidental es palpable, y líderes como <strong>Viktor Orbán</strong> en Hungría han sido voces discordantes dentro de la alianza europea.</p>

            <p>En el frente asiático, las tensiones en el estrecho de Taiwán han escalado a niveles que recuerdan los momentos más álgidos de la Guerra Fría. <strong>Xi Jinping</strong> ha intensificado la retórica sobre la reunificación, mientras que la administración estadounidense, junto con Japón y Australia, han reforzado su presencia militar en la región. Corea del Norte, bajo <strong>Kim Jong-un</strong>, ha aprovechado estas tensiones para acelerar su programa nuclear.</p>

            <p>La crisis energética global ha puesto de manifiesto la vulnerabilidad de las cadenas de suministro internacionales. Los países del Golfo, liderados por Arabia Saudí y Emiratos Árabes Unidos, han recuperado protagonismo geopolítico, navegando hábilmente entre las presiones occidentales y sus relaciones con Rusia y China. <strong>Mohammed bin Salman</strong> ha demostrado una diplomacia pragmática que desafía las expectativas tradicionales.</p>

            <p>En América Latina, el escenario es igualmente complejo. Brasil, bajo <strong>Luiz Inácio Lula da Silva</strong>, busca posicionarse como mediador en los conflictos globales, mientras que países como Colombia y Chile redefinen sus alianzas regionales. La influencia china en la región crece silenciosamente, ofreciendo alternativas de inversión que compiten directamente con los tradicionales socios occidentales.</p>

            <p>África emerge como el continente donde se libra una nueva guerra fría silenciosa. Rusia, a través de grupos mercenarios, y China, mediante su iniciativa de la Franja y la Ruta, compiten por la influencia en un continente que alberga recursos cruciales para la transición energética mundial. Francia ve erosionada su influencia tradicional en el Sahel, mientras que nuevos actores como Turquía e India buscan su espacio.</p>

            <p>El multilateralismo atraviesa una crisis profunda. Las Naciones Unidas muestran signos evidentes de obsolescencia institucional, con un Consejo de Seguridad paralizado por los vetos cruzados entre las potencias. Organizaciones como el G7 y el G20 luchan por mantener relevancia en un mundo cada vez más fragmentado en bloques regionales.</p>

            <p>La tecnología se ha convertido en el nuevo campo de batalla geopolítico. La competencia entre Estados Unidos y China por el dominio de la inteligencia artificial, los semiconductores y las tecnologías 5G está redefiniendo las cadenas de valor globales. Europa intenta mantener su autonomía estratégica, pero se encuentra atrapada entre las dos superpotencias tecnológicas.</p>

            <p>Mirando hacia el futuro, tres escenarios parecen posibles: una bipolarización renovada entre bloques liderados por Washington y Beijing, una multipolaridad caótica donde las potencias medias ganen protagonismo, o una fragmentación regional que privilegie las alianzas geográficas sobre las ideológicas. La próxima década será crucial para determinar cuál de estas tendencias prevalece.</p>

            <p>Como observadores de este complejo tablero, debemos resistir la tentación de las predicciones categóricas. La historia nos enseña que los momentos de mayor incertidumbre son también los de mayor oportunidad para el cambio. Lo que sí parece claro es que el orden mundial tal como lo conocemos está siendo desafiado desde múltiples frentes, y las decisiones que tomen los líderes mundiales en los próximos meses definirán el rumbo de las próximas décadas.</p>
        """,
        "sources_count": len(articles),
        "analysis_date": datetime.now().isoformat()
    }

# =====================================================
# FUNCIONES DE OBTENCIÓN DE DATOS
# =====================================================

def get_top_articles_from_db(limit=20):
    """
    Obtiene los artículos más importantes de la base de datos
    
    Args:
        limit (int): Número máximo de artículos a obtener
        
    Returns:
        list: Lista de artículos mock/reales
    """
    try:
        # Por ahora usar datos mock - en producción conectar a la BD real
        mock_articles = [
            {
                'id': 1,
                'title': 'Escalada militar en conflicto internacional',
                'content': 'Las tensiones militares han aumentado significativamente en la región con movilización de tropas y declaraciones oficiales que indican una posible escalada del conflicto.',
                'location': 'Europa Oriental',
                'risk_score': 0.8,
                'source': 'Reuters',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'title': 'Crisis diplomática entre potencias mundiales',
                'content': 'Las relaciones bilaterales se han deteriorado tras las últimas declaraciones oficiales, generando incertidumbre en los mercados internacionales.',
                'location': 'Asia-Pacífico',
                'risk_score': 0.7,
                'source': 'BBC',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 3,
                'title': 'Movimientos económicos estratégicos',
                'content': 'Los últimos movimientos en el sector energético indican cambios importantes en las alianzas comerciales globales.',
                'location': 'Medio Oriente',
                'risk_score': 0.6,
                'source': 'CNN',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 4,
                'title': 'Amenaza nuclear en Asia Pacific aumenta tensiones',
                'content': 'Expertos en seguridad expresan preocupación por el desarrollo de armas nucleares en la región, escalando las tensiones internacionales.',
                'location': 'Asia Pacific',
                'risk_score': 0.95,
                'source': 'BBC News',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 5,
                'title': 'Cumbre económica internacional concluye exitosamente',
                'content': 'Los líderes mundiales alcanzan acuerdos comerciales importantes para la estabilidad económica global.',
                'location': 'Geneva',
                'risk_score': 0.3,
                'source': 'AP News',
                'created_at': datetime.now().isoformat()
            }
        ]
        
        # Simular más artículos para análisis robusto
        for i in range(6, limit + 1):
            mock_articles.append({
                'id': i,
                'title': f'Desarrollo geopolítico importante #{i}',
                'content': f'Análisis de eventos significativos en diferentes regiones que impactan la estabilidad global y regional. Evento {i} con implicaciones importantes para el equilibrio de poder mundial.',
                'location': f'Región {i % 6 + 1}',
                'risk_score': 0.4 + (i % 6) * 0.1,
                'source': f'Agencia Internacional {i}',
                'created_at': datetime.now().isoformat()
            })
        
        return mock_articles[:limit]
        
    except Exception as e:
        logger.error(f"Error obteniendo artículos: {e}")
        return []

# =====================================================
# VERSIÓN ALTERNATIVA DE GROQ (CON FORMATO DIFERENTE)
# =====================================================

def generate_groq_alternative_analysis(articles):
    """
    Versión alternativa del análisis Groq con formato más estructurado
    
    Args:
        articles (list): Lista de artículos para analizar
        
    Returns:
        dict: Análisis geopolítico alternativo
    """
    try:
        from groq import Groq
        
        # Inicializar cliente Groq
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY no encontrada en variables de entorno")
        
        client = Groq(api_key=groq_api_key)
        
        # Preparar contexto de artículos
        articles_context = ""
        for i, article in enumerate(articles[:20], 1):
            articles_context += f"""
            Artículo {i}:
            Título: {article.get('title', 'Sin título')}
            Ubicación: {article.get('location', 'Sin ubicación')}
            Contenido: {article.get('content', 'Sin contenido')[:300]}
            Nivel de Riesgo: {article.get('risk_score', 0)}
            Fuente: {article.get('source', 'Sin fuente')}
            ---
            """
        
        # Prompt especializado para análisis geopolítico
        prompt = f"""
        Como analista geopolítico senior, analiza los siguientes {len(articles)} artículos de noticias y genera un análisis integral en estilo periodístico profesional.

        CONTEXTO DE ARTÍCULOS:
        {articles_context}

        INSTRUCCIONES ESPECÍFICAS:
        1. Escribe en español con estilo periodístico profesional
        2. Estructura el análisis en párrafos bien definidos
        3. Identifica patrones y conexiones entre eventos
        4. Evalúa implicaciones geopolíticas a corto y mediano plazo
        5. Menciona regiones y actores clave
        6. Usa un tono objetivo pero accesible
        7. Longitud: aproximadamente 800-1200 palabras

        ESTRUCTURA REQUERIDA:
        - Título llamativo y profesional
        - Subtítulo que capture la esencia del análisis
        - Introducción que establezca el contexto global actual
        - Desarrollo de los principales temas identificados
        - Análisis de implicaciones y tendencias
        - Conclusión que sintetice los puntos clave

        Genera el análisis ahora:
        """
        
        # Llamada a Groq
        logger.info("🤖 Generando análisis alternativo con Groq AI...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Modelo actualizado
            messages=[
                {"role": "system", "content": "Eres un analista geopolítico experto que escribe análisis profesionales en español."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        analysis_content = response.choices[0].message.content
        logger.info("✅ Análisis Groq alternativo generado exitosamente")
        
        return {
            'title': 'El Tablero Geopolítico se Reconfigura en Tiempo Real',
            'subtitle': 'Análisis integral de los desarrollos más significativos que están redefiniendo el equilibrio mundial',
            'content': analysis_content,
            'sources_count': len(articles),
            'generated_at': datetime.now().isoformat(),
            'ai_model': 'Groq Llama-3.1-8b-instant',
            'analysis_type': 'geopolitical_journalistic_alternative'
        }
        
    except Exception as e:
        logger.error(f"Error en análisis Groq alternativo: {e}")
        return generate_fallback_analysis(articles)

# =====================================================
# ENDPOINT FLASK COMPLETO
# =====================================================

def create_groq_analysis_endpoint(app):
    """
    Crea el endpoint Flask para el análisis Groq
    
    Args:
        app: Instancia de Flask
    """
    
    @app.route('/api/generate-ai-analysis', methods=['POST'])
    def generate_groq_ai_analysis():
        """
        Endpoint para generar análisis geopolítico con Groq IA
        """
        try:
            data = request.get_json() or {}
            
            # Obtener artículos desde la base de datos o usar los proporcionados
            articles = data.get('articles')
            if not articles:
                articles = get_top_articles_from_db(limit=20)
            
            if not articles:
                return jsonify({
                    'error': 'No se encontraron artículos para analizar',
                    'success': False
                }), 400
            
            # Determinar tipo de análisis
            analysis_type = data.get('analysis_type', 'standard')
            
            if analysis_type == 'alternative':
                analysis_result = generate_groq_alternative_analysis(articles)
            else:
                analysis_result = generate_groq_geopolitical_analysis(articles)
            
            # Estructurar respuesta
            response = {
                'success': True,
                'analysis': analysis_result,
                'metadata': {
                    'articles_analyzed': len(articles),
                    'generation_time': datetime.now().isoformat(),
                    'endpoint_version': '1.0',
                    'analysis_type': analysis_type
                }
            }
            
            logger.info(f"✅ Análisis geopolítico generado: {len(articles)} artículos procesados")
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"❌ Error en endpoint de análisis: {e}")
            return jsonify({
                'error': f'Error generando análisis: {str(e)}',
                'success': False
            }), 500

# =====================================================
# FUNCIÓN DE TESTING
# =====================================================

def test_groq_analysis():
    """
    Función para probar el análisis Groq independientemente
    """
    # Cargar variables de entorno
    load_dotenv()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Obtener artículos de prueba
    test_articles = get_top_articles_from_db(limit=5)
    
    print("🧪 Iniciando test del análisis Groq...")
    print(f"📰 Artículos obtenidos: {len(test_articles)}")
    
    # Generar análisis
    result = generate_groq_geopolitical_analysis(test_articles)
    
    print("✅ Análisis generado:")
    print(f"Título: {result.get('title', 'N/A')}")
    print(f"Subtítulo: {result.get('subtitle', 'N/A')}")
    print(f"Contenido: {len(result.get('content', ''))} caracteres")
    print(f"Fuentes: {result.get('sources_count', 0)}")
    
    return result

# =====================================================
# CONFIGURACIÓN PARA EJECUTAR COMO SCRIPT INDEPENDIENTE
# =====================================================

if __name__ == "__main__":
    print("🚀 Test independiente del análisis geopolítico Groq")
    result = test_groq_analysis()
    
    # Guardar resultado en archivo
    with open('test_groq_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("💾 Resultado guardado en 'test_groq_result.json'")
