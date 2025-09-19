#!/usr/bin/env python3
"""
Test del sistema de fallback para cuando Groq API no funciona
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def test_fallback_system():
    """Test del sistema de fallback completo"""
    print("🧪 Testing sistema de fallback para IA")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Test 1: Verificar modelos disponibles
    print("\n📊 1. Verificando modelos de IA disponibles...")
    
    try:
        from ai.multi_model_client import MultiModelAIClient
        client = MultiModelAIClient()
        
        print(f"✅ Multi-model client inicializado")
        print(f"📝 Modelos disponibles: {client.available_models}")
        print(f"🎯 Prioridad de modelos: {client.priority}")
        
        # Test 2: Probar generación de análisis
        print("\n🧠 2. Probando generación de análisis...")
        
        # Datos de prueba
        test_articles = [
            {
                'title': 'Crisis diplomática entre países vecinos',
                'content': 'Las tensiones aumentan en la región debido a disputas comerciales',
                'published_at': '2024-01-15'
            },
            {
                'title': 'Elecciones controvertidas generan protestas',
                'content': 'Los ciudadanos expresan descontento con los resultados electorales',
                'published_at': '2024-01-14'
            }
        ]
        
        result = client.generate_analysis(test_articles)
        
        if result and 'analysis' in result:
            print("✅ Análisis generado exitosamente")
            print(f"🔧 Fuente utilizada: {result.get('source', 'unknown')}")
            print(f"📊 Artículos analizados: {result.get('articles_analyzed', 0)}")
            print(f"📅 Generado en: {result.get('generated_at', 'N/A')}")
            
            # Mostrar una muestra del análisis
            analysis_text = result['analysis']
            print(f"📄 Muestra del análisis ({len(analysis_text)} caracteres):")
            print("-" * 30)
            print(analysis_text[:300] + "..." if len(analysis_text) > 300 else analysis_text)
            print("-" * 30)
            
            return True
        else:
            print("❌ Error generando análisis")
            return False
            
    except Exception as e:
        print(f"❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_huggingface_local():
    """Test específico de HuggingFace local"""
    print("\n🤗 3. Probando HuggingFace local...")
    
    try:
        from transformers import pipeline
        
        # Test generación de texto simple
        generator = pipeline('text-generation', 
                           model='microsoft/DialoGPT-small',
                           return_full_text=False,
                           max_new_tokens=50,
                           do_sample=True,
                           temperature=0.7)
        
        prompt = "Análisis geopolítico: La situación actual muestra"
        result = generator(prompt)
        
        if result and len(result) > 0:
            print("✅ HuggingFace local funcionando")
            print(f"📝 Resultado: {result[0]['generated_text']}")
            return True
        else:
            print("❌ HuggingFace no generó resultado válido")
            return False
            
    except Exception as e:
        print(f"❌ Error con HuggingFace: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando tests del sistema de fallback")
    print("=" * 60)
    
    # Test del sistema completo
    fallback_ok = test_fallback_system()
    
    # Test específico de HuggingFace
    hf_ok = test_huggingface_local()
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"{'✅' if fallback_ok else '❌'} Sistema de fallback multi-modelo")
    print(f"{'✅' if hf_ok else '❌'} HuggingFace local")
    
    if fallback_ok:
        print("\n🎉 ¡Sistema de fallback operativo!")
        print("💡 El sistema puede funcionar sin API keys externas")
        print("🔄 Cuando Groq/OpenAI fallen, se usará el sistema local")
    else:
        print("\n⚠️  Problema con el sistema de fallback")
        print("🔧 Verifica la configuración e importaciones")
    
    return fallback_ok and hf_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)