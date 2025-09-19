#!/usr/bin/env python3
"""
Sistema de Análisis NLP Avanzado para Extracción de Entidades Geopolíticas
Extrae: países, políticos, armamento, intensidad de conflicto, ubicaciones, etc.
"""

import sqlite3
import json
import re
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import spacy
import requests
from groq import Groq

class AdvancedGeopoliticalNLP:
    """Sistema NLP avanzado para análisis geopolítico completo"""
    
    def __init__(self, db_path: str = './data/geopolitical_intel.db', groq_client=None):
        self.db_path = db_path
        self.groq_client = groq_client
        self.nlp_model = None
        
        # Diccionarios de entidades geopolíticas
        self.countries_database = self._load_countries_database()
        self.weapons_database = self._load_weapons_database()
        self.politicians_database = self._load_politicians_database()
        
        # Patrones de expresiones regulares
        self.intensity_patterns = self._compile_intensity_patterns()
        self.conflict_patterns = self._compile_conflict_patterns()
        
        self._load_nlp_model()
    
    def _load_nlp_model(self):
        """Cargar modelo NLP de spaCy"""
        try:
            # Intentar cargar modelo en español
            self.nlp_model = spacy.load("es_core_news_sm")
        except OSError:
            try:
                # Fallback a modelo en inglés
                self.nlp_model = spacy.load("en_core_web_sm")
                print("⚠️ Usando modelo en inglés. Instalar es_core_news_sm para mejor rendimiento.")
            except OSError:
                print("❌ No se encontraron modelos spaCy. Ejecutar: python -m spacy download es_core_news_sm")
                self.nlp_model = None
    
    def _load_countries_database(self) -> List[str]:
        """Base de datos de países y sus variantes"""
        return [
            # Países principales en conflictos actuales
            'Ucrania', 'Rusia', 'China', 'Estados Unidos', 'EEUU', 'USA',
            'Israel', 'Palestina', 'Gaza', 'Cisjordania',
            'Irán', 'Irak', 'Siria', 'Turquía',
            'Corea del Norte', 'Corea del Sur',
            'India', 'Pakistán', 'Afganistán',
            'Yemen', 'Arabia Saudí', 'Emiratos Árabes Unidos',
            'Venezuela', 'Colombia', 'Brasil',
            'Nigeria', 'Etiopía', 'Sudán', 'Somalia',
            'Myanmar', 'Birmania', 'Filipinas',
            'Serbia', 'Kosovo', 'Bosnia', 'Albania',
            'Taiwán', 'Hong Kong', 'Tíbet',
            'Crimea', 'Donbás', 'Lugansk', 'Donetsk',
            # Organizaciones y regiones
            'OTAN', 'NATO', 'Unión Europea', 'UE',
            'Oriente Medio', 'Medio Oriente', 'Cáucaso',
            'Balcanes', 'Europa del Este', 'Asia Central'
        ]
    
    def _load_weapons_database(self) -> Dict[str, List[str]]:
        """Base de datos de armamento y modelos específicos"""
        return {
            'missiles': [
                'HIMARS', 'Patriot', 'THAAD', 'Iron Dome', 'S-400', 'S-300',
                'Iskander', 'Kinzhal', 'Kh-47M2', 'Storm Shadow', 'SCALP',
                'Tomahawk', 'ATACMS', 'GMLRS', 'Javelin', 'NLAW',
                'Stinger', 'Igla', 'BUK', 'Tor', 'Pantsir'
            ],
            'aircraft': [
                'F-16', 'F-35', 'F-22', 'F/A-18', 'A-10',
                'Su-27', 'Su-30', 'Su-35', 'Su-57', 'MiG-29', 'MiG-31',
                'Tu-95', 'Tu-160', 'B-52', 'B-2', 'B-1B',
                'Eurofighter', 'Rafale', 'Gripen',
                'J-20', 'J-16', 'J-10'
            ],
            'vehicles': [
                'M1 Abrams', 'Leopard 2', 'Challenger 2', 'Merkava',
                'T-72', 'T-80', 'T-90', 'T-14 Armata',
                'Bradley', 'Stryker', 'MRAP', 'Humvee',
                'BMP', 'BTR', 'BRDM', 'BMD'
            ],
            'naval': [
                'USS', 'HMS', 'Admiral Kuznetsov', 'Liaoning',
                'Nimitz', 'Gerald R. Ford', 'Queen Elizabeth',
                'Type 055', 'Type 052D', 'Arleigh Burke',
                'Ticonderoga', 'Virginia', 'Los Angeles', 'Seawolf'
            ],
            'artillery': [
                'M777', 'M109', 'CAESAR', 'PzH 2000', 'K9 Thunder',
                'Grad', 'Smerch', 'Uragan', 'TOS-1', 'Katyusha',
                'M270', 'M142', 'LR-PRS'
            ]
        }
    
    def _load_politicians_database(self) -> List[str]:
        """Base de datos de políticos relevantes en conflictos geopolíticos"""
        return [
            # Líderes mundiales actuales
            'Vladimir Putin', 'Volodymyr Zelensky', 'Joe Biden', 'Xi Jinping',
            'Benjamin Netanyahu', 'Mahmoud Abbas', 'Ayatollah Khamenei',
            'Kim Jong-un', 'Moon Jae-in', 'Narendra Modi', 'Imran Khan',
            'Mohammed bin Salman', 'Mohammed bin Zayed', 'Recep Tayyip Erdogan',
            'Emmanuel Macron', 'Olaf Scholz', 'Giorgia Meloni', 'Pedro Sánchez',
            'Lula da Silva', 'Nicolás Maduro', 'Gustavo Petro',
            # Líderes militares y ministros de defensa
            'Lloyd Austin', 'Sergei Shoigu', 'Wei Fenghe', 'Ben Wallace',
            'Sébastien Lecornu', 'Christine Lambrecht', 'Margarita Robles',
            # Secretarios y ministros de relaciones exteriores  
            'Antony Blinken', 'Sergey Lavrov', 'Wang Yi', 'James Cleverly',
            'Catherine Colonna', 'Annalena Baerbock', 'José Manuel Albares'
        ]
    
    def _compile_intensity_patterns(self) -> Dict[str, List[str]]:
        """Patrones para detectar intensidad de conflicto"""
        return {
            'high_intensity': [
                r'\b(guerra|conflicto armado|invasión|bombardeo|ataque aéreo)\b',
                r'\b(masacre|genocidio|crímenes de guerra|limpieza étnica)\b',
                r'\b(estado de sitio|ley marcial|toque de queda)\b',
                r'\b(miles de muertos|cientos de víctimas|bajas masivas)\b'
            ],
            'medium_intensity': [
                r'\b(enfrentamientos|escaramuzas|incidente fronterizo)\b',
                r'\b(tensión|crisis|escalada|provocación)\b',
                r'\b(sanciones|embargo|bloqueo económico)\b',
                r'\b(ejercicios militares|despliegue de tropas)\b'
            ],
            'low_intensity': [
                r'\b(negociaciones|diplomacia|diálogo)\b',
                r'\b(acuerdo|tregua|alto el fuego|cese)\b',
                r'\b(cooperación|alianza|tratado)\b',
                r'\b(intercambio|comercio|inversión)\b'
            ]
        }
    
    def _compile_conflict_patterns(self) -> Dict[str, List[str]]:
        """Patrones para tipos de conflicto"""
        return {
            'territorial': [
                r'\b(territorio|frontera|límite|soberanía)\b',
                r'\b(anexión|ocupación|secesión|independencia)\b',
                r'\b(disputas territoriales|reclamos territoriales)\b'
            ],
            'military': [
                r'\b(operación militar|invasión|ofensiva)\b',
                r'\b(tropas|ejército|fuerzas armadas|militar)\b',
                r'\b(combate|batalla|enfrentamiento armado)\b'
            ],
            'cyber': [
                r'\b(ciberataque|hack|malware|ransomware)\b',
                r'\b(infraestructura crítica|sistemas informáticos)\b',
                r'\b(guerra cibernética|ciber)\b'
            ],
            'economic': [
                r'\b(sanciones económicas|embargo|bloqueo)\b',
                r'\b(guerra comercial|aranceles|comercio)\b',
                r'\b(crisis económica|colapso financiero)\b'
            ]
        }
    
    def extract_countries(self, text: str) -> List[str]:
        """Extraer países mencionados en el texto"""
        countries_found = []
        text_lower = text.lower()
        
        for country in self.countries_database:
            if country.lower() in text_lower:
                countries_found.append(country)
        
        # Usar NLP para entidades geopolíticas si disponible
        if self.nlp_model:
            doc = self.nlp_model(text)
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC']:  # Geopolitical entities, Locations
                    if ent.text not in countries_found:
                        countries_found.append(ent.text)
        
        return list(set(countries_found))
    
    def extract_politicians(self, text: str) -> List[str]:
        """Extraer políticos mencionados en el texto"""
        politicians_found = []
        
        # Buscar políticos conocidos
        for politician in self.politicians_database:
            if politician.lower() in text.lower():
                politicians_found.append(politician)
        
        # Usar NLP para entidades de persona si disponible
        if self.nlp_model:
            doc = self.nlp_model(text)
            for ent in doc.ents:
                if ent.label_ == 'PER':  # Personas
                    # Filtrar posibles políticos (nombres con al menos 2 palabras)
                    if len(ent.text.split()) >= 2:
                        politicians_found.append(ent.text)
        
        return list(set(politicians_found))
    
    def extract_weapons(self, text: str) -> Dict[str, List[str]]:
        """Extraer armamento y modelos específicos"""
        weapons_found = {
            'missiles': [],
            'aircraft': [],
            'vehicles': [],
            'naval': [],
            'artillery': [],
            'general': []
        }
        
        text_upper = text.upper()
        
        # Buscar armas específicas por categoría
        for category, weapons_list in self.weapons_database.items():
            for weapon in weapons_list:
                if weapon.upper() in text_upper:
                    weapons_found[category].append(weapon)
        
        # Patrones adicionales para armamento general
        general_patterns = [
            r'\b(misil|cohete|proyectil)\b',
            r'\b(tanque|blindado|vehículo militar)\b',
            r'\b(avión|caza|bombardero|dron)\b',
            r'\b(buque|submarino|fragata|destructor)\b',
            r'\b(artillería|cañón|obús|mortero)\b'
        ]
        
        for pattern in general_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            weapons_found['general'].extend(matches)
        
        # Limpiar duplicados
        for category in weapons_found:
            weapons_found[category] = list(set(weapons_found[category]))
        
        return weapons_found
    
    def calculate_conflict_intensity(self, text: str) -> Tuple[float, str]:
        """Calcular intensidad del conflicto basado en el contenido"""
        text_lower = text.lower()
        
        high_score = 0
        medium_score = 0
        low_score = 0
        
        # Contar matches por nivel de intensidad
        for pattern in self.intensity_patterns['high_intensity']:
            high_score += len(re.findall(pattern, text_lower))
        
        for pattern in self.intensity_patterns['medium_intensity']:
            medium_score += len(re.findall(pattern, text_lower))
        
        for pattern in self.intensity_patterns['low_intensity']:
            low_score += len(re.findall(pattern, text_lower))
        
        # Calcular score total
        total_score = (high_score * 3) + (medium_score * 2) + (low_score * 1)
        max_possible = 15  # Máximo teórico
        
        intensity_percentage = min((total_score / max_possible) * 100, 100)
        
        # Determinar categoría
        if high_score > 0 or intensity_percentage > 70:
            category = 'alto'
        elif medium_score > 0 or intensity_percentage > 30:
            category = 'medio'
        else:
            category = 'bajo'
        
        return intensity_percentage, category
    
    def identify_conflict_type(self, text: str) -> List[str]:
        """Identificar tipos de conflicto presentes"""
        conflict_types = []
        text_lower = text.lower()
        
        for conflict_type, patterns in self.conflict_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    conflict_types.append(conflict_type)
                    break
        
        return list(set(conflict_types))
    
    def extract_locations(self, text: str) -> List[str]:
        """Extraer ubicaciones específicas mencionadas"""
        locations = []
        
        if self.nlp_model:
            doc = self.nlp_model(text)
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC']:
                    locations.append(ent.text)
        
        # Patrones adicionales para ciudades y regiones comunes en conflictos
        location_patterns = [
            r'\b(Kiev|Kyiv|Moscú|Beijing|Pekín|Washington|Tel Aviv|Jerusalén)\b',
            r'\b(Gaza|Cisjordania|Crimea|Donbás|Lugansk|Donetsk)\b',
            r'\b(Mar del Sur de China|Estrecho de Taiwán|Golfo Pérsico)\b'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            locations.extend(matches)
        
        return list(set(locations))
    
    def analyze_media_bias(self, source: str) -> Dict[str, Any]:
        """Analizar sesgo del medio de comunicación"""
        
        # Base de datos simplificada de medios y sus características
        media_database = {
            'CNN': {'country': 'Estados Unidos', 'bias': 'center-left', 'credibility': 0.8},
            'BBC': {'country': 'Reino Unido', 'bias': 'center', 'credibility': 0.9},
            'Reuters': {'country': 'Reino Unido', 'bias': 'center', 'credibility': 0.95},
            'Associated Press': {'country': 'Estados Unidos', 'bias': 'center', 'credibility': 0.9},
            'RT': {'country': 'Rusia', 'bias': 'right', 'credibility': 0.3},
            'Fox News': {'country': 'Estados Unidos', 'bias': 'right', 'credibility': 0.6},
            'Al Jazeera': {'country': 'Qatar', 'bias': 'center-left', 'credibility': 0.7},
            'El País': {'country': 'España', 'bias': 'center-left', 'credibility': 0.8},
            'El Mundo': {'country': 'España', 'bias': 'center-right', 'credibility': 0.8},
            'La Vanguardia': {'country': 'España', 'bias': 'center', 'credibility': 0.8}
        }
        
        source_clean = source.strip() if source else 'Unknown'
        
        for media_name, info in media_database.items():
            if media_name.lower() in source_clean.lower():
                return {
                    'source_country': info['country'],
                    'source_bias': info['bias'],
                    'source_credibility': info['credibility']
                }
        
        # Default para fuentes desconocidas
        return {
            'source_country': 'Unknown',
            'source_bias': 'unknown',
            'source_credibility': 0.5
        }
    
    def generate_ai_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """Generar análisis IA usando Groq"""
        if not self.groq_client:
            return {}
        
        try:
            prompt = f"""
            Analiza este artículo geopolítico y extrae información estructurada:

            Título: {title}
            Contenido: {content[:1000]}...

            Responde SOLO con un JSON válido con la siguiente estructura:
            {{
                "summary": "Resumen de 2-3 líneas",
                "conflict_intensity": "número entre 0-100",
                "urgency_level": "low|medium|high|critical",
                "impact_score": "número entre 0-1",
                "key_events": ["evento1", "evento2"],
                "main_actors": ["actor1", "actor2"],
                "geopolitical_implications": "breve análisis"
            }}
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres un analista geopolítico experto. Responde solo con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-70b-versatile",
                max_tokens=500,
                temperature=0.2
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except Exception as e:
            print(f"⚠️ Error en análisis IA: {e}")
            return {}
    
    def process_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar un artículo completo con análisis NLP avanzado"""
        
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        source = article_data.get('source', '')
        
        full_text = f"{title} {content}"
        
        # Extraer entidades
        countries = self.extract_countries(full_text)
        politicians = self.extract_politicians(full_text)
        weapons = self.extract_weapons(full_text)
        locations = self.extract_locations(full_text)
        
        # Análisis de conflicto
        intensity_score, intensity_category = self.calculate_conflict_intensity(full_text)
        conflict_types = self.identify_conflict_type(full_text)
        
        # Análisis de medios
        media_info = self.analyze_media_bias(source)
        
        # Análisis IA si disponible
        ai_analysis = self.generate_ai_analysis(title, content)
        
        # Compilar resultado
        result = {
            # Entidades extraídas
            'countries_involved': json.dumps(countries, ensure_ascii=False),
            'politicians_involved': json.dumps(politicians, ensure_ascii=False),
            'weapons_mentioned': json.dumps(weapons, ensure_ascii=False),
            'location_extracted': json.dumps(locations, ensure_ascii=False),
            
            # Análisis de conflicto
            'conflict_intensity': intensity_score,
            'conflict_type': ', '.join(conflict_types) if conflict_types else 'general',
            'risk_level': intensity_category,
            
            # Información de medios
            'source_country': media_info.get('source_country'),
            'source_bias': media_info.get('source_bias'),
            'source_credibility': media_info.get('source_credibility'),
            
            # Análisis IA
            'ai_summary': ai_analysis.get('summary', ''),
            'urgency_level': ai_analysis.get('urgency_level', 'medium'),
            'impact_score': ai_analysis.get('impact_score', 0.5),
            
            # Metadata de procesamiento
            'processing_confidence': min(0.9, 0.5 + (len(countries) + len(politicians)) * 0.1),
            'model_version': 'advanced_nlp_v1.0',
            'last_processed': datetime.now().isoformat(),
            
            # Datos estructurados adicionales
            'metadata_json': json.dumps({
                'entities_count': {
                    'countries': len(countries),
                    'politicians': len(politicians),
                    'weapons': sum(len(w) for w in weapons.values()),
                    'locations': len(locations)
                },
                'analysis_date': datetime.now().isoformat(),
                'ai_analysis': ai_analysis
            }, ensure_ascii=False)
        }
        
        return result

def main():
    """Función de prueba del sistema NLP"""
    print("🧠 SISTEMA DE ANÁLISIS NLP AVANZADO")
    print("=" * 40)
    
    # Crear instancia del analizador
    nlp_analyzer = AdvancedGeopoliticalNLP()
    
    # Texto de prueba
    test_text = """
    El presidente Vladimir Putin ordenó el despliegue de misiles Iskander en la región de Kaliningrado,
    en respuesta a las tensiones con la OTAN. Los ministros de defensa de Estados Unidos y Reino Unido
    se reunieron para discutir el envío de tanques Leopard 2 y sistemas Patriot a Ucrania.
    Volodymyr Zelensky agradeció el apoyo militar occidental en su lucha contra la invasión rusa.
    """
    
    # Crear datos de artículo de prueba
    test_article = {
        'title': 'Escalada militar en Europa del Este',
        'content': test_text,
        'source': 'Reuters'
    }
    
    # Procesar artículo
    result = nlp_analyzer.process_article(test_article)
    
    # Mostrar resultados
    print("📊 Resultados del análisis:")
    for key, value in result.items():
        if key == 'metadata_json':
            metadata = json.loads(value)
            print(f"   {key}: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
        else:
            print(f"   {key}: {value}")

if __name__ == "__main__":
    main()