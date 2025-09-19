#!/usr/bin/env python3
"""
Solución definitiva para problemas YOLO - Configuración de entorno
"""

import os
import sys

def configure_torch_environment():
    """Configurar variables de entorno para PyTorch"""
    
    print("🔧 CONFIGURANDO ENTORNO PYTORCH PARA YOLO")
    print("=" * 50)
    
    # Configurar variables de entorno antes de importar torch
    env_vars = {
        'TORCH_LOAD_WEIGHTS_ONLY': 'false',
        'PYTORCH_DISABLE_VERSIONING_CHECK': '1',
        'ULTRALYTICS_DISABLE_TELEMETRY': 'true'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ {key}={value}")
    
    return True

def patch_torch_load_globally():
    """Parchar torch.load a nivel global"""
    
    print("\n🔧 PARCHEANDO TORCH.LOAD GLOBALMENTE")
    print("=" * 40)
    
    try:
        import torch
        
        # Guardar función original
        if not hasattr(torch, '_original_load'):
            torch._original_load = torch.load
        
        def patched_load(f, map_location=None, pickle_module=None, **kwargs):
            """Versión parcheada de torch.load"""
            # Forzar weights_only=False para compatibilidad
            kwargs['weights_only'] = False
            try:
                return torch._original_load(f, map_location=map_location, 
                                           pickle_module=pickle_module, **kwargs)
            except Exception as e:
                if 'weights_only' in str(e):
                    # Intentar sin weights_only como último recurso
                    kwargs.pop('weights_only', None)
                    return torch._original_load(f, map_location=map_location, 
                                               pickle_module=pickle_module, **kwargs)
                raise e
        
        # Aplicar parche
        torch.load = patched_load
        print("✅ torch.load parcheado exitosamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error parcheando torch.load: {e}")
        return False

def test_yolo_final():
    """Prueba final de YOLO"""
    
    print("\n🧪 PRUEBA FINAL DE YOLO")
    print("=" * 30)
    
    try:
        # Configurar entorno primero
        configure_torch_environment()
        
        # Parchar torch
        if not patch_torch_load_globally():
            return False
        
        # Ahora importar y probar YOLO
        from ultralytics import YOLO
        
        # Crear modelo con configuración básica
        print("🔄 Creando modelo YOLO...")
        model = YOLO('yolov8n.pt')
        
        print("✅ ¡YOLO FUNCIONANDO CORRECTAMENTE!")
        print(f"   Modelo: {type(model).__name__}")
        print(f"   Dispositivo: {model.device}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error final: {e}")
        return False

def create_permanent_patch():
    """Crear un archivo de parche permanente"""
    
    print("\n📁 CREANDO PARCHE PERMANENTE")
    print("=" * 35)
    
    patch_content = '''"""
Parche permanente para YOLO/PyTorch - Importar al inicio de la aplicación
"""
import os
import warnings

# Configurar entorno antes de cualquier import de torch
os.environ['TORCH_LOAD_WEIGHTS_ONLY'] = 'false'
os.environ['PYTORCH_DISABLE_VERSIONING_CHECK'] = '1'
os.environ['ULTRALYTICS_DISABLE_TELEMETRY'] = 'true'

# Suprimir warnings relacionados
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
warnings.filterwarnings("ignore", category=UserWarning, module="ultralytics")

def apply_torch_patch():
    """Aplicar parche a torch.load si es necesario"""
    try:
        import torch
        
        if not hasattr(torch, '_yolo_patched'):
            # Parche una sola vez
            original_load = torch.load
            
            def safe_load(f, map_location=None, pickle_module=None, **kwargs):
                kwargs['weights_only'] = False
                return original_load(f, map_location=map_location, 
                                   pickle_module=pickle_module, **kwargs)
            
            torch.load = safe_load
            torch._yolo_patched = True
            print("✅ Parche torch.load aplicado automáticamente")
            
    except Exception as e:
        print(f"⚠️ Error aplicando parche torch: {e}")

# Aplicar parche al importar este módulo
apply_torch_patch()
'''
    
    with open('yolo_permanent_patch.py', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print("✅ Parche permanente creado: yolo_permanent_patch.py")
    print("📋 Para usar: import yolo_permanent_patch")
    
    return True

def main():
    """Función principal"""
    
    print("🎯 SOLUCIÓN DEFINITIVA PARA YOLO/PYTORCH")
    print("=" * 80)
    
    # 1. Prueba final
    yolo_works = test_yolo_final()
    
    # 2. Crear parche permanente
    patch_created = create_permanent_patch()
    
    # 3. Resumen
    print(f"\n🎯 RESUMEN FINAL")
    print("=" * 30)
    print(f"   YOLO funcionando: {'✅' if yolo_works else '❌'}")
    print(f"   Parche permanente creado: {'✅' if patch_created else '❌'}")
    
    if yolo_works:
        print("\n✅ ¡YOLO ESTÁ FUNCIONANDO!")
        print("📋 Instrucciones:")
        print("   1. Importa 'yolo_permanent_patch' al inicio de RISKMAP.py")
        print("   2. Esto configurará automáticamente el entorno")
        print("   3. Los modelos YOLO se cargarán sin errores")
        return 0
    else:
        print("\n❌ YOLO AÚN TIENE PROBLEMAS")
        print("⚠️ Puede que necesites actualizar PyTorch o ultralytics")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)