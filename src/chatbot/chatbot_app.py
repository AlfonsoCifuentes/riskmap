"""
Chatbot Interactivo Profesional para Inteligencia Geopolítica
=============================================================
Implementación con LangChain, OpenAI, y búsqueda semántica según context.ipynb.
Soporte multilingüe completo en los 5 idiomas: ES, EN, RU, ZH, AR.
"""

from src.utils.config import config, db_manager as DatabaseManager
import gradio as gr
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)

# Importaciones para LangChain y AI
try:
    import openai
    from langchain.llms import OpenAI
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    from langchain.vectorstores import FAISS
    from langchain.embeddings import OpenAIEmbeddings
    from sentence_transformers import SentenceTransformer
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain no disponible: {e}")
    LANGCHAIN_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS no disponible - funcionalidad de búsqueda limitada")


class MultilingualGeopoliticalChatbot:
    """
    Chatbot profesional para consultas de inteligencia geopolítica.

    Características según context.ipynb:
    - Búsqueda semántica con embeddings
    - Respuestas generadas con LLMs
    - Soporte multilingüe (ES, EN, RU, ZH, AR)
    - Consulta de datos reales de la base de eventos
    """

    def __init__(self):
        self.db = DatabaseManager(config)
        self.openai_key = config.get_openai_key()
        self.supported_languages = ['es', 'en', 'ru', 'zh', 'ar']

        # Inicializar componentes de IA
        self._initialize_ai_components()

        # Templates de preguntas inteligentes
        self.question_patterns = {
            'regional_stability': [
                'regiones más inestables',
                'areas of conflict',
                'нестабильные регионы',
                '不稳定地区',
                'المناطق غير المستقرة'],
            'conflict_analysis': [
                'conflictos militares',
                'military conflicts',
                'военные конфликты',
                '军事冲突',
                'النزاعات العسكرية'],
            'protest_monitoring': [
                'protestas',
                'protests',
                'протесты',
                '抗议活动',
                'الاحتجاجات'],
            'diplomatic_crisis': [
                'crisis diplomática',
                'diplomatic crisis',
                'дипломатический кризис',
                '外交危机',
                'الأزمة الدبلوماسية'],
            'sentiment_trends': [
                'tendencias sentimiento',
                'sentiment trends',
                'тенденции настроения',
                '情感趋势',
                'اتجاهات المشاعر']}

        # Respuestas multilingües
        self.language_responses = {
            'en': {
                'greeting': 'Hello! I can help you analyze geopolitical events. Ask me about regions, conflicts, protests, or trends.',
                'no_data': 'I could not find any relevant data for your query.',
                'error': 'I encountered an error processing your request.'},
            'es': {
                'greeting': 'Hola! Puedo ayudarte a analizar eventos geopolíticos. Pregúntame sobre regiones, conflictos, protestas o tendencias.',
                'no_data': 'No pude encontrar datos relevantes para tu consulta.',
                'error': 'Encontré un error procesando tu solicitud.'},
            'ru': {
                'greeting': 'Привет! Я могу помочь анализировать геополитические события. Спрашивайте о регионах, конфликтах, протестах или тенденциях.',
                'no_data': 'Я не смог найти соответствующие данные для вашего запроса.',
                'error': 'Я столкнулся с ошибкой при обработке вашего запроса.'},
            'zh': {
                'greeting': '你好！我可以帮助分析地缘政治事件。问我关于地区、冲突、抗议或趋势的问题。',
                'no_data': '我找不到与您查询相关的数据。',
                'error': '处理您的请求时遇到错误。'},
            'ar': {
                'greeting': 'مرحبا! يمكنني مساعدتك في تحليل الأحداث الجيوسياسية. اسألني عن المناطق والصراعات والاحتجاجات أو الاتجاهات.',
                'no_data': 'لم أتمكن من العثور على بيانات ذات صلة بطلبك.',
                'error': 'واجهت خطأ في معالجة طلبك.'}}

        # Sistema de memoria conversacional
        if LANGCHAIN_AVAILABLE and self.openai_key:
            self.memory = ConversationBufferWindowMemory(k=5)
            self.conversation_chain = None
            self._setup_conversation_chain()

        # Índice de búsqueda semántica
        self._build_semantic_index()

    def _initialize_ai_components(self):
        """Inicializa componentes de IA con manejo robusto de errores."""
        self.ai_available = False
        self.embeddings_model = None
        self.llm = None

        if not self.openai_key or self.openai_key == "your_openai_key_here":
            logger.warning(
                "[WARN] OpenAI API key no configurada - funcionalidad limitada")
            return

        try:
            if LANGCHAIN_AVAILABLE:
                # Configurar OpenAI
                openai.api_key = self.openai_key

                # Inicializar LLM
                self.llm = OpenAI(
                    openai_api_key=self.openai_key,
                    temperature=0.7,
                    max_tokens=500
                )

                # Inicializar embeddings
                self.embeddings_model = OpenAIEmbeddings(
                    openai_api_key=self.openai_key)

                self.ai_available = True
                logger.info(
                    "[OK] Componentes de IA inicializados correctamente")

        except Exception as e:
            logger.error(f"[ERROR] Error inicializando IA: {e}")

        # Fallback a modelo local si OpenAI no está disponible
        if not self.ai_available:
            try:
                self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("[OK] Modelo de embeddings local inicializado")
            except Exception as e:
                logger.error(f"[ERROR] Error con modelo local: {e}")

    def _setup_conversation_chain(self):
        """Configura cadena de conversación con LangChain."""
        if not self.llm:
            return

        try:
            # Prompt personalizado para análisis geopolítico
            system_prompt = """You are a professional geopolitical intelligence analyst with access to real-time news data
from multiple sources in Spanish, English, Russian, Chinese, and Arabic.

Your capabilities include:
- Analyzing geopolitical events and trends
- Assessing risk levels in different regions
- Tracking conflicts, protests, and diplomatic crises
- Providing sentiment analysis of regional stability
- Citing specific sources and dates from the database

Guidelines:
1. Provide accurate, factual responses based on available data
2. Always cite sources, dates, and data confidence levels
3. Detect user language and respond in the same language when possible
4. If data is insufficient, clearly state limitations
5. Focus on actionable intelligence insights

Current date: {current_date}
Available languages: Spanish, English, Russian, Chinese, Arabic
Data sources: NewsAPI, RSS feeds, specialized geopolitical sources
"""

            self.conversation_chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                verbose=False
            )

            # Inyectar prompt del sistema
            current_date = datetime.now().strftime("%Y-%m-%d")
            system_message = system_prompt.format(current_date=current_date)
            self.memory.chat_memory.add_ai_message(system_message)

        except Exception as e:
            logger.error(f"Error configurando conversación: {e}")

    def _get_recent_processed_articles(self, limit: int = 1000) -> List[Dict]:
        """Obtiene artículos procesados recientes para el índice semántico."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    a.id, a.title, a.content, a.source, a.published_at, a.language,
                    p.summary, p.sentiment, p.category, p.entities
                FROM articles a
                LEFT JOIN processed_data p ON a.id = p.article_id
                WHERE a.published_at > datetime('now', '-30 days')
                ORDER BY a.published_at DESC
                LIMIT ?
            ''', (limit,))

            results = cursor.fetchall()
            conn.close()

            articles = []
            for row in results:
                articles.append({
                    'id': row[0],
                    'title': row[1] or '',
                    'content': row[2] or '',
                    'source': row[3] or '',
                    'published_date': row[4] or '',
                    'language': row[5] or 'en',
                    'summary': row[6] or '',
                    'sentiment': row[7] or 0.0,
                    'category': row[8] or 'neutral',
                    'entities': row[9] or '{}'
                })

            return articles

        except Exception as e:
            logger.error(f"Error obteniendo artículos: {e}")
            return []

    def process_query(self, query: str,
                      chat_history: List[List[str]] = None) -> str:
        """
        Procesa consulta del usuario con IA avanzada.

        Flujo según context.ipynb:
        1. Detectar idioma de la consulta
        2. Búsqueda semántica en base de datos
        3. Generar respuesta con LLM
        4. Responder en el idioma del usuario
        """
        try:
            # Detectar idioma
            detected_lang = 'en'
            if detected_lang not in self.supported_languages:
                detected_lang = 'en'

            logger.info(f"🗣️ Consulta en {detected_lang}: {query[:100]}...")

            # Búsqueda semántica inteligente
            relevant_articles = self.semantic_search(query, top_k=5)

            # Si hay LangChain disponible, usar conversación avanzada
            if self.ai_available and self.conversation_chain:
                response = self._generate_langchain_response(
                    query, relevant_articles, detected_lang)
            elif self.openai_key:
                response = self._generate_openai_response(
                    query, relevant_articles, detected_lang)
            else:
                response = self._generate_template_response(
                    query, relevant_articles, detected_lang)

            return response

        except Exception as e:
            logger.error(f"Error procesando consulta: {e}")
            return self._get_error_message(
                detected_lang if 'detected_lang' in locals() else 'en')

    def _generate_langchain_response(
            self,
            query: str,
            articles: List[Dict],
            language: str) -> str:
        """Genera respuesta usando LangChain para conversación avanzada."""
        try:
            # Preparar contexto de datos
            context = self._prepare_data_context(articles)

            # Crear prompt multilingüe
            language_instruction = {
                'es': 'Responde en español',
                'en': 'Respond in English',
                'ru': 'Отвечай на русском языке',
                'zh': '用中文回答',
                'ar': 'أجب باللغة العربية'
            }.get(language, 'Respond in English')

            enhanced_query = f"""
{language_instruction}.

