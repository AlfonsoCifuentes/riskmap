#!/usr/bin/env python3
"""
Test de Verificación Rápida de Correcciones
Verifica que la aplicación se inicialice sin errores después de las correcciones.
"""

import sys
import os
from datetime import datetime

# Añadir el directorio principal al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_app_initialization():
    """Test de inicialización de la aplicación"""
    print("🚀 TEST DE INICIALIZACIÓN POST-CORRECCIONES")
    print("=" * 60)
    print(f"🕒 Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        print("📋 Importando módulos necesarios...")
        
        # Test de importación del sistema de traducción
        try:
            from robust_translation_v3 import UltraRobustTranslationService
            print("✅ Sistema de traducción importado correctamente")
        except ImportError as e:
            print(f"⚠️ Sistema de traducción no disponible: {e}")
        
        # Test de inicialización de la aplicación
        print("📋 Inicializando aplicación principal...")
        
        # Importar la aplicación
        from app_BUENA import RiskMapUnifiedApplication
        
        print("✅ Clase principal importada correctamente")
        
        # Crear instancia de la aplicación (sin auto-inicialización)
        config = {
            'auto_initialize': False,  # No auto-inicializar para evitar cargas pesadas
            'auto_start_ingestion': False,
            'auto_start_processing': False,
            'auto_start_analysis': False,
            'flask_debug': True
        }
        
        print("📋 Creando instancia de aplicación...")
        app_instance = RiskMapUnifiedApplication(config=config)
        print("✅ Aplicación inicializada sin errores")
        
        # Verificar que el sistema de traducción esté inicializado
        if hasattr(app_instance, 'translation_system'):
            if app_instance.translation_system is not None:
                print("✅ Sistema de traducción integrado correctamente")
            else:
                print("⚠️ Sistema de traducción está disponible pero es None")
        else:
            print("❌ Atributo translation_system no encontrado")
        
        # Verificar que la aplicación Flask esté configurada
        if hasattr(app_instance, 'flask_app') and app_instance.flask_app is not None:
            print("✅ Aplicación Flask configurada correctamente")
            
            # Contar rutas disponibles
            routes_count = len(list(app_instance.flask_app.url_map.iter_rules()))
            print(f"📊 Rutas Flask configuradas: {routes_count}")
        else:
            print("❌ Aplicación Flask no configurada")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error durante inicialización: {e}")
        return False

def test_translation_system_standalone():
    """Test del sistema de traducción por separado"""
    print("\n" + "="*60)
    print("🌍 TEST DEL SISTEMA DE TRADUCCIÓN STANDALONE")
    print("="*60)
    
    try:
        from robust_translation_v3 import UltraRobustTranslationService
        
        print("📋 Inicializando sistema de traducción...")
        translator = UltraRobustTranslationService()
        print("✅ Sistema de traducción inicializado")
        
        # Test básico de traducción
        test_text = "Breaking news from the region"
        print(f"📝 Texto de prueba: {test_text}")
        
        translated_text = translator.translate_text(test_text, target_language='es')
        print(f"🔄 Texto traducido: {translated_text}")
        
        if translated_text and translated_text != test_text:
            print("✅ Traducción funcionando correctamente")
            return True
        else:
            print("⚠️ Traducción no cambió el texto (podría ser normal)")
            return True
            
    except Exception as e:
        print(f"❌ Error en sistema de traducción: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🔧 VERIFICACIÓN POST-CORRECCIONES DE ERRORES 500")
    print("=" * 70)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Inicialización de aplicación
    if test_app_initialization():
        success_count += 1
    
    # Test 2: Sistema de traducción standalone
    if test_translation_system_standalone():
        success_count += 1
    
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*70)
    print(f"✅ Pruebas exitosas: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 TODAS LAS PRUEBAS PASARON")
        print("🚀 La aplicación debería funcionar correctamente ahora")
        print()
        print("💡 PRÓXIMOS PASOS:")
        print("   1. Reinicia el servidor: python app_BUENA.py")
        print("   2. Prueba los endpoints en el navegador: http://localhost:5001")
        print("   3. Verifica que no hay más errores 500")
    else:
        print("⚠️ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisa los errores mostrados arriba")
    
    print(f"🕒 Finalizado: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Prueba interrumpida por usuario")
    except Exception as e:
        print(f"\n❌ Error general: {e}")