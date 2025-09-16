"""
Script de Prueba - Análisis Geopolítico con Groq
===============================================

Este script permite probar la funcionalidad de análisis geopolítico
de manera independiente, sin necesidad del servidor Flask completo.

Uso:
    python test_groq_standalone.py

Requisitos:
    - groq (pip install groq)
    - python-dotenv (pip install python-dotenv)
    - Archivo .env con GROQ_API_KEY
"""

import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_sample_articles():
    """Obtiene artículos de muestra para el análisis"""
    return [
        {
            'id': 1,
            'title': 'Escalada militar en conflicto internacional',
            'content': 'Las tensiones militares han aumentado significativamente en la región con movilización de tropas y declaraciones oficiales que indican una posible escalada del conflicto. Los líderes mundiales expresan preocupación por las implicaciones.',
            'location': 'Europa Oriental',
            'risk_score': 0.8,
            'source': 'Reuters'
        },
        {
            'id': 2,
            'title': 'Crisis diplomática entre potencias mundiales',
            'content': 'Las relaciones bilaterales se han deteriorado tras las últimas declaraciones oficiales, generando incertidumbre en los mercados internacionales y afectando las cadenas de suministro globales.',
            'location': 'Asia-Pacífico',
            'risk_score': 0.7,
            'source': 'BBC'
        },
        {
            'id': 3,
            'title': 'Amenaza nuclear aumenta tensiones regionales',
            'content': 'Expertos en seguridad expresan preocupación por el desarrollo de capacidades nucleares en la región, escalando las tensiones internacionales y provocando respuestas diplomáticas.',
            'location': 'Asia Pacific',
            'risk_score': 0.95,
            'source': 'CNN'
        },
        {
            'id': 4,
            'title': 'Cumbre económica busca estabilidad global',
            'content': 'Los líderes mundiales se reúnen para discutir medidas económicas coordinadas que permitan estabilizar los mercados y fortalecer la cooperación internacional en tiempos de incertidumbre.',
            'location': 'Geneva',
            'risk_score': 0.3,
            'source': 'AP News'
        },
        {
            'id': 5,
            'title': 'Movimientos estratégicos en sector energético',
            'content': 'Los últimos desarrollos en el sector energético indican cambios importantes en las alianzas comerciales globales, con implicaciones geopolíticas significativas para el equilibrio de poder.',
            'location': 'Medio Oriente',
            'risk_score': 0.6,
            'source': 'Financial Times'
        }
    ]

def test_groq_analysis_standalone():
    """
    Prueba el análisis Groq de manera independiente
    """
    try:
        print("🚀 Iniciando prueba del análisis geopolítico con Groq...")
        
        # Verificar API Key
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("❌ Error: GROQ_API_KEY no encontrada en el archivo .env")
            print("💡 Asegúrate de tener un archivo .env con: GROQ_API_KEY=tu_clave_aquí")
            return False
        
        print(f"✅ API Key encontrada: {'*' * 10}{api_key[-4:]}")
        
        # Importar Groq
        try:
            from groq import Groq
            print("✅ Librería Groq importada correctamente")
        except ImportError:
            print("❌ Error: Librería Groq no instalada")
            print("💡 Instala con: pip install groq")
            return False
        
        # Obtener artículos de muestra
        articles = get_sample_articles()
        print(f"📰 Artículos de muestra obtenidos: {len(articles)}")
        
        # Preparar contexto
        articles_context = "\n\n".join([
            f"ARTÍCULO {i+1}:\nTítulo: {article['title']}\nContenido: {article['content']}\nUbicación: {article['location']}\nRiesgo: {article['risk_score']}"
            for i, article in enumerate(articles)
        ])
        
        # Crear prompt
        prompt = f"""
        Eres un periodista experto en geopolítica con 25 años de experiencia. Analiza los siguientes {len(articles)} artículos y genera un análisis geopolítico profesional.

        ARTÍCULOS:
        {articles_context}

        INSTRUCCIONES:
        1. Escribe en español con estilo periodístico humano
        2. Menciona líderes políticos específicos cuando sea relevante
        3. Conecta los eventos y analiza tendencias
        4. Usa párrafos HTML (<p>) para el contenido
        5. Enfatiza conceptos clave con <strong>

        RESPONDE SOLO CON JSON:
        {{
          "title": "Titular impactante y profesional",
          "subtitle": "Subtítulo que resuma el análisis",
          "content": "Contenido completo en HTML con párrafos <p>",
          "sources_count": {len(articles)}
        }}
        """
        
        # Inicializar cliente Groq
        client = Groq(api_key=api_key)
        print("🤖 Cliente Groq inicializado, generando análisis...")
        
        # Llamada a la API
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un analista geopolítico experto. Respondes ÚNICAMENTE en formato JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=2500,
            response_format={"type": "json_object"}
        )
        
        # Procesar respuesta
        response_content = response.choices[0].message.content
        print("✅ Respuesta recibida de Groq")
        
        try:
            analysis_data = json.loads(response_content)
            print("✅ JSON parseado correctamente")
            
            # Mostrar resultados
            print("\n" + "="*60)
            print("📊 RESULTADO DEL ANÁLISIS GEOPOLÍTICO")
            print("="*60)
            print(f"📰 Título: {analysis_data.get('title', 'N/A')}")
            print(f"📝 Subtítulo: {analysis_data.get('subtitle', 'N/A')}")
            print(f"📄 Contenido: {len(analysis_data.get('content', ''))} caracteres")
            print(f"📚 Fuentes: {analysis_data.get('sources_count', 0)}")
            print("="*60)
            
            # Guardar resultado
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"groq_analysis_test_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Resultado guardado en: {filename}")
            
            # Mostrar preview del contenido
            content = analysis_data.get('content', '')
            if content:
                print("\n📖 Preview del contenido:")
                print("-" * 40)
                # Mostrar primeros 300 caracteres
                preview = content.replace('<p>', '').replace('</p>', '\n').replace('<strong>', '**').replace('</strong>', '**')
                print(preview[:300] + "..." if len(preview) > 300 else preview)
                print("-" * 40)
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"🔍 Contenido recibido: {response_content[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def main():
    """Función principal"""
    print("🌍 Test Independiente - Análisis Geopolítico Groq")
    print("=" * 50)
    
    success = test_groq_analysis_standalone()
    
    if success:
        print("\n✅ Prueba completada exitosamente")
        print("🎉 El análisis geopolítico con Groq está funcionando correctamente")
    else:
        print("\n❌ Prueba fallida")
        print("🔧 Revisa la configuración y vuelve a intentar")
    
    print("\n👋 Fin de la prueba")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
