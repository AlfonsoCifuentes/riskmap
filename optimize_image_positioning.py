#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para ejecutar el sistema inteligente de posicionamiento de imágenes
"""

import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from src.intelligence.smart_image_positioning import SmartImagePositioning
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Función principal para ejecutar todo el sistema de posicionamiento inteligente
    """
    logger.info("🚀 Iniciando sistema inteligente de posicionamiento de imágenes")
    
    try:
        # Inicializar sistema
        smart_positioning = SmartImagePositioning()
        
        # Paso 1: Actualizar fingerprints de imágenes
        logger.info("📋 Paso 1: Actualizando fingerprints de imágenes...")
        fingerprint_results = smart_positioning.update_all_image_fingerprints()
        logger.info(f"✅ Fingerprints actualizados: {fingerprint_results}")
        
        # Paso 2: Detectar y resolver imágenes duplicadas
        logger.info("📋 Paso 2: Detectando imágenes duplicadas...")
        duplicates = smart_positioning.check_duplicate_images()
        
        if duplicates:
            logger.info(f"🔍 Encontrados {len(duplicates)} pares de imágenes similares")
            
            # Resolver duplicados
            logger.info("📋 Resolviendo imágenes duplicadas...")
            resolution_results = smart_positioning.resolve_duplicate_images(duplicates)
            logger.info(f"✅ Duplicados resueltos: {resolution_results}")
        else:
            logger.info("✅ No se encontraron imágenes duplicadas")
        
        # Paso 3: Optimizar imágenes de baja calidad
        logger.info("📋 Paso 3: Optimizando imágenes de baja calidad...")
        optimization_results = smart_positioning.optimize_low_quality_images(quality_threshold=0.5)
        logger.info(f"✅ Optimización completada: {optimization_results}")
        
        # Paso 4: Asignar posiciones inteligentes en el mosaico
        logger.info("📋 Paso 4: Asignando posiciones del mosaico basadas en análisis CV...")
        position_results = smart_positioning.assign_mosaic_positions()
        logger.info(f"✅ Posiciones asignadas: {position_results}")
        
        # Paso 5: Mostrar estadísticas finales
        logger.info("📋 Paso 5: Obteniendo estadísticas finales...")
        stats = smart_positioning.get_positioning_statistics()
        
        print("\n" + "="*60)
        print("📊 RESUMEN DEL SISTEMA DE POSICIONAMIENTO INTELIGENTE")
        print("="*60)
        
        print(f"\n🎯 FINGERPRINTS DE IMÁGENES:")
        print(f"   • Procesadas: {fingerprint_results.get('processed', 0)}")
        print(f"   • Actualizadas: {fingerprint_results.get('updated', 0)}")
        print(f"   • Fallidas: {fingerprint_results.get('failed', 0)}")
        
        if duplicates:
            print(f"\n🔄 RESOLUCIÓN DE DUPLICADOS:")
            print(f"   • Pares similares encontrados: {len(duplicates)}")
            print(f"   • Resueltos: {resolution_results.get('resolved', 0)}")
            print(f"   • Fallidos: {resolution_results.get('failed', 0)}")
        
        print(f"\n🎨 OPTIMIZACIÓN DE CALIDAD:")
        print(f"   • Imágenes de baja calidad identificadas: {optimization_results.get('identified', 0)}")
        print(f"   • Mejoradas: {optimization_results.get('improved', 0)}")
        print(f"   • Fallidas: {optimization_results.get('failed', 0)}")
        
        print(f"\n📍 POSICIONAMIENTO EN MOSAICO:")
        print(f"   • Total procesado: {position_results.get('processed', 0)}")
        print(f"   • Hero (grandes): {position_results.get('hero', 0)}")
        print(f"   • Featured (medianas): {position_results.get('featured', 0)}")
        print(f"   • Standard (estándar): {position_results.get('standard', 0)}")
        print(f"   • Thumbnail (pequeñas): {position_results.get('thumbnail', 0)}")
        
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"   • Total artículos con imágenes: {stats.get('total_with_images', 0)}")
        print(f"   • Con fingerprints: {stats.get('with_fingerprints', 0)}")
        print(f"   • Cobertura de fingerprints: {stats.get('coverage', {}).get('fingerprints', 0)}%")
        print(f"   • Calidad promedio: {stats.get('average_quality', 0)}")
        
        if 'positions' in stats:
            print(f"\n🗂️ DISTRIBUCIÓN DE POSICIONES:")
            for position, count in stats['positions'].items():
                if position:
                    print(f"   • {position}: {count} artículos")
        
        print("\n" + "="*60)
        print("🎉 SISTEMA DE POSICIONAMIENTO COMPLETADO EXITOSAMENTE")
        print("="*60)
        
        # Crear informe detallado
        create_positioning_report(smart_positioning, stats, duplicates, optimization_results)
        
    except Exception as e:
        logger.error(f"❌ Error en el sistema de posicionamiento: {e}")
        raise

