#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de integración con Ollama para modelos locales
Soporte para Qwen y Llama en ejecución local
"""

import json
import logging
import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class OllamaModel(Enum):
    """Modelos disponibles en Ollama"""
    QWEN_7B = "qwen:7b"
    QWEN_14B = "qwen:14b"
    QWEN_32B = "qwen:32b"
    QWEN_CODER = "qwen2.5-coder:7b"
    LLAMA3_8B = "llama3:8b"
    LLAMA3_70B = "llama3:70b"
    LLAMA3_1_8B = "llama3.1:8b"
    LLAMA3_1_70B = "llama3.1:70b"
    LLAMA3_2_1B = "llama3.2:1b"
    LLAMA3_2_3B = "llama3.2:3b"
    # Nuevos modelos avanzados
    DEEPSEEK_R1_1_5B = "deepseek-r1:1.5b"
    DEEPSEEK_R1_7B = "deepseek-r1:7b"
    DEEPSEEK_R1_8B = "deepseek-r1:8b"
    DEEPSEEK_R1_14B = "deepseek-r1:14b"
    DEEPSEEK_R1_32B = "deepseek-r1:32b"
    GEMMA2_2B = "gemma2:2b"
    GEMMA2_9B = "gemma2:9b"
    GEMMA2_27B = "gemma2:27b"

@dataclass
class OllamaConfig:
    """Configuración para el servicio Ollama"""
    base_url: str = "http://localhost:11434"
    timeout: int = 300
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 0.9
    top_k: int = 40
    stream: bool = False
    
class OllamaService:
    """
    Servicio para interactuar con modelos Ollama locales
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.session = None
        
        # Configuración desde variables de entorno
        self.config.base_url = os.getenv('OLLAMA_BASE_URL', self.config.base_url)
        self.config.timeout = int(os.getenv('OLLAMA_TIMEOUT', str(self.config.timeout)))
        
        # Modelos disponibles por defecto
        self.available_models = []
        self.preferred_models = {
            'analysis': OllamaModel.DEEPSEEK_R1_7B,    # DeepSeek-R1 para análisis profundo
            'reasoning': OllamaModel.DEEPSEEK_R1_14B,   # DeepSeek-R1 para razonamiento complejo
            'generation': OllamaModel.LLAMA3_1_8B,      # Llama para generación general
            'coding': OllamaModel.QWEN_CODER,           # Qwen para tareas técnicas
            'lightweight': OllamaModel.GEMMA2_2B,       # Gemma para tareas rápidas
            'multilingual': OllamaModel.QWEN_7B,        # Qwen para multiidioma
            'advanced': OllamaModel.GEMMA2_9B           # Gemma para tareas avanzadas
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    def check_ollama_status(self) -> bool:
        """
        Verificar si Ollama está ejecutándose
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama no está disponible: {e}")
            return False
            
    def get_available_models(self) -> List[Dict]:
        """
        Obtener lista de modelos disponibles en Ollama
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.available_models = data.get('models', [])
                return self.available_models
            else:
                logger.error(f"Error obteniendo modelos: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error conectando con Ollama: {e}")
            return []
            
    def install_model(self, model: Union[str, OllamaModel]) -> bool:
        """
        Instalar un modelo en Ollama
        """
        model_name = model.value if isinstance(model, OllamaModel) else model
        
        try:
            logger.info(f"🚀 Instalando modelo {model_name}...")
            
            response = requests.post(
                f"{self.config.base_url}/api/pull",
                json={"name": model_name},
                timeout=1800,  # 30 minutos para descarga
                stream=True
            )
            
            if response.status_code == 200:
                # Procesar respuesta streaming
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            status = data.get('status', '')
                            if 'downloading' in status.lower():
                                logger.info(f"📥 {status}")
                            elif 'pulling' in status.lower():
                                logger.info(f"⬇️ {status}")
                            elif 'success' in status.lower():
                                logger.info(f"✅ Modelo {model_name} instalado correctamente")
                                return True
                        except json.JSONDecodeError:
                            continue
                            
                logger.info(f"✅ Modelo {model_name} instalado")
                return True
            else:
                logger.error(f"Error instalando modelo: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error instalando modelo {model_name}: {e}")
            return False
            
    def generate_completion(
        self, 
        prompt: str,
        model: Union[str, OllamaModel] = OllamaModel.QWEN_7B,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Generar una respuesta usando un modelo de Ollama
        """
        model_name = model.value if isinstance(model, OllamaModel) else model
        
        try:
            # Preparar el payload
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": kwargs.get('stream', self.config.stream),
                "options": {
                    "temperature": kwargs.get('temperature', self.config.temperature),
                    "top_p": kwargs.get('top_p', self.config.top_p),
                    "top_k": kwargs.get('top_k', self.config.top_k),
                    "num_predict": kwargs.get('max_tokens', self.config.max_tokens)
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            logger.info(f"🤖 Generando respuesta con {model_name}")
            
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"Error en generación: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return None
            
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Union[str, OllamaModel] = OllamaModel.QWEN_7B,
        **kwargs
    ) -> Optional[str]:
        """
        Generar respuesta usando el endpoint de chat
        """
        model_name = model.value if isinstance(model, OllamaModel) else model
        
        try:
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": kwargs.get('stream', self.config.stream),
                "options": {
                    "temperature": kwargs.get('temperature', self.config.temperature),
                    "top_p": kwargs.get('top_p', self.config.top_p),
                    "top_k": kwargs.get('top_k', self.config.top_k),
                    "num_predict": kwargs.get('max_tokens', self.config.max_tokens)
                }
            }
            
            logger.info(f"💬 Chat con {model_name}")
            
            response = requests.post(
                f"{self.config.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', {})
                return message.get('content', '').strip()
            else:
                logger.error(f"Error en chat: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error en chat: {e}")
            return None
            
    async def async_generate_completion(
        self,
        prompt: str,
        model: Union[str, OllamaModel] = OllamaModel.QWEN_7B,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Versión asíncrona de generate_completion
        """
        model_name = model.value if isinstance(model, OllamaModel) else model
        
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.config.temperature),
                    "top_p": kwargs.get('top_p', self.config.top_p),
                    "top_k": kwargs.get('top_k', self.config.top_k),
                    "num_predict": kwargs.get('max_tokens', self.config.max_tokens)
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                )
                
            async with self.session.post(
                f"{self.config.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '').strip()
                else:
                    logger.error(f"Error async en generación: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error async generando respuesta: {e}")
            return None
            
    def analyze_geopolitical_content(
        self,
        content: str,
        model: Union[str, OllamaModel] = OllamaModel.DEEPSEEK_R1_7B
    ) -> Dict[str, Any]:
        """
        Análisis especializado de contenido geopolítico usando DeepSeek-R1
        """
        system_prompt = """Eres un analista geopolítico experto especializado en razonamiento profundo. 
        Analiza el siguiente contenido con pensamiento crítico y proporciona:

1. Nivel de riesgo (high/medium/low) con justificación detallada
2. Probabilidad de conflicto (0.0-1.0) basada en análisis histórico
3. Países/regiones involucradas con sus roles específicos
4. Temas clave identificados con contexto histórico
5. Sentiment score (-1.0 a 1.0) considerando múltiples perspectivas
6. Resumen analítico en español (máximo 250 palabras) con insights profundos
7. Implicaciones a corto y largo plazo
8. Recomendaciones estratégicas

Responde en formato JSON válido con análisis fundamentado."""

        try:
            response = self.generate_completion(
                prompt=f"Analiza este contenido geopolítico con razonamiento profundo:\n\n{content}",
                model=model,
                system_prompt=system_prompt,
                temperature=0.2,  # Baja temperatura para análisis más preciso
                max_tokens=3000
            )
            
            if response:
                try:
                    # Intentar parsear JSON
                    analysis = json.loads(response)
                    # Agregar metadatos del modelo
                    analysis['model_used'] = model.value if isinstance(model, OllamaModel) else model
                    analysis['analysis_type'] = 'deepseek_reasoning'
                    return analysis
                except json.JSONDecodeError:
                    # Si no es JSON válido, crear estructura mejorada
                    return {
                        'risk_level': 'medium',
                        'conflict_probability': 0.5,
                        'countries': [],
                        'key_topics': [],
                        'sentiment_score': 0.0,
                        'summary': response[:250] + '...' if len(response) > 250 else response,
                        'implications': {
                            'short_term': 'Análisis en progreso',
                            'long_term': 'Evaluación pendiente'
                        },
                        'recommendations': ['Monitoreo continuo requerido'],
                        'raw_analysis': response,
                        'model_used': model.value if isinstance(model, OllamaModel) else model,
                        'analysis_type': 'deepseek_reasoning'
                    }
            else:
                return self._get_default_analysis()
                
        except Exception as e:
            logger.error(f"Error en análisis geopolítico con {model}: {e}")
            return self._get_default_analysis()
            
    def generate_lightweight_summary(
        self,
        title: str,
        content: str,
        model: Union[str, OllamaModel] = OllamaModel.GEMMA2_2B
    ) -> str:
        """
        Generar resumen rápido usando Gemma (modelo ligero y eficiente)
        """
        system_prompt = """Eres un periodista experto en síntesis rápida. Crea un resumen:
- Máximo 100 palabras
- En español claro y directo
- Captura los puntos esenciales
- Estilo informativo y objetivo"""

        try:
            prompt = f"Título: {title}\n\nContenido: {content[:2000]}\n\nResumen conciso:"
            
            response = self.generate_completion(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=150
            )
            
            return response.strip() if response else "Resumen no disponible"
            
        except Exception as e:
            logger.error(f"Error generando resumen ligero: {e}")
            return "Error generando resumen"
            
    def perform_deep_reasoning(
        self,
        question: str,
        context: str = "",
        model: Union[str, OllamaModel] = OllamaModel.DEEPSEEK_R1_14B
    ) -> Dict[str, Any]:
        """
        Realizar razonamiento profundo usando DeepSeek-R1
        """
        system_prompt = """Eres un sistema de razonamiento avanzado. Analiza la pregunta paso a paso:

1. Comprende el contexto y la pregunta
2. Identifica los elementos clave
3. Desarrolla un razonamiento lógico
4. Considera múltiples perspectivas
5. Llega a conclusiones fundamentadas
6. Proporciona confianza en tu respuesta (0.0-1.0)

Responde en formato JSON con tu proceso de razonamiento detallado."""

        try:
            full_prompt = f"Contexto: {context}\n\nPregunta: {question}\n\nRazonamiento profundo:"
            
            response = self.generate_completion(
                prompt=full_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.1,  # Temperatura muy baja para razonamiento preciso
                max_tokens=2500
            )
            
            if response:
                try:
                    reasoning = json.loads(response)
                    reasoning['model_used'] = model.value if isinstance(model, OllamaModel) else model
                    reasoning['reasoning_type'] = 'deepseek_advanced'
                    return reasoning
                except json.JSONDecodeError:
                    return {
                        'question': question,
                        'reasoning_steps': [response],
                        'conclusion': response[:200] + '...' if len(response) > 200 else response,
                        'confidence': 0.7,
                        'model_used': model.value if isinstance(model, OllamaModel) else model,
                        'reasoning_type': 'deepseek_advanced',
                        'raw_response': response
                    }
            else:
                return {
                    'question': question,
                    'reasoning_steps': ['Error en el procesamiento'],
                    'conclusion': 'No se pudo completar el razonamiento',
                    'confidence': 0.0,
                    'model_used': model.value if isinstance(model, OllamaModel) else model,
                    'reasoning_type': 'error'
                }
                
        except Exception as e:
            logger.error(f"Error en razonamiento profundo: {e}")
            return {
                'question': question,
                'reasoning_steps': [f'Error: {str(e)}'],
                'conclusion': 'Error en el procesamiento',
                'confidence': 0.0,
                'model_used': 'error',
                'reasoning_type': 'error'
            }
            
    def generate_article_summary(
        self,
        title: str,
        content: str,
        model: Union[str, OllamaModel] = OllamaModel.LLAMA3_1_8B
    ) -> str:
        """
        Generar resumen de artículo
        """
        system_prompt = """Eres un periodista experto. Crea un resumen conciso y informativo del artículo proporcionado. 
El resumen debe ser:
- Máximo 150 palabras
- En español
- Objetivo y neutral
- Que capture los puntos más importantes"""

        try:
            prompt = f"Título: {title}\n\nContenido: {content}\n\nResumen:"
            
            response = self.generate_completion(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=200
            )
            
            return response.strip() if response else "Resumen no disponible"
            
        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
            return "Error generando resumen"
            
    def _get_default_analysis(self) -> Dict[str, Any]:
        """
        Análisis por defecto en caso de error
        """
        return {
            'risk_level': 'medium',
            'conflict_probability': 0.5,
            'countries': [],
            'key_topics': [],
            'sentiment_score': 0.0,
            'summary': 'Análisis no disponible',
            'raw_analysis': ''
        }

# Instancia global del servicio
ollama_service = OllamaService()

def setup_ollama_models():
    """
    Configurar e instalar modelos recomendados incluyendo DeepSeek-R1 y Gemma
    """
    logger.info("🚀 Configurando modelos Ollama con DeepSeek-R1 y Gemma...")
    
    if not ollama_service.check_ollama_status():
        logger.error("❌ Ollama no está ejecutándose. Por favor, inicia Ollama primero.")
        return False
        
    # Modelos recomendados para el sistema (organizados por prioridad)
    recommended_models = [
        # Modelos principales (alta prioridad)
        OllamaModel.DEEPSEEK_R1_7B,   # Análisis profundo y razonamiento
        OllamaModel.GEMMA2_2B,        # Tareas rápidas y ligeras
        OllamaModel.QWEN_7B,          # Análisis multiidioma
        
        # Modelos avanzados (media prioridad)
        OllamaModel.LLAMA3_1_8B,      # Generación de texto
        OllamaModel.GEMMA2_9B,        # Tareas avanzadas
        OllamaModel.QWEN_CODER,       # Tareas técnicas
        
        # Modelos especializados (baja prioridad)
        OllamaModel.DEEPSEEK_R1_14B,  # Razonamiento complejo (solo si hay recursos)
    ]
    
    installed_models = ollama_service.get_available_models()
    installed_names = [model.get('name', '') for model in installed_models]
    
    successful_installs = 0
    
    for i, model in enumerate(recommended_models):
        if model.value not in installed_names:
            logger.info(f"📦 Instalando {model.value} ({i+1}/{len(recommended_models)})...")
            
            # Mostrar información del modelo
            model_info = {
                OllamaModel.DEEPSEEK_R1_7B: "🧠 DeepSeek-R1 7B - Razonamiento profundo",
                OllamaModel.DEEPSEEK_R1_14B: "🧠 DeepSeek-R1 14B - Razonamiento avanzado",
                OllamaModel.GEMMA2_2B: "⚡ Gemma 2B - Respuestas rápidas",
                OllamaModel.GEMMA2_9B: "🎯 Gemma 9B - Análisis avanzado",
                OllamaModel.QWEN_7B: "🌍 Qwen 7B - Multiidioma",
                OllamaModel.LLAMA3_1_8B: "📝 Llama 3.1 8B - Generación",
                OllamaModel.QWEN_CODER: "💻 Qwen Coder - Tareas técnicas"
            }
            
            logger.info(f"ℹ️  {model_info.get(model, 'Modelo especializado')}")
            
            success = ollama_service.install_model(model)
            if success:
                logger.info(f"✅ {model.value} instalado correctamente")
                successful_installs += 1
            else:
                logger.error(f"❌ Error instalando {model.value}")
                
                # Para modelos grandes, continuar con los siguientes
                if model in [OllamaModel.DEEPSEEK_R1_14B]:
                    logger.info("⏭️ Continuando con modelos más ligeros...")
                    continue
        else:
            logger.info(f"✅ {model.value} ya está instalado")
            successful_installs += 1
    
    # Mostrar resumen
    final_models = ollama_service.get_available_models()
    
    logger.info(f"""
🎉 CONFIGURACIÓN COMPLETADA
✅ Modelos instalados exitosamente: {successful_installs}/{len(recommended_models)}
📋 Total de modelos disponibles: {len(final_models)}

🤖 Capacidades del sistema:
- 🧠 Razonamiento profundo: DeepSeek-R1
- ⚡ Análisis rápido: Gemma 2B
- 🌍 Soporte multiidioma: Qwen
- 📝 Generación de texto: Llama 3.1
- 💻 Tareas técnicas: Qwen Coder

🚀 El sistema está listo para análisis geopolítico avanzado!
""")
            
    return successful_installs >= 3  # Al menos 3 modelos para funcionalidad básica

if __name__ == "__main__":
    # Ejemplo de uso
    setup_ollama_models()
    
    # Prueba básica
    if ollama_service.check_ollama_status():
        response = ollama_service.generate_completion(
            "Explica qué es la geopolítica en 100 palabras",
            model=OllamaModel.QWEN_7B
        )
        print(f"Respuesta: {response}")
