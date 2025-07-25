"""
Geographic Region Analyzer
Analyzes articles using AI to extract geographic regions and generates CSV data for heatmap visualization.
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any
import sqlite3
import logging


class GeographicAnalyzer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.csv_path = "data/geographic_analysis.csv"

        # Geographic regions mapping
        self.regions_mapping = {
            'North America': ['united states', 'usa', 'canada', 'mexico', 'us', 'american'],
            'South America': ['brazil', 'argentina', 'chile', 'colombia', 'peru', 'venezuela', 'ecuador'],
            'Europe': ['germany', 'france', 'italy', 'spain', 'uk', 'britain', 'poland', 'netherlands', 'belgium'],
            'Eastern Europe': ['russia', 'ukraine', 'belarus', 'moldova', 'georgia', 'armenia', 'azerbaijan'],
            'Middle East': ['israel', 'palestine', 'iran', 'iraq', 'syria', 'lebanon', 'turkey', 'saudi arabia', 'uae'],
            'Asia': ['china', 'japan', 'south korea', 'india', 'pakistan', 'bangladesh', 'thailand', 'vietnam'],
            'Southeast Asia': ['indonesia', 'philippines', 'malaysia', 'singapore', 'myanmar', 'cambodia', 'laos'],
            'Africa': ['south africa', 'nigeria', 'egypt', 'kenya', 'ethiopia', 'ghana', 'morocco', 'algeria'],
            'Oceania': ['australia', 'new zealand', 'fiji', 'papua new guinea'],
            'Central Asia': ['kazakhstan', 'uzbekistan', 'turkmenistan', 'kyrgyzstan', 'tajikistan', 'afghanistan']
        }

        # Risk weight by keywords
        self.risk_keywords = {
            'high': [
                'war',
                'conflict',
                'attack',
                'bombing',
                'terrorism',
                'crisis',
                'sanctions',
                'invasion'],
            'medium': [
                'protest',
                'tension',
                'dispute',
                'negotiation',
                'diplomatic',
                'trade war'],
            'low': [
                'cooperation',
                'agreement',
                'partnership',
                'summit',
                'visit',
                'economic growth']}

    def analyze_article_geography(
            self, article_content: str, article_title: str) -> Dict[str, Any]:
        """
        Analyze article content to extract geographic regions and risk levels.
        """
        content_lower = (article_content + " " + article_title).lower()

        # Extract regions mentioned
        regions_found = []
        for region, keywords in self.regions_mapping.items():
            for keyword in keywords:
                if keyword in content_lower:
                    regions_found.append(region)
                    break

        # Determine risk level
        risk_level = 'low'
        for level, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    risk_level = level
                    if level == 'high':  # Stop at highest risk
                        break
            if risk_level == 'high':
                break

        # Calculate risk score
        risk_scores = {'low': 1, 'medium': 2, 'high': 3}
        risk_score = risk_scores.get(risk_level, 1)

        return {
            'regions': list(set(regions_found)),
            'risk_level': risk_level,
            'risk_score': risk_score,
            'content_length': len(article_content)
        }

    def process_all_articles(self) -> None:
        """
        Process all articles in database and generate geographic analysis CSV.
        """
        self.logger.info("Starting geographic analysis of all articles...")

        # Connect to database
        try:
            # Use absolute path or correct relative path
            db_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'data',
                'geopolitical_intel.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all articles
            cursor.execute("""
                SELECT id, title, content, source, language, created_at, risk_level
                FROM articles
                WHERE content IS NOT NULL AND content != ''
                ORDER BY created_at DESC
            """)

            articles = cursor.fetchall()
            self.logger.info(f"📊 Found {len(articles)} articles to analyze")

            # Prepare CSV data
            csv_data = []
            region_stats = {}

            for article in articles:
                article_id, title, content, source, language, created_at, db_risk_level = article

                # Analyze geography
                analysis = self.analyze_article_geography(content, title)

                # Process each region found
                for region in analysis['regions']:
                    if region not in region_stats:
                        region_stats[region] = {
                            'articles_count': 0,
                            'total_risk_score': 0,
                            'high_risk_count': 0,
                            'medium_risk_count': 0,
                            'low_risk_count': 0,
                            'sources': set(),
                            'languages': set()
                        }

                    # Update statistics
                    stats = region_stats[region]
                    stats['articles_count'] += 1
                    stats['total_risk_score'] += analysis['risk_score']
                    stats[f"{analysis['risk_level']}_risk_count"] += 1
                    stats['sources'].add(source)
                    stats['languages'].add(language)

                    # Add to CSV data
                    csv_data.append({
                        'region': region,
                        'article_id': article_id,
                        'title': title[:100],  # Truncate for CSV
                        'source': source,
                        'language': language,
                        'risk_level': analysis['risk_level'],
                        'risk_score': analysis['risk_score'],
                        'created_at': created_at,
                        'analysis_date': datetime.now().isoformat()
                    })

            # Write detailed CSV
            self.write_detailed_csv(csv_data)

            # Write summary CSV for heatmap
            self.write_heatmap_csv(region_stats)

            conn.close()
            self.logger.info("✅ Geographic analysis completed successfully")

        except Exception as e:
            self.logger.error(f"Error in geographic analysis: {str(e)}")
            raise

    def write_detailed_csv(self, csv_data: List[Dict]) -> None:
        """Write detailed analysis to CSV."""
        detailed_path = "data/geographic_analysis_detailed.csv"

        if csv_data:
            fieldnames = csv_data[0].keys()
            with open(detailed_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

            self.logger.info(f"📄 Detailed analysis saved to {detailed_path}")

    def write_heatmap_csv(self, region_stats: Dict) -> None:
        """Write heatmap summary to CSV."""
        heatmap_data = []

        for region, stats in region_stats.items():
            avg_risk_score = stats['total_risk_score'] / \
                stats['articles_count'] if stats['articles_count'] > 0 else 0

            heatmap_data.append({
                'region': region,
                'articles_count': stats['articles_count'],
                'average_risk_score': round(avg_risk_score, 2),
                'high_risk_articles': stats['high_risk_count'],
                'medium_risk_articles': stats['medium_risk_count'],
                'low_risk_articles': stats['low_risk_count'],
                'unique_sources': len(stats['sources']),
                'unique_languages': len(stats['languages']),
                # Cap at 100
                'risk_intensity': min(stats['articles_count'] * avg_risk_score, 100),
                'last_updated': datetime.now().isoformat()
            })

        # Sort by risk intensity
        heatmap_data.sort(key=lambda x: x['risk_intensity'], reverse=True)

        # Write heatmap CSV
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            if heatmap_data:
                fieldnames = heatmap_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(heatmap_data)

        self.logger.info(f"Heatmap data saved to {self.csv_path}")
        self.logger.info(f"Analyzed {len(region_stats)} regions")

    def get_heatmap_data(self) -> List[Dict]:
        """Read heatmap data from CSV."""
        if not os.path.exists(self.csv_path):
            self.logger.warning("Heatmap CSV not found, generating...")
            self.process_all_articles()

        heatmap_data = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                heatmap_data = list(reader)
        except Exception as e:
            self.logger.error(f"❌ Error reading heatmap CSV: {str(e)}")

        return heatmap_data

    def refresh_analysis(self) -> None:
        """Refresh the geographic analysis."""
        self.logger.info("🔄 Refreshing geographic analysis...")
        self.process_all_articles()
