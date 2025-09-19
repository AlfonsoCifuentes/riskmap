#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación previa al enriquecimiento masivo
Comprueba estado de la base de datos y servicios de IA
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from src.ai.unified_ai_service import unified_ai_service
from src.ai.ollama_service import ollama_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_status(db_path: str = "geopolitical_data.db"):
    """
    Verificar estado de la base de datos
    """
    print("🗄️ VERIFICANDO BASE DE DATOS...")
    print("=" * 50)
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total de artículos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        # Artículos con contenido
        cursor.execute("SELECT COUNT(*) FROM articles WHERE content IS NOT NULL AND length(trim(content)) > 50")
        articles_with_content = cursor.fetchone()[0]
        
        # Artículos ya enriquecidos
        cursor.execute("SELECT COUNT(*) FROM articles WHERE groq_enhanced = 1")
        enriched_articles = cursor.fetchone()[0]
        
        # Artículos que necesitan enriquecimiento
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE content IS NOT NULL 
            AND length(trim(content)) > 50
            AND (
                groq_enhanced = 0 
                OR groq_enhanced IS NULL
                OR country IS NULL 
                OR region IS NULL
                OR summary IS NULL
                OR length(trim(summary)) < 20
            )
        """)
        need_enrichment = cursor.fetchone()[0]
        
        # Artículos recientes (últimos 7 días)
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE datetime(published_date) > datetime('now', '-7 days')
            AND content IS NOT NULL 
            AND length(trim(content)) > 50
        """)
        recent_articles = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"📊 Total de artículos: {total_articles:,}")
        print(f"📰 Artículos con contenido: {articles_with_content:,}")
        print(f"✅ Artículos ya enriquecidos: {enriched_articles:,}")
        print(f"🎯 Artículos que necesitan enriquecimiento: {need_enrichment:,}")
        print(f"📅 Artículos recientes (7 días): {recent_articles:,}")
        
        enrichment_percentage = (enriched_articles / max(articles_with_content, 1)) * 100
        print(f"📈 Porcentaje enriquecido: {enrichment_percentage:.1f}%")
        
        if need_enrichment > 0:
            print(f"\n💡 Se procesarán {need_enrichment:,} artículos")
            estimated_time = (need_enrichment * 3) / 60  # ~3 segundos por artículo
            print(f"⏱️ Tiempo estimado: {estimated_time:.1f} minutos")
        else:
            print("\n✅ Todos los artículos están enriquecidos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def check_ai_services():
    """
    Verificar estado de servicios de IA
    """
    print("\n🤖 VERIFICANDO SERVICIOS DE IA...")
    print("=" * 50)
    
    try:
        # Estado del servicio unificado
        status = unified_ai_service.get_service_status()
        
        print(f"🏥 Estado de servicios:")
        print(f"  └─ Ollama: {'✅ Disponible' if status['ollama']['available'] else '❌ No disponible'}")
        print(f"  └─ Groq: {'✅ Disponible' if status['groq']['available'] else '❌ No disponible'}")
        print(f"  └─ Proveedor preferido: {status['preferred_provider']}")
        
        if status['ollama']['available']:
            models = status['ollama']['models']
            print(f"\n🤖 Modelos Ollama disponibles ({len(models)}):")
            for model in models:
                print(f"  └─ {model}")
            
            capabilities = status['capabilities']
            print(f"\n🎯 Capacidades especializadas:")
            print(f"  └─ Análisis profundo (DeepSeek): {'✅' if capabilities['deep_reasoning'] else '❌'}")
            print(f"  └─ Resúmenes rápidos (Gemma): {'✅' if capabilities['fast_processing'] else '❌'}")
            print(f"  └─ Soporte multiidioma (Qwen): {'✅' if capabilities['multilingual'] else '❌'}")
            print(f"  └─ Propósito general (Llama): {'✅' if capabilities['general_purpose'] else '❌'}")
            
            missing_models = []
            if not capabilities['deep_reasoning']:
                missing_models.append("DeepSeek-R1")
            if not capabilities['fast_processing']:
                missing_models.append("Gemma2")
            if not capabilities['multilingual']:
                missing_models.append("Qwen")
            if not capabilities['general_purpose']:
                missing_models.append("Llama3.1")
            
            if missing_models:
                print(f"\n⚠️ Modelos faltantes: {', '.join(missing_models)}")
                print("💡 Ejecuta: python install_ollama.py")
            else:
                print("\n✅ Todos los modelos especializados están disponibles")
        
        return status['ollama']['available'] or status['groq']['available']
        
    except Exception as e:
        print(f"❌ Error verificando servicios de IA: {e}")
        return False

def test_enrichment_sample():
    """
    Probar enriquecimiento con un artículo de muestra
    """
    print("\n🧪 PROBANDO ENRIQUECIMIENTO DE MUESTRA...")
    print("=" * 50)
    
    try:
        import asyncio
        
        test_content = """
        TÍTULO: Escalada de tensiones en Europa Oriental
        CONTENIDO: Las recientes decisiones militares han aumentado las tensiones geopolíticas 
        en la región. Varios países han expresado preocupación por el escalamiento del conflicto.
        Los líderes internacionales buscan soluciones diplomáticas mientras mantienen vigilancia militar.
        """
        
        print("🔄 Ejecutando análisis de prueba...")
        
        response = asyncio.run(unified_ai_service.analyze_geopolitical_content(
            content=test_content,
            prefer_local=True
        ))
        
        if response.success:
            print("✅ Prueba exitosa")
            print(f"🤖 Proveedor usado: {response.provider}")
            print(f"📋 Modelo: {response.model}")
            print(f"📄 Resumen: {response.content[:100]}...")
            
            if response.metadata:
                fields = list(response.metadata.keys())
                print(f"🎯 Campos disponibles: {', '.join(fields[:5])}...")
            
            return True
        else:
            print(f"❌ Error en prueba: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def check_system_resources():
    """
    Verificar recursos del sistema
    """
    print("\n💻 VERIFICANDO RECURSOS DEL SISTEMA...")
    print("=" * 50)
    
    try:
        import psutil
        
        # Memoria
        memory = psutil.virtual_memory()
        print(f"🧠 Memoria RAM:")
        print(f"  └─ Total: {memory.total / (1024**3):.1f} GB")
        print(f"  └─ Disponible: {memory.available / (1024**3):.1f} GB")
        print(f"  └─ Uso: {memory.percent}%")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"⚡ CPU: {cpu_percent}% uso")
        
        # Disco
        disk = psutil.disk_usage('.')
        print(f"💾 Disco:")
        print(f"  └─ Espacio libre: {disk.free / (1024**3):.1f} GB")
        
        # Recomendaciones
        if memory.available < 4 * (1024**3):  # Menos de 4GB disponibles
            print("\n⚠️ Poca memoria disponible. Considera reducir workers paralelos.")
        
        if cpu_percent > 80:
            print("\n⚠️ CPU muy cargada. El procesamiento puede ser lento.")
        
        return True
        
    except ImportError:
        print("📦 psutil no disponible - saltando verificación de recursos")
        return True
    except Exception as e:
        print(f"❌ Error verificando recursos: {e}")
        return True

def print_recommendations():
    """
    Imprimir recomendaciones para el enriquecimiento
    """
    print("\n💡 RECOMENDACIONES PARA EL ENRIQUECIMIENTO:")
    print("=" * 50)
    print("🚀 Para empezar:")
    print("  └─ python enrich_massive_database.py")
    print("\n⚙️ Opciones avanzadas:")
    print("  └─ --workers 3          # Reducir workers si hay poca memoria")
    print("  └─ --batch-size 50      # Lotes más pequeños para sistemas lentos")
    print("  └─ --force              # Re-enriquecer todos los artículos")
    print("\n📊 Monitoreo durante el proceso:")
    print("  └─ python monitor_fallback.py    # Monitor en tiempo real")
    print("  └─ tail -f massive_enrichment.log  # Seguir logs")
    print("\n🛑 Para detener:")
    print("  └─ Ctrl+C (guardará progreso)")

def main():
    """
    Función principal de verificación
    """
    print("🔍 VERIFICACIÓN PREVIA AL ENRIQUECIMIENTO MASIVO")
    print("=" * 60)
    
    checks = []
    
    # 1. Verificar base de datos
    db_ok = check_database_status()
    checks.append(("Base de datos", db_ok))
    
    # 2. Verificar servicios de IA
    ai_ok = check_ai_services()
    checks.append(("Servicios de IA", ai_ok))
    
    # 3. Probar enriquecimiento
    if ai_ok:
        test_ok = test_enrichment_sample()
        checks.append(("Prueba de enriquecimiento", test_ok))
    
    # 4. Verificar recursos del sistema
    resources_ok = check_system_resources()
    checks.append(("Recursos del sistema", resources_ok))
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📋 RESUMEN DE VERIFICACIÓN:")
    
    all_ok = True
    for check_name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {check_name}")
        if not status:
            all_ok = False
    
    if all_ok:
        print(f"\n🎉 ¡Sistema listo para enriquecimiento masivo!")
        print_recommendations()
    else:
        print(f"\n⚠️ Hay problemas que necesitan resolverse antes de continuar.")
        print("\n🔧 Posibles soluciones:")
        print("  └─ Verificar que Ollama esté corriendo: ollama serve")
        print("  └─ Instalar modelos: python install_ollama.py")
        print("  └─ Verificar configuración de Groq API key")

if __name__ == "__main__":
    main()
