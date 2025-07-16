"""
Generador de Reportes de Inteligencia Geopolítica Avanzado.
=========================================================
Crea reportes profesionales en HTML/PDF con análisis automático.
Diseñado para datos 100% reales de fuentes verificadas.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
from io import BytesIO
from jinja2 import Environment, FileSystemLoader, Template
# Try to import WeasyPrint, fall back to reportlab if not available
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logging.warning("WeasyPrint not available, using reportlab for PDF generation")

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False
    logging.warning("xhtml2pdf not available, using reportlab for PDF generation")

# Import reportlab as fallback
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab not available, PDF generation will be limited")

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config, DatabaseManager, ensure_directory

logger = logging.getLogger(__name__)


class AdvancedReportGenerator:
    """Generador avanzado de reportes de inteligencia geopolítica."""
    
    def __init__(self):
        self.db = DatabaseManager(config)
        self.output_dir = ensure_directory(config.get('reporting.output_dir', 'reports'))
        self.report_config = config.get('reporting', {})
        
        # Configuración de idiomas soportados
        self.supported_languages = ['es', 'en', 'ru', 'zh', 'ar']
        
        # Configurar Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        if not template_dir.exists():
            template_dir = Path(__file__).parent.parent / "reports"
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        
        # Plantillas de reportes por tipo
        self.templates = {
            'daily': 'daily_report_template.html',
            'executive': 'executive_report_template.html'
        }
        
        # Secciones del reporte (métodos disponibles)
        self.report_sections = {
            'executive_summary': self._generate_executive_summary,
            'risk_assessment': self._generate_risk_assessment,
            'geopolitical_trends': self._generate_geopolitical_trends,
            'regional_analysis': self._generate_regional_analysis,
            'trend_analysis': self._generate_trend_analysis,
            'data_sources': self._generate_data_sources
            # 'sentiment_analysis': self._generate_sentiment_analysis,  # TODO: Implementar
            # 'entity_tracking': self._generate_entity_tracking,        # TODO: Implementar
            # 'source_reliability': self._generate_source_reliability,  # TODO: Implementar
            # 'recommendations': self._generate_recommendations         # TODO: Implementar
        }
        
        # Configuración de gráficos
        self.chart_config = {
            'theme': 'plotly_white',
            'color_palette': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'font_family': 'Arial, sans-serif',
            'title_size': 18,
            'axis_size': 12
        }
    
    def generate_comprehensive_report(
        self, 
        report_type: str = 'daily',
        date_range: Tuple[datetime, datetime] = None,
        include_charts: bool = True,
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """Genera reporte integral de inteligencia geopolítica."""
        
        if date_range is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1 if report_type == 'daily' else 7)
            date_range = (start_date, end_date)
        
        if languages is None:
            languages = self.supported_languages
        
        logger.info(f"Generando reporte {report_type} para período {date_range[0]} - {date_range[1]}")
        
        # Recopilar datos
        report_data = self._collect_comprehensive_data(date_range, languages)
        
        # Generar análisis
        analysis = self._perform_comprehensive_analysis(report_data)
        
        # Crear visualizaciones
        charts = self._generate_charts(report_data) if include_charts else {}
        
        # Ensamblar reporte
        report = self._assemble_report(
            report_type, 
            report_data, 
            analysis, 
            charts, 
            date_range
        )
        
        # Guardar archivos
        output_files = self._save_report(report, report_type, date_range[1])
        
        logger.info(f"Reporte {report_type} generado exitosamente")
        
        return {
            'report': report,
            'files': output_files,
            'metrics': {
                'articles_analyzed': len(report_data.get('articles', [])),
                'languages_covered': len(languages),
                'risk_events': len(analysis.get('risk_events', [])),
                'generation_time': datetime.now().isoformat()
            }
        }
        
    def generate_daily_report(self, target_date: datetime = None) -> Dict[str, Any]:
        """Genera reporte diario usando la plantilla profesional."""
        if target_date is None:
            target_date = datetime.now()
        
        logger.info(f"Generando reporte diario para {target_date.strftime('%Y-%m-%d')}")
        
        # Recopilar datos del día
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Obtener datos de la base de datos
        daily_data = self._get_daily_data(start_date, end_date)
        
        # Preparar contexto para la plantilla
        template_context = {
            'report_date': target_date.strftime('%d de %B de %Y'),
            'total_events': daily_data['total_events'],
            'high_priority_events': daily_data['high_priority_events'],
            'countries_mentioned': daily_data['countries_mentioned'],
            'sources_monitored': daily_data['sources_monitored'],
            'critical_alerts': daily_data['critical_alerts'],
            'daily_events': daily_data['events'],
            'regional_summaries': daily_data['regional_summaries'],
            'generation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'next_update': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 00:00')
        }
        
        # Generar HTML usando Jinja2
        template = self.jinja_env.get_template(self.templates['daily'])
        html_content = template.render(**template_context)
        
        # Guardar archivo
        filename = f"riskmap_daily_{target_date.strftime('%Y%m%d')}"
        output_files = self._save_report_files(html_content, filename, daily_data)
        
        return {
            'html_content': html_content,
            'files': output_files,
            'data': daily_data,
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_executive_report(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Genera reporte ejecutivo usando la plantilla profesional."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=7)  # Reporte semanal por defecto
        
        logger.info(f"Generando reporte ejecutivo para período {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
        
        # Recopilar datos del período
        executive_data = self._get_executive_data(start_date, end_date)
        
        # Generar gráficos
        charts = self._generate_executive_charts(executive_data)
        
        # Preparar contexto para la plantilla
        period_str = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
        template_context = {
            'report_period': period_str,
            'generation_date': datetime.now().strftime('%d de %B de %Y'),
            'total_articles': executive_data['total_articles'],
            'languages_count': len(executive_data['languages']),
            'threat_level': executive_data['threat_level'],
            'executive_summary': executive_data['executive_summary'],
            'conflict_count': executive_data['metrics']['conflicts'],
            'diplomatic_crises': executive_data['metrics']['diplomatic_crises'],
            'protests_count': executive_data['metrics']['protests'],
            'countries_affected': executive_data['countries_affected'],
            'high_risk_regions': executive_data['high_risk_regions'],
            'featured_events': executive_data['featured_events'],
            'strategic_recommendations': executive_data['recommendations'],
            'category_chart': charts['category_distribution'],
            'timeline_chart': charts['timeline'],
            'classification': 'RESTRINGIDO',
            'distribution': 'Solo personal autorizado',
            'validity_period': '7 días'
        }
        
        # Generar HTML usando Jinja2
        template = self.jinja_env.get_template(self.templates['executive'])
        html_content = template.render(**template_context)
        
        # Guardar archivo
        filename = f"riskmap_executive_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        output_files = self._save_report_files(html_content, filename, executive_data)
        
        return {
            'html_content': html_content,
            'files': output_files,
            'data': executive_data,
            'charts': charts,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_daily_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Obtiene datos para reporte diario."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Eventos del día
            cursor.execute("""
                SELECT title, summary, category, country, sentiment, source, 
                       published_at, source_url
                FROM articles 
                WHERE published_at BETWEEN ? AND ?
                ORDER BY published_at DESC
                LIMIT 50
            """, (start_date.isoformat(), end_date.isoformat()))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'title': row[0],
                    'summary': row[1],
                    'category': row[2],
                    'region': row[3],
                    'sentiment': row[4],
                    'source': row[5],
                    'time': datetime.fromisoformat(row[6]).strftime('%H:%M'),
                    'source_url': row[7]
                })
            
            # Estadísticas
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE published_at BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            total_events = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE published_at BETWEEN ? AND ? 
                AND category IN ('Conflicto militar', 'Crisis diplomática')
            """, (start_date.isoformat(), end_date.isoformat()))
            high_priority = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT country) FROM articles 
                WHERE published_at BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            countries = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT source) FROM articles 
                WHERE published_at BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            sources = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_events': total_events,
                'high_priority_events': high_priority,
                'countries_mentioned': countries,
                'sources_monitored': sources,
                'events': events[:20],  # Top 20 eventos
                'critical_alerts': [],  # Implementar lógica de alertas
                'regional_summaries': self._get_regional_summaries(start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos diarios: {e}")
            return self._get_empty_daily_data()
    
    def _get_executive_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Obtiene datos para reporte ejecutivo."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Métricas generales
            cursor.execute("""
                SELECT COUNT(*), COUNT(DISTINCT language), COUNT(DISTINCT country)
                FROM articles 
                WHERE published_at BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            
            total_articles, languages_count, countries_count = cursor.fetchone()
            
            # Métricas por categoría
            cursor.execute("""
                SELECT category, COUNT(*) 
                FROM articles 
                WHERE published_at BETWEEN ? AND ?
                GROUP BY category
            """, (start_date.isoformat(), end_date.isoformat()))
            
            category_metrics = dict(cursor.fetchall())
            
            # Eventos destacados
            cursor.execute("""
                SELECT title, summary, category, country, sentiment, source, 
                       DATE(published_at) as date, source_url
                FROM articles 
                WHERE published_at BETWEEN ? AND ?
                AND category IN ('Conflicto militar', 'Crisis diplomática', 'Protesta')
                ORDER BY published_at DESC
                LIMIT 20
            """, (start_date.isoformat(), end_date.isoformat()))
            
            featured_events = []
            for row in cursor.fetchall():
                featured_events.append({
                    'date': row[6],
                    'region': row[3],
                    'category': row[2],
                    'summary': row[1],
                    'sentiment': row[4],
                    'source': row[5],
                    'source_url': row[7]
                })
            
            conn.close()
            
            # Análisis de nivel de amenaza
            threat_level = self._calculate_threat_level(category_metrics)
            
            return {
                'total_articles': total_articles,
                'languages': [f"Lang_{i}" for i in range(languages_count)],
                'countries_affected': countries_count,
                'threat_level': threat_level,
                'executive_summary': self._generate_executive_summary_text(category_metrics, threat_level),
                'metrics': {
                    'conflicts': category_metrics.get('Conflicto militar', 0),
                    'diplomatic_crises': category_metrics.get('Crisis diplomática', 0),
                    'protests': category_metrics.get('Protesta', 0)
                },
                'high_risk_regions': self._get_high_risk_regions(start_date, end_date),
                'featured_events': featured_events,
                'recommendations': self._generate_strategic_recommendations(category_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos ejecutivos: {e}")
            return self._get_empty_executive_data()
    
    def _save_report_files(self, html_content: str, filename: str, data: Dict = None) -> Dict[str, str]:
        """Guarda archivos de reporte en HTML y PDF."""
        output_files = {}
        
        # Crear directorio de salida
        output_dir = Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar HTML
        html_path = output_dir / f"{filename}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        output_files['html'] = str(html_path)
        
        # Intentar generar PDF
        try:
            if WEASYPRINT_AVAILABLE:
                # Intentar con WeasyPrint (mejor calidad)
                pdf_path = output_dir / f"{filename}.pdf"
                weasyprint.HTML(string=html_content).write_pdf(str(pdf_path))
                output_files['pdf'] = str(pdf_path)
                logger.info(f"PDF generado con WeasyPrint: {pdf_path}")
            elif XHTML2PDF_AVAILABLE:
                # Fallback a xhtml2pdf
                pdf_path = output_dir / f"{filename}.pdf"
                with open(pdf_path, 'wb') as pdf_file:
                    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
                    if not pisa_status.err:
                        output_files['pdf'] = str(pdf_path)
                        logger.info(f"PDF generado con xhtml2pdf: {pdf_path}")
            elif REPORTLAB_AVAILABLE:
                # Fallback a reportlab para generar PDF simple
                pdf_path = output_dir / f"{filename}.pdf"
                self._generate_simple_pdf_report(data, pdf_path)
                output_files['pdf'] = str(pdf_path)
                logger.info(f"PDF generado con reportlab: {pdf_path}")
            else:
                logger.warning("No hay bibliotecas PDF disponibles")
        except Exception as e:
            logger.warning(f"No se pudo generar PDF: {e}")
        
        return output_files
        
        for format_type in formats:
            filename = f"daily_report_{date.strftime('%Y%m%d')}.{format_type}"
            file_path = self.output_dir / filename
            
            if format_type == 'html':
                output_files[format_type] = self._save_html_report(report_content, file_path)
            elif format_type == 'pdf':
                output_files[format_type] = self._save_pdf_report(report_content, file_path)
        
        logger.info(f"Daily report generated: {list(output_files.values())}")
        return output_files
    
    def generate_weekly_report(self, end_date: datetime = None) -> Dict[str, str]:
        """Generate weekly intelligence report."""
        if end_date is None:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=7)
        
        logger.info(f"Generating weekly report for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Collect data for the report
        data = self._collect_weekly_data(start_date, end_date)
        
        # Generate report sections
        sections = {}
        enabled_sections = self.report_config.get('sections', ['executive_summary', 'risk_assessment', 'regional_analysis', 'trend_analysis'])
        
        for section_name in enabled_sections:
            if section_name in self.templates['sections']:
                logger.info(f"Generating section: {section_name}")
                sections[section_name] = self.templates['sections'][section_name](data, end_date, start_date)
        
        # Generate final report
        report_content = self._compile_report(sections, data, end_date, 'weekly', start_date)
        
        # Save report in configured formats
        output_files = {}
        formats = self.report_config.get('formats', ['html'])
        
        for format_type in formats:
            filename = f"weekly_report_{end_date.strftime('%Y%m%d')}.{format_type}"
            file_path = self.output_dir / filename
            
            if format_type == 'html':
                output_files[format_type] = self._save_html_report(report_content, file_path)
            elif format_type == 'pdf':
                output_files[format_type] = self._save_pdf_report(report_content, file_path)
        
        logger.info(f"Weekly report generated: {list(output_files.values())}")
        return output_files
    
    def _collect_daily_data(self, date: datetime) -> Dict[str, Any]:
        """Collect data for daily report."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        data = {}
        
        # Total articles
        cursor.execute('''
            SELECT COUNT(*) FROM articles 
            WHERE published_at >= ? AND published_at < ?
        ''', (start_date, end_date))
        data['total_articles'] = cursor.fetchone()[0]
        
        # Articles by category
        cursor.execute('''
            SELECT p.category, COUNT(*) as count, AVG(p.sentiment) as avg_sentiment
            FROM processed_data p
            JOIN articles a ON p.article_id = a.id
            WHERE a.published_at >= ? AND a.published_at < ?
            GROUP BY p.category
            ORDER BY count DESC
        ''', (start_date, end_date))
        data['categories'] = [
            {
                'category': row[0],
                'count': row[1],
                'avg_sentiment': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        # Regional events
        cursor.execute('''
            SELECT 
                json_extract(p.entities, '$.GPE') as countries,
                COUNT(*) as event_count,
                AVG(p.sentiment) as avg_sentiment,
                p.category
            FROM processed_data p
            JOIN articles a ON p.article_id = a.id
            WHERE a.published_at >= ? AND a.published_at < ?
                AND json_extract(p.entities, '$.GPE') IS NOT NULL
            GROUP BY countries
            ORDER BY event_count DESC
            LIMIT 20
        ''', (start_date, end_date))
        
        regional_events = []
        for row in cursor.fetchall():
            try:
                countries = json.loads(row[0]) if row[0] else []
                regional_events.append({
                    'countries': countries,
                    'event_count': row[1],
                    'avg_sentiment': row[2],
                    'category': row[3]
                })
            except (json.JSONDecodeError, TypeError):
                continue
        
        data['regional_events'] = regional_events
        
        # Top articles by significance (negative sentiment + conflict categories)
        cursor.execute('''
            SELECT 
                a.title, a.source, a.published_at, a.url,
                p.category, p.sentiment, p.summary,
                json_extract(p.entities, '$.GPE') as countries
            FROM processed_data p
            JOIN articles a ON p.article_id = a.id
            WHERE a.published_at >= ? AND a.published_at < ?
                AND (p.category IN ('military_conflict', 'protest', 'diplomatic_crisis') 
                     OR p.sentiment < -0.3)
            ORDER BY 
                CASE 
                    WHEN p.category = 'military_conflict' THEN 1
                    WHEN p.category = 'diplomatic_crisis' THEN 2
                    WHEN p.category = 'protest' THEN 3
                    ELSE 4
                END,
                p.sentiment ASC
            LIMIT 10
        ''', (start_date, end_date))
        
        significant_articles = []
        for row in cursor.fetchall():
            try:
                countries = json.loads(row[7]) if row[7] else []
                significant_articles.append({
                    'title': row[0],
                    'source': row[1],
                    'published_at': row[2],
                    'url': row[3],
                    'category': row[4],
                    'sentiment': row[5],
                    'summary': row[6],
                    'countries': countries
                })
            except (json.JSONDecodeError, TypeError):
                countries = []
                significant_articles.append({
                    'title': row[0],
                    'source': row[1],
                    'published_at': row[2],
                    'url': row[3],
                    'category': row[4],
                    'sentiment': row[5],
                    'summary': row[6],
                    'countries': countries
                })
        
        data['significant_articles'] = significant_articles
        
        # Language distribution
        cursor.execute('''
            SELECT language, COUNT(*) as count
            FROM articles
            WHERE published_at >= ? AND published_at < ?
            GROUP BY language
            ORDER BY count DESC
        ''', (start_date, end_date))
        data['languages'] = dict(cursor.fetchall())
        
        conn.close()
        return data
    
    def _collect_weekly_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect data for weekly report."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        data = {}
        
        # Total articles
        cursor.execute('''
            SELECT COUNT(*) FROM articles 
            WHERE published_at >= ? AND published_at < ?
        ''', (start_date, end_date))
        data['total_articles'] = cursor.fetchone()[0]
        
        # Daily trends
        cursor.execute('''
            SELECT 
                DATE(a.published_at) as date,
                COUNT(*) as article_count,
                AVG(p.sentiment) as avg_sentiment
            FROM processed_data p
            JOIN articles a ON p.article_id = a.id
            WHERE a.published_at >= ? AND a.published_at < ?
            GROUP BY DATE(a.published_at)
            ORDER BY date
        ''', (start_date, end_date))
        data['daily_trends'] = [
            {
                'date': row[0],
                'article_count': row[1],
                'avg_sentiment': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        # Category trends
        cursor.execute('''
            SELECT 
                p.category, 
                COUNT(*) as count, 
                AVG(p.sentiment) as avg_sentiment,
                MIN(p.sentiment) as min_sentiment,
                MAX(p.sentiment) as max_sentiment
            FROM processed_data p
            JOIN articles a ON p.article_id = a.id
            WHERE a.published_at >= ? AND a.published_at < ?
            GROUP BY p.category
            ORDER BY count DESC
        ''', (start_date, end_date))
        data['categories'] = [
            {
                'category': row[0],
                'count': row[1],
                'avg_sentiment': row[2],
                'min_sentiment': row[3],
                'max_sentiment': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # Top risk regions
        cursor.execute('''
            SELECT 
                json_extract(p.entities, '$.GPE') as countries,
                COUNT(*) as event_count,
                AVG(p.sentiment) as avg_sentiment,
                COUNT(DISTINCT p.category) as category_diversity,
                GROUP_CONCAT(DISTINCT p.category) as categories
            FROM processed_data p
            JOIN articles a ON p.article_id = a.id
            WHERE a.published_at >= ? AND a.published_at < ?
                AND json_extract(p.entities, '$.GPE') IS NOT NULL
            GROUP BY countries
            HAVING event_count >= 3
            ORDER BY 
                CASE WHEN avg_sentiment < -0.2 THEN 1 ELSE 2 END,
                event_count DESC
            LIMIT 15
        ''', (start_date, end_date))
        
        risk_regions = []
        for row in cursor.fetchall():
            try:
                countries = json.loads(row[0]) if row[0] else []
                risk_regions.append({
                    'countries': countries,
                    'event_count': row[1],
                    'avg_sentiment': row[2],
                    'category_diversity': row[3],
                    'categories': row[4].split(',') if row[4] else []
                })
            except (json.JSONDecodeError, TypeError):
                continue
        
        data['risk_regions'] = risk_regions
        
        # Significant events
        cursor.execute('''
            SELECT 
                a.title, a.source, a.published_at, a.url,
                p.category, p.sentiment, p.summary,
                json_extract(p.entities, '$.GPE') as countries
            FROM processed_data p
            JOIN articles a ON p.article_id = a.id
            WHERE a.published_at >= ? AND a.published_at < ?
                AND (p.category IN ('military_conflict', 'protest', 'diplomatic_crisis') 
                     OR p.sentiment < -0.4)
            ORDER BY 
                CASE 
                    WHEN p.category = 'military_conflict' THEN 1
                    WHEN p.category = 'diplomatic_crisis' THEN 2
                    WHEN p.category = 'protest' THEN 3
                    ELSE 4
                END,
                p.sentiment ASC
            LIMIT 20
        ''', (start_date, end_date))
        
        significant_events = []
        for row in cursor.fetchall():
            try:
                countries = json.loads(row[7]) if row[7] else []
                significant_events.append({
                    'title': row[0],
                    'source': row[1],
                    'published_at': row[2],
                    'url': row[3],
                    'category': row[4],
                    'sentiment': row[5],
                    'summary': row[6],
                    'countries': countries
                })
            except (json.JSONDecodeError, TypeError):
                countries = []
                significant_events.append({
                    'title': row[0],
                    'source': row[1],
                    'published_at': row[2],
                    'url': row[3],
                    'category': row[4],
                    'sentiment': row[5],
                    'summary': row[6],
                    'countries': countries
                })
        
        data['significant_events'] = significant_events
        
        conn.close()
        return data
    
    def _generate_executive_summary(self, data: Dict[str, Any], date: datetime, start_date: datetime = None) -> str:
        """Generate executive summary section."""
        total_articles = data.get('total_articles', 0)
        categories = data.get('categories', [])
        risk_regions = data.get('risk_regions', [])
        
        # Calculate risk level
        if risk_regions:
            avg_risk_sentiment = sum(r['avg_sentiment'] for r in risk_regions[:5]) / min(len(risk_regions), 5)
            high_risk_count = sum(1 for r in risk_regions if r['avg_sentiment'] < -0.3)
        else:
            avg_risk_sentiment = 0
            high_risk_count = 0
        
        # Determine overall risk level
        if high_risk_count >= 3 or avg_risk_sentiment < -0.4:
            risk_level = "HIGH"
            risk_color = "red"
        elif high_risk_count >= 1 or avg_risk_sentiment < -0.2:
            risk_level = "MEDIUM"
            risk_color = "orange"
        else:
            risk_level = "LOW"
            risk_color = "green"
        
        # Most active categories
        top_categories = sorted(categories, key=lambda x: x['count'], reverse=True)[:3]
        
        period = "daily" if start_date is None else "weekly"
        period_text = date.strftime('%Y-%m-%d') if start_date is None else f"{start_date.strftime('%Y-%m-%d')} to {date.strftime('%Y-%m-%d')}"
        
        summary = f"""
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <p><strong>Period:</strong> {period_text}</p>
            
            <div class="key-metrics">
                <div class="metric">
                    <span class="metric-value">{total_articles}</span>
                    <span class="metric-label">Total Articles Analyzed</span>
                </div>
                <div class="metric">
                    <span class="metric-value" style="color: {risk_color};">{risk_level}</span>
                    <span class="metric-label">Global Risk Level</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{len(risk_regions)}</span>
                    <span class="metric-label">Active Risk Regions</span>
                </div>
            </div>
            
            <h3>Key Findings</h3>
            <ul>
        """
        
        # Add key findings based on data
        if high_risk_count > 0:
            summary += f"<li><strong>High Risk Alert:</strong> {high_risk_count} regions showing significant negative sentiment</li>"
        
        if top_categories:
            top_cat = top_categories[0]
            summary += f"<li><strong>Most Active Category:</strong> {top_cat['category'].replace('_', ' ').title()} with {top_cat['count']} events</li>"
        
        if risk_regions:
            top_region = risk_regions[0]
            region_name = ', '.join(top_region['countries'][:2]) if top_region['countries'] else 'Unknown'
            summary += f"<li><strong>Top Risk Region:</strong> {region_name} with {top_region['event_count']} events</li>"
        
        summary += """
            </ul>
        </div>
        """
        
        return summary
    
    def _generate_risk_assessment(self, data: Dict[str, Any], date: datetime, start_date: datetime = None) -> str:
        """Generate risk assessment section."""
        risk_regions = data.get('risk_regions', [])
        categories = data.get('categories', [])
        
        assessment = """
        <div class="risk-assessment">
            <h2>Risk Assessment</h2>
            
            <h3>High-Risk Regions</h3>
            <table class="risk-table">
                <thead>
                    <tr>
                        <th>Region</th>
                        <th>Events</th>
                        <th>Avg Sentiment</th>
                        <th>Risk Level</th>
                        <th>Primary Categories</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for region in risk_regions[:10]:
            region_name = ', '.join(region['countries'][:2]) if region['countries'] else 'Unknown'
            event_count = region['event_count']
            sentiment = region['avg_sentiment']
            
            # Determine risk level
            if sentiment < -0.3 and event_count >= 5:
                risk_level = '<span style="color: red;">HIGH</span>'
            elif sentiment < -0.1 or event_count >= 3:
                risk_level = '<span style="color: orange;">MEDIUM</span>'
            else:
                risk_level = '<span style="color: green;">LOW</span>'
            
            categories_text = ', '.join(region.get('categories', [])[:3])
            
            assessment += f"""
                <tr>
                    <td>{region_name}</td>
                    <td>{event_count}</td>
                    <td>{sentiment:.2f}</td>
                    <td>{risk_level}</td>
                    <td>{categories_text}</td>
                </tr>
            """
        
        assessment += """
                </tbody>
            </table>
            
            <h3>Category Risk Analysis</h3>
            <table class="category-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Event Count</th>
                        <th>Avg Sentiment</th>
                        <th>Risk Indicator</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for category in categories:
            cat_name = category['category'].replace('_', ' ').title()
            count = category['count']
            sentiment = category['avg_sentiment']
            
            # Risk indicator
            if category['category'] in ['military_conflict', 'diplomatic_crisis'] and sentiment < -0.2:
                risk_indicator = '🔴 High'
            elif sentiment < -0.1:
                risk_indicator = '🟡 Medium'
            else:
                risk_indicator = '🟢 Low'
            
            assessment += f"""
                <tr>
                    <td>{cat_name}</td>
                    <td>{count}</td>
                    <td>{sentiment:.2f}</td>
                    <td>{risk_indicator}</td>
                </tr>
            """
        
        assessment += """
                </tbody>
            </table>
        </div>
        """
        
        return assessment
    
    def _generate_regional_analysis(self, data: Dict[str, Any], date: datetime, start_date: datetime = None) -> str:
        """Generate regional analysis section."""
        regional_events = data.get('regional_events', []) or data.get('risk_regions', [])
        
        analysis = """
        <div class="regional-analysis">
            <h2>Regional Analysis</h2>
        """
        
        if not regional_events:
            analysis += "<p>No significant regional events detected in this period.</p>"
        else:
            # Group regions by continent/area (simplified)
            regions_by_area = self._group_regions_by_area(regional_events)
            
            for area, regions in regions_by_area.items():
                analysis += f"<h3>{area}</h3>"
                analysis += "<ul>"
                
                for region in regions[:5]:  # Top 5 per area
                    region_name = ', '.join(region['countries'][:2]) if region['countries'] else 'Unknown'
                    event_count = region['event_count']
                    sentiment = region['avg_sentiment']
                    
                    sentiment_text = "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"
                    
                    analysis += f"""
                        <li>
                            <strong>{region_name}:</strong> 
                            {event_count} events, {sentiment_text} sentiment ({sentiment:.2f})
                        </li>
                    """
                
                analysis += "</ul>"
        
        analysis += """
        </div>
        """
        
        return analysis
    
    def _generate_trend_analysis(self, data: Dict[str, Any], date: datetime, start_date: datetime = None) -> str:
        """Generate trend analysis section."""
        daily_trends = data.get('daily_trends', [])
        categories = data.get('categories', [])
        
        analysis = """
        <div class="trend-analysis">
            <h2>Trend Analysis</h2>
        """
        
        if daily_trends:
            analysis += "<h3>Daily Activity Trends</h3>"
            analysis += "<table class='trend-table'>"
            analysis += "<thead><tr><th>Date</th><th>Articles</th><th>Avg Sentiment</th><th>Trend</th></tr></thead>"
            analysis += "<tbody>"
            
            for i, trend in enumerate(daily_trends):
                date_str = trend['date']
                count = trend['article_count']
                sentiment = trend['avg_sentiment']
                
                # Calculate trend (compare with previous day)
                if i > 0:
                    prev_count = daily_trends[i-1]['article_count']
                    if count > prev_count * 1.2:
                        trend_indicator = "[STATS] Increasing"
                    elif count < prev_count * 0.8:
                        trend_indicator = "📉 Decreasing"
                    else:
                        trend_indicator = "➡️ Stable"
                else:
                    trend_indicator = "➡️ Baseline"
                
                analysis += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td>{count}</td>
                        <td>{sentiment:.2f}</td>
                        <td>{trend_indicator}</td>
                    </tr>
                """
            
            analysis += "</tbody></table>"
        
        analysis += "<h3>Category Trends</h3>"
        analysis += "<p>Analysis of event categories and their sentiment patterns:</p>"
        analysis += "<ul>"
        
        for category in categories:
            cat_name = category['category'].replace('_', ' ').title()
            count = category['count']
            avg_sentiment = category['avg_sentiment']
            
            # Determine trend description
            if category['category'] == 'military_conflict' and avg_sentiment < -0.3:
                trend_desc = "Heightened military tensions"
            elif category['category'] == 'protest' and count > 5:
                trend_desc = "Increased civil unrest activity"
            elif category['category'] == 'diplomatic_crisis' and avg_sentiment < -0.2:
                trend_desc = "Deteriorating diplomatic relations"
            else:
                trend_desc = "Normal activity levels"
            
            analysis += f"<li><strong>{cat_name}:</strong> {trend_desc} ({count} events, sentiment: {avg_sentiment:.2f})</li>"
        
        analysis += "</ul>"
        analysis += "</div>"
        
        return analysis
    
    def _generate_geopolitical_trends(self, data: Dict[str, Any], date: datetime, start_date: datetime = None) -> str:
        """Generate geopolitical trends analysis section."""
        try:
            trends_analysis = """
            <div class="geopolitical-trends">
                <h2>Geopolitical Trends Analysis</h2>
                
                <h3>Global Tension Indicators</h3>
                <div class="trend-indicators">
            """
            
            # Analizar tendencias por región
            regional_events = data.get('regional_events', {})
            threat_level = data.get('threat_level', 'medium')
            
            # Indicadores de tensión global
            trends_analysis += f"""
                <div class="tension-level {threat_level}">
                    <h4>Current Global Tension Level: {threat_level.upper()}</h4>
                    <div class="tension-bar">
                        <div class="tension-fill {threat_level}" style="width: {self._get_tension_percentage(threat_level)}%"></div>
                    </div>
                </div>
            """
            
            # Tendencias por categoría
            category_metrics = data.get('category_metrics', {})
            if category_metrics:
                trends_analysis += "<h3>Category Trends</h3><ul class='category-trends'>"
                
                for category, count in category_metrics.items():
                    trend_status = "increasing" if count > 5 else "stable" if count > 2 else "low"
                    trends_analysis += f"""
                    <li class="trend-{trend_status}">
                        <strong>{category.replace('_', ' ').title()}:</strong> 
                        {count} events ({trend_status} activity)
                    </li>
                    """
                
                trends_analysis += "</ul>"
            
            # Tendencias emergentes
            emerging_topics = data.get('emerging_topics', [])
            if emerging_topics:
                trends_analysis += """
                <h3>Emerging Topics</h3>
                <div class="emerging-topics">
                """
                
                for topic in emerging_topics[:5]:  # Top 5 emerging topics
                    trends_analysis += f"""
                    <div class="topic-card">
                        <h4>{topic.get('name', 'Unknown Topic')}</h4>
                        <p>Mentions: {topic.get('count', 0)}</p>
                        <p>Trend: {topic.get('trend', 'stable')}</p>
                    </div>
                    """
                
                trends_analysis += "</div>"
            
            # Predicciones de tendencias
            trends_analysis += """
                <h3>Trend Predictions</h3>
                <div class="predictions">
                    <p><strong>Short-term (1-7 days):</strong> Based on current patterns, expect continued monitoring of diplomatic activities and regional tensions.</p>
                    <p><strong>Medium-term (1-4 weeks):</strong> Potential escalation in regions showing increased military activity or diplomatic strain.</p>
                    <p><strong>Key Factors to Watch:</strong> Economic indicators, military movements, diplomatic communications, and social unrest metrics.</p>
                </div>
            """
            
            trends_analysis += "</div>"
            
            return trends_analysis
            
        except Exception as e:
            logger.error(f"Error generating geopolitical trends: {e}")
            return "<div class='error'>Error generating geopolitical trends analysis</div>"
    
    def _get_tension_percentage(self, level: str) -> int:
        """Convert tension level to percentage for display."""
        level_map = {
            'low': 25,
            'medium': 50,
            'high': 75,
            'critical': 95
        }
        return level_map.get(level.lower(), 50)

    def _generate_data_sources(self, data: Dict[str, Any], date: datetime, start_date: datetime = None) -> str:
        """Generate data sources section."""
        languages = data.get('languages', {})
        total_articles = data.get('total_articles', 0)
        
        sources = """
        <div class="data-sources">
            <h2>Data Sources & Methodology</h2>
            
            <h3>Article Sources</h3>
            <p>This report is based on automated analysis of {total_articles} articles from multiple sources:</p>
            <ul>
                <li>NewsAPI.org - Global news aggregation</li>
                <li>RSS feeds from major international news outlets</li>
                <li>Multi-language sources covering geopolitical events</li>
            </ul>
            
            <h3>Language Distribution</h3>
            <table class="language-table">
                <thead>
                    <tr><th>Language</th><th>Articles</th><th>Percentage</th></tr>
                </thead>
                <tbody>
        """.format(total_articles=total_articles)
        
        for lang, count in languages.items():
            percentage = (count / total_articles * 100) if total_articles > 0 else 0
            lang_name = {
                'en': 'English',
                'es': 'Spanish',
                'ru': 'Russian',
                'zh': 'Chinese',
                'ar': 'Arabic'
            }.get(lang, lang.upper())
            
            sources += f"""
                <tr>
                    <td>{lang_name}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """
        
        sources += """
                </tbody>
            </table>
            
            <h3>Analysis Methodology</h3>
            <ul>
                <li><strong>Language Detection:</strong> Automatic detection using langdetect library</li>
                <li><strong>Translation:</strong> Machine translation to English for unified analysis</li>
                <li><strong>Classification:</strong> XLM-RoBERTa based multilingual text classification</li>
                <li><strong>Sentiment Analysis:</strong> Transformer-based sentiment scoring</li>
                <li><strong>Entity Recognition:</strong> spaCy NLP models for location/organization extraction</li>
                <li><strong>Risk Assessment:</strong> Weighted scoring based on sentiment, category, and event frequency</li>
            </ul>
            
            <h3>Report Generation</h3>
            <p>This report was automatically generated on {timestamp} using the Geopolitical Intelligence System.</p>
        </div>
        """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
        
        return sources
    
    def _group_regions_by_area(self, regional_events: List[Dict]) -> Dict[str, List[Dict]]:
        """Group regions by geographical area."""
        area_mapping = {
            'Europe': ['ukraine', 'russia', 'poland', 'germany', 'france', 'uk', 'spain', 'italy', 'turkey'],
            'Middle East': ['syria', 'iran', 'israel', 'palestine', 'iraq', 'saudi arabia', 'yemen', 'lebanon'],
            'Asia': ['china', 'japan', 'korea', 'india', 'pakistan', 'afghanistan', 'thailand', 'vietnam'],
            'Africa': ['nigeria', 'egypt', 'south africa', 'ethiopia', 'libya', 'sudan', 'morocco'],
            'Americas': ['usa', 'america', 'brazil', 'argentina', 'mexico', 'colombia', 'venezuela', 'canada']
        }
        
        grouped = {area: [] for area in area_mapping.keys()}
        grouped['Other'] = []
        
        for event in regional_events:
            countries = [c.lower() for c in event.get('countries', [])]
            assigned = False
            
            for area, area_countries in area_mapping.items():
                if any(country in area_countries for country in countries):
                    grouped[area].append(event)
                    assigned = True
                    break
            
            if not assigned:
                grouped['Other'].append(event)
        
        # Remove empty areas
        return {area: events for area, events in grouped.items() if events}
    
    def _compile_report(self, sections: Dict[str, str], data: Dict[str, Any], 
                       date: datetime, report_type: str, start_date: datetime = None) -> str:
        """Compile final report from sections."""
        period_text = date.strftime('%Y-%m-%d') if start_date is None else f"{start_date.strftime('%Y-%m-%d')} to {date.strftime('%Y-%m-%d')}"
        
        # Significant events section
        significant_events = data.get('significant_events', []) or data.get('significant_articles', [])
        events_html = ""
        
        if significant_events:
            events_html = """
            <div class="significant-events">
                <h2>Significant Events</h2>
                <div class="events-list">
            """
            
            for event in significant_events[:10]:
                countries_text = ', '.join(event.get('countries', [])[:3]) if event.get('countries') else 'Global'
                sentiment_class = 'negative' if event.get('sentiment', 0) < -0.1 else 'neutral'
                
                events_html += f"""
                    <div class="event-item {sentiment_class}">
                        <h4>{event.get('title', 'Unknown Title')}</h4>
                        <div class="event-meta">
                            <span class="source">{event.get('source', 'Unknown')}</span>
                            <span class="category">{event.get('category', 'Unknown').replace('_', ' ').title()}</span>
                            <span class="region">{countries_text}</span>
                            <span class="date">{event.get('published_at', '')}</span>
                        </div>
                        {f'<p class="summary">{event.get("summary", "")}</p>' if event.get('summary') else ''}
                        <a href="{event.get('url', '#')}" target="_blank" class="read-more">Read Full Article →</a>
                    </div>
                """
            
            events_html += """
                </div>
            </div>
            """
        
        # Compile all sections
        report_content = self.templates['html'].format(
            title=f"Geopolitical Intelligence Report - {report_type.title()}",
            period=period_text,
            generated_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            executive_summary=sections.get('executive_summary', ''),
            risk_assessment=sections.get('risk_assessment', ''),
            regional_analysis=sections.get('regional_analysis', ''),
            trend_analysis=sections.get('trend_analysis', ''),
            significant_events=events_html,
            data_sources=sections.get('data_sources', '')
        )
        
        return report_content
    
    def _save_html_report(self, content: str, file_path: Path) -> str:
        """Save report as HTML file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"HTML report saved: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}")
            raise
    
    def _save_pdf_report(self, content: str, file_path: Path) -> str:
        """Save report as PDF file."""
        try:
            # Try WeasyPrint first
            if WEASYPRINT_AVAILABLE:
                weasyprint.HTML(string=content).write_pdf(str(file_path))
                logger.info(f"PDF report saved with WeasyPrint: {file_path}")
                return str(file_path)
            elif XHTML2PDF_AVAILABLE:
                # Fallback to xhtml2pdf
                with open(file_path, "w+b") as pdf_file:
                    pisa_status = pisa.CreatePDF(content, dest=pdf_file)
                    
                if pisa_status.err:
                    raise Exception(f"PDF generation failed: {pisa_status.err}")
                
                logger.info(f"PDF report saved with xhtml2pdf: {file_path}")
                return str(file_path)
            elif REPORTLAB_AVAILABLE:
                # Fallback to reportlab - convert content to simple text format
                simple_data = {'executive_summary': 'Reporte generado desde HTML'}
                self._generate_simple_pdf_report(simple_data, file_path)
                logger.info(f"PDF report saved with reportlab: {file_path}")
                return str(file_path)
            else:
                logger.error("No PDF generation libraries available")
                raise ImportError("PDF generation libraries not available")
            
        except Exception as e:
            logger.error(f"Error saving PDF report: {e}")
            raise
    
    def _get_html_template(self) -> str:
        """Get HTML template for reports."""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1a237e, #3f51b5);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
        }}
        
        .header .subtitle {{
            margin: 0.5rem 0 0 0;
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .section {{
            background: white;
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #1a237e;
            border-bottom: 3px solid #3f51b5;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .section h3 {{
            color: #3f51b5;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}
        
        .key-metrics {{
            display: flex;
            justify-content: space-around;
            margin: 2rem 0;
            flex-wrap: wrap;
        }}
        
        .metric {{
            text-align: center;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
            margin: 0.5rem;
            flex: 1;
            min-width: 150px;
        }}
        
        .metric-value {{
            display: block;
            font-size: 2rem;
            font-weight: bold;
            color: #1a237e;
        }}
        
        .metric-label {{
            display: block;
            font-size: 0.9rem;
            color: #666;
            margin-top: 0.5rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}
        
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background-color: #3f51b5;
            color: white;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .event-item {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: white;
        }}
        
        .event-item.negative {{
            border-left: 4px solid #dc3545;
        }}
        
        .event-item h4 {{
            margin: 0 0 1rem 0;
            color: #1a237e;
        }}
        
        .event-meta {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #666;
            flex-wrap: wrap;
        }}
        
        .event-meta span {{
            background: #f8f9fa;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }}
        
        .summary {{
            margin: 1rem 0;
            font-style: italic;
            color: #555;
        }}
        
        .read-more {{
            color: #3f51b5;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .read-more:hover {{
            text-decoration: underline;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #666;
            border-top: 1px solid #ddd;
            margin-top: 2rem;
        }}
        
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .header h1 {{ font-size: 2rem; }}
            .key-metrics {{ flex-direction: column; }}
            .event-meta {{ flex-direction: column; gap: 0.5rem; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p class="subtitle">Period: {period}</p>
        <p class="subtitle">Generated: {generated_time}</p>
    </div>
    
    <div class="section">
        {executive_summary}
    </div>
    
    <div class="section">
        {risk_assessment}
    </div>
    
    <div class="section">
        {regional_analysis}
    </div>
    
    <div class="section">
        {trend_analysis}
    </div>
    
    <div class="section">
        {significant_events}
    </div>
    
    <div class="section">
        {data_sources}
    </div>
    
    <div class="footer">
        <p>This report was automatically generated by the Geopolitical Intelligence System</p>
        <p>For more information, visit the interactive dashboard</p>
    </div>
</body>
</html>
        '''


# Instancia singleton del generador
report_generator = AdvancedReportGenerator()

def generate_daily_intelligence_report() -> Dict[str, Any]:
    """Genera reporte diario de inteligencia."""
    return report_generator.generate_comprehensive_report('daily')

def generate_weekly_analysis() -> Dict[str, Any]:
    """Genera análisis semanal."""
    return report_generator.generate_comprehensive_report('weekly')

def generate_crisis_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Genera reporte de crisis para período específico."""
    return report_generator.generate_comprehensive_report(
        'crisis', 
        date_range=(start_date, end_date)
    )

def main():
    """Función principal para generación de reportes."""
    generator = AdvancedReportGenerator()
    
    try:
        # Generar reporte diario
        daily_result = generator.generate_comprehensive_report('daily')
        print(f"Reporte diario generado: {daily_result['files']}")
        
        # Generar análisis semanal
        weekly_result = generator.generate_comprehensive_report('weekly')
        print(f"Análisis semanal generado: {weekly_result['files']}")
        
        print("\n[OK] Generación de reportes completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        raise

    def _generate_simple_pdf_report(self, data: Dict, pdf_path: Path) -> None:
        """Genera un reporte PDF simple usando reportlab."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab not available")
        
        try:
            # Crear documento PDF
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.darkblue
            )
            story.append(Paragraph("Reporte de Inteligencia Geopolítica", title_style))
            story.append(Spacer(1, 12))
            
            # Fecha
            story.append(Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Resumen ejecutivo
            if data and 'executive_summary' in data:
                story.append(Paragraph("Resumen Ejecutivo", styles['Heading2']))
                story.append(Paragraph(data['executive_summary'], styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Métricas principales
            if data and 'metrics' in data:
                story.append(Paragraph("Métricas Principales", styles['Heading2']))
                metrics_data = [
                    ['Métrica', 'Valor'],
                    ['Total de Artículos', str(data.get('total_articles', 0))],
                    ['Países Afectados', str(data.get('countries_affected', 0))],
                    ['Nivel de Amenaza', str(data.get('threat_level', 'N/A'))],
                ]
                
                if 'metrics' in data:
                    metrics_data.extend([
                        ['Conflictos Militares', str(data['metrics'].get('conflicts', 0))],
                        ['Crisis Diplomáticas', str(data['metrics'].get('diplomatic_crises', 0))],
                        ['Protestas', str(data['metrics'].get('protests', 0))]
                    ])
                
                table = Table(metrics_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 20))
            
            # Eventos destacados
            if data and 'featured_events' in data and data['featured_events']:
                story.append(Paragraph("Eventos Destacados", styles['Heading2']))
                for i, event in enumerate(data['featured_events'][:5]):  # Primeros 5 eventos
                    story.append(Paragraph(f"{i+1}. {event.get('summary', 'Sin resumen')}", styles['Normal']))
                    story.append(Paragraph(f"   País: {event.get('region', 'N/A')} | Categoría: {event.get('category', 'N/A')}", styles['Italic']))
                    story.append(Spacer(1, 8))
            
            # Construir PDF
            doc.build(story)
            logger.info(f"PDF simple generado con reportlab: {pdf_path}")
            
        except Exception as e:
            logger.error(f"Error generando PDF simple: {e}")
            raise


def main():
    """Función principal para generación de reportes."""
    generator = AdvancedReportGenerator()
    
    try:
        # Generar reporte diario
        daily_result = generator.generate_comprehensive_report('daily')
        print(f"Reporte diario generado: {daily_result['files']}")
        
        # Generar análisis semanal
        weekly_result = generator.generate_comprehensive_report('weekly')
        print(f"Análisis semanal generado: {weekly_result['files']}")
        
        print("\n[OK] Generación de reportes completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        raise


if __name__ == "__main__":
    main()
