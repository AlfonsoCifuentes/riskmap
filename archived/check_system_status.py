#!/usr/bin/env python3
"""
Script simple para verificar el estado de la BD y del sistema
"""

import sqlite3
import requests
from pathlib import Path

def check_database():
    """Verificar estado de la BD"""
    print("🔍 Verificando base de datos...")
    
    db_path = Path("./data/geopolitical_intel.db")
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return False
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            # Contar artículos totales
            cursor = conn.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            
            # Contar artículos con summaries limpios
            cursor = conn.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE summary NOT LIKE '%<think>%' 
                AND summary IS NOT NULL 
                AND summary != ''
            """)
            clean = cursor.fetchone()[0]
            
            # Contar artículos con summaries problemáticos
            cursor = conn.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE summary LIKE '%<think>%'
            """)
            problematic = cursor.fetchone()[0]
            
            print(f"✅ Total artículos: {total}")
            print(f"✅ Summaries limpios: {clean}")
            print(f"⚠️ Summaries problemáticos: {problematic}")
            
            return True
    
    except Exception as e:
        print(f"❌ Error en BD: {e}")
        return False

def check_server():
    """Verificar si el servidor está corriendo"""
    print("\n🌐 Verificando servidor...")
    
    try:
        response = requests.get('http://localhost:5001/api/articles', timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"✅ Servidor corriendo - Status: {response.status_code}")
            print(f"✅ Artículos devueltos: {len(articles)}")
            
            if len(articles) > 0:
                first = articles[0]
                summary = first.get('summary', '')
                
                if '<think>' in summary:
                    print("❌ PROBLEMA: Summaries aún contienen <think>")
                else:
                    print("✅ Summaries limpios en API")
                    
                if 'picsum.photos' in first.get('image_url', ''):
                    print("✅ Placeholder corregido en API")
                else:
                    print("⚠️ Placeholder no corregido")
            
            return True
        else:
            print(f"❌ Servidor responde con código {response.status_code}")
            return False
    
    except requests.ConnectionError:
        print("❌ No se puede conectar al servidor (no está corriendo)")
        return False
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return False

def main():
    """Main function"""
    print("🧪 VERIFICACIÓN COMPLETA DEL SISTEMA")
    print("=" * 50)
    
    db_ok = check_database()
    server_ok = check_server()
    
    print("\n📋 RESUMEN:")
    print(f"  Base de datos: {'✅' if db_ok else '❌'}")
    print(f"  Servidor API: {'✅' if server_ok else '❌'}")
    
    if db_ok and server_ok:
        print("\n🎉 ¡Sistema funcionando correctamente!")
    elif db_ok:
        print("\n⚠️ BD OK pero servidor no responde - reiniciar aplicación")
    else:
        print("\n❌ Problemas en el sistema")

if __name__ == "__main__":
    main()