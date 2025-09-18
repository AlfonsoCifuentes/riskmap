#!/usr/bin/env python3
"""
Script de verificación COMPLETA del mosaico limpio
"""

import re
import os

def comprehensive_mosaic_verification():
    """
    Verifica exhaustivamente que el mosaico esté completamente limpio
    """
    
    dashboard_file = "src/web/templates/dashboard_BUENO.html"
    
    print("🔍 VERIFICACIÓN COMPLETA DEL MOSAICO LIMPIO")
    print("=" * 60)
    
    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 1. VERIFICANDO FUNCIONES GENERADORAS DE HTML...")
        print("-" * 50)
        
        # Buscar todas las funciones que retornan HTML del mosaico
        pattern = r'return `[^`]*mosaic-article[^`]*`'
        matches = re.findall(pattern, content, re.DOTALL)
        
        cv_indicator_found = 0
        
        for i, match in enumerate(matches):
            print(f"🎯 Función {i+1}:")
            
            # Verificar que NO contiene indicador CV
            if "${cvIndicator}" in match:
                print("❌ PROBLEMA: Indicador CV aún presente")
                cv_indicator_found += 1
            else:
                print("✅ SIN indicador CV")
            
            # Verificar que SÍ contiene título
            if "mosaic-title" in match:
                print("✅ SÍ contiene título")
            else:
                print("❌ PROBLEMA: NO contiene título")
        
        print(f"\n📊 Total funciones verificadas: {len(matches)}")
        print(f"🚨 Indicadores CV encontrados: {cv_indicator_found}")
        
        print("\n📋 2. VERIFICANDO JAVASCRIPT DINÁMICO...")
        print("-" * 50)
        
        # Verificar que applyComputerVisionToMosaic esté deshabilitado
        cv_function_calls = content.count("applyComputerVisionToMosaic();")
        cv_function_calls_commented = content.count("// applyComputerVisionToMosaic();") + content.count("//     applyComputerVisionToMosaic();")
        
        print(f"🔧 Llamadas a applyComputerVisionToMosaic: {cv_function_calls}")
        print(f"💤 Llamadas comentadas: {cv_function_calls_commented}")
        
        if cv_function_calls == 0:
            print("✅ Función CV completamente deshabilitada")
        else:
            print("⚠️  Aún hay llamadas activas a la función CV")
        
        print("\n📋 3. VERIFICANDO ELEMENTOS HTML DINÁMICOS...")
        print("-" * 50)
        
        # Buscar código que añade elementos dinámicamente al mosaico
        dynamic_additions = [
            "appendChild(qualityIndicator)",
            "cv-quality-indicator",
            "insertAdjacentHTML"
        ]
        
        for element in dynamic_additions:
            count = content.count(element)
            if count > 0:
                print(f"📍 {element}: {count} ocurrencias encontradas")
            else:
                print(f"✅ {element}: No encontrado")
        
        print("\n📋 4. VERIFICANDO ESTRUCTURA ESPERADA...")
        print("-" * 50)
        
        # Verificar que las funciones generan solo imagen + título
        expected_structure = [
            "mosaic-article",
            "mosaic-content",
            "mosaic-title"
        ]
        
        for element in expected_structure:
            count = content.count(element)
            print(f"✅ {element}: {count} ocurrencias")
        
        # Verificar elementos que NO deberían estar en el HTML generado
        unwanted_elements = [
            "${cvIndicator}",
            "mosaic-meta",
            "mosaic-location",
            "mosaic-risk-badge",
            "${article.summary}",
            "${article.description}"
        ]
        
        print("\n🚫 Elementos NO deseados en HTML generado:")
        unwanted_found = 0
        for element in unwanted_elements:
            # Buscar solo en las funciones que generan HTML
            for match in matches:
                if element in match:
                    print(f"❌ {element}: ENCONTRADO en HTML generado")
                    unwanted_found += 1
                    break
            else:
                print(f"✅ {element}: No encontrado en HTML generado")
        
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE VERIFICACIÓN:")
        print(f"✅ Funciones HTML verificadas: {len(matches)}")
        print(f"✅ Indicadores CV en HTML: {cv_indicator_found} (esperado: 0)")
        print(f"✅ Llamadas CV dinámicas activas: {cv_function_calls} (esperado: 0)")
        print(f"✅ Elementos no deseados: {unwanted_found} (esperado: 0)")
        
        if cv_indicator_found == 0 and cv_function_calls == 0 and unwanted_found == 0:
            print("\n🎉 ¡MOSAICO COMPLETAMENTE LIMPIO!")
            print("   Solo mostrará: imagen de fondo + título")
        else:
            print("\n⚠️  AÚN HAY PROBLEMAS QUE RESOLVER")
        
        print("\n📋 ESTADO FINAL ESPERADO:")
        print("   - Cada tarjeta del mosaico:")
        print("     ✅ Imagen de fondo")
        print("     ✅ Título superpuesto elegantemente")
        print("     ❌ SIN indicador CV (CV: X%)")
        print("     ❌ SIN metadata adicional")
        print("     ❌ SIN texto de resumen")
        print("     ❌ SIN elementos superpuestos extras")
        
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {dashboard_file}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    comprehensive_mosaic_verification()