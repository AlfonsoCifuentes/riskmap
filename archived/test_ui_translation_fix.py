#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar:
1. Eliminación de contenido superpuesto en mosaico
2. Sistema de traducción funcionando
"""

import requests
import json
import time
from typing import Dict, Any

class UITranslationTester:
    def __init__(self, base_url='http://localhost:5001'):
        self.base_url = base_url
    
    def test_translation_endpoint(self):
        """Probar endpoint de traducción"""
        print("🔍 Probando endpoint de traducción...")
        
        test_texts = [
            "Breaking News: Major Political Event Unfolds",
            "International Crisis Develops Rapidly",
            "Global Economic Impact Expected"
        ]
        
        for text in test_texts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/translate",
                    json={
                        'text': text,
                        'target_lang': 'es'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"✅ '{text}' → '{data['translated_text']}'")
                    else:
                        print(f"❌ Error en traducción: {data.get('error')}")
                else:
                    print(f"❌ Error HTTP {response.status_code}: {response.text}")
                    
            except requests.RequestException as e:
                print(f"❌ Error de conexión: {e}")
            
            time.sleep(0.5)
    
    def test_articles_endpoint(self):
        """Probar endpoint de artículos"""
        print("\n🔍 Probando endpoint de artículos...")
        
        try:
            response = requests.get(f"{self.base_url}/api/articles?limit=3", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('articles'):
                    articles = data['articles'][:3]
                    print(f"✅ {len(articles)} artículos cargados")
                    
                    for i, article in enumerate(articles, 1):
                        title = article.get('title', 'Sin título')[:50]
                        has_image = bool(article.get('image_url') or article.get('image'))
                        
                        print(f"  📰 Artículo {i}: {title}... [Imagen: {'✅' if has_image else '❌'}]")
                else:
                    print(f"❌ No se encontraron artículos: {data}")
            else:
                print(f"❌ Error HTTP {response.status_code}: {response.text}")
                
        except requests.RequestException as e:
            print(f"❌ Error de conexión: {e}")
    
    def generate_test_report(self):
        """Generar reporte de pruebas"""
        print("\n" + "="*60)
        print("📋 REPORTE DE PRUEBAS - UI y TRADUCCIÓN")
        print("="*60)
        
        # Prueba 1: Endpoint de traducción
        print("\n🔧 PRUEBA 1: Sistema de Traducción")
        self.test_translation_endpoint()
        
        # Prueba 2: Artículos
        print("\n🔧 PRUEBA 2: Artículos del Mosaico")
        self.test_articles_endpoint()
        
        # Instrucciones finales
        print(f"\n" + "="*60)
        print("📋 INSTRUCCIONES PARA VERIFICACIÓN MANUAL:")
        print("="*60)
        print(f"1. 🌐 Abre: {self.base_url}")
        print("2. 🔍 Inspecciona los artículos del mosaico:")
        print("   - ✅ Solo debería aparecer el TÍTULO sobre la imagen")
        print("   - ❌ NO debería aparecer ubicación, badges o contenido extra")
        print("   - 🇪🇸 Todos los títulos deberían estar en ESPAÑOL")
        print("3. 🖱️ Usa F12 y verifica la consola:")
        print("   - Busca mensajes de traducción: '📖 Traduciendo título'")
        print("   - Verifica errores: '❌ Error durante la traducción'")
        print("4. 🔄 Recarga la página para probar múltiples veces")

def main():
    print("🚀 Iniciando pruebas de UI y Traducción...")
    print("⚠️ ASEGÚRATE de que el servidor esté corriendo (app_BUENA.py)")
    
    # Esperar confirmación
    input("🔵 Presiona ENTER cuando el servidor esté funcionando...")
    
    tester = UITranslationTester()
    tester.generate_test_report()
    
    print(f"\n✅ Pruebas completadas. Revisa los resultados arriba.")
    print(f"💡 Si algo no funciona, verifica que el servidor esté corriendo en puerto 5001")

if __name__ == "__main__":
    main()