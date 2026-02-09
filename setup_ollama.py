#!/usr/bin/env python3
"""
INSTALADOR Y CONFIGURADOR DE OLLAMA PARA RISKMAP
Automatiza la instalación y configuración de modelos locales
Creado por: AI Assistant
Fecha: 2024
"""

import requests
import subprocess
import time
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Colores para terminal
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
ENDC = '\033[0m'

class OllamaInstaller:
    """Instalador automático de Ollama y modelos"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.recommended_models = {
            'qwen2.5:7b-instruct': {
                'purpose': 'Traducción multiidioma',
                'size': '~4GB',
                'speed': 'Rápido'
            },
            'llama3.1:8b': {
                'purpose': 'Análisis geopolítico',
                'size': '~4.7GB', 
                'speed': 'Medio'
            },
            'gemma2:2b': {
                'purpose': 'Fallback rápido',
                'size': '~1.6GB',
                'speed': 'Muy rápido'
            }
        }
    
    def check_ollama_installed(self) -> bool:
        """Verificar si Ollama está instalado"""
        try:
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_ollama_running(self) -> bool:
        """Verificar si Ollama está ejecutándose"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def install_ollama_windows(self) -> bool:
        """Instalar Ollama en Windows"""
        print(f"{BLUE}📥 INSTALANDO OLLAMA EN WINDOWS{ENDC}")
        print("=" * 50)
        
        # URL de descarga para Windows
        download_url = "https://ollama.ai/download/OllamaSetup.exe"
        
        print(f"🌐 Descargando Ollama desde: {download_url}")
        print("⏳ Esto puede tomar varios minutos...")
        
        try:
            # Descargar instalador
            response = requests.get(download_url, timeout=300)
            installer_path = Path("OllamaSetup.exe")
            
            with open(installer_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Instalador descargado: {installer_path}")
            print(f"{YELLOW}⚠️ EJECUTA MANUALMENTE: {installer_path}{ENDC}")
            print(f"{YELLOW}⚠️ Después de la instalación, ejecuta 'ollama serve' en otra terminal{ENDC}")
            
            return True
            
        except Exception as e:
            print(f"{RED}❌ Error descargando Ollama: {e}{ENDC}")
            return False
    
    def start_ollama_service(self) -> bool:
        """Intentar iniciar servicio de Ollama"""
        print(f"{BLUE}🚀 INICIANDO SERVICIO OLLAMA{ENDC}")
        
        if self.check_ollama_running():
            print("✅ Ollama ya está ejecutándose")
            return True
        
        try:
            # Intentar iniciar en background
            if os.name == 'nt':  # Windows
                subprocess.Popen(['ollama', 'serve'], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Linux/Mac
                subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Esperar a que inicie
            print("⏳ Esperando que Ollama inicie...")
            for i in range(30):
                time.sleep(2)
                if self.check_ollama_running():
                    print("✅ Ollama iniciado correctamente")
                    return True
                print(f"   Esperando... ({i+1}/30)")
            
            print(f"{RED}❌ Ollama no pudo iniciarse automáticamente{ENDC}")
            print(f"{YELLOW}💡 Ejecuta manualmente: ollama serve{ENDC}")
            return False
            
        except Exception as e:
            print(f"{RED}❌ Error iniciando Ollama: {e}{ENDC}")
            return False
    
    def install_model(self, model_name: str) -> bool:
        """Instalar un modelo específico"""
        print(f"{BLUE}📦 INSTALANDO MODELO: {model_name}{ENDC}")
        
        model_info = self.recommended_models.get(model_name, {})
        print(f"   Propósito: {model_info.get('purpose', 'N/A')}")
        print(f"   Tamaño: {model_info.get('size', 'N/A')}")
        print(f"   Velocidad: {model_info.get('speed', 'N/A')}")
        
        try:
            # Usar subprocess para mostrar progreso
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print("📥 Descargando...")
            while True:
                if process.stdout is not None:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        # Mostrar progreso
                        if 'pulling' in output.lower() or '%' in output:
                            print(f"   {output.strip()}")
                else:
                    break
            
            return_code = process.poll()
            
            if return_code == 0:
                print(f"✅ {model_name} instalado correctamente")
                return True
            else:
                print(f"{RED}❌ Error instalando {model_name}{ENDC}")
                return False
                
        except Exception as e:
            print(f"{RED}❌ Error instalando {model_name}: {e}{ENDC}")
            return False
    
    def verify_installation(self) -> Dict:
        """Verificar instalación completa"""
        print(f"{BLUE}🔍 VERIFICANDO INSTALACIÓN{ENDC}")
        print("=" * 50)
        
        results = {
            'ollama_installed': self.check_ollama_installed(),
            'ollama_running': self.check_ollama_running(),
            'models_available': {},
            'total_models': 0
        }
        
        print(f"Ollama instalado: {'✅' if results['ollama_installed'] else '❌'}")
        print(f"Ollama ejecutándose: {'✅' if results['ollama_running'] else '❌'}")
        
        if results['ollama_running']:
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    models_data = response.json().get('models', [])
                    available_models = [model['name'] for model in models_data]
                    results['total_models'] = len(available_models)
                    
                    print(f"\n📦 MODELOS DISPONIBLES ({len(available_models)}):")
                    for model_name in self.recommended_models:
                        is_available = any(model_name in available for available in available_models)
                        results['models_available'][model_name] = is_available
                        status = "✅" if is_available else "❌"
                        print(f"   {status} {model_name}")
                    
                    # Mostrar otros modelos
                    other_models = [m for m in available_models 
                                  if not any(rec in m for rec in self.recommended_models)]
                    if other_models:
                        print(f"\n📋 OTROS MODELOS:")
                        for model in other_models[:5]:  # Mostrar máximo 5
                            print(f"   • {model}")
                        if len(other_models) > 5:
                            print(f"   ... y {len(other_models) - 5} más")
                            
            except Exception as e:
                print(f"❌ Error verificando modelos: {e}")
        
        return results
    
    def install_all_recommended(self) -> Dict:
        """Instalar todos los modelos recomendados"""
        print(f"{PURPLE}🚀 INSTALACIÓN COMPLETA DE MODELOS RECOMENDADOS{ENDC}")
        print("=" * 60)
        
        if not self.check_ollama_running():
            print(f"{RED}❌ Ollama no está ejecutándose{ENDC}")
            return {'error': 'Ollama no disponible'}
        
        results = {}
        total_models = len(self.recommended_models)
        
        for i, model_name in enumerate(self.recommended_models, 1):
            print(f"\n[{i}/{total_models}] {model_name}")
            print("-" * 40)
            
            # Verificar si ya está instalado
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    available_models = [m['name'] for m in response.json().get('models', [])]
                    if any(model_name in available for available in available_models):
                        print(f"✅ {model_name} ya está instalado")
                        results[model_name] = 'already_installed'
                        continue
            except:
                pass
            
            # Instalar modelo
            success = self.install_model(model_name)
            results[model_name] = 'installed' if success else 'failed'
        
        return results

def main():
    """Función principal de instalación"""
    print(f"{PURPLE}{'='*70}{ENDC}")
    print(f"{PURPLE}  INSTALADOR AUTOMÁTICO DE OLLAMA PARA RISKMAP{ENDC}")
    print(f"{PURPLE}{'='*70}{ENDC}")
    print()
    
    installer = OllamaInstaller()
    
    # Paso 1: Verificar instalación de Ollama
    print(f"{BLUE}PASO 1: VERIFICAR OLLAMA{ENDC}")
    ollama_installed = installer.check_ollama_installed()
    ollama_running = installer.check_ollama_running()
    
    if not ollama_installed:
        print("❌ Ollama no está instalado")
        if os.name == 'nt':
            installer.install_ollama_windows()
            print(f"{YELLOW}⚠️ Instala Ollama manualmente y reinicia este script{ENDC}")
            sys.exit(1)
        else:
            print("💡 Instala Ollama desde: https://ollama.ai/download")
            sys.exit(1)
    else:
        print("✅ Ollama está instalado")
    
    # Paso 2: Iniciar servicio
    print(f"\n{BLUE}PASO 2: INICIAR SERVICIO{ENDC}")
    if not ollama_running:
        if not installer.start_ollama_service():
            print(f"{YELLOW}⚠️ Inicia Ollama manualmente: 'ollama serve'{ENDC}")
            print("Después ejecuta este script de nuevo.")
            sys.exit(1)
    else:
        print("✅ Ollama ya está ejecutándose")
    
    # Paso 3: Instalar modelos
    print(f"\n{BLUE}PASO 3: INSTALAR MODELOS{ENDC}")
    install_results = installer.install_all_recommended()
    
    # Paso 4: Verificación final
    print(f"\n{BLUE}PASO 4: VERIFICACIÓN FINAL{ENDC}")
    verification = installer.verify_installation()
    
    # Resumen final
    print(f"\n{PURPLE}📋 RESUMEN DE INSTALACIÓN{ENDC}")
    print("=" * 50)
    
    if verification['ollama_running'] and verification['total_models'] > 0:
        successful_models = sum(1 for v in verification['models_available'].values() if v)
        print(f"✅ Ollama funcionando con {verification['total_models']} modelos")
        print(f"✅ Modelos recomendados disponibles: {successful_models}/{len(installer.recommended_models)}")
        
        if successful_models == len(installer.recommended_models):
            print(f"\n{GREEN}🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE{ENDC}")
            print("Ya puedes usar el sistema mejorado de traducción y análisis geopolítico")
        else:
            print(f"\n{YELLOW}⚠️ INSTALACIÓN PARCIAL{ENDC}")
            print("Algunos modelos no se instalaron. Revisa los errores anteriores.")
    else:
        print(f"\n{RED}❌ INSTALACIÓN FALLIDA{ENDC}")
        print("Ollama no está funcionando correctamente")
    
    print(f"\n{BLUE}PRÓXIMOS PASOS:{ENDC}")
    print("1. Ejecutar: python enhanced_translation_geo_system.py")
    print("2. Procesar base de datos con el nuevo sistema")
    print("3. Verificar mejoras en traducción y análisis geopolítico")

if __name__ == "__main__":
    main()