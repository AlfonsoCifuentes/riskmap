#!/usr/bin/env python3
"""
Test final de arranque de la aplicación - Solo verifica que inicie sin procesamiento masivo
"""

import sys
import os
import time
import subprocess
import signal
from datetime import datetime

def test_app_startup():
    """Test de arranque de la aplicación con timeout"""
    
    print("🚀 TESTING APP_BUENA.PY STARTUP OPTIMIZATION")
    print("=" * 60)
    print(f"🕒 Inicio del test: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Start the application with a timeout
        print("🔄 Iniciando app_BUENA.py...")
        print("   (Presiona Ctrl+C para parar después de verificar arranque)")
        
        # Use subprocess to run the app with monitoring
        process = subprocess.Popen(
            [sys.executable, "app_BUENA.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        start_time = time.time()
        lines_seen = 0
        nlp_processing_detected = False
        server_started = False
        
        print("\n📋 MONITORING APP OUTPUT:")
        print("-" * 40)
        
        try:
            for line in process.stdout:
                lines_seen += 1
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Print first 20 lines and any important lines
                if lines_seen <= 20 or "Processing" in line or "NLP" in line or "Running on" in line or "error" in line.lower():
                    print(f"[{elapsed:5.1f}s] {line.strip()}")
                
                # Check for key indicators
                if "Processing" in line and "articles" in line:
                    nlp_processing_detected = True
                    print(f"⚠️  [ALERT] NLP Processing detected at {elapsed:.1f}s: {line.strip()}")
                
                if "Running on http" in line or "Flask development server is running" in line:
                    server_started = True
                    print(f"🎉 [SUCCESS] Server started at {elapsed:.1f}s!")
                    break
                
                # Stop after 60 seconds or if too many lines
                if elapsed > 60 or lines_seen > 100:
                    print(f"\n⏰ Timeout or line limit reached after {elapsed:.1f}s")
                    break
                    
        except KeyboardInterrupt:
            print(f"\n⚠️  User interrupted at {time.time() - start_time:.1f}s")
        
        finally:
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        # Results
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"🎯 TEST RESULTS (Total time: {total_time:.1f}s):")
        print(f"   📄 Lines monitored: {lines_seen}")
        print(f"   🧠 NLP processing detected: {'YES ❌' if nlp_processing_detected else 'NO ✅'}")
        print(f"   🌐 Server started: {'YES ✅' if server_started else 'NO ❌'}")
        
        if not nlp_processing_detected and total_time < 30:
            print("\n🎉 OPTIMIZATION SUCCESSFUL!")
            print("   ✅ No massive NLP processing detected")
            print("   ✅ Fast startup time")
            print("   ✅ Application starts quickly")
        elif nlp_processing_detected:
            print("\n⚠️  OPTIMIZATION MAY NEED WORK")
            print("   ❌ NLP processing was detected during startup")
            print("   📝 May still be processing articles unnecessarily")
        else:
            print("\n⏰ STARTUP TIME CONCERNS")
            print(f"   ⚠️  Took {total_time:.1f}s to start")
            print("   📝 May indicate background processing")
        
        return not nlp_processing_detected and total_time < 30
        
    except Exception as e:
        print(f"❌ Error during startup test: {e}")
        return False

if __name__ == "__main__":
    print("🔧 STARTUP OPTIMIZATION TEST")
    print("This will start app_BUENA.py and monitor for unnecessary processing")
    print("Press Ctrl+C to stop the test once server starts\n")
    
    success = test_app_startup()
    
    if success:
        print("\n✅ Startup optimization test PASSED")
    else:
        print("\n❌ Startup optimization test needs attention")