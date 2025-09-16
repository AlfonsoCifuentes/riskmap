#!/usr/bin/env python3
"""
Script para eliminar todos los carteles de estado/demostración del proyecto
"""

import os
import re
import glob

def clean_status_banners():
    """Remove all status banners from template files"""
    
    # Patterns to remove
    patterns_to_remove = [
        r'<div class="section-status"><div class="data-status fallback-data"><i class="fas fa-brain"></i><span>Análisis basado en datos RSS</span></div></div>',
        r'<div class="section-status"><div class="data-status simulation"><i class="fas fa-satellite"></i><span>Imágenes satelitales simuladas</span></div></div>',
        r'<div class="data-status fallback-data">\s*<i class="fas fa-brain"></i>\s*<span>Análisis basado en datos RSS</span>\s*</div>',
        r'<div class="data-status real-data">\s*<i class="fas fa-chart-line"></i>\s*<span>Análisis basado en datos RSS reales</span>\s*</div>',
        r'<div class="data-status simulation">\s*<i class="fas fa-satellite"></i>\s*<span>Imágenes satelitales simuladas</span>\s*</div>',
        r'<div class="data-status">\s*<i class="fas fa-.*"></i>\s*<span>Sistema en modo demostración.*</span>\s*</div>',
        r'<div class="data-status">\s*<i class="fas fa-.*"></i>\s*<span>Sistema en desarrollo.*</span>\s*</div>',
        r'<div class="data-status">\s*<i class="fas fa-.*"></i>\s*<span>Fuentes RSS en tiempo real</span>\s*</div>',
        r'<div class="data-status">\s*<i class="fas fa-.*"></i>\s*<span>Análisis IA basado en datos RSS</span>\s*</div>',
    ]
    
    # Files to process
    template_files = [
        'src/web/templates/*.html',
        'src/dashboard/templates/*.html'
    ]
    
    processed_files = []
    
    for pattern in template_files:
        files = glob.glob(pattern)
        for file_path in files:
            if os.path.exists(file_path):
                print(f"🔧 Processing: {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply all removal patterns
                for remove_pattern in patterns_to_remove:
                    content = re.sub(remove_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
                
                # Clean up extra empty lines
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"   ✅ Cleaned status banners from {file_path}")
                    processed_files.append(file_path)
                else:
                    print(f"   ℹ️ No changes needed in {file_path}")
    
    print(f"\n🎉 Processing complete! Modified {len(processed_files)} files:")
    for file_path in processed_files:
        print(f"   - {file_path}")

if __name__ == "__main__":
    clean_status_banners()
