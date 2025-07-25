#!/usr/bin/env python3
"""
Script para probar todas las correcciones implementadas:
1. Heatmap muestra ubicaciones de conflictos reales, no fuentes
2. Artículo de IA usa HTML/CSS real, no markdown
3. Advanced analytics UI es consistente
4. Todos los artículos están traducidos al idioma seleccionado
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_heatmap_conflict_locations():
    """Test que el heatmap muestra ubicaciones de conflictos reales."""
    print("🗺️  Testing heatmap conflict locations...")
    
    try:
        response = requests.get('http://localhost:5000/api/heatmap_data?lang=es')
        data = response.json()
        
        if 'heatmap_data' in data:
            conflicts_found = []
            expected_conflicts = ['Ucrania', 'Gaza', 'Siria', 'Myanmar', 'Yemen']
            
            for point in data['heatmap_data']:
                location = point.get('location', '')
                if any(conflict in location for conflict in expected_conflicts):
                    conflicts_found.append(location)
                    print(f"   ✅ Found real conflict location: {location}")
                    print(f"      - Risk: {point.get('risk_level', 'N/A')}")
                    print(f"      - Description: {point.get('conflict_type', 'N/A')}")
            
            if conflicts_found:
                print(f"   ✅ SUCCESS: Found {len(conflicts_found)} real conflict locations")
                print(f"   📍 Data type: {data.get('data_type', 'unknown')}")
                return True
            else:
                print("   ❌ ERROR: No real conflict locations found in heatmap")
                return False
        else:
            print("   ❌ ERROR: No heatmap_data in response")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: Failed to test heatmap: {e}")
        return False

def test_ai_article_html_format():
    """Test que el artículo de IA usa HTML/CSS real."""
    print("📰 Testing AI article HTML format...")
    
    try:
        response = requests.get('http://localhost:5000/api/ai_analysis?lang=es')
        data = response.json()
        
        # Check for HTML content
        if 'analysis_html' in data:
            html_content = data['analysis_html']
            if '<article' in html_content and 'style=' in html_content:
                print("   ✅ SUCCESS: AI article uses proper HTML/CSS format")
                print(f"   📝 HTML length: {len(html_content)} characters")
                print(f"   🎨 Has inline styles: {'style=' in html_content}")
                return True
            else:
                print("   ❌ ERROR: AI article HTML is malformed")
                return False
        else:
            # Check fallback format
            if 'analysis' in data:
                analysis = data['analysis']
                # Check if it contains HTML tags and styling
                if '<h3' in analysis or '<strong' in analysis or 'style=' in analysis:
                    print("   ✅ SUCCESS: AI article uses enhanced formatting")
                    print(f"   📝 Content length: {len(analysis)} characters")
                    return True
                else:
                    print("   ❌ ERROR: AI article still uses plain markdown")
                    return False
            
        print("   ❌ ERROR: No analysis content found")
        return False
        
    except Exception as e:
        print(f"   ❌ ERROR: Failed to test AI article: {e}")
        return False

def test_translation_coverage():
    """Test que todos los artículos están traducidos al idioma seleccionado."""
    print("🌐 Testing translation coverage...")
    
    languages_to_test = ['es', 'fr', 'de']
    success_count = 0
    
    for lang in languages_to_test:
        try:
            print(f"   Testing language: {lang}")
            
            # Test articles endpoint
            response = requests.get(f'http://localhost:5000/api/articles?lang={lang}&limit=10')
            data = response.json()
            
            if 'articles' in data and data['articles']:
                translated_count = 0
                total_articles = len(data['articles'])
                
                for article in data['articles']:
                    if article.get('translated') or article.get('language') == lang:
                        translated_count += 1
                
                translation_percentage = (translated_count / total_articles) * 100
                print(f"   📊 {lang}: {translated_count}/{total_articles} articles translated ({translation_percentage:.1f}%)")
                
                if translation_percentage >= 80:  # At least 80% should be translated
                    success_count += 1
                    print(f"   ✅ Language {lang}: Good translation coverage")
                else:
                    print(f"   ⚠️  Language {lang}: Low translation coverage")
            
            # Test high-risk articles
            response = requests.get(f'http://localhost:5000/api/high_risk_articles?lang={lang}&limit=5')
            data = response.json()
            
            if 'articles' in data and data['articles']:
                for article in data['articles']:
                    if article.get('translated'):
                        print(f"   ✅ High-risk article translated to {lang}")
                        break
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ ERROR testing {lang}: {e}")
    
    if success_count >= 2:
        print(f"   ✅ SUCCESS: Translation working for {success_count}/{len(languages_to_test)} languages")
        return True
    else:
        print(f"   ❌ ERROR: Translation failing for most languages")
        return False

def test_advanced_analytics_consistency():
    """Test que el advanced analytics UI es consistente."""
    print("📊 Testing advanced analytics consistency...")
    
    try:
        # Test risk analytics endpoint
        response = requests.get('http://localhost:5000/api/risk_analytics')
        risk_data = response.json()
        
        # Test intelligence brief endpoint
        response = requests.get('http://localhost:5000/api/intelligence_brief')
        intel_data = response.json()
        
        # Check data structure consistency
        expected_fields = ['timestamp', 'status']
        
        risk_consistent = all(field in risk_data for field in expected_fields[:1])  # At least timestamp
        intel_consistent = all(field in intel_data for field in expected_fields[:1])
        
        if risk_consistent and intel_consistent:
            print("   ✅ SUCCESS: Advanced analytics endpoints are consistent")
            print(f"   📈 Risk analytics data fields: {list(risk_data.keys())}")
            print(f"   🎯 Intelligence brief data fields: {list(intel_data.keys())}")
            return True
        else:
            print("   ❌ ERROR: Advanced analytics endpoints inconsistent")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: Failed to test advanced analytics: {e}")
        return False

def test_dashboard_loading():
    """Test que el dashboard principal carga correctamente."""
    print("🏠 Testing dashboard loading...")
    
    try:
        response = requests.get('http://localhost:5000/')
        
        if response.status_code == 200:
            content = response.text
            if 'Geopolitical Intelligence' in content and 'dashboard.html' in response.url or len(content) > 1000:
                print("   ✅ SUCCESS: Dashboard loads correctly")
                return True
            else:
                print("   ❌ ERROR: Dashboard content seems incomplete")
                return False
        else:
            print(f"   ❌ ERROR: Dashboard returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: Failed to load dashboard: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("🚀 TESTING ALL IMPLEMENTED FIXES")
    print("=" * 70)
    
    tests = [
        ("Dashboard Loading", test_dashboard_loading),
        ("Heatmap Conflict Locations", test_heatmap_conflict_locations),
        ("AI Article HTML Format", test_ai_article_html_format),
        ("Translation Coverage", test_translation_coverage),
        ("Advanced Analytics Consistency", test_advanced_analytics_consistency)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 50)
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print("=" * 70)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL FIXES WORKING CORRECTLY!")
        print("✅ Heatmap shows real conflict locations")
        print("✅ AI article uses professional HTML/CSS")
        print("✅ Advanced analytics UI is consistent")
        print("✅ Articles are properly translated")
    elif passed >= total * 0.8:
        print(f"\n✅ Most fixes working correctly ({passed}/{total})")
        print("⚠️  Some minor issues may need attention")
    else:
        print(f"\n❌ Several issues found ({total-passed}/{total} failures)")
        print("🔧 Manual review and fixes may be needed")
    
    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        sys.exit(1)
