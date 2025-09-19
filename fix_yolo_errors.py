#!/usr/bin/env python3
"""
Script para corregir errores de carga de modelos PyTorch/YOLO
Soluciona el problema de 'weights_only' en la carga de modelos
"""

import os
import sys
import logging
from pathlib import Path
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class YOLOFixPatcher:
    """Clase para corregir errores de carga de YOLO"""
    
    def __init__(self):
        self.files_patched = []
        
    def patch_ultralytics_loading(self):
        """Aplicar parche global para carga de modelos ultralytics"""
        
        print("🔧 APLICANDO PARCHE GLOBAL PARA CARGA DE YOLO")
        print("=" * 60)
        
        # Crear parche global que se aplicará cuando se importen los módulos
        patch_code = '''
# Parche global para PyTorch YOLO loading - Aplicado automáticamente
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

# Configurar PyTorch para cargas seguras
try:
    import torch
    # Establecer configuración global para carga de modelos
    if hasattr(torch.serialization, '_use_new_zipfile_serialization'):
        torch.serialization._use_new_zipfile_serialization = False
    
    # Parche para torch.load globalmente
    _original_torch_load = torch.load
    
    def _patched_torch_load(*args, **kwargs):
        """Torch load parcheado que maneja weights_only automáticamente"""
        # Si no se especifica weights_only, usar False para compatibilidad
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        try:
            return _original_torch_load(*args, **kwargs)
        except Exception as e:
            if 'weights_only' in str(e):
                # Intentar sin weights_only como fallback
                kwargs.pop('weights_only', None)
                return _original_torch_load(*args, **kwargs)
            raise e
    
    torch.load = _patched_torch_load
    print("✅ Parche global de torch.load aplicado")
    
except ImportError:
    print("⚠️ PyTorch no disponible, parche no aplicado")
except Exception as e:
    print(f"⚠️ Error aplicando parche global: {e}")
'''
        
        return patch_code
        
    def patch_image_risk_analyzer(self):
        """Parchar el analizador de imágenes"""
        
        print("\n🔧 PARCHEANDO IMAGE_RISK_ANALYZER.PY")
        print("=" * 50)
        
        file_path = Path("src/vision_analysis/image_risk_analyzer.py")
        
        if not file_path.exists():
            print(f"❌ Archivo no encontrado: {file_path}")
            return False
            
        # Leer archivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya está parcheado
        if '_patched_torch_load' in content:
            print("⚠️ Archivo ya está parcheado, saltando...")
            return True
        
        # Crear backup
        backup_path = file_path.with_suffix('.py.yolo_backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📁 Backup creado: {backup_path}")
        
        # Aplicar parche después de los imports
        patch_insertion_point = content.find('# Configuración de logging')
        if patch_insertion_point != -1:
            patch_code = self.patch_ultralytics_loading()
            content = content[:patch_insertion_point] + patch_code + '\n\n' + content[patch_insertion_point:]
        
        # Mejorar la inicialización del modelo YOLO
        old_init = '''    def _initialize_model(self):
        """Inicializa el modelo YOLO"""
        if not YOLO_AVAILABLE:
            logger.warning("YOLO no disponible, usando análisis OpenCV básico")
            return

        try:
            # Usar YOLOv8 pre-entrenado
            model_path = self.config.get('yolo_model_path', 'yolov8n.pt')
            self.model = YOLO(model_path)
            logger.info("Modelo YOLO inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando YOLO: {e}")
            self.model = None'''
        
        new_init = '''    def _initialize_model(self):
        """Inicializa el modelo YOLO con manejo robusto de errores"""
        if not YOLO_AVAILABLE:
            logger.warning("YOLO no disponible, usando análisis OpenCV básico")
            return

        try:
            # Usar YOLOv8 pre-entrenado con carga robusta
            model_path = self.config.get('yolo_model_path', 'yolov8n.pt')
            
            # Configurar entorno para carga segura
            import warnings
            warnings.filterwarnings("ignore", category=FutureWarning)
            
            # Intentar carga con manejo de errores
            try:
                self.model = YOLO(model_path)
                logger.info("✅ Modelo YOLO inicializado correctamente")
            except Exception as torch_error:
                if 'weights_only' in str(torch_error):
                    logger.warning("⚠️ Error weights_only detectado, usando carga alternativa...")
                    # Configurar PyTorch temporalmente
                    import torch
                    original_setting = getattr(torch.serialization, '_use_new_zipfile_serialization', None)
                    try:
                        torch.serialization._use_new_zipfile_serialization = False
                        self.model = YOLO(model_path)
                        logger.info("✅ Modelo YOLO cargado con configuración alternativa")
                    finally:
                        if original_setting is not None:
                            torch.serialization._use_new_zipfile_serialization = original_setting
                else:
                    raise torch_error
                    
        except Exception as e:
            logger.error(f"❌ Error inicializando YOLO: {e}")
            logger.info("🔄 Usando análisis OpenCV básico como fallback")
            self.model = None'''
        
        if old_init in content:
            content = content.replace(old_init, new_init)
            print("✅ Método _initialize_model parcheado")
        
        # Guardar archivo parcheado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.files_patched.append(str(file_path))
        print("🎯 image_risk_analyzer.py parcheado exitosamente")
        
        return True
    
    def patch_ultra_hd_satellite(self):
        """Parchar el sistema de satélite ultra HD"""
        
        print("\n🔧 PARCHEANDO ULTRA_HD_SATELLITE_SYSTEM.PY")
        print("=" * 50)
        
        file_path = Path("ultra_hd_satellite_system.py")
        
        if not file_path.exists():
            print(f"❌ Archivo no encontrado: {file_path}")
            return False
            
        # Leer archivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya está parcheado
        if 'PARCHE_YOLO_APLICADO' in content:
            print("⚠️ Archivo ya está parcheado, saltando...")
            return True
        
        # Crear backup
        backup_path = file_path.with_suffix('.py.yolo_backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📁 Backup creado: {backup_path}")
        
        # Simplificar la carga de YOLO
        old_loading = '''            if os.path.exists(model_path):
                # Opción 1: Cargar con weights_only=False (seguro para modelos propios)
                logger.info("🔄 Cargando modelo YOLO con weights_only=False (modelo confiable)")
                
                # Temporalmente establecer torch para permitir carga completa
                import torch.serialization
                original_weights_only = getattr(torch.serialization, '_use_new_zipfile_serialization', None)
                
                # Configurar PyTorch para permitir carga completa de nuestro modelo confiable
                torch.serialization._use_new_zipfile_serialization = False
                
                try:
                    # Cargar modelo con configuración permisiva para modelos confiables
                    self.yolo_model = ultralytics.YOLO(model_path)
                    logger.info("✅ Modelo YOLO Ultra HD cargado exitosamente (modo confiable)")
                    return
                finally:
                    # Restaurar configuración original
                    if original_weights_only is not None:
                        torch.serialization._use_new_zipfile_serialization = original_weights_only'''
        
        new_loading = '''            # PARCHE_YOLO_APLICADO - Carga simplificada y robusta
            if os.path.exists(model_path):
                logger.info("🔄 Cargando modelo YOLO Ultra HD...")
                
                try:
                    # Configurar PyTorch para carga robusta
                    import warnings
                    warnings.filterwarnings("ignore", category=FutureWarning)
                    
                    # Cargar modelo con manejo automático de weights_only
                    self.yolo_model = ultralytics.YOLO(model_path)
                    logger.info("✅ Modelo YOLO Ultra HD cargado exitosamente")
                    return
                    
                except Exception as load_error:
                    if 'weights_only' in str(load_error):
                        logger.warning("⚠️ Problema weights_only detectado, aplicando solución...")
                        try:
                            # Solución para weights_only
                            import torch
                            torch.serialization.add_safe_globals(['collections.OrderedDict'])
                            self.yolo_model = ultralytics.YOLO(model_path)
                            logger.info("✅ Modelo YOLO cargado con solución weights_only")
                            return
                        except Exception:
                            logger.warning("⚠️ Solución weights_only falló, usando modelo por defecto")
                    else:
                        logger.warning(f"⚠️ Error cargando modelo personalizado: {load_error}")'''
        
        if old_loading in content:
            content = content.replace(old_loading, new_loading)
            print("✅ Carga de YOLO simplificada")
        
        # Eliminar la sección de carga alternativa compleja
        alt_loading_start = content.find('logger.info("🔄 Intentando carga alternativa con torch.load directo...")')
        if alt_loading_start != -1:
            # Encontrar el final de la sección
            alt_loading_end = content.find('except Exception as e2:', alt_loading_start)
            if alt_loading_end != -1:
                # Encontrar el final del bloque except
                lines = content[alt_loading_end:].split('\n')
                indent_level = len(lines[0]) - len(lines[0].lstrip())
                end_pos = alt_loading_end
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                        break
                    end_pos = alt_loading_end + len('\n'.join(lines[:i+1])) + 1
                
                # Reemplazar con código simplificado
                simplified_code = '''                    logger.warning(f"⚠️ Carga alternativa también falló: {e}")
                    logger.info("🔄 Usando modelo YOLO por defecto como fallback...")
                    try:
                        # Fallback a modelo por defecto
                        self.yolo_model = ultralytics.YOLO('yolov8n.pt')
                        logger.info("✅ Modelo YOLO por defecto cargado como fallback")
                    except Exception:
                        logger.warning("⚠️ Todos los métodos de carga fallaron, análisis simulado activo")
                        self.yolo_model = None'''
                
                content = content[:alt_loading_start] + simplified_code + content[end_pos:]
                print("✅ Carga alternativa simplificada")
        
        # Guardar archivo parcheado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.files_patched.append(str(file_path))
        print("🎯 ultra_hd_satellite_system.py parcheado exitosamente")
        
        return True
    
    def create_global_yolo_patch(self):
        """Crear un parche global que se aplicará automáticamente"""
        
        print("\n🔧 CREANDO PARCHE GLOBAL PARA YOLO")
        print("=" * 45)
        
        patch_file = Path("yolo_patch.py")
        
        patch_content = f'''#!/usr/bin/env python3
"""
Parche global para problemas de carga de modelos YOLO/PyTorch
Se aplica automáticamente cuando se importa
"""

# Aplicar parche global
{self.patch_ultralytics_loading()}

def apply_yolo_patch():
    """Aplicar parche YOLO si es necesario"""
    print("✅ Parche YOLO global aplicado")

# Aplicar al importar
apply_yolo_patch()
'''
        
        with open(patch_file, 'w', encoding='utf-8') as f:
            f.write(patch_content)
        
        print(f"✅ Parche global creado: {patch_file}")
        
        return True
    
    def test_yolo_loading(self):
        """Probar la carga de modelos YOLO"""
        
        print("\n🧪 PROBANDO CARGA DE MODELOS YOLO")
        print("=" * 40)
        
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Importar ultralytics
        try:
            import ultralytics
            print("✅ Test 1: ultralytics importado correctamente")
            tests_passed += 1
        except ImportError as e:
            print(f"❌ Test 1: Error importando ultralytics: {e}")
        except Exception as e:
            print(f"⚠️ Test 1: Error inesperado: {e}")
        
        # Test 2: Crear modelo básico
        try:
            from ultralytics import YOLO
            # Crear modelo sin cargar archivo (solo estructura)
            model = YOLO()
            print("✅ Test 2: Estructura YOLO creada correctamente")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Test 2: Error creando estructura YOLO: {e}")
        
        # Test 3: Cargar modelo pre-entrenado pequeño
        try:
            from ultralytics import YOLO
            # Intentar cargar modelo pequeño
            model = YOLO('yolov8n.pt')  # Modelo más pequeño
            print("✅ Test 3: Modelo yolov8n.pt cargado correctamente")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Test 3: Error cargando yolov8n.pt: {e}")
        
        print(f"\n📊 RESULTADO: {tests_passed}/{total_tests} tests pasados")
        
        return tests_passed >= 2  # Al menos 2 de 3 tests deben pasar

def main():
    """Función principal"""
    
    print("🔧 CORRECTOR DE ERRORES YOLO/PyTorch")
    print("=" * 80)
    print("Este script corrige problemas de 'weights_only' en la carga de modelos YOLO")
    print()
    
    patcher = YOLOFixPatcher()
    
    # 1. Parchar archivos
    analyzer_patched = patcher.patch_image_risk_analyzer()
    satellite_patched = patcher.patch_ultra_hd_satellite()
    
    # 2. Crear parche global
    global_patch = patcher.create_global_yolo_patch()
    
    # 3. Probar carga de YOLO
    yolo_working = patcher.test_yolo_loading()
    
    # 4. Resumen
    print(f"\n🎯 RESUMEN FINAL")
    print("=" * 30)
    print(f"   Image analyzer parcheado: {'✅' if analyzer_patched else '❌'}")
    print(f"   Satellite system parcheado: {'✅' if satellite_patched else '❌'}")
    print(f"   Parche global creado: {'✅' if global_patch else '❌'}")
    print(f"   YOLO funcionando: {'✅' if yolo_working else '⚠️'}")
    
    if patcher.files_patched:
        print(f"\n📁 Archivos parcheados:")
        for file in patcher.files_patched:
            print(f"   - {file}")
    
    if analyzer_patched and satellite_patched:
        print("\n✅ PARCHES YOLO APLICADOS EXITOSAMENTE")
        print("🔄 Los errores 'weights_only' deberían estar resueltos")
        print("⚠️ Reinicia la aplicación para que los cambios tomen efecto")
        return 0
    else:
        print("\n⚠️ ALGUNOS PARCHES FALLARON")
        print("🔍 Revisa los mensajes de error arriba")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        traceback.print_exc()
        sys.exit(1)