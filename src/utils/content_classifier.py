#!/usr/bin/env python3
"""
Content Classifier for Geopolitical Intelligence System
"""

import re
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

class ContentClassifier:
    """Classifies news content into geopolitical categories."""
    
    def __init__(self):
        # Category classification patterns
        self.categories = {
            'military_conflict': {
                'keywords': [
                    'war', 'guerra', 'guerre', 'krieg', 'война',
                    'military', 'militar', 'militaire', 'militär', 'военный',
                    'army', 'ejército', 'armée', 'armee', 'армия',
                    'defense', 'defensa', 'défense', 'verteidigung', 'оборона',
                    'attack', 'ataque', 'attaque', 'angriff', 'атака',
                    'invasion', 'invasión', 'invasion', 'invasion', 'вторжение',
                    'combat', 'combate', 'combat', 'kampf', 'бой',
                    'battle', 'batalla', 'bataille', 'schlacht', 'битва',
                    'weapons', 'armas', 'armes', 'waffen', 'оружие',
                    'missile', 'misil', 'missile', 'rakete', 'ракета',
                    'bombing', 'bombardeo', 'bombardement', 'bombardierung',
                    'airstrike', 'ataque aéreo', 'frappe aérienne', 'luftangriff'
                ],
                'weight': 1.0
            },
            'diplomatic_relations': {
                'keywords': [
                    'diplomacy', 'diplomacia', 'diplomatie', 'diplomatie', 'дипломатия',
                    'ambassador', 'embajador', 'ambassadeur', 'botschafter', 'посол',
                    'embassy', 'embajada', 'ambassade', 'botschaft', 'посольство',
                    'treaty', 'tratado', 'traité', 'vertrag', 'договор',
                    'agreement', 'acuerdo', 'accord', 'vereinbarung', 'соглашение',
                    'negotiation', 'negociación', 'négociation', 'verhandlung',
                    'summit', 'cumbre', 'sommet', 'gipfel', 'саммит',
                    'alliance', 'alianza', 'alliance', 'allianz', 'альянс',
                    'partnership', 'asociación', 'partenariat', 'partnerschaft',
                    'cooperation', 'cooperación', 'coopération', 'zusammenarbeit',
                    'bilateral', 'bilateral', 'bilatéral', 'bilateral', 'двусторонний',
                    'multilateral', 'multilateral', 'multilatéral', 'multilateral'
                ],
                'weight': 0.8
            },
            'economic_security': {
                'keywords': [
                    'sanctions', 'sanciones', 'sanctions', 'sanktionen', 'санкции',
                    'embargo', 'embargo', 'embargo', 'embargo', 'эмбарго',
                    'trade war', 'guerra comercial', 'guerre commerciale',
                    'tariff', 'arancel', 'tarif', 'zoll', 'тариф',
                    'economic', 'económico', 'économique', 'wirtschaftlich',
                    'finance', 'finanzas', 'finance', 'finanzen', 'финансы',
                    'currency', 'moneda', 'devise', 'währung', 'валюта',
                    'inflation', 'inflación', 'inflation', 'inflation', 'инфляция',
                    'recession', 'recesión', 'récession', 'rezession', 'рецессия',
                    'gdp', 'pib', 'pib', 'bip', 'ввп',
                    'investment', 'inversión', 'investissement', 'investition',
                    'market', 'mercado', 'marché', 'markt', 'рынок'
                ],
                'weight': 0.7
            },
            'energy_resources': {
                'keywords': [
                    'oil', 'petróleo', 'pétrole', 'öl', '��ефть',
                    'gas', 'gas', 'gaz', 'gas', 'газ',
                    'energy', 'energía', 'énergie', 'energie', 'энергия',
                    'pipeline', 'oleoducto', 'pipeline', 'pipeline', 'трубопровод',
                    'nuclear', 'nuclear', 'nucléaire', 'nuklear', 'ядерный',
                    'renewable', 'renovable', 'renouvelable', 'erneuerbar',
                    'coal', 'carbón', 'charbon', 'kohle', 'уголь',
                    'electricity', 'electricidad', 'électricité', 'elektrizität',
                    'power grid', 'red eléctrica', 'réseau électrique',
                    'mining', 'minería', 'exploitation minière', 'bergbau',
                    'resources', 'recursos', 'ressources', 'ressourcen', 'ресурсы',
                    'lithium', 'litio', 'lithium', 'lithium', 'литий',
                    'rare earth', 'tierras raras', 'terres rares', 'seltene erden'
                ],
                'weight': 0.8
            },
            'climate_environment': {
                'keywords': [
                    'climate', 'clima', 'climat', 'klima', 'климат',
                    'environment', 'medio ambiente', 'environnement', 'umwelt',
                    'global warming', 'calentamiento global', 'réchauffement',
                    'carbon', 'carbono', 'carbone', 'kohlenstoff', 'углерод',
                    'emissions', 'emisiones', 'émissions', 'emissionen',
                    'pollution', 'contaminación', 'pollution', 'verschmutzung',
                    'deforestation', 'deforestación', 'déforestation',
                    'biodiversity', 'biodiversidad', 'biodiversité', 'biodiversität',
                    'sustainability', 'sostenibilidad', 'durabilité', 'nachhaltigkeit',
                    'green', 'verde', 'vert', 'grün', 'зеленый',
                    'renewable', 'renovable', 'renouvelable', 'erneuerbar',
                    'paris agreement', 'acuerdo de parís', 'accord de paris'
                ],
                'weight': 0.6
            },
            'cyber_security': {
                'keywords': [
                    'cyber', 'cibernético', 'cyber', 'cyber', 'кибер',
                    'hacking', 'piratería', 'piratage', 'hacking', 'взлом',
                    'malware', 'malware', 'malware', 'malware', 'вредоносное по',
                    'ransomware', 'ransomware', 'rançongiciel', 'ransomware',
                    'data breach', 'violación de datos', 'violation de données',
                    'surveillance', 'vigilancia', 'surveillance', 'überwachung',
                    'espionage', 'espionaje', 'espionnage', 'spionage', 'шпионаж',
                    'intelligence', 'inteligencia', 'renseignement', 'geheimdienst',
                    'digital', 'digital', 'numérique', 'digital', 'цифровой',
                    'internet', 'internet', 'internet', 'internet', 'интернет',
                    'technology', 'tecnología', 'technologie', 'technologie'
                ],
                'weight': 0.7
            },
            'terrorism_security': {
                'keywords': [
                    'terrorism', 'terrorismo', 'terrorisme', 'terrorismus', 'терроризм',
                    'terrorist', 'terrorista', 'terroriste', 'terrorist', 'террорист',
                    'extremism', 'extremismo', 'extrémisme', 'extremismus',
                    'radical', 'radical', 'radical', 'radikal', 'радикальный',
                    'security', 'seguridad', 'sécurité', 'sicherheit', 'безопасность',
                    'threat', 'amenaza', 'menace', 'bedrohung', 'угроза',
                    'violence', 'violencia', 'violence', 'gewalt', 'насил��е',
                    'assassination', 'asesinato', 'assassinat', 'attentat',
                    'bomb', 'bomba', 'bombe', 'bombe', 'бомба',
                    'explosion', 'explosión', 'explosion', 'explosion', 'взрыв'
                ],
                'weight': 0.9
            },
            'migration_refugees': {
                'keywords': [
                    'migration', 'migración', 'migration', 'migration', 'миграция',
                    'refugee', 'refugiado', 'réfugié', 'flüchtling', 'беженец',
                    'asylum', 'asilo', 'asile', 'asyl', 'убежище',
                    'border', 'frontera', 'frontière', 'grenze', 'граница',
                    'immigration', 'inmigración', 'immigration', 'einwanderung',
                    'displacement', 'desplazamiento', 'déplacement', 'vertreibung',
                    'humanitarian', 'humanitario', 'humanitaire', 'humanitär',
                    'crisis', 'crisis', 'crise', 'krise', 'кризис',
                    'camp', 'campamento', 'camp', 'lager', 'лагерь'
                ],
                'weight': 0.6
            },
            'sports_entertainment': {
                'keywords': [
                    # Sports - English
                    'sports', 'sport', 'football', 'soccer', 'basketball', 'baseball',
                    'tennis', 'golf', 'hockey', 'volleyball', 'swimming', 'athletics',
                    'gymnastics', 'boxing', 'wrestling', 'mma', 'ufc', 'olympics',
                    'world cup', 'championship', 'tournament', 'league', 'season',
                    'team', 'player', 'coach', 'stadium', 'match', 'game',
                    'victory', 'defeat', 'champion', 'winner', 'score',
                    
                    # Sports - Spanish
                    'deporte', 'deportes', 'fútbol', 'baloncesto', 'tenis', 'golf',
                    'hockey', 'voleibol', 'natación', 'atletismo', 'gimnasia',
                    'boxeo', 'lucha', 'olímpicos', 'mundial', 'campeonato',
                    'torneo', 'liga', 'temporada', 'equipo', 'jugador',
                    'entrenador', 'estadio', 'partido', 'juego', 'victoria',
                    'derrota', 'campeón', 'ganador', 'marcador',
                    
                    # Sports - French
                    'sport', 'football', 'basket', 'tennis', 'golf', 'hockey',
                    'volley', 'natation', 'athlétisme', 'gymnastique', 'boxe',
                    'lutte', 'olympiques', 'mondial', 'championnat', 'tournoi',
                    'ligue', 'saison', 'équipe', 'joueur', 'entraîneur',
                    'stade', 'match', 'jeu', 'victoire', 'défaite', 'champion',
                    
                    # Sports - German
                    'sport', 'fußball', 'basketball', 'tennis', 'golf', 'hockey',
                    'volleyball', 'schwimmen', 'leichtathletik', 'turnen', 'boxen',
                    'ringen', 'olympische', 'weltmeisterschaft', 'turnier', 'liga',
                    'saison', 'mannschaft', 'spieler', 'trainer', 'stadion',
                    'spiel', 'sieg', 'niederlage', 'meister',
                    
                    # Entertainment
                    'entertainment', 'celebrity', 'movie', 'film', 'music',
                    'fashion', 'beauty', 'cooking', 'recipe', 'lifestyle',
                    'entretenimiento', 'celebridad', 'película', 'música',
                    'moda', 'belleza', 'cocina', 'receta', 'estilo de vida',
                    'divertissement', 'célébrité', 'musique', 'mode',
                    'beauté', 'cuisine', 'recette', 'style de vie',
                    'unterhaltung', 'prominente', 'musik', 'mode',
                    'schönheit', 'kochen', 'rezept', 'lebensstil'
                ],
                'weight': 1.0  # High weight to ensure sports content is identified
            }
        }
    
    def classify(self, text: str) -> str:
        """Classify text into the most relevant geopolitical category."""
        try:
            text_lower = text.lower()
            
            # First check if it's sports/entertainment content
            if self._is_sports_entertainment(text_lower):
                return 'sports_entertainment'
            
            # Calculate scores for each geopolitical category
            category_scores = {}
            
            for category, data in self.categories.items():
                # Skip sports_entertainment category in geopolitical classification
                if category == 'sports_entertainment':
                    continue
                    
                keywords = data['keywords']
                weight = data['weight']
                
                matches = 0
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        matches += 1
                
                # Calculate weighted score
                score = (matches / len(keywords)) * weight
                category_scores[category] = score
            
            # Find category with highest score
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                best_score = category_scores[best_category]
                
                # Only return category if score is above threshold
                if best_score > 0.1:
                    return best_category
            
            # Default category
            return 'general_news'
            
        except Exception as e:
            logger.error(f"Content classification error: {e}")
            return 'general_news'
    
    def _is_sports_entertainment(self, text: str) -> bool:
        """Check if text is primarily about sports or entertainment."""
        sports_keywords = self.categories['sports_entertainment']['keywords']
        
        # Count sports/entertainment keyword matches
        matches = sum(1 for keyword in sports_keywords if keyword.lower() in text)
        
        # Strong sports indicators that should immediately classify as sports
        strong_sports_indicators = [
            'cricket', 'críquet', 'pcb', 'bcci', 'icc',  # Cricket specific
            'fifa', 'uefa', 'nba', 'nfl', 'mlb', 'nhl',  # Major sports organizations
            'olympics', 'olímpicos', 'world cup', 'mundial',  # Major events
            'championship', 'campeonato', 'tournament', 'torneo',  # Competitions
            'player', 'jugador', 'coach', 'entrenador',  # Sports roles
            'stadium', 'estadio', 'match', 'partido',  # Sports venues/events
            'team', 'equipo', 'league', 'liga',  # Sports organizations
            'goal', 'gol', 'score', 'marcador', 'victory', 'victoria'  # Sports outcomes
        ]
        
        # Check for strong sports indicators
        text_lower = text.lower()
        for indicator in strong_sports_indicators:
            if indicator.lower() in text_lower:
                return True
        
        # If we have multiple sports keywords, it's likely sports content
        return matches >= 2
    
    def get_category_scores(self, text: str) -> Dict[str, float]:
        """Get scores for all categories."""
        try:
            text_lower = text.lower()
            category_scores = {}
            
            for category, data in self.categories.items():
                keywords = data['keywords']
                weight = data['weight']
                
                matches = 0
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        matches += 1
                
                score = (matches / len(keywords)) * weight
                category_scores[category] = round(score, 3)
            
            return category_scores
            
        except Exception as e:
            logger.error(f"Category scoring error: {e}")
            return {}
    
    def is_geopolitically_relevant(self, text: str, threshold: float = 0.05) -> bool:
        """Check if text is geopolitically relevant."""
        scores = self.get_category_scores(text)
        max_score = max(scores.values()) if scores else 0
        return max_score > threshold

def main():
    """Test content classifier."""
    classifier = ContentClassifier()
    
    # Test cases
    test_texts = [
        "Military forces advance in Eastern Europe amid rising tensions",
        "Diplomatic summit scheduled to discuss trade agreements",
        "Oil prices surge following pipeline disruption",
        "Climate change summit addresses carbon emissions",
        "Cyber attack targets government infrastructure",
        "Terrorist threat level raised in major cities",
        "Refugee crisis worsens at border crossing",
        "Local football team wins championship match"
    ]
    
    for text in test_texts:
        category = classifier.classify(text)
        scores = classifier.get_category_scores(text)
        relevant = classifier.is_geopolitically_relevant(text)
        
        print(f"\\nText: {text}")
        print(f"Category: {category}")
        print(f"Relevant: {relevant}")
        print(f"Top scores: {dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3])}")

if __name__ == "__main__":
    main()