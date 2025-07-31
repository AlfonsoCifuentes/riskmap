"""
Test script para verificar la funcionalidad de Groq integrada
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variables de entorno cargadas")
except ImportError:
    print("⚠️ python-dotenv no instalado")

def test_groq_integration():
    """Test de la integración con Groq"""
    print("🧪 Iniciando test de integración Groq...")
    
    # Check API key
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key:
        print(f"✅ GROQ_API_KEY encontrada: {groq_api_key[:10]}...")
    else:
        print("❌ GROQ_API_KEY no encontrada")
        return False
    
    # Test basic import
    try:
        from groq import Groq
        print("✅ Librería Groq importada correctamente")
    except ImportError as e:
        print(f"❌ Error importando Groq: {e}")
        return False
    
    # Test client creation
    try:
        client = Groq(api_key=groq_api_key)
        print("✅ Cliente Groq creado correctamente")
    except Exception as e:
        print(f"❌ Error creando cliente Groq: {e}")
        return False
    
    # Test basic API call
    try:
        print("🤖 Probando llamada básica a la API...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "Hola, ¿puedes responder brevemente que funciona correctamente?"}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✅ Respuesta de Groq: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error en llamada a API Groq: {e}")
        return False

def test_app_methods():
    """Test de los métodos de la aplicación"""
    print("\n🧪 Probando métodos de la aplicación...")
    
    try:
        # Import the app class
        from app_moderncopia31alas945 import RiskMapUnifiedApplication
        print("✅ Clase RiskMapUnifiedApplication importada")
        
        # Create instance
        app = RiskMapUnifiedApplication()
        print("✅ Instancia de aplicación creada")
        
        # Test get articles from DB
        articles = app.get_top_articles_from_db(limit=5)
        print(f"✅ Artículos obtenidos: {len(articles)}")
        
        if articles:
            print("📰 Ejemplo de artículo:")
            for key, value in articles[0].items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {key}: {value}")
        
        # Test analysis method
        if articles:
            print("\n🤖 Probando análisis Groq...")
            analysis = app._generate_groq_geopolitical_analysis(articles[:3])
            print("✅ Análisis generado:")
            print(f"   Título: {analysis.get('title', 'N/A')}")
            print(f"   Subtítulo: {analysis.get('subtitle', 'N/A')}")
            print(f"   Contenido: {len(analysis.get('content', ''))} caracteres")
            print(f"   Fuentes: {analysis.get('sources_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando métodos de la aplicación: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Test de Integración Groq - RiskMap")
    print("=" * 50)
    
    # Test Groq
    groq_success = test_groq_integration()
    
    # Test app methods
    app_success = test_app_methods()
    
    print("\n" + "=" * 50)
    if groq_success and app_success:
        print("🎉 TODOS LOS TESTS PASARON CORRECTAMENTE")
        print("✅ La integración con Groq está funcionando")
        print("✅ Los métodos de la aplicación están operativos")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        if not groq_success:
            print("❌ Problemas con la integración de Groq")
        if not app_success:
            print("❌ Problemas con los métodos de la aplicación")
