#!/usr/bin/env python3
"""
Script para ejecutar el Sistema Avanzado de Inteligencia Geopolítica
Incluye recolección completa, análisis con IA, y población de base de datos
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestration.advanced_orchestrator import run_advanced_orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('advanced_orchestrator.log')
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Función principal para ejecutar el sistema completo"""
    
    print("🌍 SISTEMA AVANZADO DE INTELIGENCIA GEOPOLÍTICA")
    print("=" * 60)
    print("🔍 Capacidades incluidas:")
    print("  • Recolección RSS/NewsAPI con análisis de IA")
    print("  • Validación de imágenes con modelos de visión")
    print("  • Detección geográfica avanzada (distingue fuente vs contenido)")
    print("  • Datasets de Energía/Petróleo (EIA, World Bank)")
    print("  • Datos Militares (SIPRI, HuggingFace)")
    print("  • Comercio Internacional (World Bank, WTO, IMF)")
    print("  • Conflictos Históricos (UCDP, COW)")
    print("  • Solo IA real - Sin fallbacks manuales")
    print("=" * 60)
    
    response = input("\n¿Ejecutar recolección completa? (y/N): ")
    if response.lower() != 'y':
        print("❌ Ejecución cancelada")
        return
    
    try:
        logger.info("🚀 Iniciando sistema avanzado...")
        
        # Ejecutar orchestrador avanzado
        results = await run_advanced_orchestrator()
        
        if results:
            print("\n✅ EJECUCIÓN COMPLETADA EXITOSAMENTE")
            print(f"📊 Resumen: {results.get('summary', {})}")
            
            # Mostrar detalles por categoría
            collections = results.get('collections', {})
            for category, data in collections.items():
                print(f"\n📁 {category.upper()}:")
                if 'error' in data:
                    print(f"   ❌ Error: {data['error']}")
                else:
                    sources = data.get('sources_processed', [])
                    print(f"   ✅ Fuentes procesadas: {len(sources)}")
                    if sources:
                        print(f"   📋 Fuentes: {', '.join(sources)}")
            
            # Verificar si hay errores
            errors = results.get('errors', [])
            if errors:
                print(f"\n⚠️  ERRORES ENCONTRADOS ({len(errors)}):")
                for error in errors:
                    print(f"   • {error}")
            
            print(f"\n🗄️  Base de datos actualizada con datos especializados")
            print(f"📈 Dashboard listo para mostrar datos reales")
            
        else:
            print("\n❌ EJECUCIÓN FALLIDA")
            print("Revisa los logs para más detalles")
            
    except KeyboardInterrupt:
        print("\n⏹️  Ejecución interrumpida por el usuario")
        
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        print(f"\n💥 Error crítico: {e}")
        print("Revisa advanced_orchestrator.log para detalles completos")


def test_ai_models():
    """Prueba los modelos de IA antes de la ejecución completa"""
    print("\n🧠 PROBANDO MODELOS DE IA...")
    print("-" * 40)
    
    try:
        from transformers import pipeline
        import torch
        
        print(f"✅ PyTorch disponible: {torch.__version__}")
        print(f"🔥 CUDA disponible: {torch.cuda.is_available()}")
        
        # Probar modelo de clasificación
        print("🔍 Probando clasificación de texto...")
        classifier = pipeline("zero-shot-classification", 
                            model="MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli")
        
        result = classifier("Russia invades Ukraine causing international crisis", 
                          ["military conflict", "political tension", "economic crisis"])
        print(f"   Resultado: {result['labels'][0]} ({result['scores'][0]:.3f})")
        
        # Probar modelo de NER
        print("🏷️  Probando extracción de entidades...")
        ner = pipeline("ner", model="numind/NuNER-v2.0", aggregation_strategy="simple")
        
        entities = ner("Conflict in Syria affects Lebanon and Jordan")
        locations = [ent['word'] for ent in entities if ent['entity_group'] in ['GPE', 'LOC']]
        print(f"   Ubicaciones detectadas: {locations}")
        
        print("✅ Todos los modelos funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando modelos de IA: {e}")
        return False


def show_menu():
    """Muestra menú de opciones"""
    print("\n📋 OPCIONES DISPONIBLES:")
    print("1. 🧠 Probar modelos de IA")
    print("2. 🚀 Ejecutar recolección completa")
    print("3. 📊 Solo datos de energía")
    print("4. ⚔️  Solo datos militares")
    print("5. 💼 Solo datos comerciales")
    print("6. 📜 Solo conflictos históricos")
    print("7. 📰 Solo noticias con IA")
    print("8. ❌ Salir")
    
    return input("\nSelecciona una opción (1-8): ")


async def run_specific_collection(collection_type: str):
    """Ejecuta una recolección específica"""
    try:
        from src.orchestration.advanced_orchestrator import AdvancedGeopoliticalOrchestrator
        
        orchestrator = AdvancedGeopoliticalOrchestrator()
        
        print(f"\n🔄 Ejecutando recolección: {collection_type.upper()}")
        
        if collection_type == "energy":
            result = await orchestrator.collect_energy_data()
        elif collection_type == "military":
            result = await orchestrator.collect_military_data()
        elif collection_type == "trade":
            result = await orchestrator.collect_trade_data()
        elif collection_type == "historical":
            result = await orchestrator.collect_historical_conflicts()
        elif collection_type == "news":
            result = await orchestrator._collect_news_with_ai_analysis()
        else:
            print("❌ Tipo de recolección no válido")
            return
        
        print(f"✅ Recolección completada:")
        print(f"   📁 Fuentes: {len(result.get('sources_processed', []))}")
        print(f"   📊 Estado: {'✅ Exitoso' if 'error' not in result else '❌ Con errores'}")
        
        if 'error' in result:
            print(f"   ⚠️  Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error en recolección específica: {e}")


async def interactive_mode():
    """Modo interactivo con menú"""
    while True:
        choice = show_menu()
        
        if choice == "1":
            test_ai_models()
            
        elif choice == "2":
            await main()
            
        elif choice == "3":
            await run_specific_collection("energy")
            
        elif choice == "4":
            await run_specific_collection("military")
            
        elif choice == "5":
            await run_specific_collection("trade")
            
        elif choice == "6":
            await run_specific_collection("historical")
            
        elif choice == "7":
            await run_specific_collection("news")
            
        elif choice == "8":
            print("👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción no válida")
        
        input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-ai":
            test_ai_models()
        elif sys.argv[1] == "--full":
            asyncio.run(main())
        elif sys.argv[1] == "--interactive":
            asyncio.run(interactive_mode())
        else:
            print("Opciones: --test-ai, --full, --interactive")
    else:
        # Modo interactivo por defecto
        asyncio.run(interactive_mode())
