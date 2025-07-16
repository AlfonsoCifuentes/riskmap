#!/usr/bin/env python3
"""
Fix Unicode Logging Issues for Windows
"""

import re
import os

def fix_unicode_in_file(file_path):
    """Replace Unicode emojis with ASCII equivalents"""
    replacements = {
        '🌍': '[GLOBAL]',
        '🔑': '[KEY]',
        '✅': '[OK]',
        '⚠️': '[WARN]',
        'ℹ️': '[INFO]',
        '🔍': '[SEARCH]',
        '📊': '[DATA]',
        '🚀': '[START]',
        '⭐': '[STAR]',
        '📰': '[NEWS]',
        '🌐': '[WEB]',
        '💾': '[SAVE]',
        '🔧': '[TOOL]',
        '📈': '[STATS]',
        '🎯': '[TARGET]',
        '🛡️': '[SECURITY]',
        '📱': '[MOBILE]',
        '💻': '[COMPUTER]',
        '🎨': '[DESIGN]',
        '📝': '[NOTES]',
        '🏆': '[SUCCESS]',
        '❌': '[ERROR]',
        '🔄': '[PROCESS]',
        '📦': '[PACKAGE]',
        '🌟': '[FEATURE]',
        '🎪': '[EVENT]',
        '🎭': '[CATEGORY]',
        '🎨': '[UI]',
        '💼': '[BUSINESS]'
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for emoji, replacement in replacements.items():
            content = content.replace(emoji, replacement)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed Unicode in: {file_path}")
            return True
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False
    
    return False

def main():
    """Fix Unicode issues in all Python files"""
    files_to_fix = [
        'main.py',
        'src/utils/config.py',
        'src/utils/secure_keys.py',
        'src/data_ingestion/global_news_collector.py',
        'src/reporting/report_generator.py',
        'src/nlp_processing/text_analyzer.py',
        'src/monitoring/system_monitor.py',
        'src/dashboard/app.py',
        'src/chatbot/chatbot_app.py'
    ]
    
    workspace_root = r'E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap'
    
    fixed_count = 0
    for file_path in files_to_fix:
        full_path = os.path.join(workspace_root, file_path)
        if os.path.exists(full_path):
            if fix_unicode_in_file(full_path):
                fixed_count += 1
    
    print(f"\n[OK] Fixed Unicode issues in {fixed_count} files")
    print("[OK] System should now work properly on Windows console")

if __name__ == "__main__":
    main()
