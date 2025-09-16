#!/usr/bin/env python3
"""
Script para detectar y traducir artículos en inglés a español
"""

import sys
import os
import sqlite3
import json

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(__file__))

def check_english_articles():
    """Verificar qué artículos están en inglés"""
    try:
        # Conectar a la base de datos
        db_path = "data/geopolitical_intel.db"
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Buscar artículos que probablemente están en inglés
        cursor.execute("""
            SELECT id, title, content, summary, source, original_language, is_translated
            FROM articles 
            WHERE (is_excluded IS NULL OR is_excluded != 1)
            AND (
                title LIKE '%the %' OR title LIKE '%The %' OR
                title LIKE '%and %' OR title LIKE '%in %' OR
                title LIKE '%of %' OR title LIKE '%to %' OR
                title LIKE '%a %' OR title LIKE '%for %' OR
                content LIKE '%the %' OR content LIKE '%and %' OR
                summary LIKE '%the %' OR summary LIKE '%and %'
            )
            ORDER BY id DESC
            LIMIT 20
        """)
        
        articles = cursor.fetchall()
        
        print(f"🔍 Encontrados {len(articles)} artículos que podrían estar en inglés:")
        print("=" * 80)
        
        for article_id, title, content, summary, source, orig_lang, is_translated in articles:
            print(f"ID: {article_id}")
            print(f"Título: {(title or '')[:80]}...")
            print(f"Fuente: {source}")
            print(f"Idioma original: {orig_lang or 'No detectado'}")
            print(f"¿Traducido?: {'Sí' if is_translated else 'No'}")
            
            # Detectar idioma simple
            if title:
                english_indicators = ['the ', 'and ', 'for ', 'with ', 'from ', 'that ', 'this ']
                spanish_indicators = ['el ', 'la ', 'de ', 'que ', 'en ', 'con ', 'para ']
                
                title_lower = title.lower()
                english_count = sum(1 for word in english_indicators if word in title_lower)
                spanish_count = sum(1 for word in spanish_indicators if word in title_lower)
                
                if english_count > spanish_count:
                    print("🇺🇸 Probablemente en INGLÉS")
                elif spanish_count > english_count:
                    print("🇪🇸 Probablemente en ESPAÑOL")
                else:
                    print("❓ Idioma incierto")
            
            print("-" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def translate_sample_articles():
    """Traducir algunos artículos de muestra"""
    try:
        # Importar función de traducción
        try:
            from translation_service import translate_text_robust
            translation_available = True
            print("✅ Servicio de traducción disponible")
        except ImportError:
            translation_available = False
            print("⚠️ Servicio de traducción no disponible, usando traducción básica")
        
        # Conectar a la base de datos
        db_path = "data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener algunos artículos en inglés
        cursor.execute("""
            SELECT id, title, content, summary
            FROM articles 
            WHERE (is_excluded IS NULL OR is_excluded != 1)
            AND (original_language IS NULL OR original_language != 'es')
            AND (
                title LIKE '%the %' OR title LIKE '%The %' OR
                title LIKE '%and %' OR title LIKE '%Breaking%'
            )
            AND (is_translated IS NULL OR is_translated != 1)
            ORDER BY id DESC
            LIMIT 5
        """)
        
        articles = cursor.fetchall()
        
        if not articles:
            print("ℹ️ No se encontraron artículos para traducir")
            conn.close()
            return
        
        print(f"🔄 Traduciendo {len(articles)} artículos de muestra...")
        print("=" * 80)
        
        for article_id, title, content, summary in articles:
            print(f"\n📰 Artículo {article_id}:")
            print(f"Original: {(title or '')[:100]}...")
            
            if translation_available:
                try:
                    # Traducir título
                    if title:
                        translated_title, detected_lang = translate_text_robust(title, 'es')
                        print(f"Traducido: {translated_title[:100]}...")
                        print(f"Idioma detectado: {detected_lang}")
                        
                        # Actualizar en la base de datos (simulación)
                        print("✅ Traducción exitosa (simulación)")
                    else:
                        print("⚠️ Título vacío")
                        
                except Exception as e:
                    print(f"❌ Error traduciendo: {e}")
            else:
                # Traducción básica
                if title:
                    basic_translation = basic_translate_text(title)
                    print(f"Traducción básica: {basic_translation[:100]}...")
                    print("✅ Traducción básica aplicada")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error en traducción: {e}")

def basic_translate_text(text):
    """Traducción básica usando diccionario"""
    if not text:
        return text
    
    translations = {
        'breaking news': 'noticias de última hora',
        'breaking': 'de última hora',
        'news': 'noticias',
        'report': 'informe',
        'the': 'el/la',
        'and': 'y',
        'for': 'para',
        'with': 'con',
        'from': 'desde',
        'in': 'en',
        'to': 'a',
        'of': 'de',
        'government': 'gobierno',
        'military': 'militar',
        'conflict': 'conflicto',
        'war': 'guerra',
        'crisis': 'crisis',
        'president': 'presidente'
    }
    
    result = text
    for english, spanish in translations.items():
        result = result.replace(english, spanish)
        result = result.replace(english.capitalize(), spanish.capitalize())
    
    return result

def main():
    """Función principal"""
    print("🌍 Script de Traducción de Artículos - RiskMap")
    print("=" * 50)
    
    print("\n1. Verificando artículos en inglés...")
    check_english_articles()
    
    print("\n2. Traduciendo artículos de muestra...")
    translate_sample_articles()
    
    print("\n✅ Proceso completado")
    print("\nPara ejecutar la traducción completa, usa:")
    print("POST /api/translate-articles desde la interfaz web")

if __name__ == "__main__":
    main()
