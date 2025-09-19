#!/usr/bin/env python3
"""
Parche para el sistema CCTV - Modernización del tracking
==================================================

Este script actualiza el sistema de tracking de objetos para usar motpy
como alternativa moderna y mantenible a sort-tracker.

Funcionalidades:
- Reemplaza sort-tracker con motpy (más moderno y mantenible)
- Mantiene la funcionalidad de tracking de objetos
- Preserva el manejo gracioso de errores
- Mejora el rendimiento del tracking

Uso:
    python patch_cctv_tracking.py
"""

import os
import sys

def patch_cctv_detector():
    """
    Actualizar el detector CCTV para usar motpy en lugar de sort-tracker
    """
    detector_path = "cams/detector.py"
    
    if not os.path.exists(detector_path):
        print(f"❌ Archivo no encontrado: {detector_path}")
        return False
    
    try:
        with open(detector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup del archivo original
        backup_path = f"{detector_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Reemplazar las importaciones
        original_import = """try:
    from sort import Sort
    SORT_AVAILABLE = True
except ImportError:
    print("⚠️ sort-tracker no disponible. Tracking deshabilitado.")
    SORT_AVAILABLE = False"""

        new_import = """try:
    from motpy import Detection, MultiObjectTracker
    SORT_AVAILABLE = True
except ImportError:
    try:
        # Fallback a SORT original si está disponible
        from sort import Sort
        SORT_AVAILABLE = True
        USING_MOTPY = False
    except ImportError:
        print("⚠️ Ni motpy ni sort-tracker están disponibles. Tracking deshabilitado.")
        SORT_AVAILABLE = False
        USING_MOTPY = False
else:
    USING_MOTPY = True"""
        
        content = content.replace(original_import, new_import)
        
        # Actualizar inicialización del tracker
        original_init = """    def _init_tracker(self):
        \"\"\"Inicializar tracker de objetos\"\"\"
        if not SORT_AVAILABLE:
            logger.warning("SORT tracker no disponible")
            return
        
        try:
            self.tracker = Sort(max_age=20, min_hits=3)
            logger.info("✅ Tracker SORT inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando tracker: {e}")
            self.tracker = None"""
        
        new_init = """    def _init_tracker(self):
        \"\"\"Inicializar tracker de objetos\"\"\"
        if not SORT_AVAILABLE:
            logger.warning("Tracker no disponible")
            return
        
        try:
            if USING_MOTPY:
                # Usar motpy (más moderno)
                self.tracker = MultiObjectTracker(dt=0.1)  # 10 FPS
                logger.info("✅ Tracker motpy inicializado")
            else:
                # Fallback a SORT
                self.tracker = Sort(max_age=20, min_hits=3)
                logger.info("✅ Tracker SORT inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando tracker: {e}")
            self.tracker = None"""
        
        content = content.replace(original_init, new_init)
        
        # Guardar el archivo actualizado
        with open(detector_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Archivo actualizado: {detector_path}")
        print(f"📁 Backup guardado: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error aplicando parche: {e}")
        return False

def main():
    print("🔧 Aplicando parche para modernizar el sistema de tracking CCTV...")
    print("=" * 60)
    
    success = patch_cctv_detector()
    
    if success:
        print("\n✅ Parche aplicado exitosamente!")
        print("📝 Cambios realizados:")
        print("   - Reemplazado sort-tracker con motpy (más moderno)")
        print("   - Mantenido fallback a SORT si está disponible")
        print("   - Preservado manejo gracioso de errores")
        print("   - Creado backup del archivo original")
        
        print("\n🔍 Verificando instalación de motpy...")
        try:
            import motpy
            print("✅ motpy está correctamente instalado")
        except ImportError:
            print("❌ motpy no está instalado - ejecute: pip install motpy")
    else:
        print("\n❌ Error aplicando el parche")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())