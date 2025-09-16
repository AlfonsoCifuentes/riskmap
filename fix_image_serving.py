#!/usr/bin/env python3
"""
Solución definitiva: Mover imágenes a la ubicación correcta donde Flask las puede servir
"""
import os
import shutil
from pathlib import Path

def fix_image_location():
    """Mover imágenes de ./static/images/news/ a src/web/static/images/news/"""
    
    print("🔧 SOLUCIÓN: Moviendo imágenes a la ubicación correcta")
    print("=" * 60)
    
    # Directorios
    source_dir = Path("./static/images/news")
    target_dir = Path("./src/web/static/images/news")
    
    print(f"📂 Origen: {source_dir}")
    print(f"📂 Destino: {target_dir}")
    
    # Verificar origen
    if not source_dir.exists():
        print(f"❌ ERROR: Directorio origen no existe")
        return False
    
    # Crear directorio destino si no existe
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directorio destino creado: {target_dir}")
    
    # Listar archivos a mover
    image_files = list(source_dir.glob("news_*"))
    print(f"📊 Archivos encontrados: {len(image_files)}")
    
    # Mover archivos
    moved = 0
    for img_file in image_files:
        try:
            target_file = target_dir / img_file.name
            
            # Si ya existe, comparar tamaños
            if target_file.exists():
                source_size = img_file.stat().st_size
                target_size = target_file.stat().st_size
                if source_size == target_size:
                    print(f"   ⏭️  {img_file.name}: Ya existe con mismo tamaño")
                    continue
                else:
                    print(f"   🔄 {img_file.name}: Sobrescribiendo (tamaños diferentes)")
            
            # Mover archivo
            shutil.move(str(img_file), str(target_file))
            print(f"   ✅ {img_file.name}: Movido ({img_file.stat().st_size:,} bytes)")
            moved += 1
            
        except Exception as e:
            print(f"   ❌ {img_file.name}: ERROR - {e}")
    
    print(f"\n📋 RESULTADO:")
    print(f"   📁 Archivos movidos: {moved}")
    print(f"   📁 Archivos totales en destino: {len(list(target_dir.glob('news_*')))}")
    
    # Verificar directorio origen
    remaining = list(source_dir.glob("news_*"))
    if len(remaining) == 0:
        print(f"   🗑️  Directorio origen vacío, eliminando...")
        try:
            source_dir.rmdir()
            print(f"   ✅ Directorio origen eliminado")
        except:
            print(f"   ⚠️  No se pudo eliminar directorio origen")
    else:
        print(f"   ⚠️  Quedan {len(remaining)} archivos en origen")
    
    return moved > 0

def verify_new_location():
    """Verificar que las imágenes están en la nueva ubicación"""
    
    print(f"\n🔍 VERIFICACIÓN:")
    target_dir = Path("./src/web/static/images/news")
    
    if target_dir.exists():
        files = list(target_dir.glob("news_*"))
        print(f"   ✅ Directorio existe: {target_dir}")
        print(f"   📊 Archivos: {len(files)}")
        
        # Mostrar primeros 5
        for f in files[:5]:
            size = f.stat().st_size
            print(f"      - {f.name}: {size:,} bytes")
        
        if len(files) > 5:
            print(f"      ... y {len(files) - 5} más")
            
    else:
        print(f"   ❌ Directorio no existe: {target_dir}")
        return False
    
    return len(files) > 0

def main():
    """Función principal"""
    success = fix_image_location()
    
    if success:
        verify_new_location()
        print(f"\n🎉 SOLUCIÓN APLICADA")
        print(f"✅ Flask ahora puede servir las imágenes desde /static/images/news/")
        print(f"🔗 URLs funcionarán: http://localhost:5001/static/images/news/news_xxx.jpg")
    else:
        print(f"\n❌ No se pudo aplicar la solución")

if __name__ == "__main__":
    main()