#!/usr/bin/env python3
"""
Test simple para verificar que Groq está funcionando
"""
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

def test_groq_simple():
    """Test básico de Groq"""
    print("🧪 Test Simple de Groq")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("❌ GROQ_API_KEY no encontrada en .env")
        return False
    
    print(f"✅ GROQ_API_KEY encontrada: {groq_api_key[:10]}...")
    
    try:
        from groq import Groq
        print("✅ Groq importado correctamente")
        
        client = Groq(api_key=groq_api_key)
        print("✅ Cliente Groq creado")
        
        # Test simple
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Di solo 'Hola, funciono correctamente'"
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"✅ Respuesta de Groq: {result}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando Groq: {e}")
        return False
    except Exception as e:
        print(f"❌ Error llamando a Groq: {e}")
        return False

if __name__ == "__main__":
    success = test_groq_simple()
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Test exitoso! Groq está funcionando correctamente")
    else:
        print("💥 Test falló. Revisa la configuración")
    print("=" * 50)
