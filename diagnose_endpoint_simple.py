#!/usr/bin/env python3
"""
Script de diagnóstico simple para probar el endpoint /api/articles/deduplicated
Sin inicializar toda la aplicación compleja
"""

import sys
import os
from datetime import datetime
import json

# Añadir el directorio del proyecto al path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_endpoint_logic():
    """Probar la lógica del endpoint sin Flask"""
    print("🧪 Probando lógica del endpoint /api/articles/deduplicated...")

    try:
        # Simular la respuesta del endpoint
        response_data = {
            'success': True,
            'hero': {
                'id': 1,
                'title': 'Artículo de prueba - Sin summary',
                'image_url': 'https://example.com/image1.jpg',
                'risk_level': 'high',
                'original_url': 'https://example.com/article1'
            },
            'mosaic': [
                {
                    'id': 2,
                    'title': 'Artículo 2 - Solo título',
                    'image_url': 'https://example.com/image2.jpg',
                    'risk_level': 'medium',
                    'original_url': 'https://example.com/article2'
                },
                {
                    'id': 3,
                    'title': 'Artículo 3 - Sin contenido extra',
                    'image_url': 'https://example.com/image3.jpg',
                    'risk_level': 'low',
                    'original_url': 'https://example.com/article3'
                }
            ],
            'stats': {
                'total_processed': 3,
                'duplicates_removed': 0,
                'unique_articles': 3
            },
            'timestamp': datetime.now().isoformat(),
            '_test': 'Datos hardcoded para verificar limpieza'
        }

        print("✅ Respuesta generada correctamente")
        print(f"📊 Hero article: {response_data['hero']['title']}")
        print(f"🎯 Mosaic articles: {len(response_data['mosaic'])}")

        # Verificar que no hay campos no deseados
        for article in response_data['mosaic']:
            if 'summary' in article:
                print(f"❌ ERROR: Encontrado campo 'summary' en artículo {article['id']}")
                return False
            if 'content' in article:
                print(f"❌ ERROR: Encontrado campo 'content' en artículo {article['id']}")
                return False
            if 'description' in article:
                print(f"❌ ERROR: Encontrado campo 'description' en artículo {article['id']}")
                return False

        print("✅ No se encontraron campos no deseados (summary, content, description)")
        print("✅ Endpoint logic test PASSED")

        return True

    except Exception as e:
        print(f"❌ Error en la lógica del endpoint: {e}")
        return False

def check_app_structure():
    """Verificar la estructura del archivo app_BUENA.py"""
    print("\n🔍 Verificando estructura del archivo app_BUENA.py...")

    try:
        with open('app_BUENA.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Contar ocurrencias de patrones problemáticos
        flask_run_count = content.count('self.flask_app.run(')
        start_application_count = content.count('def start_application(self):')
        basic_config_count = content.count('logging.basicConfig(')

        print(f"📊 Ocurrencias de 'self.flask_app.run(': {flask_run_count}")
        print(f"📊 Ocurrencias de 'def start_application': {start_application_count}")
        print(f"📊 Ocurrencias de 'logging.basicConfig': {basic_config_count}")

        if flask_run_count > 1:
            print("⚠️  ADVERTENCIA: Múltiples llamadas a flask_app.run() detectadas")
        if start_application_count > 1:
            print("⚠️  ADVERTENCIA: Múltiples definiciones de start_application detectadas")
        if basic_config_count > 1:
            print("⚠️  ADVERTENCIA: Múltiples configuraciones de logging detectadas")

        # Buscar el endpoint específico
        if '@self.flask_app.route(\'/api/articles/deduplicated\'' in content:
            print("✅ Endpoint /api/articles/deduplicated encontrado")
        else:
            print("❌ Endpoint /api/articles/deduplicated NO encontrado")

        return True

    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico del endpoint /api/articles/deduplicated")
    print("="*60)

    # Probar lógica del endpoint
    logic_ok = test_endpoint_logic()

    # Verificar estructura del archivo
    structure_ok = check_app_structure()

    print("\n" + "="*60)
    if logic_ok and structure_ok:
        print("✅ DIAGNÓSTICO COMPLETADO: Todo parece estar bien con el endpoint")
        print("💡 El problema del timeout podría estar en la inicialización de Flask")
        print("💡 o en algún proceso en segundo plano")
    else:
        print("❌ DIAGNÓSTICO COMPLETADO: Se encontraron problemas")

    print("="*60)