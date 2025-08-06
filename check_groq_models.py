#!/usr/bin/env python3
"""
Script para verificar modelos disponibles en Groq
"""

import os
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def list_groq_models():
    """Listar modelos disponibles en Groq"""
    try:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("❌ GROQ_API_KEY no encontrada")
            return
        
        client = Groq(api_key=api_key)
        
        # Listar modelos
        models = client.models.list()
        
        print("🤖 Modelos disponibles en Groq:")
        for model in models.data:
            print(f"  📋 {model.id}")
            if hasattr(model, 'owned_by'):
                print(f"      👤 Propietario: {model.owned_by}")
            print()
        
        # Probar un modelo común
        common_models = [
            "llama-3.1-8b-instant",
            "llama-3.2-1b-preview", 
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
        
        print("🧪 Probando modelos comunes...")
        for model_id in common_models:
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                print(f"✅ {model_id}: Funciona")
            except Exception as e:
                print(f"❌ {model_id}: {str(e)[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_groq_models()
