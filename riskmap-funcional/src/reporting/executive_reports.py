"""
Executive Report Generation System
Automated generation of executive reports using NLP summarization,
Jinja2 templates, and multi-format output (PDF, HTML, JSON).
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from jinja2 import Environment, FileSystemLoader, Template
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import sqlite3

# NLP for summarization
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# PDF generation
try:
    import weasyprint
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("WeasyPrint not available. PDF generation will be disabled.")

logger = logging.getLogger(__name__)

class ExecutiveReportGenerator:
    """
    Advanced executive report generator with AI-powered summarization
    and professional formatting
    """
    
    def __init__(self, template_dir: str = "templates", output_dir: str = "reports"):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Initialize NLP models
        self.summarizer = None
        self.sentiment_analyzer = None
        self._initialize_nlp_models()
        
        # Report templates
        self._create_default_templates()
        
    def _initialize_nlp_models(self):
        """Initialize NLP models for summarization"""
        try:
            logger.info("Initializing NLP models for report generation...")
            
            # Summarization model
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Sentiment analysis for tone assessment
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("NLP models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NLP models: {e}")
    
    def generate_executive_report(self, 
                                data: Dict[str, Any], 
                                report_type: str = "daily",
                                format_types: List[str] = ["html", "pdf"],
                                custom_config: Optional[Dict] = None) -> Dict[str, str]:
        """
        Generate comprehensive executive report
        
        Args:
            data: Report data including conflicts, trends, alerts
            report_type: Type of report (daily, weekly, monthly, custom)
            format_types: Output formats (html, pdf, json)
            custom_config: Custom configuration for report generation
            
        Returns:
            Dictionary with file paths for each generated format
        """
        try:
            logger.info(f"Generating {report_type} executive report...")
            
            # Process and analyze data
            processed_data = self._process_report_data(data, report_type)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(processed_data)
            
            # Create visualizations
            visualizations = self._create_visualizations(processed_data)
            
            # Compile report content
            report_content = {
                'metadata': {
                    'report_type': report_type,
                    'generation_time': datetime.now(),
                    'period_start': processed_data.get('period_start'),
                    'period_end': processed_data.get('period_end'),
                    'total_events': processed_data.get('total_events', 0)
                },
                'executive_summary': executive_summary,
                'key_findings': processed_data.get('key_findings', []),
                'threat_assessment': processed_data.get('threat_assessment', {}),
                'regional_analysis': processed_data.get('regional_analysis', {}),
                'trend_analysis': processed_data.get('trend_analysis', {}),
                'recommendations': processed_data.get('recommendations', []),
                'visualizations': visualizations,
                'detailed_data': processed_data.get('detailed_data', {})
            }
            
            # Generate reports in requested formats
            generated_files = {}
            
            for format_type in format_types:
                if format_type == "html":
                    file_path = self._generate_html_report(report_content, report_type)
                    generated_files['html'] = file_path
                elif format_type == "pdf" and PDF_AVAILABLE:
                    file_path = self._generate_pdf_report(report_content, report_type)
                    generated_files['pdf'] = file_path
                elif format_type == "json":
                    file_path = self._generate_json_report(report_content, report_type)
                    generated_files['json'] = file_path
            
            logger.info(f"Executive report generated successfully: {generated_files}")
            return generated_files
            
        except Exception as e:
            logger.error(f"Error generating executive report: {e}")
            return {}
    
    def _process_report_data(self, data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Process and analyze raw data for report generation"""
        try:
            processed = {
                'period_start': data.get('period_start', datetime.now() - timedelta(days=1)),
                'period_end': data.get('period_end', datetime.now()),
                'total_events': 0,
                'key_findings': [],
                'threat_assessment': {},
                'regional_analysis': {},
                'trend_analysis': {},
                'recommendations': [],
                'detailed_data': {}
            }
            
            # Process conflicts data
            conflicts = data.get('conflicts', [])
            processed['total_events'] = len(conflicts)
            
            if conflicts:
                # Analyze conflict distribution
                processed['regional_analysis'] = self._analyze_regional_distribution(conflicts)
                
                # Assess threat levels
                processed['threat_assessment'] = self._assess_threat_levels(conflicts)
                
                # Analyze trends
                processed['trend_analysis'] = self._analyze_trends(conflicts)
                
                # Generate key findings
                processed['key_findings'] = self._extract_key_findings(conflicts, processed)
                
                # Generate recommendations
                processed['recommendations'] = self._generate_recommendations(processed)
            
            # Process alerts data
            alerts = data.get('alerts', [])
            if alerts:
                processed['alert_summary'] = self._analyze_alerts(alerts)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing report data: {e}")
            return {}
    
    def _generate_executive_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered executive summary"""
        try:
            # Compile key information for summarization
            summary_text = self._compile_summary_text(data)
            
            # Generate summary using NLP model
            if self.summarizer and summary_text:
                # Split text if too long
                max_length = 1024
                if len(summary_text) > max_length:
                    summary_text = summary_text[:max_length]
                
                summary_result = self.summarizer(
                    summary_text,
                    max_length=150,
                    min_length=50,
                    do_sample=False
                )
                
                ai_summary = summary_result[0]['summary_text']
            else:
                ai_summary = "Summary generation not available."
            
            # Analyze sentiment/tone
            sentiment_result = None
            if self.sentiment_analyzer and summary_text:
                sentiment_result = self.sentiment_analyzer(summary_text[:512])
            
            return {
                'ai_generated_summary': ai_summary,
                'key_metrics': {
                    'total_events': data.get('total_events', 0),
                    'high_risk_events': len([e for e in data.get('detailed_data', {}).get('events', []) 
                                           if e.get('risk_level', 0) > 70]),
                    'affected_regions': len(data.get('regional_analysis', {})),
                    'trend_direction': data.get('trend_analysis', {}).get('overall_trend', 'stable')
                },
                'sentiment_analysis': {
                    'overall_tone': sentiment_result[0]['label'] if sentiment_result else 'neutral',
                    'confidence': sentiment_result[0]['score'] if sentiment_result else 0.5
                },
                'period': {
                    'start': data.get('period_start'),
                    'end': data.get('period_end')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {'ai_generated_summary': 'Error generating summary'}
    
    def _compile_summary_text(self, data: Dict[str, Any]) -> str:
        """Compile text for summarization from report data"""
        try:
            text_parts = []
            
            # Add key findings
            findings = data.get('key_findings', [])
            if findings:
                text_parts.append("Key findings: " + " ".join(findings))
            
            # Add threat assessment
            threat_assessment = data.get('threat_assessment', {})
            if threat_assessment:
                threat_level = threat_assessment.get('overall_threat_level', 'unknown')
                text_parts.append(f"Overall threat level is {threat_level}.")
            
            # Add regional information
            regional_analysis = data.get('regional_analysis', {})
            if regional_analysis:
                most_affected = max(regional_analysis.items(), key=lambda x: x[1].get('event_count', 0))
                text_parts.append(f"Most affected region is {most_affected[0]} with {most_affected[1].get('event_count', 0)} events.")
            
            # Add trend information
            trend_analysis = data.get('trend_analysis', {})
            if trend_analysis:
                trend = trend_analysis.get('overall_trend', 'stable')
                text_parts.append(f"Overall trend is {trend}.")
            
            return " ".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error compiling summary text: {e}")
            return ""
    
    def _analyze_regional_distribution(self, conflicts: List[Dict]) -> Dict[str, Any]:
        """Analyze regional distribution of conflicts"""
        try:
            regional_data = {}
            
            for conflict in conflicts:
                region = conflict.get('region', 'Unknown')
                if region not in regional_data:
                    regional_data[region] = {
                        'event_count': 0,
                        'total_risk_score': 0,
                        'countries': set(),
                        'actors': set()
                    }
                
                regional_data[region]['event_count'] += 1
                regional_data[region]['total_risk_score'] += conflict.get('risk_score', 0)
                
                if conflict.get('country'):
                    regional_data[region]['countries'].add(conflict['country'])
                
                actors = conflict.get('actors', [])
                if isinstance(actors, list):
                    regional_data[region]['actors'].update(actors)
            
            # Calculate averages and convert sets to lists
            for region, data in regional_data.items():
                if data['event_count'] > 0:
                    data['average_risk_score'] = data['total_risk_score'] / data['event_count']
                else:
                    data['average_risk_score'] = 0
                
                data['countries'] = list(data['countries'])
                data['actors'] = list(data['actors'])
            
            return regional_data
            
        except Exception as e:
            logger.error(f"Error analyzing regional distribution: {e}")
            return {}
    
    def _assess_threat_levels(self, conflicts: List[Dict]) -> Dict[str, Any]:
        """Assess overall threat levels"""
        try:
            if not conflicts:
                return {'overall_threat_level': 'low', 'threat_score': 0}
            
            risk_scores = [c.get('risk_score', 0) for c in conflicts]
            avg_risk = sum(risk_scores) / len(risk_scores)
            max_risk = max(risk_scores)
            
            # Categorize threat level
            if avg_risk >= 80:
                threat_level = 'critical'
            elif avg_risk >= 60:
                threat_level = 'high'
            elif avg_risk >= 40:
                threat_level = 'medium'
            else:
                threat_level = 'low'
            
            # Count high-risk events
            high_risk_count = len([s for s in risk_scores if s >= 70])
            
            return {
                'overall_threat_level': threat_level,
                'threat_score': avg_risk,
                'max_threat_score': max_risk,
                'high_risk_events': high_risk_count,
                'total_events': len(conflicts),
                'risk_distribution': {
                    'critical': len([s for s in risk_scores if s >= 80]),
                    'high': len([s for s in risk_scores if 60 <= s < 80]),
                    'medium': len([s for s in risk_scores if 40 <= s < 60]),
                    'low': len([s for s in risk_scores if s < 40])
                }
            }
            
        except Exception as e:
            logger.error(f"Error assessing threat levels: {e}")
            return {}
    
    def _analyze_trends(self, conflicts: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in conflict data"""
        try:
            if not conflicts:
                return {'overall_trend': 'stable'}
            
            # Sort conflicts by timestamp
            sorted_conflicts = sorted(conflicts, key=lambda x: x.get('timestamp', datetime.now()))
            
            # Calculate trend over time
            if len(sorted_conflicts) >= 2:
                # Split into two halves for comparison
                mid_point = len(sorted_conflicts) // 2
                first_half = sorted_conflicts[:mid_point]
                second_half = sorted_conflicts[mid_point:]
                
                first_avg = sum(c.get('risk_score', 0) for c in first_half) / len(first_half)
                second_avg = sum(c.get('risk_score', 0) for c in second_half) / len(second_half)
                
                trend_change = second_avg - first_avg
                
                if trend_change > 10:
                    overall_trend = 'escalating'
                elif trend_change < -10:
                    overall_trend = 'de-escalating'
                else:
                    overall_trend = 'stable'
            else:
                overall_trend = 'insufficient_data'
                trend_change = 0
            
            return {
                'overall_trend': overall_trend,
                'trend_change': trend_change,
                'trend_confidence': 'high' if abs(trend_change) > 15 else 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {'overall_trend': 'unknown'}
    
    def _extract_key_findings(self, conflicts: List[Dict], processed_data: Dict) -> List[str]:
        """Extract key findings from processed data"""
        try:
            findings = []
            
            # Total events finding
            total_events = len(conflicts)
            findings.append(f"Total of {total_events} conflict events analyzed in the reporting period.")
            
            # Threat level finding
            threat_assessment = processed_data.get('threat_assessment', {})
            threat_level = threat_assessment.get('overall_threat_level', 'unknown')
            findings.append(f"Overall threat level assessed as {threat_level.upper()}.")
            
            # Regional finding
            regional_analysis = processed_data.get('regional_analysis', {})
            if regional_analysis:
                most_affected = max(regional_analysis.items(), key=lambda x: x[1].get('event_count', 0))
                findings.append(f"{most_affected[0]} region shows highest activity with {most_affected[1].get('event_count', 0)} events.")
            
            # Trend finding
            trend_analysis = processed_data.get('trend_analysis', {})
            trend = trend_analysis.get('overall_trend', 'stable')
            if trend != 'stable':
                findings.append(f"Conflict intensity is {trend} compared to previous period.")
            
            # High-risk events finding
            high_risk_count = threat_assessment.get('high_risk_events', 0)
            if high_risk_count > 0:
                findings.append(f"{high_risk_count} events classified as high-risk requiring immediate attention.")
            
            return findings
            
        except Exception as e:
            logger.error(f"Error extracting key findings: {e}")
            return []
    
    def _generate_recommendations(self, processed_data: Dict) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on analysis"""
        try:
            recommendations = []
            
            threat_assessment = processed_data.get('threat_assessment', {})
            threat_level = threat_assessment.get('overall_threat_level', 'low')
            
            # Threat-based recommendations
            if threat_level == 'critical':
                recommendations.append({
                    'priority': 'immediate',
                    'category': 'threat_response',
                    'recommendation': 'Activate emergency response protocols and increase monitoring frequency.',
                    'rationale': 'Critical threat level detected requiring immediate action.'
                })
            elif threat_level == 'high':
                recommendations.append({
                    'priority': 'high',
                    'category': 'monitoring',
                    'recommendation': 'Enhance surveillance and prepare contingency plans.',
                    'rationale': 'High threat level indicates potential for rapid escalation.'
                })
            
            # Regional recommendations
            regional_analysis = processed_data.get('regional_analysis', {})
            if regional_analysis:
                most_affected = max(regional_analysis.items(), key=lambda x: x[1].get('event_count', 0))
                if most_affected[1].get('event_count', 0) > 5:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'regional_focus',
                        'recommendation': f'Increase resources and attention to {most_affected[0]} region.',
                        'rationale': f'Region shows highest concentration of conflict events ({most_affected[1].get("event_count", 0)} events).'
                    })
            
            # Trend-based recommendations
            trend_analysis = processed_data.get('trend_analysis', {})
            trend = trend_analysis.get('overall_trend', 'stable')
            if trend == 'escalating':
                recommendations.append({
                    'priority': 'high',
                    'category': 'trend_response',
                    'recommendation': 'Implement de-escalation measures and diplomatic interventions.',
                    'rationale': 'Escalating trend detected indicating worsening conditions.'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _analyze_alerts(self, alerts: List[Dict]) -> Dict[str, Any]:
        """Analyze alerts for report inclusion"""
        try:
            if not alerts:
                return {'total_alerts': 0}
            
            # Count by severity
            severity_counts = {}
            for alert in alerts:
                severity = alert.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Recent alerts (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_alerts = []
            for alert in alerts:
                alert_time = alert.get('timestamp')
                if isinstance(alert_time, str):
                    alert_time = datetime.fromisoformat(alert_time.replace('Z', '+00:00'))
                if alert_time and alert_time >= recent_cutoff:
                    recent_alerts.append(alert)
            
            return {
                'total_alerts': len(alerts),
                'recent_alerts_24h': len(recent_alerts),
                'severity_distribution': severity_counts,
                'critical_alerts': [a for a in alerts if a.get('severity') == 'critical']
            }
            
        except Exception as e:
            logger.error(f"Error analyzing alerts: {e}")
            return {}
    
    def _create_visualizations(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Create visualizations for the report"""
        try:
            visualizations = {}
            
            # Regional distribution chart
            regional_chart = self._create_regional_chart(data.get('regional_analysis', {}))
            if regional_chart:
                visualizations['regional_distribution'] = regional_chart
            
            # Threat level distribution
            threat_chart = self._create_threat_chart(data.get('threat_assessment', {}))
            if threat_chart:
                visualizations['threat_distribution'] = threat_chart
            
            # Timeline chart
            timeline_chart = self._create_timeline_chart(data.get('detailed_data', {}))
            if timeline_chart:
                visualizations['timeline'] = timeline_chart
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")
            return {}
    
    def _create_regional_chart(self, regional_data: Dict) -> Optional[str]:
        """Create regional distribution chart"""
        try:
            if not regional_data:
                return None
            
            regions = list(regional_data.keys())
            event_counts = [data.get('event_count', 0) for data in regional_data.values()]
            
            fig = go.Figure(data=[
                go.Bar(x=regions, y=event_counts, name='Events by Region')
            ])
            
            fig.update_layout(
                title='Conflict Events by Region',
                xaxis_title='Region',
                yaxis_title='Number of Events',
                template='plotly_white'
            )
            
            # Convert to base64 string
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Error creating regional chart: {e}")
            return None
    
    def _create_threat_chart(self, threat_data: Dict) -> Optional[str]:
        """Create threat level distribution chart"""
        try:
            risk_distribution = threat_data.get('risk_distribution', {})
            if not risk_distribution:
                return None
            
            labels = list(risk_distribution.keys())
            values = list(risk_distribution.values())
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.update_layout(
                title='Threat Level Distribution',
                template='plotly_white'
            )
            
            # Convert to base64 string
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Error creating threat chart: {e}")
            return None
    
    def _create_timeline_chart(self, detailed_data: Dict) -> Optional[str]:
        """Create timeline chart of events"""
        try:
            events = detailed_data.get('events', [])
            if not events:
                return None
            
            # Extract timestamps and risk scores
            timestamps = []
            risk_scores = []
            
            for event in events:
                timestamp = event.get('timestamp')
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamps.append(timestamp)
                    risk_scores.append(event.get('risk_score', 0))
            
            if not timestamps:
                return None
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=risk_scores,
                mode='lines+markers',
                name='Risk Score Over Time'
            ))
            
            fig.update_layout(
                title='Conflict Risk Timeline',
                xaxis_title='Time',
                yaxis_title='Risk Score',
                template='plotly_white'
            )
            
            # Convert to base64 string
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Error creating timeline chart: {e}")
            return None
    
    def _generate_html_report(self, content: Dict[str, Any], report_type: str) -> str:
        """Generate HTML report"""
        try:
            template = self.jinja_env.get_template('executive_report.html')
            
            html_content = template.render(
                report=content,
                generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            # Save to file
            filename = f"executive_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return ""
    
    def _generate_pdf_report(self, content: Dict[str, Any], report_type: str) -> str:
        """Generate PDF report"""
        try:
            if not PDF_AVAILABLE:
                logger.warning("PDF generation not available")
                return ""
            
            # First generate HTML
            html_path = self._generate_html_report(content, report_type)
            
            if html_path:
                # Convert HTML to PDF
                pdf_filename = html_path.replace('.html', '.pdf')
                
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                weasyprint.HTML(string=html_content).write_pdf(pdf_filename)
                
                return pdf_filename
            
            return ""
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return ""
    
    def _generate_json_report(self, content: Dict[str, Any], report_type: str) -> str:
        """Generate JSON report"""
        try:
            # Convert datetime objects to strings for JSON serialization
            json_content = self._serialize_for_json(content)
            
            filename = f"executive_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2, ensure_ascii=False)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {e}")
            return ""
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """Recursively serialize objects for JSON"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        else:
            return obj
    
    def _create_default_templates(self):
        """Create default report templates"""
        try:
            self.template_dir.mkdir(exist_ok=True)
            
            # Executive report HTML template
            html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Executive Conflict Intelligence Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { border-bottom: 3px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .summary-box { background: #f5f5f5; padding: 20px; border-left: 5px solid #007acc; margin: 20px 0; }
        .threat-critical { color: #d32f2f; font-weight: bold; }
        .threat-high { color: #f57c00; font-weight: bold; }
        .threat-medium { color: #fbc02d; font-weight: bold; }
        .threat-low { color: #388e3c; font-weight: bold; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007acc; }
        .metric-label { font-size: 12px; color: #666; }
        .recommendation { background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .chart { text-align: center; margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Executive Conflict Intelligence Report</h1>
        <p><strong>Report Type:</strong> {{ report.metadata.report_type|title }}</p>
        <p><strong>Period:</strong> {{ report.metadata.period_start.strftime('%Y-%m-%d') }} to {{ report.metadata.period_end.strftime('%Y-%m-%d') }}</p>
        <p><strong>Generated:</strong> {{ generation_time }}</p>
    </div>

    <div class="summary-box">
        <h2>Executive Summary</h2>
        <p>{{ report.executive_summary.ai_generated_summary }}</p>
        
        <div style="margin-top: 20px;">
            <div class="metric">
                <div class="metric-value">{{ report.executive_summary.key_metrics.total_events }}</div>
                <div class="metric-label">Total Events</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ report.executive_summary.key_metrics.high_risk_events }}</div>
                <div class="metric-label">High Risk Events</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ report.executive_summary.key_metrics.affected_regions }}</div>
                <div class="metric-label">Affected Regions</div>
            </div>
        </div>
    </div>

    <h2>Key Findings</h2>
    <ul>
        {% for finding in report.key_findings %}
        <li>{{ finding }}</li>
        {% endfor %}
    </ul>

    <h2>Threat Assessment</h2>
    <p>Overall Threat Level: 
        <span class="threat-{{ report.threat_assessment.overall_threat_level }}">
            {{ report.threat_assessment.overall_threat_level|upper }}
        </span>
    </p>
    <p>Threat Score: {{ "%.1f"|format(report.threat_assessment.threat_score) }}/100</p>

    {% if report.visualizations %}
    <h2>Analysis Charts</h2>
    {% for chart_name, chart_data in report.visualizations.items() %}
    <div class="chart">
        <h3>{{ chart_name|replace('_', ' ')|title }}</h3>
        <img src="{{ chart_data }}" alt="{{ chart_name }}" style="max-width: 100%; height: auto;">
    </div>
    {% endfor %}
    {% endif %}

    <h2>Regional Analysis</h2>
    <table>
        <thead>
            <tr>
                <th>Region</th>
                <th>Events</th>
                <th>Avg Risk Score</th>
                <th>Countries Affected</th>
            </tr>
        </thead>
        <tbody>
            {% for region, data in report.regional_analysis.items() %}
            <tr>
                <td>{{ region }}</td>
                <td>{{ data.event_count }}</td>
                <td>{{ "%.1f"|format(data.average_risk_score) }}</td>
                <td>{{ data.countries|length }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2>Recommendations</h2>
    {% for rec in report.recommendations %}
    <div class="recommendation">
        <h4>{{ rec.category|replace('_', ' ')|title }} (Priority: {{ rec.priority|title }})</h4>
        <p><strong>Recommendation:</strong> {{ rec.recommendation }}</p>
        <p><strong>Rationale:</strong> {{ rec.rationale }}</p>
    </div>
    {% endfor %}

    <div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #666;">
        <p>This report was automatically generated by the Geopolitical Intelligence System.</p>
        <p>For questions or additional analysis, contact the intelligence team.</p>
    </div>
</body>
</html>
            """
            
            template_path = self.template_dir / 'executive_report.html'
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
            
            logger.info("Default report templates created")
            
        except Exception as e:
            logger.error(f"Error creating default templates: {e}")


# Import torch for CUDA check
try:
    import torch
except ImportError:
    torch = None