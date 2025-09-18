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

# Find all non-Spanish articles (French and English)
cursor.execute("""
    SELECT id, title, content, summary 
    FROM articles 
    WHERE (
        -- French articles
        (title LIKE '%à%' OR title LIKE '%é%' OR title LIKE '%è%' OR title LIKE '%ç%' OR title LIKE '%ô%' OR title LIKE '%ü%'
         OR content LIKE '%à%' OR content LIKE '%é%' OR content LIKE '%è%' OR content LIKE '%ç%' OR content LIKE '%ô%' OR content LIKE '%ü%'
         OR summary LIKE '%à%' OR summary LIKE '%é%' OR summary LIKE '%è%' OR summary LIKE '%ç%' OR summary LIKE '%ô%' OR summary LIKE '%ü%')
        OR
        -- English articles (common English words/patterns)
        (title LIKE '% the %' OR title LIKE '% and %' OR title LIKE '% of %' OR title LIKE '% to %' 
         OR title LIKE '% in %' OR title LIKE '% for %' OR title LIKE '%The %' OR title LIKE '%And %'
         OR content LIKE '% the %' OR content LIKE '% and %' OR content LIKE '% of %'
         OR summary LIKE '% the %' OR summary LIKE '% and %' OR summary LIKE '% of %')
    )
    AND (title NOT LIKE '%español%' AND title NOT LIKE '%spanish%')
    AND title IS NOT NULL
    ORDER BY published_at DESC
    LIMIT 50
""")

non_spanish_articles = cursor.fetchall()
print(f"Found {len(non_spanish_articles)} potentially non-Spanish articles")

updated_count = 0
failed_count = 0

for article in non_spanish_articles:
    article_id, title, content, summary = article
    
    print(f"\n--- Processing Article {article_id} ---")
    print(f"Original title: {title[:100]}...")
    
    try:
        # Translate title
        translated_title = translator.translate_text(title, target_language='es')
        if isinstance(translated_title, tuple):
            translated_title = translated_title[0]  # Extract string from tuple
        
        # Translate content if available
        translated_content = content
        if content and len(content) > 50:
            try:
                translated_content = translator.translate_text(content, target_language='es')
                if isinstance(translated_content, tuple):
                    translated_content = translated_content[0]  # Extract string from tuple
            except Exception as content_error:
                print(f"  ⚠️ Error translating content: {content_error}")
                translated_content = content  # Keep original
        
        # Translate summary if available
        translated_summary = summary
        if summary and len(summary) > 50:
            try:
                translated_summary = translator.translate_text(summary, target_language='es')
                if isinstance(translated_summary, tuple):
                    translated_summary = translated_summary[0]  # Extract string from tuple
            except Exception as summary_error:
                print(f"  ⚠️ Error translating summary: {summary_error}")
                translated_summary = summary  # Keep original
        
        print(f"Translated title: {translated_title[:100]}...")
        
        # Update database
        cursor.execute("""
            UPDATE articles 
            SET title = ?, content = ?, summary = ?
            WHERE id = ?
        """, (
            translated_title,
            translated_content,
            translated_summary,
            article_id
        ))
        
        updated_count += 1
        print(f"✅ Updated article {article_id}")
        
    except Exception as e:
        print(f"❌ Error translating article {article_id}: {e}")
        failed_count += 1
        
    # Add small delay to respect rate limits
    import time
    time.sleep(0.5)

# Commit changes
conn.commit()
conn.close()

print(f"\n🎉 Translation batch complete!")
print(f"✅ Updated: {updated_count} articles")
print(f"❌ Failed: {failed_count} articles")

# Final verification
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(*) 
    FROM articles 
    WHERE (
        (title LIKE '%à%' OR title LIKE '%é%' OR title LIKE '%è%' OR title LIKE '%ç%' OR title LIKE '%ô%' OR title LIKE '%ü%')
        OR (title LIKE '% the %' OR title LIKE '% and %' OR title LIKE '% of %' OR title LIKE '%The %')
    )
    AND (title NOT LIKE '%español%' AND title NOT LIKE '%spanish%')
""")

remaining_non_spanish = cursor.fetchone()[0]
conn.close()

print(f"Remaining non-Spanish articles (estimate): {remaining_non_spanish}")

if remaining_non_spanish <= 10:
    print("🎉 ¡Casi todos los artículos están ahora en español!")
else:
    print(f"📝 Aún quedan {remaining_non_spanish} artículos por revisar")