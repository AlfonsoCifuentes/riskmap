#!/usr/bin/env python3
"""
Parche específico para YOLO ultralytics - Solución definitiva
"""

def apply_ultralytics_fix():
    """Aplicar solución específica para ultralytics"""
    try:
        import torch
        
        # Agregar globals seguros específicos para ultralytics
        safe_globals = [
            'ultralytics.nn.tasks.DetectionModel',
            'ultralytics.nn.tasks.SegmentationModel', 
            'ultralytics.nn.tasks.ClassificationModel',
            'ultralytics.nn.modules.head.Detect',
            'ultralytics.nn.modules.head.Segment',
            'ultralytics.nn.modules.head.Classify',
            'ultralytics.nn.modules.conv.Conv',
            'ultralytics.nn.modules.block.C2f',
            'ultralytics.nn.modules.block.Bottleneck',
            'collections.OrderedDict',
            'torch.nn.modules.conv.Conv2d',
            'torch.nn.modules.batchnorm.BatchNorm2d',
            'torch.nn.modules.activation.SiLU'
        ]
        
        # Agregar cada clase como global seguro
        for global_class in safe_globals:
            try:
                torch.serialization.add_safe_globals([global_class])
            except:
                pass  # Algunas clases pueden no existir
        
        print("✅ Globals seguros para ultralytics configurados")
        return True
        
    except Exception as e:
        print(f"⚠️ Error configurando globals seguros: {e}")
        return False

def test_ultralytics_with_fix():
    """Probar ultralytics después del parche"""
    print("\n🧪 PROBANDO ULTRALYTICS CON PARCHE ESPECÍFICO")
    print("=" * 50)
    
    # Aplicar el parche primero
    if not apply_ultralytics_fix():
        return False
    
    try:
        from ultralytics import YOLO
        
        # Probar carga de modelo
        model = YOLO('yolov8n.pt')
        print("✅ Modelo YOLO cargado exitosamente con parche específico")
        
        # Probar funcionalidad básica
        print("📋 Información del modelo:")
        print(f"   - Tipo: {type(model)}")
        print(f"   - Modelo cargado: {model.model is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error después del parche específico: {e}")
        return False

if __name__ == "__main__":
    success = test_ultralytics_with_fix()
    if success:
        print("\n✅ PARCHE ESPECÍFICO ULTRALYTICS EXITOSO")
    else:
        print("\n❌ PARCHE ESPECÍFICO FALLÓ")