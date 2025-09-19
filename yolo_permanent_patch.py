"""
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
