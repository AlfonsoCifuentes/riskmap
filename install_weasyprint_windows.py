#!/usr/bin/env python3
"""
Instalador de WeasyPrint para Windows
====================================
Soluciona el problema de las dependencias GTK en Windows.
"""

import os
import sys
import subprocess
import requests
import tempfile
import shutil
from pathlib import Path
import zipfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_file(url: str, filename: str) -> bool:
    """Descarga un archivo desde una URL."""
    try:
        logger.info(f"Descargando {filename} desde {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"✅ Descarga completada: {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Error descargando {filename}: {e}")
        return False

def install_gtk_runtime():
    """Instala GTK runtime necesario para WeasyPrint en Windows."""
    try:
        logger.info("🔧 Instalando GTK runtime para Windows...")
        
        # URL del instalador GTK3 para Windows (versión más reciente)
        gtk_url = "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe"
        
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            installer_path = os.path.join(temp_dir, "gtk3-installer.exe")
            
            # Descargar instalador
            if not download_file(gtk_url, installer_path):
                return False
            
            # Ejecutar instalador silenciosamente
            logger.info("🔧 Ejecutando instalador GTK3...")
            try:
                result = subprocess.run([
                    installer_path, 
                    "/S",  # Instalación silenciosa
                    "/AddToPath=yes"  # Agregar al PATH
                ], check=True, capture_output=True, text=True)
                
                logger.info("✅ GTK3 runtime instalado exitosamente")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Error ejecutando instalador: {e}")
                logger.error(f"stdout: {e.stdout}")
                logger.error(f"stderr: {e.stderr}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error instalando GTK runtime: {e}")
        return False

def install_gtk_portable():
    """Instala GTK de forma portable (alternativa)."""
    try:
        logger.info("🔧 Instalando GTK portable...")
        
        # URL del GTK portable (versión alternativa que funciona)
        gtk_url = "https://github.com/wingtk/gvsbuild/releases/download/2023.3.1/GTK3_Gvsbuild_2023.3.1_x64.zip"
        
        # Directorio de instalación
        install_dir = Path("C:/gtk3")
        install_dir.mkdir(exist_ok=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "gtk3.zip")
            
            # Descargar ZIP
            if not download_file(gtk_url, zip_path):
                return False
            
            # Extraer
            logger.info("📦 Extrayendo GTK3...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(str(install_dir))
            
            # Agregar al PATH
            gtk_bin_path = str(install_dir / "bin")
            current_path = os.environ.get('PATH', '')
            
            if gtk_bin_path not in current_path:
                logger.info("🔧 Agregando GTK3 al PATH...")
                # Agregar temporalmente al PATH de esta sesión
                os.environ['PATH'] = f"{gtk_bin_path};{current_path}"
                
                # Mensaje para agregar permanentemente
                logger.info(f"📝 Para hacer permanente, agregar al PATH del sistema: {gtk_bin_path}")
            
            logger.info("✅ GTK3 portable instalado exitosamente")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error instalando GTK portable: {e}")
        return False

def test_weasyprint():
    """Prueba si WeasyPrint funciona correctamente."""
    try:
        logger.info("🧪 Probando WeasyPrint...")
        
        from weasyprint import HTML
        
        # HTML de prueba
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Test</title>
        </head>
        <body>
            <h1>Test WeasyPrint</h1>
            <p>Si ves este PDF, WeasyPrint funciona correctamente.</p>
        </body>
        </html>
        """
        
        # Crear PDF de prueba
        test_pdf = "test_weasyprint.pdf"
        HTML(string=html_content).write_pdf(test_pdf)
        
        if os.path.exists(test_pdf):
            logger.info("✅ WeasyPrint funciona correctamente!")
            os.remove(test_pdf)
            return True
        else:
            logger.error("❌ WeasyPrint no pudo generar PDF")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando WeasyPrint: {e}")
        return False

def main():
    """Función principal del instalador."""
    logger.info("🌟 Instalador de WeasyPrint para Windows")
    logger.info("=====================================")
    
    # Verificar si ya funciona
    if test_weasyprint():
        logger.info("🎉 WeasyPrint ya funciona correctamente!")
        return True
    
    # Intentar instalar GTK runtime
    logger.info("🔧 WeasyPrint necesita GTK3. Instalando...")
    
    # Método 1: Instalador oficial
    if install_gtk_runtime():
        if test_weasyprint():
            logger.info("🎉 Instalación exitosa con método 1!")
            return True
    
    # Método 2: GTK portable
    logger.info("🔄 Probando método alternativo...")
    if install_gtk_portable():
        if test_weasyprint():
            logger.info("🎉 Instalación exitosa con método 2!")
            return True
    
    # Si nada funciona
    logger.error("❌ No se pudo instalar GTK3 automáticamente")
    logger.info("📖 Instrucciones manuales:")
    logger.info("1. Descargar GTK3 desde: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases")
    logger.info("2. Ejecutar el instalador")
    logger.info("3. Reiniciar la terminal")
    logger.info("4. Probar python main.py --status")
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
