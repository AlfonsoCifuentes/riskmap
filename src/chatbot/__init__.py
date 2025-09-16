"""
Chatbot package for interactive querying of geopolitical data.
"""

from .chatbot_app import MultilingualGeopoliticalChatbot as GeopoliticalChatbot, create_gradio_interface as create_chatbot_interface

__all__ = ['GeopoliticalChatbot', 'create_chatbot_interface']
