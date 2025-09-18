#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕵️ NAVEGADOR SISTEMÁTICO DEL WEBSITE RISKMAP
================================================================
Script para navegar por todas las páginas del website como un usuario
e identificar problemas, errores y funcionalidades que no funcionan.
"""

import requests
import json
import re
from datetime import datetime
from urllib.parse import urljoin
import time
from bs4 import BeautifulSoup

class WebsiteNavigator:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.problems = []
        self.visited_pages = {}
        self.session = requests.Session()
        self.session.timeout = 30
        
    def log_problem(self, page, problem_type, description, severity="medium"):
        """Registrar un problema encontrado"""
        problem = {
            'page': page,
            'type': problem_type,
            'description': description,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        self.problems.append(problem)
        print(f"   🔴 {severity.upper()}: {problem_type} - {description}")
        
    def log_success(self, message):
        """Registrar un éxito"""
        print(f"   ✅ {message}")
        
    def test_page(self, path, page_name):
        """Probar una página específica"""
        print(f"\n🔍 TESTING: {page_name} ({path})")
        print("-" * 60)
        
        try:
            url = urljoin(self.base_url, path)
            response = self.session.get(url)
            
            # Registrar información básica
            self.visited_pages[path] = {
                'name': page_name,
                'status': response.status_code,
                'size': len(response.content),
                'content_type': response.headers.get('content-type', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            if response.status_code != 200:
                self.log_problem(page_name, "HTTP_ERROR", 
                               f"Status code: {response.status_code}", "high")
                return False
                
            self.log_success(f"Page loads successfully (Status: {response.status_code})")
            self.log_success(f"Content size: {len(response.content)} bytes")
            
            # Verificar contenido HTML
            if 'text/html' in response.headers.get('content-type', ''):
                return self._analyze_html_page(response.text, page_name, path)
            elif 'application/json' in response.headers.get('content-type', ''):
                return self._analyze_json_response(response.json(), page_name, path)
            else:
                self.log_success(f"Content type: {response.headers.get('content-type', 'unknown')}")
                
            return True
            
        except requests.exceptions.Timeout:
            self.log_problem(page_name, "TIMEOUT", "Page took longer than 30 seconds", "high")
            return False
        except requests.exceptions.ConnectionError:
            self.log_problem(page_name, "CONNECTION_ERROR", "Cannot connect to server", "critical")
            return False
        except Exception as e:
            self.log_problem(page_name, "UNEXPECTED_ERROR", str(e), "high")
            return False
            
    def _analyze_html_page(self, html_content, page_name, path):
        """Analizar una página HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Verificar título
            title = soup.find('title')
            if title:
                self.log_success(f"Title: {title.get_text().strip()}")
            else:
                self.log_problem(page_name, "MISSING_TITLE", "No title tag found", "low")
                
            # Verificar errores JavaScript en el HTML
            if 'Error' in html_content and 'javascript' in html_content.lower():
                self.log_problem(page_name, "JAVASCRIPT_ERROR", "Potential JavaScript error in HTML", "medium")
                
            # Verificar elementos críticos
            self._check_critical_elements(soup, page_name)
            
            # Verificar enlaces rotos
            self._check_links(soup, page_name, path)
            
            # Verificar contenido específico por página
            if path == '/':
                return self._analyze_main_page(soup, page_name)
            elif path == '/about':
                return self._analyze_about_page(soup, page_name)
            elif path == '/conflict-monitoring':
                return self._analyze_conflict_monitoring(soup, page_name)
            elif path == '/dashboard':
                return self._analyze_dashboard_page(soup, page_name)
            elif path == '/multivariate':
                return self._analyze_multivariate_page(soup, page_name)
                
            return True
            
        except Exception as e:
            self.log_problem(page_name, "HTML_PARSING_ERROR", str(e), "medium")
            return False
            
    def _analyze_json_response(self, json_data, page_name, path):
        """Analizar una respuesta JSON (API)"""
        try:
            # Verificar estructura básica
            if isinstance(json_data, dict):
                self.log_success(f"Valid JSON response with {len(json_data)} keys")
                
                # Verificar campos comunes
                if 'success' in json_data:
                    if json_data['success']:
                        self.log_success("API reports success: True")
                    else:
                        self.log_problem(page_name, "API_ERROR", 
                                       f"API reports success: False - {json_data.get('error', 'Unknown error')}", "high")
                        return False
                        
                # Verificar contenido de datos
                data_fields = ['data', 'articles', 'conflict_regions', 'gdelt_events', 
                             'external_feeds', 'analytics_summary', 'sentiment_analysis']
                
                found_data = False
                for field in data_fields:
                    if field in json_data:
                        data_content = json_data[field]
                        if isinstance(data_content, list):
                            self.log_success(f"Data field '{field}': {len(data_content)} items")
                        elif isinstance(data_content, dict):
                            self.log_success(f"Data field '{field}': {len(data_content)} keys")
                        else:
                            self.log_success(f"Data field '{field}': {type(data_content).__name__}")
                        found_data = True
                        
                if not found_data:
                    self.log_problem(page_name, "NO_DATA", "No data content found in API response", "medium")
                    
            elif isinstance(json_data, list):
                self.log_success(f"Valid JSON array with {len(json_data)} items")
            else:
                self.log_problem(page_name, "INVALID_JSON_STRUCTURE", 
                               f"Unexpected JSON structure: {type(json_data)}", "medium")
                
            return True
            
        except Exception as e:
            self.log_problem(page_name, "JSON_ANALYSIS_ERROR", str(e), "medium")
            return False
            
    def _check_critical_elements(self, soup, page_name):
        """Verificar elementos críticos de la página"""
        # Verificar CSS
        css_links = soup.find_all('link', {'rel': 'stylesheet'})
        if css_links:
            self.log_success(f"Found {len(css_links)} CSS files")
        else:
            self.log_problem(page_name, "MISSING_CSS", "No CSS stylesheets found", "medium")
            
        # Verificar JavaScript
        js_scripts = soup.find_all('script')
        if js_scripts:
            self.log_success(f"Found {len(js_scripts)} JavaScript files")
        else:
            self.log_problem(page_name, "MISSING_JS", "No JavaScript files found", "low")
            
        # Verificar navegación
        nav = soup.find('nav') or soup.find('navbar')
        if nav:
            self.log_success("Navigation menu found")
        else:
            self.log_problem(page_name, "MISSING_NAVIGATION", "No navigation menu found", "medium")
            
    def _check_links(self, soup, page_name, current_path):
        """Verificar enlaces internos"""
        links = soup.find_all('a', href=True)
        internal_links = []
        
        for link in links:
            href = link['href']
            if href.startswith('/') or href.startswith(self.base_url):
                internal_links.append(href)
                
        if internal_links:
            self.log_success(f"Found {len(internal_links)} internal links")
            
            # Probar algunos enlaces críticos
            critical_links = ['/about', '/dashboard', '/multivariate', '/conflict-monitoring']
            for link_path in critical_links:
                if any(link_path in link for link in internal_links):
                    self.log_success(f"Critical link '{link_path}' found in navigation")
                else:
                    self.log_problem(page_name, "MISSING_LINK", 
                                   f"Critical link '{link_path}' not found", "medium")
        else:
            self.log_problem(page_name, "NO_INTERNAL_LINKS", "No internal links found", "low")
            
    def _analyze_main_page(self, soup, page_name):
        """Análisis específico de la página principal"""
        # Verificar elementos del dashboard
        dashboard_elements = soup.find_all(class_=lambda x: x and ('card' in x or 'dashboard' in x))
        if dashboard_elements:
            self.log_success(f"Found {len(dashboard_elements)} dashboard elements")
        else:
            self.log_problem(page_name, "MISSING_DASHBOARD_ELEMENTS", 
                           "No dashboard elements found", "medium")
            
        # Verificar si hay datos de demostración/mockup
        text_content = soup.get_text().lower()
        mockup_indicators = ['lorem ipsum', 'ejemplo', 'demo', 'placeholder', 'test data', 'mock']
        
        for indicator in mockup_indicators:
            if indicator in text_content:
                self.log_problem(page_name, "MOCK_DATA", 
                               f"Potential mock data detected: '{indicator}'", "medium")
                break
        else:
            self.log_success("No obvious mock data indicators found")
            
        return True
        
    def _analyze_about_page(self, soup, page_name):
        """Análisis específico de la página About"""
        # Verificar que mencione Google Maps (no SentinelHub)
        text_content = soup.get_text()
        
        if 'Google Maps' in text_content:
            self.log_success("References to Google Maps found (correct)")
        else:
            self.log_problem(page_name, "MISSING_GOOGLE_MAPS", 
                           "No references to Google Maps satellite system", "low")
            
        if 'SentinelHub' in text_content:
            self.log_problem(page_name, "OLD_SENTINEL_REFERENCE", 
                           "Old SentinelHub references still present", "high")
            
        # Verificar secciones clave
        key_sections = ['pipeline', 'tecnología', 'análisis', 'geopolítico']
        found_sections = 0
        
        for section in key_sections:
            if section.lower() in text_content.lower():
                found_sections += 1
                
        if found_sections >= 3:
            self.log_success(f"Key content sections found: {found_sections}/{len(key_sections)}")
        else:
            self.log_problem(page_name, "MISSING_CONTENT", 
                           f"Only {found_sections}/{len(key_sections)} key sections found", "medium")
            
        return True
        
    def _analyze_conflict_monitoring(self, soup, page_name):
        """Análisis específico de la página de monitoreo de conflictos"""
        # Verificar elementos de monitoreo
        monitoring_elements = soup.find_all(class_=lambda x: x and ('conflict' in x or 'monitoring' in x or 'alert' in x))
        
        if monitoring_elements:
            self.log_success(f"Found {len(monitoring_elements)} monitoring elements")
        else:
            self.log_problem(page_name, "MISSING_MONITORING_ELEMENTS", 
                           "No monitoring elements found", "high")
            
        return True
        
    def _analyze_dashboard_page(self, soup, page_name):
        """Análisis específico del dashboard histórico"""
        # Esta página puede usar Dash, verificar si carga correctamente
        text_content = soup.get_text()
        
        if 'dash' in text_content.lower() or 'plotly' in text_content.lower():
            self.log_success("Dash/Plotly components detected")
        
        # Verificar si hay errores de Dash
        if '404' in text_content or 'not found' in text_content.lower():
            self.log_problem(page_name, "DASH_ERROR", "Dash application may not be working", "high")
            
        return True
        
    def _analyze_multivariate_page(self, soup, page_name):
        """Análisis específico del análisis multivariable"""
        # Similar al dashboard, verificar Dash
        text_content = soup.get_text()
        
        if 'multivariate' in text_content.lower() or 'correlación' in text_content.lower():
            self.log_success("Multivariate analysis content detected")
        else:
            self.log_problem(page_name, "MISSING_MULTIVARIATE_CONTENT", 
                           "No multivariate analysis content found", "medium")
            
        return True
        
    def test_api_endpoints(self):
        """Probar todos los endpoints de la API"""
        print(f"\n🚀 TESTING API ENDPOINTS")
        print("=" * 60)
        
        api_endpoints = [
            ('/api/status', 'API Status'),
            ('/api/articles', 'Articles API'),
            ('/api/hero-article', 'Hero Article API'),
            ('/api/articles/deduplicated', 'Deduplicated Articles API'),
            ('/api/v1/docs', 'API Documentation'),
            ('/api/conflict-regions', 'Conflict Regions API'),
            ('/api/satellite-data', 'Satellite Data API'),
            ('/api/gdelt-events', 'GDELT Events API'),
            ('/api/external-feeds', 'External Feeds API'),
            ('/api/analytics/summary', 'Analytics Summary API'),
            ('/api/analytics/sentiment', 'Sentiment Analysis API'),
            ('/api/analytics/trends', 'Trends API')
        ]
        
        api_success_count = 0
        
        for endpoint, name in api_endpoints:
            if self.test_page(endpoint, name):
                api_success_count += 1
                
        print(f"\n📊 API SUMMARY: {api_success_count}/{len(api_endpoints)} endpoints working")
        return api_success_count, len(api_endpoints)
        
    def run_full_navigation(self):
        """Ejecutar navegación completa del sitio web"""
        print("🕵️ INICIANDO NAVEGACIÓN COMPLETA DEL WEBSITE RISKMAP")
        print("=" * 80)
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {self.base_url}")
        print()
        
        # Páginas principales a probar
        main_pages = [
            ('/', 'Página Principal'),
            ('/about', 'Acerca de'),
            ('/conflict-monitoring', 'Monitoreo de Conflictos'),
            ('/dashboard', 'Dashboard Histórico'),
            ('/multivariate', 'Análisis Multivariable'),
        ]
        
        print("🏠 TESTING MAIN PAGES")
        print("=" * 40)
        
        main_success_count = 0
        for path, name in main_pages:
            if self.test_page(path, name):
                main_success_count += 1
                
        # Probar APIs
        api_success_count, total_apis = self.test_api_endpoints()
        
        # Generar reporte final
        self.generate_report(main_success_count, len(main_pages), api_success_count, total_apis)
        
    def generate_report(self, main_success, total_main, api_success, total_api):
        """Generar reporte final"""
        print(f"\n🏁 REPORTE FINAL DE NAVEGACIÓN")
        print("=" * 80)
        print(f"📊 PÁGINAS PRINCIPALES: {main_success}/{total_main} funcionando ({main_success/total_main*100:.1f}%)")
        print(f"🔌 API ENDPOINTS: {api_success}/{total_api} funcionando ({api_success/total_api*100:.1f}%)")
        print(f"🐛 PROBLEMAS ENCONTRADOS: {len(self.problems)}")
        
        # Clasificar problemas por severidad
        critical_problems = [p for p in self.problems if p['severity'] == 'critical']
        high_problems = [p for p in self.problems if p['severity'] == 'high']
        medium_problems = [p for p in self.problems if p['severity'] == 'medium']
        low_problems = [p for p in self.problems if p['severity'] == 'low']
        
        print(f"\n🚨 PROBLEMAS POR SEVERIDAD:")
        print(f"   🔴 Critical: {len(critical_problems)}")
        print(f"   🟠 High: {len(high_problems)}")  
        print(f"   🟡 Medium: {len(medium_problems)}")
        print(f"   🟢 Low: {len(low_problems)}")
        
        if self.problems:
            print(f"\n📋 LISTA DETALLADA DE PROBLEMAS:")
            print("-" * 50)
            for i, problem in enumerate(self.problems, 1):
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠', 
                    'medium': '🟡',
                    'low': '🟢'
                }
                emoji = severity_emoji.get(problem['severity'], '⚪')
                print(f"{i:2d}. {emoji} {problem['page']} - {problem['type']}")
                print(f"     {problem['description']}")
                
        # Guardar reporte en archivo
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'main_pages': {'success': main_success, 'total': total_main},
                'api_endpoints': {'success': api_success, 'total': total_api},
                'total_problems': len(self.problems)
            },
            'visited_pages': self.visited_pages,
            'problems': self.problems
        }
        
        with open('navigation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n💾 Reporte detallado guardado en: navigation_report.json")
        
        # Mostrar estado general
        overall_success_rate = (main_success + api_success) / (total_main + total_api) * 100
        
        if overall_success_rate >= 90:
            print(f"\n🎉 ESTADO GENERAL: EXCELENTE ({overall_success_rate:.1f}%)")
        elif overall_success_rate >= 75:
            print(f"\n✅ ESTADO GENERAL: BUENO ({overall_success_rate:.1f}%)")
        elif overall_success_rate >= 50:
            print(f"\n⚠️  ESTADO GENERAL: NECESITA MEJORAS ({overall_success_rate:.1f}%)")
        else:
            print(f"\n❌ ESTADO GENERAL: CRÍTICO ({overall_success_rate:.1f}%)")
            
        return report_data

def main():
    navigator = WebsiteNavigator()
    report = navigator.run_full_navigation()
    
    # Retornar código de salida basado en problemas críticos
    critical_problems = [p for p in navigator.problems if p['severity'] == 'critical']
    return 1 if critical_problems else 0

if __name__ == "__main__":
    exit(main())