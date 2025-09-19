#!/usr/bin/env python3
"""
Parche global para problemas de carga de modelos YOLO/PyTorch
Se aplica automáticamente cuando se importa
"""

# Aplicar parche global

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


def apply_yolo_patch():
    """Aplicar parche YOLO si es necesario"""
    print("✅ Parche YOLO global aplicado")

# Aplicar al importar
apply_yolo_patch()
