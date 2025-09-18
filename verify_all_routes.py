#!/usr/bin/env python3
"""
Script para verificar sistemáticamente todos los routes del sistema RiskMap
y validar que funcionan correctamente con datos reales.
"""
import requests
import json
import sys
from datetime import datetime

# Base URL del servidor (asumiendo que está corriendo en localhost:5001)
BASE_URL = "http://localhost:5001"

# Lista de todos los routes a verificar
ROUTES_TO_TEST = [
    # Routes principales
    {'path': '/', 'name': 'Página Principal', 'method': 'GET'},
    {'path': '/about', 'name': 'Página About', 'method': 'GET'},
    
    # API Routes para artículos
    {'path': '/api/articles', 'name': 'API Artículos', 'method': 'GET'},
    {'path': '/api/hero-article', 'name': 'API Artículo Hero', 'method': 'GET'},
    {'path': '/api/articles/deduplicated', 'name': 'API Artículos Deduplicados', 'method': 'GET'},
    
    # API Routes para sistema
    {'path': '/api/status', 'name': 'API Status Sistema', 'method': 'GET'},
    {'path': '/api/v1/docs', 'name': 'API Documentación', 'method': 'GET'},
    
    # Dashboard routes
    {'path': '/dashboard', 'name': 'Dashboard Histórico', 'method': 'GET'},
    {'path': '/multivariate', 'name': 'Análisis Multivariable', 'method': 'GET'},
    
    # Conflict monitoring
    {'path': '/conflict-monitoring', 'name': 'Monitoreo de Conflictos', 'method': 'GET'},
    {'path': '/api/conflict-regions', 'name': 'API Regiones de Conflicto', 'method': 'GET'},
    {'path': '/api/satellite-data', 'name': 'API Datos Satelitales', 'method': 'GET'},
    
    # GDELT and external data
    {'path': '/api/gdelt-events', 'name': 'API Eventos GDELT', 'method': 'GET'},
    {'path': '/api/external-feeds', 'name': 'API Feeds Externos', 'method': 'GET'},
    
    # Analytics routes
    {'path': '/api/analytics/summary', 'name': 'API Resumen Analytics', 'method': 'GET'},
    {'path': '/api/analytics/trends', 'name': 'API Tendencias', 'method': 'GET'},
    {'path': '/api/analytics/sentiment', 'name': 'API Análisis Sentimientos', 'method': 'GET'},
]

