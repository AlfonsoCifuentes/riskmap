#!/usr/bin/env python3
"""
Configurador permanente de GTK para WeasyPrint en Windows
========================================================
Agrega el PATH de GTK permanentemente al sistema.
"""

import os
import subprocess
import sys
from pathlib import Path

def add_gtk_to_system_path():
    """Agrega el directorio GTK al PATH del sistema permanentemente."""
    try:
        gtk_path = "C:\\msys64\\mingw64\\bin"
        
        if not Path(gtk_path).exists():
            print(f"❌ Directorio GTK no encontrado: {gtk_path}")
            return False
        
        print(f"🔧 Agregando {gtk_path} al PATH del sistema...")
        
        # Usar setx para agregar permanentemente al PATH
        result = subprocess.run([
            'setx', 'PATH', f"%PATH%;{gtk_path}", '/M'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ GTK agregado permanentemente al PATH del sistema")
            print("🔄 Reinicie la terminal para que los cambios surtan efecto")
            return True
        else:
            print(f"❌ Error agregando al PATH: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_gtk_availability():
    """Prueba si las librerías GTK están disponibles."""
    try:
        # Agregar temporalmente al PATH de esta sesión
        gtk_path = "C:\\msys64\\mingw64\\bin"
        current_path = os.environ.get('PATH', '')
        
        if gtk_path not in current_path:
            os.environ['PATH'] = f"{current_path};{gtk_path}"
        
        # Probar WeasyPrint
        import weasyprint
        html = "<html><body><h1>Test</h1></body></html>"
        weasyprint.HTML(string=html).write_pdf("test_gtk.pdf")
        
        if os.path.exists("test_gtk.pdf"):
            os.remove("test_gtk.pdf")
            print("✅ WeasyPrint funciona correctamente con GTK")
            return True
        else:
            print("❌ WeasyPrint no pudo generar PDF")
            return False
            
    except Exception as e:
        print(f"❌ Error probando GTK: {e}")
        return False

def main():
    print("🌟 Configurador permanente de GTK para WeasyPrint")
    print("=================================================")
    
    # Probar si GTK ya está disponible
    if test_gtk_availability():
        print("✅ GTK ya está disponible y funcionando")
        
        # Preguntar si quiere agregarlo permanentemente
        response = input("\n¿Desea agregar GTK al PATH permanentemente? (s/N): ")
        if response.lower() in ['s', 'si', 'y', 'yes']:
            success = add_gtk_to_system_path()
            if success:
                print("\n🎉 Configuración completada!")
                print("📝 Próximos pasos:")
                print("1. Reiniciar esta terminal")
                print("2. Ejecutar: python main.py --status")
            else:
                print("\n⚠️ No se pudo agregar permanentemente al PATH")
                print("💡 Puede ejecutar temporalmente con:")
                print("$env:PATH += ';C:\\msys64\\mingw64\\bin'; python main.py --status")
        else:
            print("\n💡 Para usar temporalmente, ejecute:")
            print("$env:PATH += ';C:\\msys64\\mingw64\\bin'; python main.py --status")
    else:
        print("❌ GTK no está disponible")
        print("📖 Por favor, ejecute primero: python install_weasyprint_simple.py")
    
    return True

if __name__ == "__main__":
    main()