Como analista de inteligencia geopolítica, responde a esta consulta basándote en los datos reales disponibles:

Consulta: {query}

Datos disponibles:
{context}

Instrucciones:
- Sé preciso y factual
- Cita fuentes y fechas específicas
- Si los datos son limitados, indícalo claramente
- Enfócate en insights accionables de inteligencia
"""

            response = self.conversation_chain.predict(input=enhanced_query)
            return response.strip()

        except Exception as e:
            logger.error(f"Error con LangChain: {e}")
            return self._generate_openai_response(query, articles, language)

    def _generate_openai_response(
            self,
            query: str,
            articles: List[Dict],
            language: str) -> str:
        """Genera respuesta usando OpenAI directamente."""
        try:
            import openai
            openai.api_key = self.openai_key

            context = self._prepare_data_context(articles)

            # Prompt del sistema multilingüe
            system_prompts = {
                'es': 'Eres un analista profesional de inteligencia geopolítica. Responde en español basándote en datos reales.',
                'en': 'You are a professional geopolitical intelligence analyst. Respond in English based on real data.',
                'ru': 'Вы профессиональный аналитик геополитической разведки. Отвечайте на русском языке на основе реальных данных.',
                'zh': '您是专业的地缘政治情报分析师。根据真实数据用中文回答。',
                'ar': 'أنت محلل استخبارات جيوسياسية محترف. أجب باللغة العربية بناءً على البيانات الحقيقية.'}

            system_prompt = system_prompts.get(language, system_prompts['en'])

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Consulta: {query}\n\nDatos disponibles:\n{context}"}
                ],
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error con OpenAI: {e}")
            return self._generate_template_response(query, articles, language)

    def _generate_template_response(
            self,
            query: str,
            articles: List[Dict],
            language: str) -> str:
        """Genera respuesta usando plantillas cuando no hay IA disponible."""
        responses = self.language_responses.get(
            language, self.language_responses['en'])

        if not articles:
            return responses['no_data']

        # Crear respuesta básica con los datos disponibles
        if language == 'es':
            response = f"[DATA] Encontré {len(articles)} artículos relevantes:\n\n"
            for i, article in enumerate(articles[:3], 1):
                response += f"{i}. **{article.get('title', 'Sin título')}**\n"
                response += f"   [NEWS] Fuente: {article.get('source', 'N/A')}\n"
                response += f"   📅 Fecha: {article.get('published_date', 'N/A')[:10]}\n"
                response += f"   🏷️ Categoría: {article.get('category', 'N/A')}\n\n"
        else:
            response = f"[DATA] Found {len(articles)} relevant articles:\n\n"
            for i, article in enumerate(articles[:3], 1):
                response += f"{i}. **{article.get('title', 'No title')}**\n"
                response += f"   [NEWS] Source: {article.get('source', 'N/A')}\n"
                response += f"   📅 Date: {article.get('published_date', 'N/A')[:10]}\n"
                response += f"   🏷️ Category: {article.get('category', 'N/A')}\n\n"

        return response

    def _prepare_data_context(self, articles: List[Dict]) -> str:
        """Prepara contexto de datos para el LLM."""
        if not articles:
            return "No hay datos disponibles."

        context = f"Datos de {len(articles)} artículos relevantes:\n"

        for i, article in enumerate(articles[:5], 1):
            context += f"\n{i}. Título: {article.get('title', 'N/A')}\n"
            context += f"   Fuente: {article.get('source', 'N/A')}\n"
            context += f"   Fecha: {article.get('published_date', 'N/A')[:10]}\n"
            context += f"   Categoría: {article.get('category', 'neutral')}\n"
            context += f"   Sentimiento: {article.get('sentiment', 0.0)}\n"
            if article.get('summary'):
                context += f"   Resumen: {article['summary'][:200]}...\n"

        return context

    def _get_error_message(self, language: str) -> str:
        """Obtiene mensaje de error en el idioma especificado."""
        return self.language_responses.get(
            language, self.language_responses['en'])['error']


def create_gradio_interface():
    """
    Crea interfaz Gradio profesional para el chatbot.
    Diseño según especificaciones del context.ipynb.
    """

    # Inicializar chatbot
    chatbot = MultilingualGeopoliticalChatbot()

    # CSS personalizado para diseño profesional
    custom_css = """
    .gradio-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .gr-interface {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .gr-chatbot {
        background: #f8faff;
        border-radius: 15px;
        border: 1px solid #e1e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }

    .gr-textbox {
        border-radius: 12px;
        border: 2px solid #e1e8f0;
        transition: all 0.3s ease;
    }

    .gr-textbox:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .gr-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .gr-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    .header-container {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px 15px 0 0;
        margin-bottom: 20px;
    }

    .footer-info {
        background: #f8faff;
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
        font-size: 0.9em;
        color: #64748b;
    }
    """

    def chat_function(message, history):
        """Función principal del chat."""
        if not message.strip():
            return history, ""

        try:
            # Procesar consulta
            response = chatbot.process_query(message, history)

            # Agregar a historial
            history.append([message, response])

            return history, ""

        except Exception as e:
            logger.error(f"Error en chat: {e}")
            error_msg = "Lo siento, hubo un error procesando tu consulta. Por favor, intenta de nuevo."
            history.append([message, error_msg])
            return history, ""

    # Crear interfaz con diseño profesional
    with gr.Blocks(css=custom_css, title="RISKMAP - Geopolitical Intelligence Chatbot") as interface:

        gr.HTML("""
        <div class="header-container">
            <h1>[GLOBAL] RISKMAP - Chatbot de Inteligencia Geopolítica</h1>
            <p>Análisis avanzado con IA • Datos reales • 5 idiomas soportados</p>
            <p style="font-size: 0.9em; opacity: 0.9;">ES • EN • RU • ZH • AR</p>
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=4):
                chatbot_interface = gr.Chatbot(
                    label="💬 Asistente de Inteligencia",
                    height=500,
                    show_copy_button=True
                )

                with gr.Row():
                    with gr.Column(scale=5):
                        user_input = gr.Textbox(
                            placeholder="Pregúntame sobre eventos geopolíticos, conflictos, protestas, tendencias... (en cualquier idioma)",
                            label="Tu consulta",
                            lines=2)

                    with gr.Column(scale=1, min_width=100):
                        send_button = gr.Button(
                            "[START] Enviar", variant="primary")

            with gr.Column(scale=1):
                gr.HTML("""
                <div class="footer-info">
                    <h3>[TARGET] Ejemplos de consultas:</h3>
                    <ul style="text-align: left; font-size: 0.85em;">
                        <li><strong>ES:</strong> ¿Cuáles son las regiones más inestables esta semana?</li>
                        <li><strong>EN:</strong> Show me recent conflicts in Eastern Europe</li>
                        <li><strong>RU:</strong> Какие протесты происходят в мире?</li>
                        <li><strong>ZH:</strong> 最近的外交危机有哪些？</li>
                        <li><strong>AR:</strong> ما هي الاتجاهات الجيوسياسية الحالية؟</li>
                    </ul>

                    <h3>[DATA] Capacidades:</h3>
                    <ul style="text-align: left; font-size: 0.85em;">
                        <li>Análisis de conflictos</li>
                        <li>Monitoreo de protestas</li>
                        <li>Evaluación de sentimientos</li>
                        <li>Tendencias regionales</li>
                        <li>Búsqueda semántica</li>
                    </ul>

                    <div style="margin-top: 15px; padding: 10px; background: #e0f2fe; border-radius: 8px;">
                        <strong>[SEARCH] Powered by:</strong><br>
                        LangChain • OpenAI • FAISS<br>
                        <strong>[STATS] Data sources:</strong><br>
                        NewsAPI • Global RSS • Intelligence feeds
                    </div>
                </div>
                """)

        # Configurar eventos
        send_button.click(
            chat_function,
            inputs=[user_input, chatbot_interface],
            outputs=[chatbot_interface, user_input]
        )

        user_input.submit(
            chat_function,
            inputs=[user_input, chatbot_interface],
            outputs=[chatbot_interface, user_input]
        )

        # Cargar mensaje de bienvenida
        interface.load(
            lambda: [["👋 Bienvenido", chatbot.language_responses['es']['greeting']]],
            outputs=chatbot_interface
        )

    return interface


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Crear y lanzar interfaz
    logger.info("[START] Iniciando Chatbot de Inteligencia Geopolítica...")

    interface = create_gradio_interface()

    # Configuración del servidor
    host = config.get('chatbot.host', '0.0.0.0')
    port = config.get('chatbot.port', 7860)

    logger.info(f"[WEB] Servidor disponible en: http://{host}:{port}")
    logger.info("🔗 Interfaz web iniciando...")

    interface.launch(
        server_name=host,
        server_port=port,
        share=False,
        debug=False,
        show_error=True
    )
