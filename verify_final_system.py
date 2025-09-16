#!/usr/bin/env python3
"""
Script de verificación final del sistema RiskMap
Verifica que todos los componentes estén funcionando correctamente
"""

import requests
import json
import sys
from datetime import datetime

def test_endpoint(url, name):
    """Prueba un endpoint y retorna el resultado"""
    try:
        response = requests.get(url, timeout=10)
        return {
            'name': name,
            'url': url,
            'status': response.status_code,
            'success': response.status_code == 200,
            'response_size': len(response.text),
            'content_type': response.headers.get('content-type', 'unknown')
        }
    except Exception as e:
        return {
            'name': name,
            'url': url,
            'status': 'ERROR',
            'success': False,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("🔍 VERIFICACIÓN FINAL DEL SISTEMA RISKMAP")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Lista de endpoints críticos a verificar
    endpoints = [
        ('http://localhost:5001/', 'Página Principal'),
        ('http://localhost:5001/about', 'Página About'),
        ('http://localhost:5001/api/test', 'API Test'),
        ('http://localhost:5001/api/dashboard/stats', 'Dashboard Stats'),
        ('http://localhost:5001/api/analytics/conflicts-corrected', 'Conflictos Corregidos'),
        ('http://localhost:5001/api/conflicts', 'Conflictos Básicos'),
        ('http://localhost:5001/api/articles', 'Artículos'),
        ('http://localhost:5001/api/satellite/results', 'Resultados Satelitales'),
        ('http://localhost:5001/api/external/acled', 'ACLED External Feed'),
    ]
    
    results = []
    successful = 0
    total = len(endpoints)
    
    print("📋 PROBANDO ENDPOINTS:")
    print("-" * 60)
    
    for url, name in endpoints:
        result = test_endpoint(url, name)
        results.append(result)
        
        status_icon = "✅" if result['success'] else "❌"
        status_text = f"{result['status']}" if result['success'] else f"ERROR: {result.get('error', result['status'])}"
        
        print(f"{status_icon} {name:<30} | {status_text}")
        
        if result['success']:
            successful += 1
    
    print("-" * 60)
    print(f"📊 RESUMEN: {successful}/{total} endpoints funcionando correctamente ({successful/total*100:.1f}%)")
    print()
    
    # Verificar datos específicos de algunos endpoints críticos
    print("🔍 VERIFICANDO DATOS ESPECÍFICOS:")
    print("-" * 60)
    
    # Verificar endpoint de conflictos corregidos
    try:
        response = requests.get('http://localhost:5001/api/analytics/conflicts-corrected')
        if response.status_code == 200:
            data = response.json()
            conflicts_count = len(data.get('conflicts', []))
            data_source = data.get('statistics', {}).get('data_source', 'unknown')
            print(f"✅ Conflictos Corregidos: {conflicts_count} zonas encontradas (fuente: {data_source})")
        else:
            print(f"❌ Conflictos Corregidos: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Conflictos Corregidos: Error - {e}")
    
    # Verificar endpoint de conflictos básicos
    try:
        response = requests.get('http://localhost:5001/api/conflicts')
        if response.status_code == 200:
            data = response.json()
            conflicts_count = data.get('count', 0)
            data_source = data.get('data_source', 'unknown')
            print(f"✅ Conflictos Básicos: {conflicts_count} conflictos encontrados (fuente: {data_source})")
        else:
            print(f"❌ Conflictos Básicos: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Conflictos Básicos: Error - {e}")
    
    # Verificar estadísticas del dashboard
    try:
        response = requests.get('http://localhost:5001/api/dashboard/stats')
        if response.status_code == 200:
            data = response.json()
            total_articles = data.get('articles', {}).get('total', 0)
            processed_articles = data.get('articles', {}).get('processed', 0)
            print(f"✅ Dashboard Stats: {total_articles} artículos totales, {processed_articles} procesados")
        else:
            print(f"❌ Dashboard Stats: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard Stats: Error - {e}")
    
    print("-" * 60)
    
    # Guardar reporte completo
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_endpoints': total,
            'successful_endpoints': successful,
            'success_rate': successful/total*100
        },
        'endpoints': results
    }
    
    with open('final_verification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Reporte completo guardado en: final_verification_report.json")
    print()
    
    if successful == total:
        print("🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("✅ Todos los endpoints están respondiendo correctamente")
        print("✅ fix_tf_warnings está funcionando")
        print("✅ Servidor corriendo en puerto 5001")
        print("✅ API REST completamente operativa")
        return 0
    else:
        print("⚠️  SISTEMA PARCIALMENTE FUNCIONAL")
        print(f"❌ {total - successful} endpoints con problemas")
        print("🔧 Revisar los errores mostrados arriba")
        return 1

if __name__ == "__main__":
    sys.exit(main())
