#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurador de Credenciales para APIs Satelitales
Configuración segura de SentinelHub, Planet y otras APIs
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SatelliteCredentialsManager:
    """Gestor de credenciales para APIs satelitales"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.credentials = {}
        self.load_existing_credentials()
    
    def load_existing_credentials(self):
        """Cargar credenciales existentes"""
        try:
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            self.credentials[key.strip()] = value.strip().strip('"').strip("'")
            
            logger.info(f"Loaded existing credentials from {self.env_file}")
            
        except Exception as e:
            logger.warning(f"Could not load existing credentials: {e}")
    
    def setup_sentinelhub_credentials(self):
        """Configurar credenciales de SentinelHub"""
        print("\n🛰️  CONFIGURACIÓN DE SENTINELHUB")
        print("="*50)
        print("Para obtener credenciales:")
        print("1. Visita: https://apps.sentinel-hub.com/")
        print("2. Crea una cuenta o inicia sesión")
        print("3. Ve a 'User Settings' > 'OAuth clients'")
        print("4. Crea un nuevo OAuth client")
        print("5. Copia Client ID y Client Secret")
        print()
        
        current_client_id = self.credentials.get('SENTINELHUB_CLIENT_ID', '')
        current_secret = self.credentials.get('SENTINELHUB_CLIENT_SECRET', '')
        
        if current_client_id:
            print(f"Client ID actual: {current_client_id[:10]}...")
            use_current = input("¿Mantener credenciales actuales? (y/n): ").lower().strip()
            if use_current == 'y':
                return True
        
        client_id = input("SentinelHub Client ID: ").strip()
        client_secret = input("SentinelHub Client Secret: ").strip()
        
        if client_id and client_secret:
            self.credentials['SENTINELHUB_CLIENT_ID'] = client_id
            self.credentials['SENTINELHUB_CLIENT_SECRET'] = client_secret
            print("✅ Credenciales de SentinelHub configuradas")
            return True
        else:
            print("❌ Credenciales incompletas")
            return False
    
    def setup_planet_credentials(self):
        """Configurar credenciales de Planet"""
        print("\n🌍 CONFIGURACIÓN DE PLANET")
        print("="*50)
        print("Para obtener API key:")
        print("1. Visita: https://www.planet.com/")
        print("2. Crea una cuenta o inicia sesión")
        print("3. Ve a 'Account Settings' > 'API Keys'")
        print("4. Genera una nueva API Key")
        print()
        
        current_api_key = self.credentials.get('PLANET_API_KEY', '')
        
        if current_api_key:
            print(f"API Key actual: {current_api_key[:15]}...")
            use_current = input("¿Mantener API key actual? (y/n): ").lower().strip()
            if use_current == 'y':
                return True
        
        api_key = input("Planet API Key: ").strip()
        
        if api_key:
            self.credentials['PLANET_API_KEY'] = api_key
            print("✅ Credenciales de Planet configuradas")
            return True
        else:
            print("❌ API Key no proporcionada")
            return False
    
    def setup_optional_credentials(self):
        """Configurar credenciales opcionales"""
        print("\n🔧 CONFIGURACIONES OPCIONALES")
        print("="*50)
        
        # NASA Earthdata
        setup_nasa = input("¿Configurar NASA Earthdata? (y/n): ").lower().strip()
        if setup_nasa == 'y':
            print("\nNASA Earthdata:")
            print("1. Visita: https://urs.earthdata.nasa.gov/")
            print("2. Crea una cuenta")
            print("3. Usa tu username y password")
            
            nasa_username = input("NASA Earthdata Username: ").strip()
            nasa_password = input("NASA Earthdata Password: ").strip()
            
            if nasa_username and nasa_password:
                self.credentials['NASA_EARTHDATA_USERNAME'] = nasa_username
                self.credentials['NASA_EARTHDATA_PASSWORD'] = nasa_password
                print("✅ Credenciales NASA configuradas")
        
        # Google Earth Engine
        setup_gee = input("¿Configurar Google Earth Engine? (y/n): ").lower().strip()
        if setup_gee == 'y':
            print("\nGoogle Earth Engine:")
            print("1. Visita: https://earthengine.google.com/")
            print("2. Solicita acceso")
            print("3. Configura autenticación con gcloud")
            print("4. Para este proyecto, usar service account key")
            
            gee_service_account = input("GEE Service Account Email: ").strip()
            gee_private_key_path = input("Path to GEE Private Key JSON: ").strip()
            
            if gee_service_account:
                self.credentials['GEE_SERVICE_ACCOUNT'] = gee_service_account
            if gee_private_key_path:
                self.credentials['GEE_PRIVATE_KEY_PATH'] = gee_private_key_path
                print("✅ Credenciales GEE configuradas")
    
    def save_credentials(self):
        """Guardar credenciales en archivo .env"""
        try:
            # Backup del archivo existente
            if self.env_file.exists():
                backup_path = self.env_file.with_suffix('.env.backup')
                self.env_file.rename(backup_path)
                print(f"📝 Backup creado: {backup_path}")
            
            # Escribir nuevas credenciales
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write("# Credenciales para APIs Satelitales\n")
                f.write("# Generado automáticamente por satellite_credentials_setup.py\n")
                f.write(f"# Fecha: {os.popen('date').read().strip()}\n\n")
                
                # SentinelHub
                f.write("# SentinelHub OAuth Credentials\n")
                if 'SENTINELHUB_CLIENT_ID' in self.credentials:
                    f.write(f"SENTINELHUB_CLIENT_ID={self.credentials['SENTINELHUB_CLIENT_ID']}\n")
                if 'SENTINELHUB_CLIENT_SECRET' in self.credentials:
                    f.write(f"SENTINELHUB_CLIENT_SECRET={self.credentials['SENTINELHUB_CLIENT_SECRET']}\n")
                f.write("\n")
                
                # Planet
                f.write("# Planet API Credentials\n")
                if 'PLANET_API_KEY' in self.credentials:
                    f.write(f"PLANET_API_KEY={self.credentials['PLANET_API_KEY']}\n")
                f.write("\n")
                
                # NASA
                f.write("# NASA Earthdata Credentials\n")
                if 'NASA_EARTHDATA_USERNAME' in self.credentials:
                    f.write(f"NASA_EARTHDATA_USERNAME={self.credentials['NASA_EARTHDATA_USERNAME']}\n")
                if 'NASA_EARTHDATA_PASSWORD' in self.credentials:
                    f.write(f"NASA_EARTHDATA_PASSWORD={self.credentials['NASA_EARTHDATA_PASSWORD']}\n")
                f.write("\n")
                
                # Google Earth Engine
                f.write("# Google Earth Engine Credentials\n")
                if 'GEE_SERVICE_ACCOUNT' in self.credentials:
                    f.write(f"GEE_SERVICE_ACCOUNT={self.credentials['GEE_SERVICE_ACCOUNT']}\n")
                if 'GEE_PRIVATE_KEY_PATH' in self.credentials:
                    f.write(f"GEE_PRIVATE_KEY_PATH={self.credentials['GEE_PRIVATE_KEY_PATH']}\n")
                f.write("\n")
                
                # Otras configuraciones
                f.write("# Configuraciones de Base de Datos\n")
                if 'DATABASE_PATH' not in self.credentials:
                    f.write("DATABASE_PATH=geopolitical_risk.db\n")
                else:
                    f.write(f"DATABASE_PATH={self.credentials['DATABASE_PATH']}\n")
                
                f.write("\n# Configuraciones de Flask\n")
                if 'FLASK_ENV' not in self.credentials:
                    f.write("FLASK_ENV=development\n")
                if 'FLASK_DEBUG' not in self.credentials:
                    f.write("FLASK_DEBUG=True\n")
            
            print(f"✅ Credenciales guardadas en {self.env_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            print(f"❌ Error guardando credenciales: {e}")
            return False
    
    def test_credentials(self):
        """Probar las credenciales configuradas"""
        print("\n🧪 PROBANDO CREDENCIALES")
        print("="*50)
        
        # Test SentinelHub
        if 'SENTINELHUB_CLIENT_ID' in self.credentials and 'SENTINELHUB_CLIENT_SECRET' in self.credentials:
            print("🛰️  Probando SentinelHub...")
            try:
                from satellite_integration import SentinelHubAPI
                sh_api = SentinelHubAPI(
                    self.credentials['SENTINELHUB_CLIENT_ID'],
                    self.credentials['SENTINELHUB_CLIENT_SECRET']
                )
                if sh_api.authenticate():
                    print("✅ SentinelHub: Conexión exitosa")
                else:
                    print("❌ SentinelHub: Error de autenticación")
            except Exception as e:
                print(f"❌ SentinelHub: Error - {e}")
        
        # Test Planet
        if 'PLANET_API_KEY' in self.credentials:
            print("🌍 Probando Planet...")
            try:
                from satellite_integration import PlanetAPI
                planet_api = PlanetAPI(self.credentials['PLANET_API_KEY'])
                
                # Test simple: obtener información de cuenta
                import requests
                headers = {'Authorization': f'api-key {self.credentials["PLANET_API_KEY"]}'}
                response = requests.get('https://api.planet.com/auth/v1/experimental/public/my/subscriptions', 
                                      headers=headers, timeout=10)
                
                if response.status_code == 200:
                    print("✅ Planet: Conexión exitosa")
                else:
                    print(f"❌ Planet: Error HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Planet: Error - {e}")
    
    def generate_config_summary(self) -> Dict:
        """Generar resumen de configuración"""
        configured_apis = []
        
        if 'SENTINELHUB_CLIENT_ID' in self.credentials:
            configured_apis.append('SentinelHub')
        
        if 'PLANET_API_KEY' in self.credentials:
            configured_apis.append('Planet')
        
        if 'NASA_EARTHDATA_USERNAME' in self.credentials:
            configured_apis.append('NASA Earthdata')
        
        if 'GEE_SERVICE_ACCOUNT' in self.credentials:
            configured_apis.append('Google Earth Engine')
        
        return {
            'configured_apis': configured_apis,
            'total_credentials': len([k for k in self.credentials.keys() if k.endswith(('_KEY', '_ID', '_SECRET', '_USERNAME', '_PASSWORD'))]),
            'env_file': str(self.env_file),
            'ready_for_satellite_integration': len(configured_apis) > 0
        }

def main():
    """Función principal del configurador"""
    print("🛰️  CONFIGURADOR DE CREDENCIALES SATELITALES")
    print("="*60)
    print("Este asistente te ayudará a configurar las credenciales")
    print("necesarias para acceder a las APIs de imágenes satelitales.")
    print()
    
    manager = SatelliteCredentialsManager()
    
    # Mostrar estado actual
    summary = manager.generate_config_summary()
    if summary['configured_apis']:
        print(f"📊 APIs configuradas actualmente: {', '.join(summary['configured_apis'])}")
    else:
        print("📊 No hay APIs configuradas actualmente")
    print()
    
    # Configuración paso a paso
    print("⚙️  CONFIGURACIÓN PASO A PASO")
    print("-" * 40)
    
    # SentinelHub (recomendado)
    setup_sh = input("¿Configurar SentinelHub? (Recomendado) (y/n): ").lower().strip()
    if setup_sh == 'y':
        manager.setup_sentinelhub_credentials()
    
    # Planet (opcional pero útil)
    setup_planet = input("¿Configurar Planet? (Opcional) (y/n): ").lower().strip()
    if setup_planet == 'y':
        manager.setup_planet_credentials()
    
    # APIs adicionales (opcional)
    setup_optional = input("¿Configurar APIs adicionales? (Opcional) (y/n): ").lower().strip()
    if setup_optional == 'y':
        manager.setup_optional_credentials()
    
    # Guardar credenciales
    print("\n💾 GUARDANDO CONFIGURACIÓN")
    print("-" * 40)
    if manager.save_credentials():
        # Probar credenciales
        test_creds = input("¿Probar las credenciales configuradas? (y/n): ").lower().strip()
        if test_creds == 'y':
            manager.test_credentials()
        
        # Resumen final
        final_summary = manager.generate_config_summary()
        print(f"\n📋 RESUMEN FINAL")
        print("-" * 40)
        print(f"✅ APIs configuradas: {', '.join(final_summary['configured_apis'])}")
        print(f"📁 Archivo de configuración: {final_summary['env_file']}")
        print(f"🚀 Listo para integración satelital: {'Sí' if final_summary['ready_for_satellite_integration'] else 'No'}")
        
        if final_summary['ready_for_satellite_integration']:
            print("\n🎉 ¡Configuración completada!")
            print("Ahora puedes ejecutar:")
            print("  python satellite_integration.py")
            print("  o usar las funciones en tu aplicación principal")
        else:
            print("\n⚠️  Necesitas configurar al menos una API para continuar")
    
    else:
        print("❌ Error en la configuración. Revisa los logs.")

if __name__ == "__main__":
    main()
