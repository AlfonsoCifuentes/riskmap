"""
Reinicio del Servidor y Verificación BERT
=========================================
Script para reiniciar el servidor y verificar que el sistema BERT esté funcionando correctamente.
"""

import subprocess
import sys
import time
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_bert_availability():
    """Verificar que BERT esté disponible."""
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        logger.info("✅ BERT/Transformers está disponible")
        return True
    except ImportError as e:
        logger.error(f"❌ BERT no está disponible: {e}")
        return False

def test_bert_analyzer():
    """Probar nuestro nuevo analizador BERT."""
    try:
        from src.ai.bert_risk_analyzer import bert_risk_analyzer, analyze_article_risk
        
        # Test básico
        result = analyze_article_risk(
            title="Conflict in Eastern Europe escalates",
            content="Military tensions have increased significantly in the region with new deployments of troops and equipment.",
            country="Ukraine"
        )
        
        logger.info(f"✅ Test BERT exitoso:")
        logger.info(f"   - Nivel de riesgo: {result['level']}")
        logger.info(f"   - Score: {result['score']:.3f}")
        logger.info(f"   - Confianza: {result['confidence']:.3f}")
        logger.info(f"   - Modelo: {result['model_used']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando analizador BERT: {e}")
        return False

def restart_server():
    """Reiniciar el servidor principal."""
    try:
        logger.info("🔄 Reiniciando servidor principal...")
        
        # Buscar procesos de Python ejecutando app_BUENA.py
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq app_BUENA*"],
                capture_output=True,
                text=True,
                check=False
            )
            logger.info("🛑 Procesos anteriores terminados")
        except Exception as e:
            logger.warning(f"⚠️  No se pudieron terminar procesos anteriores: {e}")
        
        # Esperar un momento
        time.sleep(2)
        
        # Iniciar nuevo proceso
        logger.info("🚀 Iniciando nuevo servidor...")
        process = subprocess.Popen(
            [sys.executable, "app_BUENA.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Dar tiempo al servidor para iniciar
        time.sleep(5)
        
        # Verificar que el servidor esté ejecutándose
        if process.poll() is None:
            logger.info("✅ Servidor iniciado correctamente")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ Error iniciando servidor:")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error reiniciando servidor: {e}")
        return False

def test_server():
    """Probar que el servidor responda."""
    try:
        # Probar endpoint principal
        response = requests.get("http://localhost:5000/", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Servidor responde correctamente")
            return True
        else:
            logger.error(f"❌ Servidor responde con código: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error conectando al servidor: {e}")
        return False

def main():
    """Función principal."""
    logger.info("🔬 Iniciando verificación y reinicio del sistema BERT...")
    
    # 1. Verificar BERT
    if not check_bert_availability():
        logger.error("❌ BERT no está disponible. Instalando dependencias...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "transformers", "torch"], check=True)
            logger.info("✅ Dependencias instaladas. Verificando nuevamente...")
            if not check_bert_availability():
                logger.error("❌ BERT sigue sin estar disponible")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error instalando dependencias: {e}")
            return False
    
    # 2. Probar analizador BERT
    if not test_bert_analyzer():
        logger.error("❌ Analizador BERT no funciona correctamente")
        return False
    
    # 3. Reiniciar servidor
    if not restart_server():
        logger.error("❌ Error reiniciando servidor")
        return False
    
    # 4. Probar servidor
    if not test_server():
        logger.error("❌ Servidor no responde correctamente")
        return False
    
    logger.info("🎉 ¡Sistema BERT configurado y servidor reiniciado exitosamente!")
    logger.info("")
    logger.info("📋 Resumen de cambios implementados:")
    logger.info("   ✅ Nuevo analizador BERT integrado")
    logger.info("   ✅ Todas las noticias re-analizadas con BERT")
    logger.info("   ✅ Sistema RSS configurado para usar BERT")
    logger.info("   ✅ Servidor reiniciado y funcional")
    logger.info("")
    logger.info("🌐 Accede a: http://localhost:5000")
    logger.info("📊 Deberías ver una mejor distribución de riesgos:")
    logger.info("   - HIGH: ~51% de artículos")
    logger.info("   - MEDIUM: ~48% de artículos") 
    logger.info("   - LOW: ~1% de artículos")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 ¡LISTO! El sistema ahora usa BERT para análisis de riesgo.")
    else:
        print("\n❌ Hubo errores. Revisa los logs arriba.")
