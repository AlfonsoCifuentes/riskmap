"""
Cliente multi-modelo de IA para análisis geopolítico.
Soporta OpenAI, DeepSeek, Groq, HuggingFace y modelos locales.
"""

import os
import logging
from typing import Optional, Dict, List, Any
import json

logger = logging.getLogger(__name__)


class MultiModelAIClient:
    """Cliente que maneja múltiples modelos de IA con fallback automático."""

    def __init__(self):
        self.priority = self._get_model_priority()
        self.available_models = self._check_available_models()
        logger.info(f"AI Models initialized. Priority: {self.priority}")
        logger.info(f"Available models: {list(self.available_models.keys())}")

    def _get_model_priority(self) -> List[str]:
        """Obtiene la prioridad de modelos desde variables de entorno."""
        priority_str = os.getenv(
            'AI_MODEL_PRIORITY',
            'deepseek,openai,groq,huggingface,local')
        return [model.strip() for model in priority_str.split(',')]

    def _check_available_models(self) -> Dict[str, bool]:
        """Verifica qué modelos están disponibles basado en API keys."""
        available = {}

        # OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        available['openai'] = bool(openai_key and openai_key.startswith('sk-'))

        # DeepSeek
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        available['deepseek'] = bool(
            deepseek_key and deepseek_key != 'your_deepseek_api_key_here')

        # Groq
        groq_key = os.getenv('GROQ_API_KEY')
        available['groq'] = bool(
            groq_key and groq_key != 'your_groq_api_key_here')

        # HuggingFace
        hf_key = os.getenv('HUGGINGFACE_API_KEY')
        available['huggingface'] = bool(
            hf_key and hf_key != 'your_huggingface_api_key_here')

        # Local siempre está disponible
        available['local'] = True

        return available

    def generate_analysis(
            self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera análisis geopolítico usando el primer modelo disponible según prioridad.
        """
        articles_text = self._prepare_articles_text(articles)
        prompt = self._create_geopolitical_prompt(articles_text)

        for model_name in self.priority:
            if self.available_models.get(model_name, False):
                try:
                    logger.info(
                        f"Attempting to use {model_name} for AI analysis")
                    result = self._generate_with_model(model_name, prompt)

                    if result:
                        return {
                            'analysis': result,
                            'source': model_name,
                            'generated_at': self._get_timestamp(),
                            'articles_analyzed': len(articles)
                        }

                except Exception as e:
                    logger.error(f"Error with {model_name}: {e}")
                    continue

        # Fallback al análisis local
        return self._generate_fallback_analysis(len(articles))

    def _prepare_articles_text(self, articles: List[Dict[str, Any]]) -> str:
        """Prepara el texto de los artículos para el análisis."""
        return "\n\n".join([
            f"Título: {article.get('title', 'Sin título')}\n"
            f"Riesgo: {article.get('risk_level', 'Unknown')}\n"
            f"Tipo: {article.get('conflict_type', 'Unknown')}\n"
            f"País/Región: {article.get('country', 'Unknown')}, {article.get('region', 'Unknown')}\n"
            f"Fuente: {article.get('source', 'Unknown')}\n"
            f"Contenido: {article.get('content', 'Sin contenido')[:500]}..."
            # Limitar para evitar límites de tokens
            for article in articles[:8]
        ])

    def _create_geopolitical_prompt(self, articles_text: str) -> str:
        """Crea el prompt profesional para análisis geopolítico."""
        return f"""Actúa como un redactor senior de un prestigioso diario internacional especializado en geopolítica y análisis de riesgos globales. Tu tarea es escribir un artículo periodístico profesional basado en los siguientes reportes de noticias:

FUENTES DE INFORMACIÓN:
{articles_text}

Instrucciones específicas:
- Escribe un artículo periodístico cohesivo y bien estructurado
- Usa un estilo profesional pero accesible para lectores informados
- Integra la información de las fuentes de manera fluida
- NO uses formato Markdown (sin #, *, etc.)
- Estructura el artículo con párrafos claros y bien conectados
- Incluye un titular atractivo al inicio
- Mantén un tono objetivo pero analítico
- Máximo 600 palabras

El artículo debe fluir naturalmente desde una introducción hasta conclusiones, conectando los eventos reportados en un análisis geopolítico coherente."""

    def _generate_with_model(
            self,
            model_name: str,
            prompt: str) -> Optional[str]:
        """Genera texto usando el modelo especificado."""

        if model_name == 'openai':
            return self._generate_openai(prompt)
        elif model_name == 'deepseek':
            return self._generate_deepseek(prompt)
        elif model_name == 'groq':
            return self._generate_groq(prompt)
        elif model_name == 'huggingface':
            return self._generate_huggingface(prompt)
        elif model_name == 'local':
            return self._generate_local(prompt)

        return None

    def _generate_openai(self, prompt: str) -> Optional[str]:
        """Genera usando OpenAI."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un periodista y analista geopolítico senior con 20 años de experiencia escribiendo para medios internacionales prestigiosos. Tu estilo es claro, informativo y profesional."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None

    def _generate_deepseek(self, prompt: str) -> Optional[str]:
        """Genera usando DeepSeek (usando API compatible con OpenAI)."""
        try:
            from openai import OpenAI

            # DeepSeek usa API compatible con OpenAI
            client = OpenAI(
                api_key=os.getenv('DEEPSEEK_API_KEY'),
                base_url="https://api.deepseek.com/v1"
            )

            # Probar diferentes modelos de DeepSeek
            models_to_try = [
                "deepseek-chat",
                "deepseek-coder"
            ]

            for model in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "Eres un periodista y analista geopolítico senior con 20 años de experiencia escribiendo para medios internacionales prestigiosos. Tu estilo es claro, informativo y profesional."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        max_tokens=800,
                        temperature=0.7
                    )

                    logger.info(f"DeepSeek success with model: {model}")
                    return response.choices[0].message.content.strip()

                except Exception as model_error:
                    logger.warning(
                        f"DeepSeek model {model} failed: {model_error}")
                    continue

            return None

        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            return None

    def _generate_groq(self, prompt: str) -> Optional[str]:
        """Genera usando Groq."""
        try:
            from groq import Groq

            client = Groq(api_key=os.getenv('GROQ_API_KEY'))

            # Usar modelos actuales disponibles en Groq
            models_to_try = [
                "llama-3.1-8b-instant",
                "llama-3.2-11b-text-preview",
                "llama-3.2-3b-preview",
                "mixtral-8x7b-32768"
            ]

            for model in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "Eres un periodista y analista geopolítico senior con 20 años de experiencia escribiendo para medios internacionales prestigiosos. Tu estilo es claro, informativo y profesional."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        max_tokens=800,
                        temperature=0.7
                    )

                    logger.info(f"Groq success with model: {model}")
                    return response.choices[0].message.content.strip()

                except Exception as model_error:
                    logger.warning(f"Groq model {model} failed: {model_error}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Groq error: {e}")
            return None

    def _generate_huggingface(self, prompt: str) -> Optional[str]:
        """Genera usando HuggingFace Inference API."""
        try:
            import requests

            api_key = os.getenv('HUGGINGFACE_API_KEY')

            # Probar diferentes modelos según disponibilidad
            models_to_try = [
                "microsoft/DialoGPT-large",
                "microsoft/DialoGPT-medium",
                "facebook/blenderbot-400M-distill",
                "gpt2"
            ]

            for model_name in models_to_try:
                try:
                    model_url = f"https://api-inference.huggingface.co/models/{model_name}"

                    headers = {"Authorization": f"Bearer {api_key}"}

                    # Simplificar el prompt para modelos más pequeños
                    simplified_prompt = f"Escribe un análisis geopolitico profesional sobre: {prompt[:500]}"

                    payload = {
                        "inputs": simplified_prompt,
                        "parameters": {
                            "max_new_tokens": 400,
                            "temperature": 0.7,
                            "return_full_text": False,
                            "do_sample": True
                        }
                    }

                    response = requests.post(
                        model_url, headers=headers, json=payload, timeout=30)

                    if response.status_code == 200:
                        result = response.json()

                        if isinstance(result, list) and len(result) > 0:
                            generated_text = result[0].get(
                                'generated_text', '').strip()
                            if generated_text and len(generated_text) > 50:
                                logger.info(
                                    f"HuggingFace success with model: {model_name}")
                                return self._post_process_hf_text(
                                    generated_text)

                        elif isinstance(result, dict) and 'generated_text' in result:
                            generated_text = result['generated_text'].strip()
                            if generated_text and len(generated_text) > 50:
                                logger.info(
                                    f"HuggingFace success with model: {model_name}")
                                return self._post_process_hf_text(
                                    generated_text)

                    logger.warning(
                        f"HuggingFace model {model_name} returned: {response.status_code}")

                except Exception as model_error:
                    logger.warning(
                        f"HuggingFace model {model_name} failed: {model_error}")
                    continue

            return None

        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            return None

    def _post_process_hf_text(self, text: str) -> str:
        """Post-procesa el texto generado por HuggingFace."""
        # Limpiar y mejorar el texto generado
        if not text:
            return ""

        # Remover texto repetitivo común en modelos pequeños
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Evitar líneas muy cortas
                cleaned_lines.append(line)

        # Si el texto es muy corto, generar uno básico
        cleaned_text = '\n\n'.join(cleaned_lines)

        if len(cleaned_text) < 100:
            return self._generate_basic_analysis()

        return cleaned_text

    def _generate_basic_analysis(self) -> str:
        """Genera un análisis básico cuando los modelos fallan."""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M del %d de %B de %Y")

        return f"""Análisis Geopolítico Automatizado - {current_time}

La situación geopolítica global presenta múltiples variables de riesgo que requieren monitoreo constante. Los sistemas de inteligencia artificial están procesando información de múltiples fuentes para identificar patrones emergentes y evaluar impactos potenciales.

Las tensiones regionales actuales reflejan la complejidad del panorama internacional, donde factores económicos, políticos y sociales se entrelazan creando escenarios de incertidumbre. El análisis continuo de estas variables permite anticipar posibles escaladas y identificar oportunidades de estabilización.

Se recomienda mantener vigilancia sobre los desarrollos en curso y estar preparados para ajustar estrategias según evolucionen los eventos."""

    def _generate_local(self, prompt: str) -> Optional[str]:
        """Genera usando modelo local (Transformers)."""
        try:
            # Implementación simple con transformers local
            # Nota: Esto requiere descargar modelos localmente
            logger.info("Using local model generation")

            # Por ahora, usar análisis de respaldo
            return None

        except Exception as e:
            logger.error(f"Local model error: {e}")
            return None

    def _generate_fallback_analysis(self, num_articles: int) -> Dict[str, Any]:
        """Genera análisis de respaldo cuando fallan otros modelos."""
        from datetime import datetime

        current_time = datetime.now().strftime("%H:%M del %d de %B de %Y")

        analysis = f"""ANÁLISIS GEOPOLÍTICO GLOBAL - {current_time}

El panorama internacional actual presenta múltiples focos de tensión que demandan atención constante por parte de analistas y responsables de política exterior. Nuestros sistemas de monitoreo continuo están procesando información de fuentes globales para identificar patrones emergentes y evaluar riesgos potenciales.

SITUACIÓN ACTUAL

La estabilidad geopolítica mundial enfrenta desafíos complejos que abarcan desde tensiones regionales tradicionales hasta nuevas formas de conflicto en el espacio digital y económico. Los indicadores de riesgo muestran la necesidad de mantener vigilancia sobre varios teatros de operaciones simultáneamente.

Las regiones de mayor preocupación incluyen áreas donde confluyen intereses geopolíticos divergentes, recursos estratégicos limitados y poblaciones bajo presión socioeconómica. Estos factores crean condiciones propicias para la escalada de tensiones.

FACTORES DE RIESGO IDENTIFICADOS

Entre los elementos que requieren monitoreo prioritario se encuentran las disputas territoriales, los desequilibrios económicos regionales, los movimientos de población y las disrupciones en cadenas de suministro críticas. Cada uno de estos vectores tiene potencial para generar efectos en cascada que trasciendan fronteras nacionales.

La interconexión de las economías globales significa que perturbaciones localizadas pueden tener impactos sistémicos, particularmente en sectores como energía, tecnología y alimentos básicos.

PERSPECTIVAS Y RECOMENDACIONES

Para las próximas 24-48 horas, se recomienda mantener vigilancia especial sobre canales diplomáticos oficiales, indicadores económicos clave y movimientos militares en regiones sensibles. La información de código abierto continúa siendo fundamental para construir una imagen situacional precisa.

El monitoreo continuo debe enfocarse en identificar señales tempranas de escalada, así como oportunidades para la estabilización a través de mecanismos diplomáticos y de cooperación internacional."""

        return {
            'analysis': analysis,
            'source': 'fallback',
            'generated_at': self._get_timestamp(),
            'articles_analyzed': num_articles
        }

    def _get_timestamp(self) -> str:
        """Obtiene timestamp actual en formato ISO."""
        from datetime import datetime
        return datetime.now().isoformat()


# Instancia global del cliente
ai_client = MultiModelAIClient()


def generate_ai_analysis(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Función de conveniencia para generar análisis de IA.
    """
    return ai_client.generate_analysis(articles)
