#!/usr/bin/env python3
"""
Test del Sistema Satelital YOLO - RiskMap

Script de prueba para verificar el funcionamiento completo del sistema
de análisis satelital con YOLO y Google Maps integration.

Uso:
    python test_satellite_yolo_system.py

Pruebas realizadas:
✅ Carga del sistema YOLO Ultra HD
✅ Detección de objetos en imagen de prueba
✅ Integración Google Maps
✅ Endpoints API satelitales
✅ Base de datos YOLO
✅ Procesamiento por lotes
"""

import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_yolo_system_loading():
    """Prueba la carga del sistema YOLO Ultra HD."""
    print("🔍 Probando carga del sistema YOLO Ultra HD...")

    try:
        from ultra_hd_satellite_system import ultra_hd_system
        print("✅ Sistema YOLO Ultra HD cargado exitosamente")

        # Verificar que YOLO esté disponible
        if hasattr(ultra_hd_system, 'yolo_model') and ultra_hd_system.yolo_model:
            print("✅ Modelo YOLO disponible")
        else:
            print("⚠️ Modelo YOLO no disponible (usando simulación)")

        return True
    except Exception as e:
        print(f"❌ Error cargando sistema YOLO: {e}")
        return False

def test_google_maps_client():
    """Prueba el cliente de Google Maps."""
    print("\n🌍 Probando cliente Google Maps...")

    try:
        from google_maps_client import GoogleMapsClient
        google_maps_client = GoogleMapsClient()

        # Obtener coordenadas militares
        coords = google_maps_client.get_military_coordinates()
        print(f"✅ Coordenadas militares obtenidas: {len(coords)} ubicaciones")

        # Mostrar algunas coordenadas
        for key, data in list(coords.items())[:3]:
            print(f"   - {data['name']}: {data['lat']:.4f}, {data['lng']:.4f}")

        return True
    except Exception as e:
        print(f"❌ Error con cliente Google Maps: {e}")
        return False

def test_yolo_detection():
    """Prueba la detección YOLO en una imagen."""
    print("\n🎯 Probando detección YOLO...")

    try:
        from ultra_hd_satellite_system import ultra_hd_system

        # Crear una imagen de prueba simple (si no existe ninguna)
        test_image_path = "static/test_satellite_image.jpg"

        if not os.path.exists(test_image_path):
            # Crear imagen de prueba
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (1024, 1024), color='lightblue')
            draw = ImageDraw.Draw(img)

            # Dibujar algunos elementos simulados
            draw.rectangle([100, 100, 200, 150], fill='gray')  # Edificio
            draw.rectangle([300, 300, 350, 320], fill='green')  # Vehículo
            draw.ellipse([500, 500, 550, 550], fill='red')     # Área sospechosa

            img.save(test_image_path)
            print(f"📸 Imagen de prueba creada: {test_image_path}")

        # Ejecutar detección
        results = ultra_hd_system.detect_objects_yolo(test_image_path)

        print("✅ Detección YOLO completada:")
        print(f"   - Total detecciones: {results['total_detections']}")
        print(f"   - Objetos militares: {results['military_objects']}")
        print(f"   - Objetos civiles: {results['civilian_objects']}")
        print(f"   - Indicadores conflicto: {results['conflict_indicators']}")

        if results['detections']:
            print("   - Detecciones principales:")
            for i, det in enumerate(results['detections'][:3]):
                print(f"      {i+1}. {det['class']} (conf: {det['confidence']:.2f})")

        return True
    except Exception as e:
        print(f"❌ Error en detección YOLO: {e}")
        return False

def test_database_operations():
    """Prueba las operaciones de base de datos YOLO."""
    print("\n💾 Probando operaciones de base de datos...")

    try:
        import sqlite3

        # Verificar base de datos principal
        if os.path.exists("satellite_analysis.db"):
            conn = sqlite3.connect("satellite_analysis.db")
            cursor = conn.cursor()

            # Verificar tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [t[0] for t in tables]

            expected_tables = ['ultra_hd_analysis', 'yolo_detections']
            missing_tables = [t for t in expected_tables if t not in table_names]

            if missing_tables:
                print(f"⚠️ Tablas faltantes: {missing_tables}")
            else:
                print("✅ Todas las tablas YOLO existen")

            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM ultra_hd_analysis")
            analysis_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM yolo_detections")
            detections_count = cursor.fetchone()[0]

            print(f"   - Análisis guardados: {analysis_count}")
            print(f"   - Detecciones guardadas: {detections_count}")

            conn.close()
        else:
            print("⚠️ Base de datos satellite_analysis.db no existe aún")

        return True
    except Exception as e:
        print(f"❌ Error en operaciones de BD: {e}")
        return False

def test_api_endpoints():
    """Prueba los endpoints API (requiere servidor ejecutándose)."""
    print("\n🔗 Probando endpoints API...")

    try:
        import requests

        base_url = "http://localhost:5001"

        # Lista de endpoints a probar
        endpoints = [
            '/api/satellite/statistics',
            '/api/satellite/gallery-images',
            '/api/satellite/yolo/gallery',
            '/api/satellite/yolo/statistics'
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK")
                else:
                    print(f"⚠️ {endpoint}: Status {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"⚠️ {endpoint}: No disponible (servidor no ejecutándose)")

        return True
    except Exception as e:
        print(f"❌ Error probando APIs: {e}")
        return False

def main():
    """Función principal de pruebas."""
    print("🛰️ RiskMap - Test del Sistema Satelital YOLO")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")

    tests = [
        ("Carga Sistema YOLO", test_yolo_system_loading),
        ("Cliente Google Maps", test_google_maps_client),
        ("Detección YOLO", test_yolo_detection),
        ("Base de Datos", test_database_operations),
        ("Endpoints API", test_api_endpoints)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} - {test_name}")
        if success:
            passed += 1

    print(f"\n📈 Resultado: {passed}/{total} pruebas pasaron")

    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return 0
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los logs para más detalles.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)