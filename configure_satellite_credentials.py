#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de configuración rápida para credenciales satelitales
Configura variables de entorno para SentinelHub y Planet APIs
"""

import os
import sys
from pathlib import Path

def setup_satellite_credentials():
    """Configurar credenciales satelitales"""
    print("🛰️ CONFIGURACIÓN DE CREDENCIALES SATELITALES")
    print("=" * 60)
    print()
    
    print("Este script te ayudará a configurar las credenciales para:")
    print("  📡 SentinelHub (Copernicus/ESA)")
    print("  🌍 Planet Labs")
    print()
    
    # Configurar SentinelHub
    print("1️⃣ CONFIGURACIÓN SENTINELHUB")
    print("-" * 30)
    print("Para obtener credenciales de SentinelHub:")
    print("  1. Visita: https://services.sentinel-hub.com/")
    print("  2. Crea una cuenta gratuita")
    print("  3. Ve a 'User Settings' > 'OAuth clients'")
    print("  4. Crea un nuevo cliente OAuth")
    print()
    
    current_sentinel_id = os.getenv("SENTINELHUB_CLIENT_ID", "")
    current_sentinel_secret = os.getenv("SENTINELHUB_CLIENT_SECRET", "")
    
    if current_sentinel_id:
        print(f"✅ Cliente ID actual: {current_sentinel_id[:20]}...")
        update_sentinel = input("¿Actualizar credenciales de SentinelHub? (y/n): ").lower().strip()
    else:
        print("❌ No hay credenciales de SentinelHub configuradas")
        update_sentinel = input("¿Configurar SentinelHub ahora? (y/n): ").lower().strip()
    
    if update_sentinel == 'y':
        sentinel_client_id = input("Introduce SentinelHub Client ID: ").strip()
        sentinel_client_secret = input("Introduce SentinelHub Client Secret: ").strip()
        
        if sentinel_client_id and sentinel_client_secret:
            os.environ["SENTINELHUB_CLIENT_ID"] = sentinel_client_id
            os.environ["SENTINELHUB_CLIENT_SECRET"] = sentinel_client_secret
            print("✅ Credenciales de SentinelHub configuradas")
        else:
            print("⚠️ Credenciales vacías, saltando SentinelHub")
    
    print()
    
    # Configurar Planet
    print("2️⃣ CONFIGURACIÓN PLANET LABS")
    print("-" * 30)
    print("Para obtener API key de Planet:")
    print("  1. Visita: https://www.planet.com/")
    print("  2. Crea una cuenta")
    print("  3. Ve a 'Account' > 'API Keys'")
    print("  4. Genera una nueva API key")
    print()
    
    current_planet_key = os.getenv("PLANET_API_KEY", "")
    
    if current_planet_key:
        print(f"✅ API Key actual: {current_planet_key[:20]}...")
        update_planet = input("¿Actualizar API key de Planet? (y/n): ").lower().strip()
    else:
        print("❌ No hay API key de Planet configurada")
        update_planet = input("¿Configurar Planet ahora? (y/n): ").lower().strip()
    
    if update_planet == 'y':
        planet_api_key = input("Introduce Planet API Key: ").strip()
        
        if planet_api_key:
            os.environ["PLANET_API_KEY"] = planet_api_key
            print("✅ API key de Planet configurada")
        else:
            print("⚠️ API key vacía, saltando Planet")
    
    print()
    
    # Guardar en archivo .env
    print("3️⃣ GUARDADO DE CONFIGURACIÓN")
    print("-" * 30)
    
    env_file = Path(".env")
    save_to_file = input(f"¿Guardar credenciales en {env_file}? (y/n): ").lower().strip()
    
    if save_to_file == 'y':
        try:
            # Leer archivo existente
            existing_env = {}
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            existing_env[key.strip()] = value.strip()
            
            # Actualizar con nuevas credenciales
            if "SENTINELHUB_CLIENT_ID" in os.environ:
                existing_env["SENTINELHUB_CLIENT_ID"] = os.environ["SENTINELHUB_CLIENT_ID"]
            if "SENTINELHUB_CLIENT_SECRET" in os.environ:
                existing_env["SENTINELHUB_CLIENT_SECRET"] = os.environ["SENTINELHUB_CLIENT_SECRET"]
            if "PLANET_API_KEY" in os.environ:
                existing_env["PLANET_API_KEY"] = os.environ["PLANET_API_KEY"]
            
            # Escribir archivo actualizado
            with open(env_file, 'w') as f:
                f.write("# Configuración del sistema RiskMap\n")
                f.write("# Generado automáticamente\n\n")
                
                # Credenciales satelitales
                f.write("# === CREDENCIALES SATELITALES ===\n")
                for key in ["SENTINELHUB_CLIENT_ID", "SENTINELHUB_CLIENT_SECRET", "PLANET_API_KEY"]:
                    if key in existing_env:
                        f.write(f"{key}={existing_env[key]}\n")
                
                f.write("\n# === OTRAS CONFIGURACIONES ===\n")
                # Otras variables de entorno
                for key, value in existing_env.items():
                    if key not in ["SENTINELHUB_CLIENT_ID", "SENTINELHUB_CLIENT_SECRET", "PLANET_API_KEY"]:
                        f.write(f"{key}={value}\n")
            
            print(f"✅ Credenciales guardadas en {env_file}")
            print("💡 Asegúrate de cargar el archivo .env al iniciar la aplicación")
            
        except Exception as e:
            print(f"❌ Error guardando archivo .env: {e}")
    
    print()
    print("🎯 RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    
    # Estado final
    sentinel_configured = bool(os.getenv("SENTINELHUB_CLIENT_ID") and os.getenv("SENTINELHUB_CLIENT_SECRET"))
    planet_configured = bool(os.getenv("PLANET_API_KEY"))
    
    print(f"📡 SentinelHub: {'✅ Configurado' if sentinel_configured else '❌ No configurado'}")
    print(f"🌍 Planet Labs: {'✅ Configurado' if planet_configured else '❌ No configurado'}")
    
    if sentinel_configured or planet_configured:
        print()
        print("🚀 ¡Configuración completada!")
        print("   Las credenciales satelitales están listas para usar.")
        print("   Ahora puedes ejecutar 'python app_BUENA.py' y utilizar las funciones satelitales.")
    else:
        print()
        print("⚠️ No se configuraron credenciales satelitales.")
        print("   Las funciones satelitales no estarán disponibles.")
        print("   Puedes ejecutar este script más tarde para configurarlas.")
    
    print()
    print("📋 PRÓXIMOS PASOS:")
    print("   1. Ejecuta: python app_BUENA.py")
    print("   2. Ve a: http://localhost:8050/satellite-analysis")
    print("   3. Prueba las funciones satelitales desde la interfaz web")
    print()


if __name__ == "__main__":
    try:
        setup_satellite_credentials()
    except KeyboardInterrupt:
        print("\n❌ Configuración cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")
        sys.exit(1)
