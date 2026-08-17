"""
Groq Service - Servicio independiente para análisis geopolítico con Groq AI
Maneja la comunicación con la API de Groq y genera análisis especializados
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class GroqService:
    """Servicio para análisis geopolítico con Groq AI"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.client = None
        self.available = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente de Groq"""
        try:
            if not self.api_key:
                logger.warning("GROQ_API_KEY no encontrada en variables de entorno")
                return
            
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.available = True
            logger.info("✅ Cliente Groq inicializado correctamente")
            
        except ImportError:
            logger.error("❌ Librería Groq no instalada. Ejecuta: pip install groq")
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente Groq: {e}")
    
    def is_available(self) -> bool:
        """Verifica si el servicio Groq está disponible"""
        return self.available and self.client is not None
    
    def generate_geopolitical_analysis(self, articles: List[Dict], analysis_type: str = "standard") -> Dict[str, Any]:
        """
        Genera análisis geopolítico usando Groq AI
        
        Args:
            articles: Lista de artículos para analizar
            analysis_type: Tipo de análisis ('standard', 'detailed', 'brief')
            
        Returns:
            Dict con el análisis generado
        """
        if not self.is_available():
            logger.warning("Servicio Groq no disponible, usando análisis de respaldo")
            return self._generate_fallback_analysis(articles)
        
        try:
            # Preparar contexto de artículos
            articles_context = self._prepare_articles_context(articles)
            
            # Generar prompt según tipo de análisis
            prompt = self._generate_prompt(articles_context, len(articles), analysis_type)
            
            logger.info(f"🤖 Generando análisis {analysis_type} con Groq AI...")
            
            # Llamada a la API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analista geopolítico de élite con experiencia en periodismo internacional. Tu única salida es un objeto JSON válido que sigue estrictamente la estructura solicitada."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="openai/gpt-oss-20b",
                temperature=0.75,
                max_tokens=self._get_max_tokens(analysis_type),
                response_format={"type": "json_object"}
            )
            
            response_content = chat_completion.choices[0].message.content
            logger.info("✅ Análisis Groq generado exitosamente")
            
            # Procesar respuesta
            analysis_data = self._process_groq_response(response_content, articles)
            return analysis_data
            
        except Exception as e:
            logger.error(f"❌ Error en la llamada a Groq API: {e}")
            return self._generate_fallback_analysis(articles)
    
    def _prepare_articles_context(self, articles: List[Dict]) -> str:
        """Prepara el contexto de artículos para el prompt"""
        context_parts = []
        
        for i, article in enumerate(articles[:20]):  # Limitar a 20 artículos
            title = article.get('title', 'N/A')
            content = article.get('content', 'N/A')
            location = article.get('location', 'N/A')
            risk_level = article.get('risk_level', 'N/A')
            
            # Truncar contenido si es muy largo
            if len(content) > 500:
                content = content[:500] + "..."
            
            context_parts.append(
                f"ARTÍCULO {i+1}:\n"
                f"Título: {title}\n"
                f"Contenido: {content}\n"
                f"Ubicación: {location}\n"
                f"Nivel de Riesgo: {risk_level}"
            )
        
        return "\n\n".join(context_parts)
    
    def _generate_prompt(self, articles_context: str, num_articles: int, analysis_type: str) -> str:
        """Genera el prompt según el tipo de análisis"""
        
        base_instructions = f"""
        Analiza los siguientes {num_articles} artículos de noticias y genera un análisis geopolítico en formato HTML.

        ARTÍCULOS DE CONTEXTO:
        {articles_context}

        INSTRUCCIONES CLAVE:
        1. **Estilo Periodístico Humano**: Escribe con voz personal y experta, no como IA.
        2. **Nombres Propios**: Menciona líderes, países y regiones relevantes.
        3. **Análisis Profundo**: Conecta eventos y tendencias. No te limites a resumir.
        4. **Opinión Fundamentada**: Expresa proyecciones desde el rigor analítico.
        5. **Formato HTML**: El content debe ser HTML válido usando solo <p> y <strong>.
        """
        
        if analysis_type == "brief":
            specific_instructions = """
            TIPO: ANÁLISIS BREVE
            - Máximo 3 párrafos
            - Enfoque en tendencias principales
            - Conclusiones directas
            """
        elif analysis_type == "detailed":
            specific_instructions = """
            TIPO: ANÁLISIS DETALLADO
            - 6-8 párrafos
            - Análisis regional específico
            - Proyecciones a mediano plazo
            - Factores económicos y militares
            """
        else:  # standard
            specific_instructions = """
            TIPO: ANÁLISIS ESTÁNDAR
            - 4-6 párrafos
            - Balance entre profundidad y síntesis
            - Tendencias globales y regionales
            """
        
        json_format = """
        RESPONDE ÚNICAMENTE CON UN OBJETO JSON VÁLIDO:
        {
          "title": "Titular principal impactante y profesional",
          "subtitle": "Subtítulo que resuma la esencia del análisis",
          "content": "Cuerpo completo del artículo en HTML usando solo <p> y <strong>",
          "sources_count": """ + str(num_articles) + """,
          "analysis_type": \"""" + analysis_type + """\",
          "key_regions": ["Region1", "Region2", "Region3"],
          "risk_assessment": "low|medium|high|critical",
          "confidence_level": 0.85
        }
        """
        
        return base_instructions + "\n" + specific_instructions + "\n" + json_format
    
    def _get_max_tokens(self, analysis_type: str) -> int:
        """Determina el número máximo de tokens según el tipo de análisis"""
        token_limits = {
            "brief": 1500,
            "standard": 3000,
            "detailed": 4000
        }
        return token_limits.get(analysis_type, 3000)
    
    def _process_groq_response(self, response_content: str, articles: List[Dict]) -> Dict[str, Any]:
        """Procesa la respuesta de Groq y la valida"""
        try:
            analysis_data = json.loads(response_content)
            
            # Validar campos requeridos
            required_fields = ['title', 'subtitle', 'content']
            missing_fields = [field for field in required_fields if field not in analysis_data]
            
            if missing_fields:
                logger.warning(f"Campos faltantes en respuesta Groq: {missing_fields}")
                return self._generate_fallback_analysis(articles)
            
            # Agregar metadatos
            analysis_data.update({
                'sources_count': len(articles),
                'generation_timestamp': datetime.now().isoformat(),
                'ai_generated': True,
                'service_used': 'Groq AI',
                'model': 'openai/gpt-oss-20b'
            })
            
            return analysis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON de Groq: {e}")
            logger.error(f"Contenido recibido: {response_content[:500]}...")
            return self._generate_fallback_analysis(articles)
    
    def generate_alternative_analysis(self, articles: List[Dict]) -> Dict[str, Any]:
        """Genera un análisis alternativo con enfoque económico-político"""
        if not self.is_available():
            return self._generate_fallback_analysis(articles)
        
        try:
            articles_context = self._prepare_articles_context(articles)
            
            prompt = f"""
            Como analista económico-político senior, genera un análisis que conecte los eventos geopolíticos con sus implicaciones económicas y comerciales.

            ARTÍCULOS:
            {articles_context}

            ENFOQUE ESPECÍFICO:
            - Impacto en mercados financieros y commodities
            - Rutas comerciales y cadenas de suministro
            - Políticas monetarias y comerciales
            - Inversiones e infraestructura estratégica

            Responde con JSON válido:
            {{
              "title": "Título enfocado en economía geopolítica",
              "subtitle": "Subtítulo sobre impactos económicos",
              "content": "Análisis HTML con enfoque económico-comercial",
              "sources_count": {len(articles)},
              "economic_indicators": ["Indicador1", "Indicador2"],
              "market_impact": "positive|negative|mixed|uncertain"
            }}
            """
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres un analista económico-geopolítico experto. Solo respondes JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                model="openai/gpt-oss-20b",
                temperature=0.7,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            response_content = chat_completion.choices[0].message.content
            return self._process_groq_response(response_content, articles)
            
        except Exception as e:
            logger.error(f"Error en análisis alternativo Groq: {e}")
            return self._generate_fallback_analysis(articles)
    
    def _generate_fallback_analysis(self, articles: List[Dict]) -> Dict[str, Any]:
        """Genera análisis de respaldo cuando Groq no está disponible"""
        current_date = datetime.now().strftime("%d de %B de %Y")
        
        # Analizar artículos para generar contenido contextual
        high_risk_count = len([a for a in articles if a.get('risk_level', '').lower() in ['high', 'critical']])
        regions = list(set([a.get('location', 'Desconocida') for a in articles if a.get('location')]))
        regions = regions[:5]  # Limitar a 5 regiones principales
        
        fallback_content = f"""
            <p>El panorama geopolítico mundial presenta {high_risk_count} situaciones de alto riesgo que requieren atención inmediata de la comunidad internacional. Los eventos monitoreados en las últimas horas reflejan la complejidad de un sistema internacional en transformación.</p>
            
            <p>Las regiones de {', '.join(regions[:3])} continúan siendo focos de tensión que influyen en la estabilidad global. Los desarrollos recientes sugieren un patrón de <strong>escalada controlada</strong> donde los actores internacionales buscan posiciones ventajosas sin cruzar umbrales críticos.</p>
            
            <p>El análisis de {len(articles)} fuentes indica que las <strong>dinámicas de poder regional</strong> están evolucionando más rápidamente que las estructuras institucionales internacionales. Esta asimetría temporal genera ventanas de oportunidad para cambios geopolíticos significativos.</p>
            
            <p>La comunidad internacional debe prepararse para escenarios de <strong>multipolaridad acelerada</strong>, donde las alianzas tradicionales coexisten con nuevas formas de cooperación estratégica. El monitoreo continuo de estos desarrollos será crucial para anticipar puntos de inflexión críticos.</p>
        """
        
        return {
            "title": "Reconfiguración Geopolítica en Tiempo Real",
            "subtitle": f"Análisis de {len(articles)} fuentes revela patrones emergentes de tensión global",
            "content": fallback_content,
            "sources_count": len(articles),
            "analysis_type": "fallback",
            "key_regions": regions[:3],
            "risk_assessment": "medium" if high_risk_count < 3 else "high",
            "confidence_level": 0.70,
            "ai_generated": False,
            "service_used": "Fallback Analysis",
            "generation_timestamp": datetime.now().isoformat()
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Obtiene información del servicio Groq"""
        return {
            'service_available': self.available,
            'api_key_configured': bool(self.api_key),
            'client_initialized': self.client is not None,
            'supported_models': ['openai/gpt-oss-20b', 'openai/gpt-oss-120b'],
            'max_tokens_limit': 8000,
            'service_name': 'Groq AI'
        }

# Instancia global del servicio
groq_service = GroqService()
