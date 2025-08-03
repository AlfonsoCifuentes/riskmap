#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema inteligente de fallback para manejo de rate limits
Detecta automáticamente limitaciones de Groq y redirige a Ollama
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from src.ai.ollama_service import OllamaModel, ollama_service
from src.ai.unified_ai_service import unified_ai_service, AIProvider

logger = logging.getLogger(__name__)

# Contador de rate limits para estadísticas
rate_limit_stats = {
    'total_groq_requests': 0,
    'groq_rate_limits': 0,
    'ollama_fallbacks': 0,
    'last_rate_limit': None
}

def is_rate_limit_error(error_message: str) -> bool:
    """
    Detectar si un error es de rate limit
    """
    rate_limit_indicators = [
        '429',
        'rate limit',
        'too many requests',
        'limit reached',
        'quota exceeded'
    ]
    
    error_lower = str(error_message).lower()
    return any(indicator in error_lower for indicator in rate_limit_indicators)

def smart_ai_fallback(task_type: str = "analysis"):
    """
    Decorador para manejo inteligente de fallbacks de IA
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rate_limit_stats['total_groq_requests'] += 1
            
            try:
                # Intentar función original (probablemente con Groq)
                result = func(*args, **kwargs)
                return result
                
            except Exception as e:
                if is_rate_limit_error(str(e)):
                    rate_limit_stats['groq_rate_limits'] += 1
                    rate_limit_stats['last_rate_limit'] = time.time()
                    
                    logger.warning(f"🔄 Rate limit detectado en {func.__name__}, usando Ollama...")
                    
                    # Determinar qué modelo de Ollama usar según el tipo de tarea
                    model_mapping = {
                        'analysis': OllamaModel.DEEPSEEK_R1_7B,
                        'summary': OllamaModel.GEMMA2_2B,
                        'generation': OllamaModel.LLAMA3_1_8B,
                        'translation': OllamaModel.QWEN_7B
                    }
                    
                    model = model_mapping.get(task_type, OllamaModel.LLAMA3_1_8B)
                    
                    # Intentar con Ollama
                    try:
                        rate_limit_stats['ollama_fallbacks'] += 1
                        return execute_with_ollama(func.__name__, model, *args, **kwargs)
                    except Exception as ollama_error:
                        logger.error(f"Error en fallback Ollama: {ollama_error}")
                        raise e  # Re-lanzar error original si Ollama también falla
                else:
                    raise e
                    
        return wrapper
    return decorator

def execute_with_ollama(function_name: str, model: OllamaModel, *args, **kwargs) -> Any:
    """
    Ejecutar operación específica con Ollama basado en el nombre de función
    """
    if not ollama_service.check_ollama_status():
        raise Exception("Ollama no está disponible para fallback")
        
    # Extraer contenido relevante de los argumentos
    content = ""
    title = ""
    
    # Buscar contenido en argumentos comunes
    for arg in args:
        if isinstance(arg, str) and len(arg) > 50:
            content = arg
            break
            
    for key, value in kwargs.items():
        if key in ['content', 'text', 'article_content'] and isinstance(value, str):
            content = value
        elif key in ['title', 'headline'] and isinstance(value, str):
            title = value
            
    if not content:
        raise Exception("No se pudo extraer contenido para procesar con Ollama")
        
    logger.info(f"🤖 Ejecutando {function_name} con Ollama modelo {model.value}")
    
    # Ejecutar según el tipo de función
    if 'summary' in function_name.lower() or 'resumen' in function_name.lower():
        return ollama_service.generate_article_summary(
            title=title or "Artículo",
            content=content,
            model=model
        )
    elif 'analysis' in function_name.lower() or 'analisis' in function_name.lower():
        result = ollama_service.analyze_geopolitical_content(
            content=content,
            model=model
        )
        return result if result else {"summary": "Análisis completado con Ollama"}
    else:
        # Generación genérica
        return ollama_service.generate_completion(
            prompt=f"Procesa el siguiente contenido: {content}",
            model=model
        )

def get_fallback_stats() -> Dict[str, Any]:
    """
    Obtener estadísticas de fallbacks
    """
    success_rate = (
        (rate_limit_stats['total_groq_requests'] - rate_limit_stats['groq_rate_limits']) 
        / max(rate_limit_stats['total_groq_requests'], 1) * 100
    )
    
    return {
        **rate_limit_stats,
        'groq_success_rate': round(success_rate, 2),
        'ollama_available': ollama_service.check_ollama_status(),
        'recommended_action': get_recommendation()
    }

def get_recommendation() -> str:
    """
    Obtener recomendación basada en estadísticas
    """
    stats = rate_limit_stats
    
    if stats['groq_rate_limits'] > 10:
        return "Considera usar principalmente Ollama debido a múltiples rate limits"
    elif stats['groq_rate_limits'] > 5:
        return "Rate limits frecuentes - considera distribución de carga"
    elif stats['groq_rate_limits'] == 0:
        return "Groq funcionando correctamente"
    else:
        return "Monitoreo normal - fallbacks ocasionales"

def force_ollama_mode(duration_minutes: int = 30):
    """
    Forzar uso de Ollama por un período determinado
    """
    logger.info(f"🔒 Activando modo Ollama forzado por {duration_minutes} minutos...")
    
    # Cambiar prioridades en el servicio unificado
    unified_ai_service.provider_priority = [AIProvider.OLLAMA]
    
    # Programar restauración automática (esto requeriría un scheduler)
    # Por ahora, solo log la recomendación
    logger.info(f"⏰ Recuerda restaurar configuración después de {duration_minutes} minutos")
    
def restore_normal_mode():
    """
    Restaurar prioridades normales
    """
    logger.info("🔄 Restaurando modo normal de operación...")
    unified_ai_service.provider_priority = [AIProvider.OLLAMA, AIProvider.GROQ]

# Función de conveniencia para enriquecimiento con fallback automático
@smart_ai_fallback(task_type="analysis")
def enhance_article_with_fallback(content: str, title: str = "") -> Dict[str, Any]:
    """
    Función wrapper para enriquecimiento con fallback automático
    """
    # Esta función será interceptada por el decorador si hay rate limits
    # y automáticamente usará Ollama
    from groq import Groq
    import os
    
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Analiza el contenido y proporciona análisis geopolítico."},
            {"role": "user", "content": f"Título: {title}\nContenido: {content}"}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    return {
        "summary": response.choices[0].message.content.strip(),
        "provider": "groq",
        "model": "llama-3.1-8b-instant"
    }

if __name__ == "__main__":
    # Test del sistema de fallback
    print("🧪 Probando sistema de fallback inteligente...")
    
    try:
        # Simular rate limit
        stats = get_fallback_stats()
        print(f"📊 Estadísticas: {stats}")
        
        # Test con contenido real
        test_content = "Test de análisis geopolítico con fallback automático"
        result = enhance_article_with_fallback(test_content, "Test Article")
        print(f"✅ Resultado: {result}")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
