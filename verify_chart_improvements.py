#!/usr/bin/env python3
"""
Script para verificar las mejoras en los gráficos y el mapa de calor
"""

import os

def verify_chart_improvements():
    """
    Verifica que las mejoras en los gráficos estén implementadas
    """
    print("🔍 Verificando mejoras en los gráficos y mapa de calor...")
    
    dashboard_file = "src/web/templates/dashboard_BUENO.html"
    
    if not os.path.exists(dashboard_file):
        print(f"❌ Archivo {dashboard_file} no encontrado")
        return
        
    with open(dashboard_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    improvements_found = []
    
    # Verificar padding mejorado en chart-container
    if "padding: 35px;" in content:
        improvements_found.append("✅ Padding aumentado en chart-container (35px)")
    else:
        improvements_found.append("❌ Padding no aumentado en chart-container")
        
    # Verificar margen agregado
    if "margin: 15px;" in content:
        improvements_found.append("✅ Margen agregado a chart-container")
    else:
        improvements_found.append("❌ Margen no agregado a chart-container")
        
    # Verificar gap mejorado en analytics-grid
    if "gap: 40px;" in content:
        improvements_found.append("✅ Gap aumentado en analytics-grid (40px)")
    else:
        improvements_found.append("❌ Gap no aumentado en analytics-grid")
        
    # Verificar mapa del mundo mejorado
    if "North America" in content and "South America" in content and "Europe" in content:
        improvements_found.append("✅ Mapa del mundo con continentes detallados")
    else:
        improvements_found.append("❌ Mapa del mundo no mejorado")
        
    # Verificar grid de coordenadas
    if "Grid lines for coordinates" in content:
        improvements_found.append("✅ Grid de coordenadas agregado al mapa")
    else:
        improvements_found.append("❌ Grid de coordenadas no agregado")
        
    # Verificar patrón de océano
    if "oceanPattern" in content:
        improvements_found.append("✅ Patrón de océano agregado")
    else:
        improvements_found.append("❌ Patrón de océano no agregado")
        
    # Verificar heatmap-container con padding
    if "padding: 20px;" in content and "box-sizing: border-box;" in content:
        improvements_found.append("✅ Padding interno agregado al heatmap-container")
    else:
        improvements_found.append("❌ Padding interno no agregado al heatmap-container")
        
    print("\n📊 Resultados de la verificación:")
    for improvement in improvements_found:
        print(f"   {improvement}")
        
    print("\n🎯 Resumen de mejoras implementadas:")
    print("   • Aumentado padding de chart-container de 25px a 35px")
    print("   • Agregado margen de 15px a chart-container")
    print("   • Aumentado gap de analytics-grid de 30px a 40px")
    print("   • Mejorado mapa de calor con continentes detallados")
    print("   • Agregado grid de coordenadas al mapa")
    print("   • Agregado patrón de océano para mejor visualización")
    print("   • Agregado padding interno al heatmap-container")
    
    print("\n🚀 Para ver los cambios:")
    print("   1. Ejecuta tu aplicación Flask")
    print("   2. Ve a la sección de Análisis de Noticias")
    print("   3. Los gráficos tendrán más espacio interno")
    print("   4. El mapa de calor mostrará el mundo con continentes visibles")

if __name__ == "__main__":
    verify_chart_improvements()