def create_positioning_report(smart_positioning, stats, duplicates, optimization_results):
    """
    Crear informe detallado del posicionamiento
    """
    try:
        report_path = Path("reports/smart_positioning_report.md")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 📊 Informe del Sistema Inteligente de Posicionamiento de Imágenes\n\n")
            f.write(f"**Fecha de generación:** {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}\n\n")
            
            f.write("## 🎯 Resumen Ejecutivo\n\n")
            f.write(f"- Total de artículos con imágenes: **{stats.get('total_with_images', 0)}**\n")
            f.write(f"- Calidad promedio de imágenes: **{stats.get('average_quality', 0)}**\n")
            f.write(f"- Cobertura de fingerprints: **{stats.get('coverage', {}).get('fingerprints', 0)}%**\n")
            f.write(f"- Imágenes duplicadas detectadas: **{len(duplicates)}**\n")
            f.write(f"- Imágenes optimizadas: **{optimization_results.get('improved', 0)}**\n\n")
            
            f.write("## 📍 Distribución del Mosaico\n\n")
            if 'positions' in stats:
                for position, count in stats['positions'].items():
                    if position:
                        percentage = (count / stats.get('total_with_images', 1)) * 100
                        f.write(f"- **{position.capitalize()}**: {count} artículos ({percentage:.1f}%)\n")
            
            f.write("\n## 🔧 Recomendaciones\n\n")
            f.write("### Basadas en el análisis realizado:\n\n")
            
            if stats.get('average_quality', 0) < 0.7:
                f.write("- ⚠️ **Calidad promedio baja**: Considerar mejorar fuentes de imágenes\n")
            
            if stats.get('coverage', {}).get('fingerprints', 0) < 95:
                f.write("- 🔐 **Fingerprints incompletos**: Ejecutar actualización de fingerprints\n")
            
            if len(duplicates) > 0:
                f.write("- 🔄 **Imágenes duplicadas**: Revisar y resolver duplicados detectados\n")
            
            f.write("\n## 🎨 Criterios de Posicionamiento\n\n")
            f.write("### Hero (Imagen principal):\n")
            f.write("- Calidad visual ≥ 0.8\n")
            f.write("- Score de impacto visual ≥ 0.8\n")
            f.write("- Preferencia por imágenes con caras y acción\n\n")
            
            f.write("### Featured (Destacadas):\n")
            f.write("- Calidad visual ≥ 0.7\n")
            f.write("- Score de impacto visual ≥ 0.6\n")
            f.write("- Contenido de importancia media-alta\n\n")
            
            f.write("### Standard (Estándar):\n")
            f.write("- Calidad visual ≥ 0.5\n")
            f.write("- Score de impacto visual ≥ 0.4\n")
            f.write("- Contenido general\n\n")
            
            f.write("### Thumbnail (Miniaturas):\n")
            f.write("- Calidad visual < 0.5\n")
            f.write("- Score de impacto visual < 0.4\n")
            f.write("- Imágenes de respaldo\n\n")
            
        logger.info(f"📋 Informe detallado guardado en: {report_path}")
        
    except Exception as e:
        logger.error(f"Error creando informe: {e}")

if __name__ == "__main__":
    main()
