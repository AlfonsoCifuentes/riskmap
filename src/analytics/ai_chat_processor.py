"""
AI Chat Processor for Geopolitical Intelligence
Uses completely free and open-source AI models for chat functionality
"""

import logging
import random
import re
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AIChat:
    """Chat processor using free/open-source AI models"""
    
    def __init__(self):
        self.model_initialized = False
        self.chat_model = None
        self.tokenizer = None
        self.conversation_history = []
        
        # Geopolitical knowledge base for enhanced responses
        self.geopolitical_context = {
            "conflict_zones": ["Ukraine", "Middle East", "South China Sea", "Kashmir", "Sahel", "Horn of Africa"],
            "risk_factors": ["Political instability", "Economic sanctions", "Territorial disputes", "Resource competition", "Cyber warfare"],
            "regions": {
                "Europe": ["NATO expansion", "Energy security", "Migration", "Brexit implications"],
                "Asia-Pacific": ["China-Taiwan tensions", "North Korea", "Trade wars", "ASEAN dynamics"],
                "Middle East": ["Iran nuclear program", "Israel-Palestine", "Syria", "Yemen"],
                "Africa": ["Sahel security", "Economic development", "Democratic transitions", "Resource extraction"],
                "Americas": ["US-China competition", "Venezuela crisis", "Migration patterns", "Trade agreements"]
            },
            "analysis_frameworks": [
                "Political risk assessment", "Economic impact analysis", "Security threat evaluation",
                "Social stability indicators", "Regional power dynamics", "International law implications"
            ]
        }
        
        # Initialize the model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the open-source AI model"""
        try:
            # Try to use HuggingFace transformers (completely free and open-source)
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # Use a lightweight model that works well in Spanish and for analysis
            model_name = "microsoft/DialoGPT-medium"  # Free alternative: "distilgpt2"
            
            logger.info(f"Initializing AI chat model: {model_name}")
            
            # Check if CUDA is available
            device = 0 if torch.cuda.is_available() else -1
            
            # Initialize the conversation pipeline
            self.chat_model = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=model_name,
                device=device,
                pad_token_id=50256,  # EOS token for GPT models
                max_length=512,
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
            
            self.model_initialized = True
            logger.info("AI chat model initialized successfully")
            
        except ImportError:
            logger.warning("Transformers library not available, using rule-based responses")
            self.model_initialized = False
        except Exception as e:
            logger.error(f"Error initializing AI model: {str(e)}")
            self.model_initialized = False
    
    def generate_response(self, user_message: str) -> str:
        """Generate AI response to user message"""
        try:
            # Clean and validate input
            user_message = self._clean_input(user_message)
            
            if len(user_message.strip()) < 3:
                return "Por favor, proporciona una pregunta más específica para poder ayudarte mejor."
            
            # Try to use the AI model if available
            if self.model_initialized and self.chat_model:
                response = self._generate_ai_response(user_message)
                if response:
                    return response
            
            # Fallback to intelligent rule-based responses
            return self._generate_intelligent_fallback(user_message)
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._generate_error_response()
    
    def _generate_ai_response(self, user_message: str) -> Optional[str]:
        """Generate response using the AI model"""
        try:
            # Create a geopolitical context prompt
            prompt = self._create_geopolitical_prompt(user_message)
            
            # Generate response
            outputs = self.chat_model(
                prompt,
                max_new_tokens=150,
                num_return_sequences=1,
                pad_token_id=self.chat_model.tokenizer.eos_token_id,
                temperature=0.7,
                do_sample=True
            )
            
            if outputs and len(outputs) > 0:
                response = outputs[0]['generated_text']
                # Extract only the new generated part
                response = response[len(prompt):].strip()
                
                # Clean up the response
                response = self._clean_ai_response(response)
                
                if len(response) > 20:  # Ensure we have a meaningful response
                    return response
            
        except Exception as e:
            logger.error(f"Error in AI model generation: {str(e)}")
        
        return None
    
    def _create_geopolitical_prompt(self, user_message: str) -> str:
        """Create a geopolitical context prompt for the AI"""
        context = f"""Eres un analista experto en geopolítica y seguridad internacional. Tu tarea es proporcionar análisis informados, objetivos y profesionales sobre temas geopolíticos.

Pregunta del usuario: {user_message}

Respuesta del analista:"""
        
        return context
    
    def _clean_ai_response(self, response: str) -> str:
        """Clean and format the AI-generated response"""
        # Remove potential artifacts
        response = re.sub(r'<[^>]+>', '', response)  # Remove HTML tags
        response = re.sub(r'\[.*?\]', '', response)  # Remove brackets
        response = re.sub(r'\s+', ' ', response)     # Normalize whitespace
        
        # Ensure it ends properly
        if response and not response.endswith(('.', '!', '?', ':')):
            # Find the last complete sentence
            last_period = response.rfind('.')
            if last_period > len(response) * 0.5:  # If we have at least half the response
                response = response[:last_period + 1]
        
        return response.strip()
    
    def _generate_intelligent_fallback(self, user_message: str) -> str:
        """Generate intelligent rule-based responses"""
        message_lower = user_message.lower()
        
        # Identify the type of question and context
        question_type = self._identify_question_type(message_lower)
        relevant_context = self._get_relevant_context(message_lower)
        
        # Generate contextual response based on patterns
        if "conflicto" in message_lower or "guerra" in message_lower:
            return self._generate_conflict_analysis(user_message, relevant_context)
        elif "riesgo" in message_lower or "peligro" in message_lower:
            return self._generate_risk_analysis(user_message, relevant_context)
        elif "región" in message_lower or "país" in message_lower:
            return self._generate_regional_analysis(user_message, relevant_context)
        elif "económico" in message_lower or "comercio" in message_lower:
            return self._generate_economic_analysis(user_message, relevant_context)
        elif "análisis" in message_lower or "cómo" in message_lower:
            return self._generate_methodology_explanation(user_message)
        elif "tendencia" in message_lower or "futuro" in message_lower:
            return self._generate_trend_analysis(user_message, relevant_context)
        else:
            return self._generate_general_response(user_message, relevant_context)
    
    def _identify_question_type(self, message: str) -> str:
        """Identify the type of geopolitical question"""
        if any(word in message for word in ["qué", "cuál", "cuáles"]):
            return "what"
        elif any(word in message for word in ["cómo", "de qué manera"]):
            return "how"
        elif any(word in message for word in ["por qué", "porqué"]):
            return "why"
        elif any(word in message for word in ["dónde", "donde"]):
            return "where"
        elif any(word in message for word in ["cuándo", "cuando"]):
            return "when"
        else:
            return "general"
    
    def _get_relevant_context(self, message: str) -> Dict[str, Any]:
        """Get relevant geopolitical context for the message"""
        context = {}
        
        # Check for conflict zones
        for zone in self.geopolitical_context["conflict_zones"]:
            if zone.lower() in message:
                context["conflict_zone"] = zone
                break
        
        # Check for regions
        for region, topics in self.geopolitical_context["regions"].items():
            if region.lower() in message:
                context["region"] = region
                context["regional_topics"] = topics
                break
        
        # Check for risk factors
        for factor in self.geopolitical_context["risk_factors"]:
            if factor.lower() in message:
                context["risk_factor"] = factor
                break
        
        return context
    
    def _generate_conflict_analysis(self, user_message: str, context: Dict) -> str:
        """Generate conflict analysis response"""
        base_response = f"En el análisis de conflictos geopolíticos relacionados con '{user_message}', es importante considerar varios factores clave:\n\n"
        
        if context.get("conflict_zone"):
            base_response += f"• **Zona de conflicto identificada**: {context['conflict_zone']} presenta dinámicas complejas que requieren monitoreo constante.\n"
        
        base_response += """• **Factores de escalada**: Tensiones políticas, disputas territoriales, competencia por recursos y dinámicas de poder regional.

• **Indicadores de riesgo**: Cambios en retórica oficial, movimientos militares, sanciones económicas y reacciones de la comunidad internacional.

• **Impacto potencial**: Efectos en la estabilidad regional, flujos comerciales, precios de commodities y relaciones diplomáticas.

Para un análisis más detallado, recomiendo revisar los reportes específicos en la sección de Reports de nuestro sistema."""
        
        return base_response
    
    def _generate_risk_analysis(self, user_message: str, context: Dict) -> str:
        """Generate risk analysis response"""
        base_response = f"El análisis de riesgo geopolítico para '{user_message}' involucra una evaluación multidimensional:\n\n"
        
        base_response += """• **Riesgo político**: Estabilidad institucional, cambios de gobierno, y políticas internas que afectan relaciones internacionales.

• **Riesgo económico**: Volatilidad de mercados, sanciones, disrupciones comerciales y impacto en cadenas de suministro.

• **Riesgo de seguridad**: Amenazas a la estabilidad regional, actividad militar, terrorismo y ciberseguridad.

• **Metodología de evaluación**: Utilizamos análisis de sentimiento en noticias, indicadores económicos, y patrones históricos para generar evaluaciones de riesgo.

• **Escalas de medición**: Bajo, Medio, Alto, y Crítico, con actualizaciones en tiempo real basadas en eventos emergentes."""
        
        if context.get("risk_factor"):
            base_response += f"\n\n**Factor específico identificado**: {context['risk_factor']} es particularmente relevante en este contexto."
        
        return base_response
    
    def _generate_regional_analysis(self, user_message: str, context: Dict) -> str:
        """Generate regional analysis response"""
        base_response = f"El análisis regional para '{user_message}' considera las dinámicas específicas del área:\n\n"
        
        if context.get("region") and context.get("regional_topics"):
            base_response += f"**Región: {context['region']}**\n"
            base_response += "• Temas principales:\n"
            for topic in context['regional_topics'][:3]:  # Limit to 3 topics
                base_response += f"  - {topic}\n"
            base_response += "\n"
        
        base_response += """• **Factores geográficos**: Ubicación estratégica, recursos naturales, rutas comerciales y fronteras compartidas.

• **Dinámicas políticas**: Sistemas de gobierno, alianzas regionales, organizaciones internacionales y liderazgo político.

• **Consideraciones económicas**: PIB regional, comercio internacional, inversión extranjera y desarrollo infraestructural.

• **Aspectos socioculturales**: Demografía, religión, etnicidad, migraciones y tensiones sociales.

• **Interconectividad**: Relaciones con otras regiones, dependencias económicas y vínculos de seguridad."""
        
        return base_response
    
    def _generate_economic_analysis(self, user_message: str, context: Dict) -> str:
        """Generate economic analysis response"""
        return f"""El análisis económico geopolítico de '{user_message}' examina las interconexiones entre política y economía:

• **Impacto comercial**: Efectos en flujos comerciales bilaterales y multilaterales, aranceles, y barreras no arancelarias.

• **Mercados financieros**: Volatilidad en divisas, mercados de valores, bonos soberanos y flujos de capital.

• **Recursos estratégicos**: Acceso y control de materias primas, energía, y recursos críticos para tecnología.

• **Sanciones económicas**: Implementación, efectividad y consecuencias no deseadas de medidas restrictivas.

• **Cadenas de suministro**: Disrupciones, redireccionamiento de rutas comerciales y estrategias de diversificación.

• **Indicadores clave**: PIB, inflación, desempleo, balanza comercial y reservas internacionales como métricas de estabilidad."""
    
    def _generate_methodology_explanation(self, user_message: str) -> str:
        """Generate methodology explanation"""
        return f"""Nuestra metodología de análisis geopolítico para '{user_message}' utiliza un enfoque integral:

**🔍 Recolección de datos:**
• Fuentes de noticias globales en múltiples idiomas
• Reportes gubernamentales y de organizaciones internacionales
• Análisis de redes sociales y medios digitales
• Datos económicos y estadísticas oficiales

**🧠 Procesamiento con IA:**
• Análisis de sentimiento en tiempo real
• Reconocimiento de entidades geopolíticas
• Detección de patrones y tendencias
• Clasificación automática de eventos

**📊 Evaluación de riesgo:**
• Modelos predictivos basados en datos históricos
• Indicadores tempranos de escalada
• Matrices de impacto y probabilidad
• Validación cruzada con múltiples fuentes

**📈 Visualización y reportes:**
• Dashboards interactivos en tiempo real
• Mapas de calor de riesgo geopolítico
• Alertas automáticas por nivel de riesgo
• Reportes personalizables por región o tema"""
    
    def _generate_trend_analysis(self, user_message: str, context: Dict) -> str:
        """Generate trend analysis response"""
        return f"""El análisis de tendencias geopolíticas para '{user_message}' identifica patrones emergentes:

**📈 Tendencias actuales:**
• Multipolaridad y reconfiguración del poder global
• Competencia tecnológica entre grandes potencias
• Resurgimiento del nacionalismo y proteccionismo
• Impacto del cambio climático en la geopolítica

**🔮 Proyecciones futuras:**
• Evolución de alianzas y bloques regionales
• Transformación de instituciones multilaterales
• Impacto de tecnologías emergentes (IA, quantum, espacio)
• Nuevas formas de guerra (híbrida, cibernética, información)

**⚠️ Factores de incertidumbre:**
• Crisis económicas y pandemias globales
• Movimientos populistas y cambios democráticos
• Escasez de recursos y migraciones masivas
• Disrupciones tecnológicas y sociales

Las tendencias se actualizan continuamente basándose en análisis de big data y machine learning."""
    
    def _generate_general_response(self, user_message: str, context: Dict) -> str:
        """Generate general geopolitical response"""
        responses = [
            f"Tu consulta sobre '{user_message}' toca aspectos importantes del análisis geopolítico moderno. En el contexto internacional actual, es fundamental considerar la interconexión entre factores políticos, económicos, sociales y de seguridad para comprender completamente las dinámicas globales.",
            
            f"Respecto a '{user_message}', el análisis geopolítico requiere una perspectiva multidisciplinaria que integre ciencias políticas, economía internacional, estudios de seguridad y análisis regional. Nuestro sistema utiliza técnicas avanzadas de IA para procesar información de múltiples fuentes y generar evaluaciones comprehensivas.",
            
            f"La pregunta sobre '{user_message}' se relaciona con dinámicas geopolíticas complejas que nuestro sistema monitorea continuamente. Utilizamos análisis de big data, procesamiento de lenguaje natural y modelos predictivos para ofrecer insights actualizados sobre tendencias globales y riesgos emergentes."
        ]
        
        return random.choice(responses)
    
    def _generate_error_response(self) -> str:
        """Generate error response when all else fails"""
        error_responses = [
            "Disculpa, estoy experimentando dificultades técnicas temporales. Por favor, intenta reformular tu pregunta o consulta los reportes disponibles en la sección Reports.",
            "Sistema de chat temporalmente no disponible. Para consultas específicas, te recomiendo revisar nuestros análisis detallados en la sección de Reports.",
            "Lo siento, no puedo procesar tu consulta en este momento. Nuestros análisis geopolíticos están disponibles en formato de reportes en la plataforma."
        ]
        return random.choice(error_responses)
    
    def _clean_input(self, text: str) -> str:
        """Clean and validate user input"""
        # Remove potentially harmful content
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        text = re.sub(r'[^\w\s\.\?\!\,\:\;\-\(\)áéíóúñü]', '', text, flags=re.IGNORECASE)
        
        # Limit length
        if len(text) > 500:
            text = text[:500]
        
        return text.strip()
    
    def get_chat_statistics(self) -> Dict[str, Any]:
        """Get chat statistics and model information"""
        return {
            "model_initialized": self.model_initialized,
            "model_type": "HuggingFace Transformers" if self.model_initialized else "Rule-based",
            "conversation_length": len(self.conversation_history),
            "is_open_source": True,
            "is_free": True,
            "last_update": datetime.utcnow().isoformat()
        }
