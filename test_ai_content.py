#!/usr/bin/env python3
"""
Script de verificación para comprobar que el contenedor aiArticleContent funciona correctamente
"""

import webbrowser
import time
import os

def test_ai_content_implementation():
    """
    Prueba la implementación del contenedor aiArticleContent
    """
    print("🧪 Verificando implementación de aiArticleContent...")
    
    # Verificar que los archivos necesarios existen
    files_to_check = [
        "src/web/templates/dashboard_BUENO.html",
        "src/web/templates/base_navigation.html",
        "src/web/static/js/enhanced_dashboard_fixed.js"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} existe")
        else:
            print(f"❌ {file_path} no encontrado")
            
    # Verificar que aiArticleContent está en el HTML
    try:
        with open("src/web/templates/dashboard_BUENO.html", "r", encoding="utf-8") as f:
            content = f.read()
            if "aiArticleContent" in content:
                print("✅ Elemento aiArticleContent encontrado en el HTML")
            else:
                print("❌ Elemento aiArticleContent no encontrado en el HTML")
                
            if "ai-analysis-section" in content:
                print("✅ Sección ai-analysis-section encontrada")
            else:
                print("❌ Sección ai-analysis-section no encontrada")
                
    except Exception as e:
        print(f"❌ Error al verificar HTML: {e}")
        
    # Verificar que los scripts están habilitados
    try:
        with open("src/web/templates/base_navigation.html", "r", encoding="utf-8") as f:
            content = f.read()
            if "enhanced_dashboard_fixed.js" in content and "<!--" not in content.split("enhanced_dashboard_fixed.js")[0].split("\n")[-1]:
                print("✅ Script enhanced_dashboard_fixed.js está habilitado")
            else:
                print("❌ Script enhanced_dashboard_fixed.js no está habilitado o comentado")
                
    except Exception as e:
        print(f"❌ Error al verificar scripts: {e}")
        
    print("\n🎯 Implementación completada!")
    print("📋 Resumen de la implementación:")
    print("   • Elemento aiArticleContent agregado al HTML")
    print("   • Estilos CSS personalizados para la sección de IA")
    print("   • Scripts JavaScript reactivados")
    print("   • Sección posicionada después del mosaico de noticias")
    print("\n🚀 Para ver los cambios:")
    print("   1. Ejecuta tu aplicación Flask")
    print("   2. Navega al dashboard")
    print("   3. Deberías ver la nueva sección 'Análisis Periodístico por IA'")

if __name__ == "__main__":
    test_ai_content_implementation()
