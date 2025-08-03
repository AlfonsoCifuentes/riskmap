#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de instalación y configuración de Ollama con Qwen y Llama
"""

import os
import sys
import subprocess
import json
import logging
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OllamaInstaller:
    """
    Instalador y configurador de Ollama con modelos Qwen y Llama
    """
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.models_to_install = [
            # Modelos principales (alta prioridad)
            "deepseek-r1:7b",      # Razonamiento profundo y análisis avanzado
            "gemma2:2b",           # Procesamiento rápido y eficiente
            "qwen:7b",             # Análisis multiidioma y general
            
            # Modelos secundarios (media prioridad)
            "llama3.1:8b",         # Generación de texto
            "gemma2:9b",           # Análisis avanzado
            "qwen2.5-coder:7b",    # Tareas técnicas y programación
            
            # Modelos avanzados (baja prioridad - solo si hay recursos)
            "deepseek-r1:14b"      # Razonamiento complejo (requiere más RAM)
        ]
        
    def check_ollama_installation(self) -> bool:
        """
        Verificar si Ollama está instalado
        """
        try:
            result = subprocess.run(
                ["ollama", "version"], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"✅ Ollama instalado: {result.stdout.strip()}")
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
            
    def install_ollama_windows(self) -> bool:
        """
        Instalar Ollama en Windows
        """
        logger.info("🚀 Instalando Ollama para Windows...")
        
        try:
            # URL de descarga para Windows
            download_url = "https://ollama.com/download/windows"
            
            logger.info("📥 Descargando Ollama...")
            logger.info(f"Por favor, visita: {download_url}")
            logger.info("Y sigue las instrucciones de instalación.")
            
            # Esperar confirmación del usuario
            input("\nPresiona Enter cuando hayas completado la instalación de Ollama...")
            
            # Verificar instalación
            if self.check_ollama_installation():
                logger.info("✅ Ollama instalado correctamente")
                return True
            else:
                logger.error("❌ Ollama no se detecta después de la instalación")
                return False
                
        except Exception as e:
            logger.error(f"Error instalando Ollama: {e}")
            return False
            
    def start_ollama_service(self) -> bool:
        """
        Iniciar el servicio de Ollama
        """
        try:
            logger.info("🚀 Iniciando servicio Ollama...")
            
            # En Windows, Ollama se ejecuta como servicio
            # Intentar iniciar el servicio
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Esperar un poco para que el servicio inicie
            time.sleep(5)
            
            # Verificar si el servicio está corriendo
            if self.check_ollama_running():
                logger.info("✅ Servicio Ollama iniciado correctamente")
                return True
            else:
                logger.warning("⚠️ El servicio puede estar iniciando, continuando...")
                return True
                
        except Exception as e:
            logger.error(f"Error iniciando servicio Ollama: {e}")
            return False
            
    def check_ollama_running(self) -> bool:
        """
        Verificar si Ollama está corriendo
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def wait_for_ollama(self, timeout: int = 60) -> bool:
        """
        Esperar a que Ollama esté disponible
        """
        logger.info("⏳ Esperando a que Ollama esté disponible...")
        
        for i in range(timeout):
            if self.check_ollama_running():
                logger.info("✅ Ollama está disponible")
                return True
            time.sleep(1)
            if i % 10 == 0:
                logger.info(f"⏳ Esperando... ({i}/{timeout}s)")
                
        logger.error("❌ Timeout esperando a Ollama")
        return False
        
    def install_model(self, model_name: str) -> bool:
        """
        Instalar un modelo específico
        """
        try:
            logger.info(f"📦 Instalando modelo {model_name}...")
            
            # Usar el comando pull de Ollama
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # Mostrar progreso en tiempo real
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Filtrar líneas de progreso
                    if "pulling" in output.lower() or "downloading" in output.lower():
                        logger.info(f"📥 {output.strip()}")
                    elif "success" in output.lower():
                        logger.info(f"✅ {output.strip()}")
                        
            rc = process.poll()
            if rc == 0:
                logger.info(f"✅ Modelo {model_name} instalado correctamente")
                return True
            else:
                logger.error(f"❌ Error instalando {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error instalando modelo {model_name}: {e}")
            return False
            
    def get_installed_models(self) -> List[str]:
        """
        Obtener lista de modelos instalados
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                return [model.get('name', '') for model in models]
            return []
        except Exception as e:
            logger.error(f"Error obteniendo modelos: {e}")
            return []
            
    def test_model(self, model_name: str) -> bool:
        """
        Probar un modelo instalado
        """
        try:
            logger.info(f"🧪 Probando modelo {model_name}...")
            
            test_payload = {
                "model": model_name,
                "prompt": "Hola, explica qué eres en una línea.",
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                output = result.get('response', '').strip()
                logger.info(f"✅ {model_name} responde: {output[:100]}...")
                return True
            else:
                logger.error(f"❌ Error probando {model_name}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error probando modelo {model_name}: {e}")
            return False
            
    def setup_environment_variables(self):
        """
        Configurar variables de entorno
        """
        env_file = Path(".env")
        
        env_vars = {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_TIMEOUT": "300",
            "AI_PROVIDER_PRIORITY": "ollama,groq",
            "USE_LOCAL_AI": "true"
        }
        
        logger.info("⚙️ Configurando variables de entorno...")
        
        # Leer archivo .env existente
        existing_vars = {}
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        existing_vars[key] = value
                        
        # Actualizar con nuevas variables
        existing_vars.update(env_vars)
        
        # Escribir archivo .env actualizado
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Configuración de Ollama\n")
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
            f.write("\n")
            
            # Escribir otras variables existentes
            for key, value in existing_vars.items():
                if key not in env_vars:
                    f.write(f"{key}={value}\n")
                    
        logger.info("✅ Variables de entorno configuradas")
        
    def create_installation_summary(self, installed_models: List[str]):
        """
        Crear resumen de instalación
        """
        summary = f"""
