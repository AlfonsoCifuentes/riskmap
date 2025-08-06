#!/usr/bin/env python3
"""
Mejora permanente del algoritmo de análisis de riesgo en Ollama
"""

import os
import sys

def improve_ollama_risk_analysis():
    """Aplicar mejoras al servicio de Ollama para mejor análisis de riesgo"""
    
    ollama_service_path = "src/ai/ollama_service.py"
    
    try:
        with open(ollama_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Mejorar el prompt del sistema para mejor análisis de riesgo
        improved_system_prompt = '''"""Eres un analista geopolítico experto especializado en evaluación de riesgos. 

INSTRUCCIONES CRÍTICAS PARA EVALUACIÓN DE RIESGO:

ALTO RIESGO (high):
- Conflictos armados activos, terrorismo, ataques militares
- Crisis económicas severas, colapsos financieros
- Amenazas nucleares, armas de destrucción masiva
- Asesinatos políticos, golpes de estado
- Genocidio, crímenes de guerra
- Invasiones, bombardeos, violencia masiva

RIESGO MEDIO (medium):
- Tensiones diplomáticas, sanciones económicas
- Protestas políticas, manifestaciones
- Elecciones controvertidas, cambios de gobierno
- Investigaciones de corrupción de alto nivel
- Negociaciones internacionales críticas
- Políticas que afectan relaciones internacionales

BAJO RIESGO (low):
- Deportes, entretenimiento, cultura
- Tecnología no militar, ciencia básica
- Salud pública rutinaria, clima
- Turismo, arte, educación
- Celebridades, moda, gastronomía
- Noticias locales sin impacto geopolítico

Analiza con criterio estricto y justifica tu evaluación. Responde SOLO en JSON válido:
{
    "risk_level": "high/medium/low",
    "risk_justification": "explicación detallada de por qué asignaste este nivel",
    "conflict_probability": 0.0-1.0,
    "geopolitical_relevance": 0.0-1.0,
    "countries": ["lista de países"],
    "key_topics": ["temas principales"],
    "sentiment_score": -1.0 a 1.0,
    "summary": "resumen analítico en español"
}"""'''
        
        # Reemplazar el prompt del sistema
        old_prompt_start = 'system_prompt = """Eres un analista geopolítico experto especializado en razonamiento profundo.'
        old_prompt_end = 'Responde en formato JSON válido con análisis fundamentado."""'
        
        if old_prompt_start in content and old_prompt_end in content:
            start_idx = content.find(old_prompt_start)
            end_idx = content.find(old_prompt_end) + len(old_prompt_end)
            
            if start_idx != -1 and end_idx != -1:
                new_content = content[:start_idx] + f"system_prompt = {improved_system_prompt}" + content[end_idx:]
                
                # Guardar archivo mejorado
                with open(ollama_service_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ Algoritmo de análisis de riesgo mejorado en ollama_service.py")
                print("🔄 Los nuevos artículos usarán el algoritmo mejorado")
                return True
            else:
                print("❌ No se pudo localizar el prompt del sistema")
                return False
        else:
            print("❌ No se encontró el prompt del sistema a reemplazar")
            return False
            
    except Exception as e:
        print(f"❌ Error mejorando algoritmo: {e}")
        return False

def fix_default_analysis():
    """Mejorar el análisis por defecto"""
    
    ollama_service_path = "src/ai/ollama_service.py"
    
    try:
        with open(ollama_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar el análisis por defecto
        old_default = '''return {
            'risk_level': 'medium',
            'conflict_probability': 0.5,
            'countries': [],
            'key_topics': [],
            'sentiment_score': 0.0,
            'summary': 'Análisis no disponible',
            'raw_analysis': ''
        }'''
        
        new_default = '''return {
            'risk_level': 'low',  # Por defecto bajo riesgo en lugar de medio
            'conflict_probability': 0.2,
            'countries': [],
            'key_topics': [],
            'sentiment_score': 0.0,
            'summary': 'Análisis no disponible - clasificado como bajo riesgo por defecto',
            'raw_analysis': '',
            'risk_justification': 'Análisis fallido - asignado bajo riesgo por seguridad'
        }'''
        
        if old_default in content:
            new_content = content.replace(old_default, new_default)
            
            # Guardar archivo mejorado
            with open(ollama_service_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Análisis por defecto mejorado (low en lugar de medium)")
            return True
        else:
            print("❌ No se encontró el análisis por defecto a reemplazar")
            return False
            
    except Exception as e:
        print(f"❌ Error mejorando análisis por defecto: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Mejorando algoritmo de análisis de riesgo...")
    print("=" * 60)
    
    success1 = improve_ollama_risk_analysis()
    success2 = fix_default_analysis()
    
    if success1 and success2:
        print("\n✅ Mejoras aplicadas correctamente")
        print("🔄 Los nuevos artículos tendrán análisis de riesgo más precisos")
        print("📊 Reinicia el servidor para aplicar los cambios")
    else:
        print("\n❌ Algunas mejoras fallaron")
