"""
Instalador simple de WeasyPrint para Windows usando MSYS2/winget
================================================================
"""

import subprocess
import sys
import os
from pathlib import Path

def install_via_winget():
    """Instala GTK usando winget (Windows Package Manager)."""
    try:
        print("🔧 Intentando instalar GTK via winget...")
        
        # Verificar si winget está disponible
        result = subprocess.run(['winget', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ winget no está disponible")
            return False
        
        # Instalar MSYS2 que incluye GTK
        print("📦 Instalando MSYS2...")
        result = subprocess.run([
            'winget', 'install', '--id', 'MSYS2.MSYS2', '--silent'
        ], check=True)
        
        print("✅ MSYS2 instalado. Configurando GTK...")
        
        # Configurar PATH para MSYS2
        msys2_path = Path("C:/msys64/mingw64/bin")
        if msys2_path.exists():
            current_path = os.environ.get('PATH', '')
            if str(msys2_path) not in current_path:
                os.environ['PATH'] = f"{msys2_path};{current_path}"
                print(f"✅ MSYS2 agregado al PATH: {msys2_path}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando via winget: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def install_via_conda():
    """Instala GTK usando conda-forge."""
    try:
        print("🔧 Intentando instalar GTK via conda...")
        
        # Verificar si conda está disponible
        result = subprocess.run(['conda', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ conda no está disponible")
            return False
        
        # Instalar gtk3 y dependencias
        print("📦 Instalando GTK3 desde conda-forge...")
        result = subprocess.run([
            'conda', 'install', '-c', 'conda-forge', 'gtk3', '-y'
        ], check=True)
        
        print("✅ GTK3 instalado via conda")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando via conda: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_weasyprint():
    """Prueba WeasyPrint."""
    try:
        print("🧪 Probando WeasyPrint...")
        from weasyprint import HTML
        
        html_content = "<html><body><h1>Test</h1></body></html>"
        HTML(string=html_content).write_pdf("test.pdf")
        
        if os.path.exists("test.pdf"):
            os.remove("test.pdf")
            print("✅ WeasyPrint funciona correctamente!")
            return True
        else:
            print("❌ WeasyPrint no pudo generar PDF")
            return False
            
    except Exception as e:
        print(f"❌ Error probando WeasyPrint: {e}")
        return False

def main():
    print("🌟 Instalador simplificado de WeasyPrint para Windows")
    print("===================================================")
    
    # Probar si ya funciona
    if test_weasyprint():
        print("🎉 WeasyPrint ya funciona!")
        return True
    
    # Método 1: winget
    print("\n🔄 Método 1: Instalación via winget...")
    if install_via_winget():
        if test_weasyprint():
            print("🎉 ¡Éxito con winget!")
            return True
    
    # Método 2: conda
    print("\n🔄 Método 2: Instalación via conda...")
    if install_via_conda():
        if test_weasyprint():
            print("🎉 ¡Éxito con conda!")
            return True
    
    # Si nada funciona, mostrar instrucciones manuales
    print("\n❌ Instalación automática falló")
    print("\n📖 Instrucciones manuales:")
    print("1. Instalar MSYS2 desde https://www.msys2.org/")
    print("2. Abrir terminal MSYS2 y ejecutar:")
    print("   pacman -S mingw-w64-x86_64-gtk3")
    print("3. Agregar C:\\msys64\\mingw64\\bin al PATH del sistema")
    print("4. Reiniciar la terminal y probar python main.py --status")
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
