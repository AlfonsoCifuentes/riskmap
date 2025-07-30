#!/usr/bin/env python3
"""
Risk Analyzer for Geopolitical Intelligence System
"""

import re
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    """Analyzes geopolitical risk level of news content."""
    
    def __init__(self):
        # Risk indicators with weights
        self.risk_indicators = {
            'high': {
                'keywords': [
                    'war', 'guerra', 'guerre', 'krieg', 'война',
                    'conflict', 'conflicto', 'conflit', 'konflikt', 'конфликт',
                    'attack', 'ataque', 'attaque', 'angriff', 'атака',
                    'invasion', 'invasión', 'invasion', 'invasion', 'вторжение',
                    'military action', 'acción militar', 'action militaire',
                    'nuclear', 'nuclear', 'nucléaire', 'nuklear', 'ядерный',
                    'terrorism', 'terrorismo', 'terrorisme', 'terrorismus', 'терроризм',
                    'coup', 'golpe', 'coup', 'putsch', 'переворот',
                    'revolution', 'revolución', 'révolution', 'revolution', 'революция',
                    'crisis', 'crisis', 'crise', 'krise', 'кризис',
                    'emergency', 'emergencia', 'urgence', 'notfall', 'чрезвычайная ситуация',
                    'sanctions', 'sanciones', 'sanctions', 'sanktionen', 'санкции',
                    'embargo', 'embargo', 'embargo', 'embargo', 'эмбарго',
                    'cyber attack', 'ciberataque', 'cyberattaque', 'cyberangriff',
                    'assassination', 'asesinato', 'assassinat', 'attentat',
                    'genocide', 'genocidio', 'génocide', 'völkermord'
                ],
                'weight': 1.0
            },
            'medium': {
                'keywords': [
                    'tension', 'tensión', 'tension', 'spannung', 'напряжение',
                    'dispute', 'disputa', 'dispute', 'streit', 'спор',
                    'protest', 'protesta', 'manifestation', 'protest', 'протест',
                    'demonstration', 'manifestación', 'démonstration', 'demonstration',
                    'diplomatic', 'diplomático', 'diplomatique', 'diplomatisch',
                    'negotiation', 'negociación', 'négociation', 'verhandlung',
                    'alliance', 'alianza', 'alliance', 'allianz', 'альянс',
                    'treaty', 'tratado', 'traité', 'vertrag', 'договор',
                    'trade war', 'guerra comercial', 'guerre commerciale',
                    'economic pressure', 'presión económica', 'pression économique',
                    'border', 'frontera', 'frontière', 'grenze', 'граница',
                    'migration', 'migración', 'migration', 'migration', 'миграция',
                    'refugee', 'refugiado', 'réfugié', 'flüchtling', 'беженец',
                    'election', 'elección', 'élection', 'wahl', 'выборы',
                    'political', 'político', 'politique', 'politisch', 'политический',
                    'government', 'gobierno', 'gouvernement', 'regierung', 'правительство',
                    'minister', 'ministro', 'ministre', 'minister', 'министр',
                    'parliament', 'parlamento', 'parlement', 'parlament', 'парламент'
                ],
                'weight': 0.6
            },
            'low': {
                'keywords': [
                    'cooperation', 'cooperación', 'coopération', 'zusammenarbeit',
                    'agreement', 'acuerdo', 'accord', 'vereinbarung', 'соглашение',
                    'partnership', 'asociación', 'partenariat', 'partnerschaft',
                    'dialogue', 'diálogo', 'dialogue', 'dialog', 'диалог',
                    'summit', 'cumbre', 'sommet', 'gipfel', 'саммит',
                    'conference', 'conferencia', 'conférence', 'konferenz',
                    'meeting', 'reunión', 'réunion', 'treffen', 'встреча',
                    'visit', 'visita', 'visite', 'besuch', 'визит',
                    'trade', 'comercio', 'commerce', 'handel', 'торговля',
                    'investment', 'inversión', 'investissement', 'investition',
                    'development', 'desarrollo', 'développement', 'entwicklung',
                    'aid', 'ayuda', 'aide', 'hilfe', 'помощь',
                    'humanitarian', 'humanitario', 'humanitaire', 'humanitär'
                ],
                'weight': 0.3
            }
        }
        
        # Regional risk modifiers
        self.regional_risk = {
            'Ukraine': 0.3,
            'Russia': 0.2,
            'Middle East': 0.25,
            'Israel': 0.2,
            'Iran': 0.2,
            'Syria': 0.25,
            'Iraq': 0.2,
            'Afghanistan': 0.2,
            'North Korea': 0.25,
            'China': 0.15,
            'Taiwan': 0.2,
            'Kashmir': 0.2,
            'Balkans': 0.15,
            'Sahel': 0.15,
            'Horn of Africa': 0.15
        }
    
    def analyze_risk(self, text: str) -> Dict[str, any]:
        """Analyze risk level of given text."""
        try:
            text_lower = text.lower()
            
            # Calculate base risk score
            risk_score = 0.0
            matched_indicators = []
            
            for risk_level, data in self.risk_indicators.items():
                keywords = data['keywords']
                weight = data['weight']
                
                matches = 0
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        matches += 1
                        matched_indicators.append((keyword, risk_level))
                
                # Add weighted score
                risk_score += (matches / len(keywords)) * weight
            
            # Apply regional modifiers
            regional_modifier = 0.0
            detected_region = None
            
            for region, modifier in self.regional_risk.items():
                if region.lower() in text_lower:
                    regional_modifier = max(regional_modifier, modifier)
                    detected_region = region
            
            # Combine base score with regional modifier
            final_score = min(1.0, risk_score + regional_modifier)
            
            # Determine risk level
            if final_score >= 0.7:
                level = 'high'
            elif final_score >= 0.4:
                level = 'medium'
            else:
                level = 'low'
            
            return {
                'level': level,
                'score': round(final_score, 3),
                'indicators': matched_indicators[:5],  # Top 5 indicators
                'region': detected_region,
                'regional_modifier': regional_modifier
            }
            
        except Exception as e:
            logger.error(f"Risk analysis error: {e}")
            return {
                'level': 'low',
                'score': 0.0,
                'indicators': [],
                'region': None,
                'regional_modifier': 0.0
            }
    
    def get_risk_explanation(self, analysis: Dict) -> str:
        """Get human-readable explanation of risk analysis."""
        level = analysis['level']
        score = analysis['score']
        indicators = analysis['indicators']
        region = analysis['region']
        
        explanation = f"Risk Level: {level.upper()} (Score: {score})"
        
        if indicators:
            explanation += f"\\nKey indicators: {', '.join([ind[0] for ind in indicators])}"
        
        if region:
            explanation += f"\\nHigh-risk region detected: {region}"
        
        return explanation

def main():
    """Test risk analyzer."""
    analyzer = RiskAnalyzer()
    
    # Test cases
    test_texts = [
        "Military conflict escalates in Eastern Europe with new attacks reported",
        "Diplomatic talks continue between world leaders on trade agreements",
        "Local sports team wins championship in peaceful celebration",
        "Nuclear threats emerge as tensions rise between nations",
        "Economic cooperation summit planned for next month"
    ]
    
    for text in test_texts:
        analysis = analyzer.analyze_risk(text)
        print(f"\\nText: {text}")
        print(f"Analysis: {analysis}")
        print(f"Explanation: {analyzer.get_risk_explanation(analysis)}")

if __name__ == "__main__":
    main()