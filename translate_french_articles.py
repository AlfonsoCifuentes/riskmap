#!/usr/bin/env python3

import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from robust_translation_v3 import UltraRobustTranslationService
import traceback

# Initialize translator
translator = UltraRobustTranslationService()

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Find French articles
cursor.execute("""
    SELECT id, title, content, summary 
    FROM articles 
    WHERE (title LIKE '%à%' OR title LIKE '%é%' OR title LIKE '%è%' OR title LIKE '%ç%' OR title LIKE '%ô%' OR title LIKE '%ü%'
           OR content LIKE '%à%' OR content LIKE '%é%' OR content LIKE '%è%' OR content LIKE '%ç%' OR content LIKE '%ô%' OR content LIKE '%ü%'
           OR summary LIKE '%à%' OR summary LIKE '%é%' OR summary LIKE '%è%' OR summary LIKE '%ç%' OR summary LIKE '%ô%' OR summary LIKE '%ü%')
    AND (title NOT LIKE '%español%' AND title NOT LIKE '%spanish%')
    ORDER BY published_at DESC
    LIMIT 20
""")

french_articles = cursor.fetchall()
print(f"Found {len(french_articles)} potentially French articles")

updated_count = 0

for article in french_articles:
    article_id, title, content, summary = article
    
    print(f"\n--- Processing Article {article_id} ---")
    print(f"Original title: {title[:100]}...")
    
    try:
        # Translate title
        translated_title = translator.translate_text(title, target_language='es')
        if isinstance(translated_title, tuple):
            translated_title = translated_title[0]  # Extract string from tuple
        
        # Translate content if available
        translated_content = None
        if content:
            translated_content = translator.translate_text(content, target_language='es')
            if isinstance(translated_content, tuple):
                translated_content = translated_content[0]  # Extract string from tuple
        
        # Translate summary if available
        translated_summary = None
        if summary:
            translated_summary = translator.translate_text(summary, target_language='es')
            if isinstance(translated_summary, tuple):
                translated_summary = translated_summary[0]  # Extract string from tuple
        
        print(f"Translated title: {translated_title[:100]}...")
        
        # Update database
        cursor.execute("""
            UPDATE articles 
            SET title = ?, content = ?, summary = ?
            WHERE id = ?
        """, (
            translated_title,
            translated_content or content,  # Keep original if translation fails
            translated_summary or summary,  # Keep original if translation fails
            article_id
        ))
        
        updated_count += 1
        print(f"✅ Updated article {article_id}")
        
    except Exception as e:
        print(f"❌ Error translating article {article_id}: {e}")
        traceback.print_exc()

# Commit changes
conn.commit()
conn.close()

print(f"\n🎉 Translation complete!")
print(f"Updated {updated_count} articles to Spanish")

# Verify no more French articles remain
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(*) 
    FROM articles 
    WHERE (title LIKE '%à%' OR title LIKE '%é%' OR title LIKE '%è%' OR title LIKE '%ç%' OR title LIKE '%ô%' OR title LIKE '%ü%'
           OR content LIKE '%à%' OR content LIKE '%é%' OR content LIKE '%è%' OR content LIKE '%ç%' OR content LIKE '%ô%' OR content LIKE '%ü%'
           OR summary LIKE '%à%' OR summary LIKE '%é%' OR summary LIKE '%è%' OR summary LIKE '%ç%' OR summary LIKE '%ô%' OR summary LIKE '%ü%')
    AND (title NOT LIKE '%español%' AND title NOT LIKE '%spanish%')
""")

remaining_french = cursor.fetchone()[0]
conn.close()

print(f"Remaining potentially French articles: {remaining_french}")