🎉 INSTALACIÓN DE OLLAMA COMPLETADA

📋 Resumen:
- Ollama: ✅ Instalado y corriendo
- URL: {self.ollama_url}
- Modelos instalados: {len(installed_models)}

🤖 Modelos disponibles:
"""
        for model in installed_models:
            summary += f"  - {model}\n"
            
        summary += """
🚀 Próximos pasos:
1. El sistema ahora puede usar IA local con Ollama
2. Reinicia la aplicación para aplicar los cambios
3. Los análisis usarán modelos locales por defecto

💡 Comandos útiles:
- Ver modelos: ollama list
- Ejecutar modelo: ollama run <modelo>
- Detener servicio: ollama stop (si es necesario)

✅ ¡Ollama está listo para usar!
"""
        
        logger.info(summary)
        
        # Guardar resumen en archivo
        with open("ollama_installation_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)
            
    def run_installation(self) -> bool:
        """
        Ejecutar proceso completo de instalación
        """
        logger.info("🚀 Iniciando instalación de Ollama con Qwen y Llama")
        
        # 1. Verificar si Ollama ya está instalado
        if not self.check_ollama_installation():
            logger.info("📦 Ollama no está instalado")
            if os.name == 'nt':  # Windows
                if not self.install_ollama_windows():
                    return False
            else:
                logger.error("❌ Instalación automática solo soportada en Windows")
                logger.info("Por favor, instala Ollama manualmente desde: https://ollama.com")
                return False
                
        # 2. Iniciar servicio si no está corriendo
        if not self.check_ollama_running():
            if not self.start_ollama_service():
                logger.error("❌ No se pudo iniciar el servicio Ollama")
                return False
                
        # 3. Esperar a que Ollama esté disponible
        if not self.wait_for_ollama():
            return False
            
        # 4. Instalar modelos requeridos
        installed_models = self.get_installed_models()
        logger.info(f"📋 Modelos ya instalados: {installed_models}")
        
        success_count = 0
        for model in self.models_to_install:
            if model not in installed_models:
                if self.install_model(model):
                    success_count += 1
                    # Probar el modelo
                    self.test_model(model)
                else:
                    logger.warning(f"⚠️ No se pudo instalar {model}")
            else:
                logger.info(f"✅ Modelo {model} ya está instalado")
                success_count += 1
                
        # 5. Configurar variables de entorno
        self.setup_environment_variables()
        
        # 6. Verificación final
        final_models = self.get_installed_models()
        logger.info(f"📋 Modelos finales instalados: {final_models}")
        
        # 7. Crear resumen
        self.create_installation_summary(final_models)
        
        if success_count >= 2:  # Al menos 2 modelos instalados
            logger.info("🎉 Instalación completada exitosamente")
            return True
        else:
            logger.error("❌ La instalación no se completó correctamente")
            return False

def main():
    """
    Función principal
    """
    installer = OllamaInstaller()
    
    try:
        success = installer.run_installation()
        if success:
            print("\n" + "="*60)
            print("🎉 OLLAMA INSTALADO EXITOSAMENTE")
            print("="*60)
            print("El sistema ahora puede usar IA local.")
            print("Reinicia la aplicación para aplicar los cambios.")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("❌ ERROR EN LA INSTALACIÓN")
            print("="*60)
            print("Revisa los logs para más detalles.")
            print("="*60)
            
    except KeyboardInterrupt:
        print("\n❌ Instalación cancelada por el usuario")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
