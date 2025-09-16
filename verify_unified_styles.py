#!/usr/bin/env python3
"""
Script para verificar que las páginas apliquen estilos CSS unificados.
Verifica que todas las secciones de video vigilancia y análisis histórico
tengan consistencia de diseño con el dashboard principal.
"""

import os
import re
from pathlib import Path

def verify_unified_styles():
    """Verifica que los estilos CSS sean consistentes entre páginas"""
    
    # Directorio de templates
    templates_dir = Path("src/web/templates")
    
    # Archivos clave a verificar
    key_files = [
        "conflict_monitoring.html",
        "video_surveillance.html", 
        "historical_analysis.html"
    ]
    
    print("🎨 VERIFICACIÓN DE ESTILOS CSS UNIFICADOS")
    print("=" * 60)
    
    unified_patterns = {
        "color_scheme": [
            r"#667eea",  # Color primario azul
            r"#764ba2",  # Color secundario púrpura
            r"rgba\(255, 255, 255, 0\.05\)",  # Fondo de tarjetas
            r"rgba\(255, 255, 255, 0\.1\)",   # Bordes
        ],
        "typography": [
            r"'Orbitron', monospace",  # Fuente para títulos y números
            r"font-size: 2\.5rem",     # Tamaño de títulos principales
            r"font-weight: 700",       # Peso de fuente para títulos
        ],
        "layout": [
            r"border-radius: 12px",    # Radio de bordes unificado
            r"padding: 25px",          # Padding estándar para tarjetas
            r"backdrop-filter: blur\(10px\)",  # Efecto de desenfoque
            r"transform: translateY\(-5px\)",  # Efecto hover
        ],
        "animations": [
            r"transition: all 0\.3s ease",  # Transiciones suaves
            r"box-shadow: 0 10px 30px rgba\(102, 126, 234, 0\.2\)",  # Sombras hover
        ]
    }
    
    results = {}
    
    for filename in key_files:
        filepath = templates_dir / filename
        
        if not filepath.exists():
            print(f"❌ Archivo no encontrado: {filename}")
            continue
            
        print(f"\n📄 Verificando: {filename}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        file_results = {}
        
        for category, patterns in unified_patterns.items():
            matches = 0
            total_patterns = len(patterns)
            
            for pattern in patterns:
                if re.search(pattern, content):
                    matches += 1
                    
            coverage = (matches / total_patterns) * 100 if total_patterns > 0 else 0
            file_results[category] = {
                'matches': matches,
                'total': total_patterns,
                'coverage': coverage
            }
            
            status = "✅" if coverage >= 80 else "⚠️" if coverage >= 50 else "❌"
            print(f"  {status} {category.title()}: {matches}/{total_patterns} ({coverage:.1f}%)")
            
        results[filename] = file_results
    
    # Verificaciones específicas
    print("\n🔍 VERIFICACIONES ESPECÍFICAS")
    print("-" * 40)
    
    # Verificar títulos unificados
    for filename in key_files:
        filepath = templates_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificar clase page-title
            has_page_title = 'class="page-title"' in content
            print(f"  {'✅' if has_page_title else '❌'} {filename}: Clase page-title presente")
            
            # Verificar gradiente de fondo
            has_gradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' in content
            print(f"  {'✅' if has_gradient else '❌'} {filename}: Gradiente unificado presente")
    
    # Resumen general
    print("\n📊 RESUMEN GENERAL")
    print("-" * 40)
    
    overall_coverage = {}
    for category in unified_patterns.keys():
        total_matches = sum(results[f][category]['matches'] for f in results.keys())
        total_possible = sum(results[f][category]['total'] for f in results.keys())
        coverage = (total_matches / total_possible) * 100 if total_possible > 0 else 0
        overall_coverage[category] = coverage
        
        status = "✅" if coverage >= 80 else "⚠️" if coverage >= 50 else "❌"
        print(f"  {status} {category.title()}: {coverage:.1f}% de cobertura general")
    
    avg_coverage = sum(overall_coverage.values()) / len(overall_coverage)
    print(f"\n🎯 Cobertura promedio de estilos unificados: {avg_coverage:.1f}%")
    
    if avg_coverage >= 85:
        print("🎉 ¡Excelente! Los estilos están bien unificados")
    elif avg_coverage >= 70:
        print("👍 Buena unificación, pero hay espacio para mejoras")
    else:
        print("⚠️ Se necesita más trabajo en la unificación de estilos")
    
    return results

if __name__ == "__main__":
    verify_unified_styles()