class RouteVerifier:
    def __init__(self):
        self.results = []
        self.working_routes = 0
        self.failing_routes = 0
        
    def test_route(self, route_info):
        """Test a single route and return results"""
        try:
            url = f"{BASE_URL}{route_info['path']}"
            print(f"🔍 Testing: {route_info['name']} ({route_info['path']})")
            
            response = requests.get(url, timeout=10)
            
            result = {
                'name': route_info['name'],
                'path': route_info['path'],
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'content_type': response.headers.get('content-type', 'unknown'),
                'content_length': len(response.content),
                'error': None
            }
            
            # Check if it's JSON and try to parse
            if 'application/json' in result['content_type']:
                try:
                    json_data = response.json()
                    result['json_valid'] = True
                    result['has_data'] = bool(json_data)
                    
                    # Check for specific data patterns
                    if isinstance(json_data, dict):
                        if 'articles' in json_data:
                            result['articles_count'] = len(json_data.get('articles', []))
                        elif 'data' in json_data:
                            result['data_count'] = len(json_data.get('data', []))
                        elif isinstance(json_data, list):
                            result['items_count'] = len(json_data)
                    
                except json.JSONDecodeError:
                    result['json_valid'] = False
            
            # Check content for mock data indicators
            content_text = response.text.lower()
            mock_indicators = ['mock', 'placeholder', 'fake', 'test data', 'lorem ipsum']
            result['has_mock_data'] = any(indicator in content_text for indicator in mock_indicators)
            
            if result['success']:
                self.working_routes += 1
                print(f"   ✅ SUCCESS: {result['status_code']} - {result['content_length']} bytes")
                if result.get('articles_count'):
                    print(f"      📊 Contains {result['articles_count']} articles")
                if result.get('has_mock_data'):
                    print(f"      ⚠️  WARNING: Contains potential mock data")
            else:
                self.failing_routes += 1
                print(f"   ❌ FAILED: {result['status_code']}")
                
        except requests.exceptions.RequestException as e:
            result = {
                'name': route_info['name'],
                'path': route_info['path'],
                'success': False,
                'error': str(e)
            }
            self.failing_routes += 1
            print(f"   ❌ ERROR: {e}")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self):
        """Run all route tests"""
        print("=" * 60)
        print("🚀 INICIANDO VERIFICACIÓN COMPLETA DE ROUTES")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {BASE_URL}")
        print(f"📋 Total routes a verificar: {len(ROUTES_TO_TEST)}")
        print()
        
        for i, route in enumerate(ROUTES_TO_TEST, 1):
            print(f"[{i}/{len(ROUTES_TO_TEST)}] ", end="")
            self.test_route(route)
            print()
        
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("=" * 60)
        print("📊 REPORTE FINAL DE VERIFICACIÓN")
        print("=" * 60)
        
        print(f"✅ Routes funcionando: {self.working_routes}")
        print(f"❌ Routes fallando: {self.failing_routes}")
        print(f"📊 Tasa de éxito: {(self.working_routes/len(ROUTES_TO_TEST)*100):.1f}%")
        print()
        
        # Working routes
        working = [r for r in self.results if r.get('success')]
        if working:
            print("✅ ROUTES FUNCIONANDO CORRECTAMENTE:")
            for route in working:
                status = f"({route['status_code']})" if 'status_code' in route else ""
                mock_warning = " ⚠️ MOCK DATA" if route.get('has_mock_data') else ""
                print(f"   ✓ {route['name']} {status}{mock_warning}")
        
        print()
        
        # Failing routes
        failing = [r for r in self.results if not r.get('success')]
        if failing:
            print("❌ ROUTES CON PROBLEMAS:")
            for route in failing:
                error_info = f"- {route.get('error', 'Status: ' + str(route.get('status_code', 'Unknown')))}"
                print(f"   ✗ {route['name']}: {error_info}")
        
        print()
        
        # Data quality analysis
        routes_with_data = [r for r in self.results if r.get('has_data')]
        routes_with_mock = [r for r in self.results if r.get('has_mock_data')]
        
        print("📈 ANÁLISIS DE CALIDAD DE DATOS:")
        print(f"   📊 Routes con datos reales: {len(routes_with_data)}")
        print(f"   ⚠️  Routes con posibles datos simulados: {len(routes_with_mock)}")
        
        if routes_with_mock:
            print("   🔍 Routes que requieren revisión por datos simulados:")
            for route in routes_with_mock:
                print(f"      - {route['name']}")
        
        print()
        print("=" * 60)
        
        # Return summary for further processing
        return {
            'total': len(ROUTES_TO_TEST),
            'working': self.working_routes,
            'failing': self.failing_routes,
            'success_rate': self.working_routes/len(ROUTES_TO_TEST)*100,
            'routes_with_mock': len(routes_with_mock),
            'needs_attention': failing + routes_with_mock
        }

def main():
    print("RiskMap Routes Verification Tool")
    print("Verificando que el servidor esté ejecutándose...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        print(f"✅ Servidor detectado - Status: {response.status_code}")
    except requests.exceptions.RequestException:
        print(f"❌ Error: Servidor no encontrado en {BASE_URL}")
        print("   Asegúrate de que app_BUENA.py esté ejecutándose en el puerto 5001")
        sys.exit(1)
    
    verifier = RouteVerifier()
    summary = verifier.run_all_tests()
    
    # Exit with error if there are critical failures
    if summary and summary['failing'] > 0:
        print(f"⚠️  Se encontraron {summary['failing']} routes con problemas que requieren atención.")
        return summary['failing']
    elif summary:
        print("🎉 Todos los routes están funcionando correctamente!")
        return 0
    else:
        print("❌ Error en la verificación")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)