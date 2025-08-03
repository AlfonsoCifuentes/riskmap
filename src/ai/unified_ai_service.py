#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptador unificado para servicios de IA
Integra Groq (remoto) y Ollama (local) con fallback automático
"""

import logging
import asyncio
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Importar servicios
from src.ai.ollama_service import OllamaService, OllamaModel, ollama_service

load_dotenv()

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Proveedores de IA disponibles"""
    GROQ = "groq"
    OLLAMA = "ollama"
    AUTO = "auto"  # Selección automática

class TaskType(Enum):
    """Tipos de tareas de IA"""
    ANALYSIS = "analysis"
    GENERATION = "generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CLASSIFICATION = "classification"

@dataclass
class AIResponse:
    """Respuesta unificada de servicios de IA"""
    content: str
    provider: str
    model: str
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class UnifiedAIService:
    """
    Servicio unificado que maneja múltiples proveedores de IA
    con fallback automático y selección inteligente
    """
    
    def __init__(self):
        self.ollama_service = ollama_service
        self.groq_available = bool(os.getenv('GROQ_API_KEY'))
        self.ollama_available = False
        
        # Verificar disponibilidad de servicios
        self._check_service_availability()
        
        # Configuración de modelos por tarea
        self.task_models = {
            TaskType.ANALYSIS: {
                AIProvider.GROQ: "llama-3.1-8b-instant",
                AIProvider.OLLAMA: OllamaModel.DEEPSEEK_R1_7B  # DeepSeek para análisis profundo
            },
            TaskType.GENERATION: {
                AIProvider.GROQ: "llama-3.1-8b-instant", 
                AIProvider.OLLAMA: OllamaModel.LLAMA3_1_8B
            },
            TaskType.SUMMARIZATION: {
                AIProvider.GROQ: "llama-3.1-8b-instant",
                AIProvider.OLLAMA: OllamaModel.GEMMA2_2B  # Gemma para resúmenes rápidos
            },
            TaskType.TRANSLATION: {
                AIProvider.GROQ: "llama-3.1-8b-instant",
                AIProvider.OLLAMA: OllamaModel.QWEN_7B  # Qwen para multiidioma
            },
            TaskType.CLASSIFICATION: {
                AIProvider.GROQ: "llama-3.1-8b-instant",
                AIProvider.OLLAMA: OllamaModel.GEMMA2_9B  # Gemma avanzado para clasificación
            }
        }
        
        # Prioridades por defecto (local primero para privacidad)
        self.provider_priority = [AIProvider.OLLAMA, AIProvider.GROQ]
        
    def _check_service_availability(self):
        """Verificar qué servicios están disponibles"""
        try:
            self.ollama_available = self.ollama_service.check_ollama_status()
            logger.info(f"🤖 Ollama disponible: {self.ollama_available}")
            logger.info(f"☁️ Groq disponible: {self.groq_available}")
        except Exception as e:
            logger.error(f"Error verificando servicios: {e}")
            self.ollama_available = False
            
    def get_optimal_provider(
        self, 
        task_type: TaskType,
        prefer_local: bool = True,
        content_length: Optional[int] = None
    ) -> AIProvider:
        """
        Seleccionar el proveedor óptimo basado en la tarea y disponibilidad
        """
        # Priorizar local si se solicita y está disponible
        if prefer_local and self.ollama_available:
            return AIProvider.OLLAMA
            
        # Para contenido muy largo, preferir Groq si está disponible
        if content_length and content_length > 8000 and self.groq_available:
            return AIProvider.GROQ
            
        # Fallback basado en disponibilidad
        for provider in self.provider_priority:
            if provider == AIProvider.OLLAMA and self.ollama_available:
                return AIProvider.OLLAMA
            elif provider == AIProvider.GROQ and self.groq_available:
                return AIProvider.GROQ
                
        # Si nada está disponible, retornar AUTO para manejo de error
        return AIProvider.AUTO
        
    async def analyze_geopolitical_content(
        self,
        content: str,
        provider: AIProvider = AIProvider.AUTO,
        prefer_local: bool = True
    ) -> AIResponse:
        """
        Análisis geopolítico unificado con fallback
        """
        if provider == AIProvider.AUTO:
            provider = self.get_optimal_provider(
                TaskType.ANALYSIS, 
                prefer_local=prefer_local,
                content_length=len(content)
            )
            
        # Intentar con el proveedor seleccionado
        response = await self._try_analysis_with_provider(content, provider)
        
        # Fallback si falla
        if not response.success:
            fallback_provider = AIProvider.GROQ if provider == AIProvider.OLLAMA else AIProvider.OLLAMA
            if self._is_provider_available(fallback_provider):
                logger.warning(f"Fallback de {provider.value} a {fallback_provider.value}")
                response = await self._try_analysis_with_provider(content, fallback_provider)
                
        return response
        
    async def _try_analysis_with_provider(
        self, 
        content: str, 
        provider: AIProvider
    ) -> AIResponse:
        """
        Intentar análisis con un proveedor específico
        """
        try:
            if provider == AIProvider.OLLAMA and self.ollama_available:
                return await self._analyze_with_ollama(content)
            elif provider == AIProvider.GROQ and self.groq_available:
                return await self._analyze_with_groq(content)
            else:
                return AIResponse(
                    content="",
                    provider=provider.value,
                    model="none",
                    success=False,
                    error=f"Proveedor {provider.value} no disponible"
                )
                
        except Exception as e:
            logger.error(f"Error con proveedor {provider.value}: {e}")
            # Si Groq falla por rate limit, intentar automáticamente con Ollama
            if "429" in str(e) or "rate_limit" in str(e).lower():
                logger.warning(f"🔄 Rate limit detectado en {provider.value}, cambiando a Ollama...")
                if self.ollama_available and provider != AIProvider.OLLAMA:
                    return await self._analyze_with_ollama(content)
            
            return AIResponse(
                content="",
                provider=provider.value,
                model="error",
                success=False,
                error=str(e)
            )
            
    async def _analyze_with_ollama(self, content: str) -> AIResponse:
        """
        Análisis usando Ollama local
        """
        try:
            model = self.task_models[TaskType.ANALYSIS][AIProvider.OLLAMA]
            
            analysis = self.ollama_service.analyze_geopolitical_content(
                content=content,
                model=model
            )
            
            if analysis and 'summary' in analysis:
                return AIResponse(
                    content=analysis.get('summary', ''),
                    provider="ollama",
                    model=model.value,
                    success=True,
                    metadata=analysis
                )
            else:
                return AIResponse(
                    content="",
                    provider="ollama", 
                    model=model.value,
                    success=False,
                    error="No se pudo generar análisis"
                )
                
        except Exception as e:
            logger.error(f"Error en análisis Ollama: {e}")
            return AIResponse(
                content="",
                provider="ollama",
                model="error",
                success=False,
                error=str(e)
            )
            
    async def _analyze_with_groq(self, content: str) -> AIResponse:
        """
        Análisis usando Groq (mantener compatibilidad con código existente)
        """
        try:
            # Importar Groq dinámicamente para evitar dependencias
            from groq import Groq
            
            client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            model = self.task_models[TaskType.ANALYSIS][AIProvider.GROQ]
            
            system_prompt = """Eres un analista geopolítico experto. Analiza el contenido y proporciona:
            - Nivel de riesgo (high/medium/low)
            - Probabilidad de conflicto (0.0-1.0)
            - Países/regiones involucradas
            - Resumen en español (máximo 200 palabras)
            
            Responde en formato JSON válido."""
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analiza: {content}"}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            
            return AIResponse(
                content=result,
                provider="groq",
                model=model,
                success=True,
                metadata={"tokens_used": response.usage.total_tokens if response.usage else 0}
            )
            
        except Exception as e:
            logger.error(f"Error en análisis Groq: {e}")
            return AIResponse(
                content="",
                provider="groq",
                model="error", 
                success=False,
                error=str(e)
            )
            
    def generate_summary(
        self,
        title: str,
        content: str,
        provider: AIProvider = AIProvider.AUTO,
        max_words: int = 150
    ) -> AIResponse:
        """
        Generar resumen con el proveedor especificado y fallback automático
        """
        if provider == AIProvider.AUTO:
            provider = self.get_optimal_provider(TaskType.SUMMARIZATION)
            
        try:
            if provider == AIProvider.OLLAMA and self.ollama_available:
                model = self.task_models[TaskType.SUMMARIZATION][AIProvider.OLLAMA]
                summary = self.ollama_service.generate_article_summary(
                    title=title,
                    content=content,
                    model=model
                )
                
                return AIResponse(
                    content=summary,
                    provider="ollama",
                    model=model.value,
                    success=bool(summary and "error" not in summary.lower())
                )
                
            elif provider == AIProvider.GROQ and self.groq_available:
                return self._generate_summary_groq(title, content, max_words)
            else:
                # Fallback a Ollama si está disponible
                if self.ollama_available:
                    logger.info("🔄 Usando Ollama como fallback para resumen...")
                    model = self.task_models[TaskType.SUMMARIZATION][AIProvider.OLLAMA]
                    summary = self.ollama_service.generate_article_summary(
                        title=title,
                        content=content,
                        model=model
                    )
                    
                    return AIResponse(
                        content=summary,
                        provider="ollama_fallback",
                        model=model.value,
                        success=bool(summary and "error" not in summary.lower())
                    )
                
                return AIResponse(
                    content=f"Resumen de: {title}",
                    provider="fallback",
                    model="none",
                    success=False,
                    error="Ningún proveedor disponible"
                )
                
        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
            
            # Si Groq falla por rate limit, intentar automáticamente con Ollama
            if ("429" in str(e) or "rate_limit" in str(e).lower()) and self.ollama_available:
                logger.warning(f"🔄 Rate limit detectado, usando Ollama para resumen...")
                try:
                    model = self.task_models[TaskType.SUMMARIZATION][AIProvider.OLLAMA]
                    summary = self.ollama_service.generate_article_summary(
                        title=title,
                        content=content,
                        model=model
                    )
                    
                    return AIResponse(
                        content=summary,
                        provider="ollama_emergency",
                        model=model.value,
                        success=bool(summary and "error" not in summary.lower()),
                        metadata={"fallback_reason": "groq_rate_limit"}
                    )
                except Exception as fallback_error:
                    logger.error(f"Error en fallback Ollama: {fallback_error}")
            
            return AIResponse(
                content="Error generando resumen",
                provider=provider.value,
                model="error",
                success=False,
                error=str(e)
            )
            
    def _generate_summary_groq(self, title: str, content: str, max_words: int) -> AIResponse:
        """
        Generar resumen usando Groq
        """
        try:
            from groq import Groq
            
            client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            model = self.task_models[TaskType.SUMMARIZATION][AIProvider.GROQ]
            
            prompt = f"""Crea un resumen conciso del siguiente artículo en español.
            Máximo {max_words} palabras.
            
            Título: {title}
            
            Contenido: {content[:4000]}  # Limitar para no exceder tokens
            
            Resumen:"""
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300
            )
            
            summary = response.choices[0].message.content.strip()
            
            return AIResponse(
                content=summary,
                provider="groq",
                model=model,
                success=True,
                metadata={"tokens_used": response.usage.total_tokens if response.usage else 0}
            )
            
        except Exception as e:
            logger.error(f"Error en resumen Groq: {e}")
            return AIResponse(
                content="Error generando resumen",
                provider="groq",
                model="error",
                success=False,
                error=str(e)
            )
            
    def _is_provider_available(self, provider: AIProvider) -> bool:
        """
        Verificar si un proveedor está disponible
        """
        if provider == AIProvider.OLLAMA:
            return self.ollama_available
        elif provider == AIProvider.GROQ:
            return self.groq_available
        return False
        
    def get_service_status(self) -> Dict[str, Any]:
        """
        Obtener estado de todos los servicios incluyendo modelos avanzados
        """
        # Actualizar disponibilidad
        self._check_service_availability()
        
        ollama_models = []
        specialized_models = {
            'deepseek_available': False,
            'gemma_available': False,
            'qwen_available': False,
            'llama_available': False
        }
        
        if self.ollama_available:
            ollama_models = self.ollama_service.get_available_models()
            model_names = [model.get('name', '') for model in ollama_models]
            
            # Verificar disponibilidad de modelos especializados
            specialized_models['deepseek_available'] = any('deepseek' in name.lower() for name in model_names)
            specialized_models['gemma_available'] = any('gemma' in name.lower() for name in model_names)
            specialized_models['qwen_available'] = any('qwen' in name.lower() for name in model_names)
            specialized_models['llama_available'] = any('llama' in name.lower() for name in model_names)
            
        return {
            'ollama': {
                'available': self.ollama_available,
                'models': [model.get('name', '') for model in ollama_models],
                'base_url': self.ollama_service.config.base_url,
                'specialized_models': specialized_models
            },
            'groq': {
                'available': self.groq_available,
                'api_key_configured': bool(os.getenv('GROQ_API_KEY'))
            },
            'preferred_provider': self.provider_priority[0].value if self.provider_priority else 'none',
            'capabilities': {
                'deep_reasoning': specialized_models['deepseek_available'],
                'fast_processing': specialized_models['gemma_available'],
                'multilingual': specialized_models['qwen_available'],
                'general_purpose': specialized_models['llama_available']
            }
        }
        
    async def perform_deep_analysis(
        self,
        content: str,
        question: str = "Realiza un análisis geopolítico profundo",
        provider: AIProvider = AIProvider.AUTO
    ) -> AIResponse:
        """
        Realizar análisis profundo usando DeepSeek-R1 con razonamiento avanzado
        """
        if provider == AIProvider.AUTO:
            provider = self.get_optimal_provider(TaskType.ANALYSIS, prefer_local=True)
            
        try:
            if provider == AIProvider.OLLAMA and self.ollama_available:
                # Usar método de razonamiento profundo de DeepSeek
                reasoning_result = self.ollama_service.perform_deep_reasoning(
                    question=question,
                    context=content,
                    model=OllamaModel.DEEPSEEK_R1_7B
                )
                
                return AIResponse(
                    content=reasoning_result.get('conclusion', ''),
                    provider="ollama_deepseek",
                    model="deepseek-r1:7b",
                    success=reasoning_result.get('confidence', 0) > 0.5,
                    metadata=reasoning_result
                )
            elif provider == AIProvider.GROQ and self.groq_available:
                # Fallback a Groq para análisis profundo
                return await self._analyze_with_groq(content)
            else:
                return AIResponse(
                    content="Análisis no disponible",
                    provider="none",
                    model="none",
                    success=False,
                    error="Ningún proveedor de análisis profundo disponible"
                )
                
        except Exception as e:
            logger.error(f"Error en análisis profundo: {e}")
            return AIResponse(
                content="Error en análisis",
                provider=provider.value,
                model="error",
                success=False,
                error=str(e)
            )
            
    def generate_fast_summary(
        self,
        title: str,
        content: str,
        max_words: int = 100
    ) -> AIResponse:
        """
        Generar resumen rápido usando Gemma (optimizado para velocidad)
        """
        try:
            if self.ollama_available:
                # Usar Gemma para resúmenes rápidos
                summary = self.ollama_service.generate_lightweight_summary(
                    title=title,
                    content=content,
                    model=OllamaModel.GEMMA2_2B
                )
                
                return AIResponse(
                    content=summary,
                    provider="ollama_gemma",
                    model="gemma2:2b",
                    success=bool(summary and "error" not in summary.lower()),
                    metadata={"processing_type": "fast", "max_words": max_words}
                )
            elif self.groq_available:
                # Fallback a Groq
                return self._generate_summary_groq(title, content, max_words)
            else:
                return AIResponse(
                    content=f"Resumen rápido de: {title}",
                    provider="fallback",
                    model="none",
                    success=False,
                    error="Ningún proveedor disponible para resúmenes rápidos"
                )
                
        except Exception as e:
            logger.error(f"Error generando resumen rápido: {e}")
            return AIResponse(
                content="Error generando resumen",
                provider="error",
                model="error",
                success=False,
                error=str(e)
            )

# Instancia global del servicio unificado
unified_ai_service = UnifiedAIService()

# Funciones de conveniencia para mantener compatibilidad
async def analyze_with_ai(content: str, prefer_local: bool = True) -> Dict[str, Any]:
    """
    Función de conveniencia para análisis geopolítico
    """
    response = await unified_ai_service.analyze_geopolitical_content(
        content=content,
        prefer_local=prefer_local
    )
    
    if response.success and response.metadata:
        return response.metadata
    else:
        # Retornar estructura por defecto
        return {
            'risk_level': 'medium',
            'conflict_probability': 0.5,
            'countries': [],
            'key_topics': [],
            'sentiment_score': 0.0,
            'summary': response.content or 'Análisis no disponible',
            'provider': response.provider,
            'model': response.model
        }

def generate_summary_ai(title: str, content: str, prefer_local: bool = True) -> str:
    """
    Función de conveniencia para generar resúmenes
    """
    provider = AIProvider.OLLAMA if prefer_local else AIProvider.AUTO
    response = unified_ai_service.generate_summary(
        title=title,
        content=content,
        provider=provider
    )
    
    return response.content if response.success else f"Resumen de: {title}"
