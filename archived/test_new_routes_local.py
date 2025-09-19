#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar las nuevas rutas API localmente
"""

import sys
sys.path.append('.')

import requests
import json
from datetime import datetime

# Rutas a verificar - Las que están fallando
new_routes = [
    '/api/v1/docs',
    '/api/conflict-regions', 
    '/api/satellite-data',
    '/api/gdelt-events',
    '/api/external-feeds',
    '/api/analytics/summary',
    '/api/analytics/sentiment'
]

base_url = "http://localhost:5001"

def test_route(route):
    """Probar una ruta específica"""
    try:
        response = requests.get(f"{base_url}{route}", timeout=30)
        
        print(f"\n🔍 Testing: {route}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS - Size: {len(response.content)} bytes")
                
                # Mostrar claves principales del JSON
                if isinstance(data, dict):
                    print(f"   📊 Keys: {list(data.keys())}")
                    
                    # Mostrar información específica por endpoint
                    if 'success' in data and data['success']:
                        print(f"   ✅ API Success: True")
                        
                        # Información específica por tipo de endpoint
                        if route == '/api/conflict-regions' and 'conflict_regions' in data:
                            print(f"   📊 Regions found: {len(data['conflict_regions'])}")
                        elif route == '/api/gdelt-events' and 'gdelt_events' in data:
                            print(f"   📊 Events found: {len(data['gdelt_events'])}")
                        elif route == '/api/analytics/summary' and 'analytics_summary' in data:
                            summary = data['analytics_summary']
                            print(f"   📊 Total articles: {summary.get('total_articles', 0)}")
                        elif route == '/api/analytics/sentiment' and 'sentiment_analysis' in data:
                            sentiment = data['sentiment_analysis']
                            print(f"   📊 Sentiments analyzed: {sentiment.get('total_analyzed', 0)}")
                        elif route == '/api/external-feeds' and 'external_feeds' in data:
                            feeds = data['external_feeds']
                            print(f"   📊 Active feeds: {feeds.get('total_sources', 0)}")
                        elif route == '/api/satellite-data' and 'satellite_data' in data:
                            satellite = data['satellite_data']
                            print(f"   📊 Provider: {satellite.get('provider', 'Unknown')}")
                        elif route == '/api/v1/docs':
                            endpoints = data.get('endpoints', {})
                            total_endpoints = sum(len(group.keys()) for group in endpoints.values())
                            print(f"   📊 Documented endpoints: {total_endpoints}")
                    
            except json.JSONDecodeError:
                print(f"   ✅ SUCCESS - HTML/Text response - Size: {len(response.content)} bytes")
                
        elif response.status_code == 404:
            print(f"   ❌ FAILED: 404 - Route not found")
        elif response.status_code == 500:
            print(f"   ❌ FAILED: 500 - Internal server error")
            try:
                error_data = response.json()
                print(f"   🔍 Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   🔍 Raw error: {response.text[:200]}...")
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.reason}")
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ TIMEOUT - Route took longer than 30 seconds")
    except requests.exceptions.ConnectionError:
        print(f"   🔌 CONNECTION ERROR - Server may not be running")
    except Exception as e:
        print(f"   ❌ ERROR - {str(e)}")

def main():
    print("="*60)
    print("🧪 TESTING NEW ROUTES LOCALLY")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {base_url}")
    print(f"📋 Testing {len(new_routes)} new routes")
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️  Server status: {response.status_code}")
    except:
        print("❌ Server not responding - make sure it's running on port 5001")
        return
    
    print("\n" + "="*60)
    print("🚀 TESTING NEW ROUTES")
    print("="*60)
    
    success_count = 0
    
    # Probar cada ruta nueva
    for route in new_routes:
        test_route(route)
        
        # Verificar si fue exitosa
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            if response.status_code == 200:
                success_count += 1
        except:
            pass
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"✅ Routes working: {success_count}/{len(new_routes)}")
    print(f"📊 Success rate: {(success_count/len(new_routes)*100):.1f}%")
    
    if success_count == len(new_routes):
        print("\n🎉 All new routes are working correctly!")
    elif success_count > 0:
        print(f"\n⚠️  {len(new_routes)-success_count} routes still need to be fixed")
    else:
        print("\n❌ All new routes are failing - server may need restart")

if __name__ == "__main__":
    main()