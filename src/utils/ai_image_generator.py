"""
AI Image Generator for Geopolitical Analysis
Uses AI to analyze article content and generate appropriate image prompts, then creates images using free AI services.
"""

import os
import requests
import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

class AIImageGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.images_dir = "data/generated_images"
        
        # Create images directory
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Pollinations AI (Free image generation)
        self.pollinations_base_url = "https://image.pollinations.ai/prompt"
        
    def analyze_article_for_image_prompt(self, article_content: str, article_title: str) -> str:
        """
        Use AI to analyze article content and generate an appropriate image prompt.
        """
        try:
            # Try to import AI models, fallback if not available
            try:
                from src.analytics.ai_models import AIModels
                ai_models = AIModels(self.config)
                
                # Create prompt for AI to generate image description
                analysis_prompt = f"""
                Analiza el siguiente artículo geopolítico y genera un prompt muy detallado para crear una imagen que represente visualmente el tema principal del artículo.

                Título: {article_title}
                
                Contenido del artículo: {article_content[:1500]}...

                Instrucciones para el prompt de imagen:
                1. Debe ser descriptivo y visual
                2. Incluir elementos geopolíticos relevantes (mapas, banderas, edificios gubernamentales, etc.)
                3. Transmitir el tono y gravedad de la situación
                4. Ser profesional y periodístico
                5. Incluir colores y composición apropiados
                6. Máximo 200 palabras
                7. En inglés para mejor compatibilidad con generadores de imagen

                Genera SOLO el prompt para la imagen, sin explicaciones adicionales:
                """
                
                # Get image prompt from AI
                image_prompt = ai_models.generate_response(analysis_prompt)
                
                # Clean and enhance the prompt
                if image_prompt:
                    # Remove quotes and clean
                    image_prompt = image_prompt.strip().strip('"').strip("'")
                    
                    # Add style keywords for better results
                    enhanced_prompt = f"{image_prompt}, professional news photography, high quality, detailed, photorealistic, journalism style, editorial photography"
                    
                    self.logger.info(f"Generated image prompt: {enhanced_prompt[:100]}...")
                    return enhanced_prompt
                    
            except ImportError:
                self.logger.warning("AI models not available, using fallback prompt generation")
                
            # Fallback prompt
            return self.generate_fallback_prompt(article_title, article_content)
                
        except Exception as e:
            self.logger.error(f"Error generating AI image prompt: {str(e)}")
            return self.generate_fallback_prompt(article_title, article_content)
    
    def generate_fallback_prompt(self, title: str, content: str) -> str:
        """Generate a simple fallback prompt based on keywords."""
        
        # Keywords mapping to visual elements
        keyword_mapping = {
            'war': 'military conflict, news photography, serious tone',
            'conflict': 'tension, diplomatic meeting, news background',
            'economy': 'financial charts, business meeting, professional setting',
            'trade': 'shipping containers, global commerce, world map',
            'diplomatic': 'government buildings, handshake, official meeting',
            'crisis': 'emergency, serious news, breaking news style',
            'sanctions': 'government officials, serious discussion, world map',
            'election': 'voting, democracy, political rally, flags',
            'climate': 'environmental, global map, natural elements',
            'technology': 'modern city, digital elements, innovation'
        }
        
        # Extract relevant keywords
        text_lower = (title + " " + content).lower()
        found_elements = []
        
        for keyword, visual in keyword_mapping.items():
            if keyword in text_lower:
                found_elements.append(visual)
        
        if found_elements:
            prompt = f"Professional news photography showing {', '.join(found_elements[:3])}, high quality, editorial style, photojournalism"
        else:
            prompt = "Professional geopolitical news photography, world map background, serious tone, editorial style, high quality"
        
        return prompt
    
    def generate_image_from_prompt(self, prompt: str, filename: str) -> Optional[str]:
        """
        Generate image using free AI service (Pollinations AI).
        """
        try:
            # Clean filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
            image_path = os.path.join(self.images_dir, f"{safe_filename}_{int(time.time())}.png")
            
            # Prepare URL for Pollinations AI
            # Format: https://image.pollinations.ai/prompt/{prompt}?width=800&height=600&nologo=true
            encoded_prompt = requests.utils.quote(prompt)
            pollinations_url = f"{self.pollinations_base_url}/{encoded_prompt}?width=800&height=600&nologo=true&enhance=true"
            
            self.logger.info(f"Generating image with Pollinations AI...")
            
            # Request image
            response = requests.get(pollinations_url, timeout=30)
            
            if response.status_code == 200:
                # Save image
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                self.logger.info(f"✅ Image generated successfully: {image_path}")
                return image_path
            else:
                self.logger.error(f"❌ Failed to generate image. Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error generating image: {str(e)}")
            return None
    
    def generate_image_for_analysis(self, analysis_content: str, analysis_title: str = "Geopolitical Analysis") -> Optional[str]:
        """
        Complete pipeline: analyze content with AI, generate prompt, create image.
        """
        try:
            self.logger.info("Starting AI image generation pipeline...")
            
            # Step 1: Generate image prompt using AI
            image_prompt = self.analyze_article_for_image_prompt(analysis_content, analysis_title)
            
            # Step 2: Generate image from prompt
            filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            image_path = self.generate_image_from_prompt(image_prompt, filename)
            
            if image_path:
                # Return relative path for web serving
                relative_path = image_path.replace('\\', '/').replace('data/', '/static/data/')
                self.logger.info(f"✅ Image generation completed: {relative_path}")
                return relative_path
            else:
                self.logger.warning("⚠️ Image generation failed, using default")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error in image generation pipeline: {str(e)}")
            return None
    
    def cleanup_old_images(self, max_age_hours: int = 24):
        """Clean up old generated images to save disk space."""
        try:
            current_time = time.time()
            deleted_count = 0
            
            for filename in os.listdir(self.images_dir):
                file_path = os.path.join(self.images_dir, filename)
                if os.path.isfile(file_path):
                    file_age_hours = (current_time - os.path.getmtime(file_path)) / 3600
                    if file_age_hours > max_age_hours:
                        os.remove(file_path)
                        deleted_count += 1
            
            if deleted_count > 0:
                self.logger.info(f"🧹 Cleaned up {deleted_count} old images")
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up images: {str(e)}")
