#!/usr/bin/env python3
"""
AUDITORÍA SISTEMÁTICA DEL WEBSITE - RISKMAP
==========================================

Plan metódico para verificar y actualizar cada página del website
asegurando que use la estructura unificada de base de datos.
"""

def audit_plan():
    """Plan de auditoría sistemática"""
    print("🔍 PLAN DE AUDITORÍA SISTEMÁTICA DEL WEBSITE")
    print("=" * 80)
    
    # Páginas principales del navbar (en orden de revisión)
    pages_to_audit = [
        {
            'route': '/news-analysis',
            'template': 'dashboard_BUENO.html',
            'description': 'Página de análisis de noticias (PRIORITARIA - Error reportado)',
            'api_endpoints': ['/api/articles', '/api/hero-article', '/api/articles/deduplicated'],
            'priority': 1
        },
        {
            'route': '/dashboard',
            'template': 'dashboard_BUENO.html', 
            'description': 'Dashboard principal',
            'api_endpoints': ['/api/articles', '/api/status'],
            'priority': 2
        },
        {
            'route': '/conflict-monitoring',
            'template': 'conflict_monitoring.html',
            'description': 'Monitoreo de conflictos',
            'api_endpoints': ['/api/conflict-regions', '/api/gdelt-events'],
            'priority': 3
        },
        {
            'route': '/satellite-analysis', 
            'template': 'satellite_analysis.html',
            'description': 'Análisis satelital',
            'api_endpoints': ['/api/satellite-data'],
            'priority': 4
        },
        {
            'route': '/trends-analysis',
            'template': 'trends_analysis.html', 
            'description': 'Análisis de tendencias',
            'api_endpoints': ['/api/articles'],
            'priority': 5
        },
        {
            'route': '/early-warning',
            'template': 'early_warning.html',
            'description': 'Sistema de alerta temprana',
            'api_endpoints': ['/api/articles', '/api/status'],
            'priority': 6
        },
        {
            'route': '/executive-reports',
            'template': 'executive_reports.html',
            'description': 'Reportes ejecutivos', 
            'api_endpoints': ['/api/articles'],
            'priority': 7
        },
        {
            'route': '/data-intelligence',
            'template': 'data_intelligence.html',
            'description': 'Inteligencia de datos',
            'api_endpoints': ['/api/articles', '/api/external-feeds'],
            'priority': 8
        },
        {
            'route': '/video-surveillance',
            'template': 'video_surveillance.html',
            'description': 'Video vigilancia',
            'api_endpoints': [],
            'priority': 9
        }
    ]
    
    print("📋 PÁGINAS IDENTIFICADAS PARA AUDITORÍA:")
    for page in pages_to_audit:
        priority_icon = "🚨" if page['priority'] <= 2 else "⚠️" if page['priority'] <= 5 else "📝"
        print(f"{priority_icon} P{page['priority']} - {page['route']}")
        print(f"     Template: {page['template']}")
        print(f"     APIs: {', '.join(page['api_endpoints']) if page['api_endpoints'] else 'Ninguna'}")
        print(f"     Descripción: {page['description']}")
        print()
    
    return pages_to_audit

def audit_checklist():
    """Lista de verificación para cada página"""
    print("✅ CHECKLIST DE AUDITORÍA POR PÁGINA")
    print("=" * 80)
    
    checklist_items = [
        "🗄️ Verificar queries SQL usan 'unified_articles' en lugar de 'articles'",
        "🔍 Comprobar que los nombres de columnas son correctos",
        "📊 Validar que los endpoints API funcionan sin errores",
        "🌐 Revisar que el template existe y está accesible", 
        "⚡ Verificar que los datos se cargan correctamente",
        "🎯 Comprobar filtros y ordenamiento usando nuevas columnas",
        "📱 Validar respuesta JSON de endpoints",
        "🔧 Actualizar JavaScript si es necesario para nuevos campos"
    ]
    
    for i, item in enumerate(checklist_items, 1):
        print(f"{i}. {item}")
    
    return checklist_items

if __name__ == "__main__":
    pages = audit_plan()
    checklist = audit_checklist()
    
    print("🎯 INICIANDO AUDITORÍA SISTEMÁTICA")
    print("=" * 80)
    print("Empezando por /news-analysis como solicitado...")