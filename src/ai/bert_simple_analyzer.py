"""
Analizador de riesgo BERT simplificado sin pipeline
"""
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import sqlite3

class SimpleBertRiskAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_name = 'nlptown/bert-base-multilingual-uncased-sentiment'
        self.tokenizer = None
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Cache de palabras clave para análisis rápido
        self.high_risk_keywords = [
            'guerra', 'conflict', 'ataque', 'attack', 'terrorismo', 'terrorism',
            'crisis', 'violencia', 'violence', 'bomba', 'bomb', 'militar', 'military',
            'invasion', 'invasión', 'amenaza', 'threat', 'sanción', 'sanction',
            'muerte', 'death', 'muerto', 'killed', 'disparos', 'shooting',
            'explosion', 'explosión', 'evacuación', 'evacuation', 'refugiados', 'refugees'
        ]
        
        self.medium_risk_keywords = [
            'tension', 'tensión', 'politica', 'politics', 'elecciones', 'elections',
            'protesta', 'protest', 'manifestación', 'demonstration', 'económico', 'economic',
            'gobierno', 'government', 'diplomacia', 'diplomacy', 'negociaciones', 'negotiations'
        ]
        
        try:
            self._load_model()
        except Exception as e:
            self.logger.error(f"Error loading BERT model: {e}")
            self.tokenizer = None
            self.model = None
    
    def _load_model(self):
        """Cargar modelo BERT"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self.logger.info(f"BERT model loaded successfully on {self.device}")
        except Exception as e:
            self.logger.error(f"Failed to load BERT model: {e}")
            raise
    
    def _keyword_analysis(self, text):
        """Análisis basado en palabras clave como fallback"""
        text_lower = text.lower()
        
        high_risk_count = sum(1 for keyword in self.high_risk_keywords if keyword in text_lower)
        medium_risk_count = sum(1 for keyword in self.medium_risk_keywords if keyword in text_lower)
        
        # Determinar nivel de riesgo basado en conteo de palabras clave
        if high_risk_count >= 2:
            return 'HIGH', 0.8 + min(high_risk_count * 0.1, 0.2)
        elif high_risk_count >= 1:
            return 'HIGH', 0.7 + high_risk_count * 0.1
        elif medium_risk_count >= 2:
            return 'MEDIUM', 0.6 + min(medium_risk_count * 0.05, 0.15)
        elif medium_risk_count >= 1:
            return 'MEDIUM', 0.5 + medium_risk_count * 0.1
        else:
            return 'LOW', 0.3
    
    def _bert_analysis(self, text):
        """Análisis usando BERT si está disponible"""
        if not self.model or not self.tokenizer:
            return None
        
        try:
            # Tokenizar texto
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=512
            ).to(self.device)
            
            # Inferencia
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
            # Convertir a probabilidades de riesgo
            # Asumiendo que el modelo de sentiment tiene 5 clases (muy negativo a muy positivo)
            probs = predictions.cpu().numpy()[0]
            
            # Mapear sentiment a riesgo (más negativo = más riesgo)
            negative_score = probs[0] + probs[1]  # Very negative + negative
            neutral_score = probs[2]  # Neutral
            positive_score = probs[3] + probs[4]  # Positive + very positive
            
            if negative_score > 0.6:
                risk_level = 'HIGH'
                risk_score = 0.7 + (negative_score - 0.6) * 0.75
            elif negative_score > 0.4:
                risk_level = 'MEDIUM'
                risk_score = 0.5 + (negative_score - 0.4) * 1.0
            else:
                risk_level = 'LOW'
                risk_score = 0.2 + negative_score * 0.75
                
            return risk_level, min(risk_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error in BERT analysis: {e}")
            return None
    
    def analyze_risk(self, title, content, summary=None):
        """
        Analizar riesgo de un artículo
        
        Args:
            title (str): Título del artículo
            content (str): Contenido del artículo
            summary (str, optional): Resumen del artículo
            
        Returns:
            tuple: (risk_level, risk_score)
        """
        try:
            # Combinar texto para análisis
            full_text = f"{title}. {content}"
            if summary:
                full_text += f" {summary}"
            
            # Intentar análisis BERT primero
            bert_result = self._bert_analysis(full_text)
            if bert_result:
                risk_level, risk_score = bert_result
                self.logger.info(f"BERT analysis: {risk_level} ({risk_score:.2f})")
            else:
                # Fallback a análisis por palabras clave
                risk_level, risk_score = self._keyword_analysis(full_text)
                self.logger.info(f"Keyword analysis (fallback): {risk_level} ({risk_score:.2f})")
            
            # Ajustar score basado en palabras clave adicionales
            keyword_level, keyword_score = self._keyword_analysis(full_text)
            if keyword_level == 'HIGH' and risk_level != 'HIGH':
                risk_level = 'HIGH'
                risk_score = max(risk_score, keyword_score)
            
            return risk_level, risk_score
            
        except Exception as e:
            self.logger.error(f"Error in risk analysis: {e}")
            return 'MEDIUM', 0.5

def analyze_article_risk(title, content, summary=None):
    """Función de conveniencia para análisis de riesgo"""
    analyzer = SimpleBertRiskAnalyzer()
    return analyzer.analyze_risk(title, content, summary)

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    analyzer = SimpleBertRiskAnalyzer()
    
    # Test articles
    test_articles = [
        ("Conflicto armado en región", "Se reportan ataques militares y evacuación de civiles"),
        ("Nuevas elecciones programadas", "El gobierno anuncia elecciones para el próximo año"),
        ("Festival de música local", "Gran éxito del evento cultural en la ciudad")
    ]
    
    for title, content in test_articles:
        risk_level, risk_score = analyzer.analyze_risk(title, content)
        print(f"'{title}' -> {risk_level} ({risk_score:.2f})")
