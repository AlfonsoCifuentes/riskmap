#!/usr/bin/env python3
"""
Script inteligente para resolver conflictos de dependencias automáticamente
Instala tensorflow, keras, ml-dtypes, jax, jaxlib y resuelve conflictos de versiones
"""

import subprocess
import sys
import re
import json
from typing import Dict, List, Tuple, Optional

class DependencyResolver:
    def __init__(self):
        self.packages = ['tensorflow', 'keras', 'ml-dtypes', 'jax', 'jaxlib', 'transformers']
        self.version_constraints = {}
        self.max_iterations = 10
        self.current_iteration = 0
        
    def run_pip_command(self, command: List[str]) -> Tuple[str, str, int]:
        """Ejecuta un comando pip y retorna stdout, stderr, y código de retorno"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout al ejecutar comando", 1
        except Exception as e:
            return "", f"Error ejecutando comando: {e}", 1
    
    def parse_dependency_error(self, error_text: str) -> List[Dict[str, str]]:
        """Parsea errores de dependencias y extrae los requerimientos"""
        conflicts = []
        
        # Patrón para encontrar conflictos de versiones
        # Ejemplo: "tensorflow-intel 2.15.1 requires keras<2.16,>=2.15.0, but you have keras 3.11.1"
        pattern = r'(\S+)\s+([\d.]+(?:\w+)?)\s+requires\s+([^,\s]+)([<>=!~,.\d\w]+),?\s+but you have\s+([^,\s]+)\s+([\d.]+(?:\w+)?)'
        
        matches = re.findall(pattern, error_text)
        
        for match in matches:
            parent_package = match[0].replace('-intel', '')  # tensorflow-intel -> tensorflow
            parent_version = match[1]
            required_package = match[2]
            version_spec = match[3]
            current_package = match[4]
            current_version = match[5]
            
            conflicts.append({
                'parent_package': parent_package,
                'parent_version': parent_version,
                'required_package': required_package,
                'version_spec': version_spec,
                'current_package': current_package,
                'current_version': current_version
            })
            
        return conflicts
    
    def extract_compatible_version(self, version_spec: str) -> Optional[str]:
        """Extrae una versión compatible del especificador de versión"""
        # Maneja especificadores como: >=2.15.0,<2.16, ~=0.3.1, >=0.5.0
        
        # Para ~= (compatible release)
        if '~=' in version_spec:
            match = re.search(r'~=([\d.]+)', version_spec)
            if match:
                return match.group(1)
        
        # Para >=X,<Y (rango)
        min_match = re.search(r'>=([\d.]+)', version_spec)
        max_match = re.search(r'<([\d.]+)', version_spec)
        
        if min_match and max_match:
            min_ver = min_match.group(1)
            max_ver = max_match.group(1)
            # Retorna la versión mínima como más segura
            return min_ver
        elif min_match:
            return min_match.group(1)
        elif max_match:
            # Para <X, usar una versión ligeramente menor
            parts = max_match.group(1).split('.')
            if len(parts) >= 2:
                major, minor = int(parts[0]), int(parts[1])
                if minor > 0:
                    return f"{major}.{minor-1}.0"
                else:
                    return f"{major-1}.99.0" if major > 0 else "0.99.0"
        
        # Para >= solo
        exact_match = re.search(r'([\d.]+)', version_spec)
        if exact_match:
            return exact_match.group(1)
            
        return None
    
    def install_packages(self, packages_with_versions: Dict[str, Optional[str]]) -> Tuple[str, str, int]:
        """Instala paquetes con versiones específicas"""
        install_list = []
        
        for package, version in packages_with_versions.items():
            if version:
                install_list.append(f"{package}=={version}")
            else:
                install_list.append(package)
        
        print(f"🔄 Instalando: {', '.join(install_list)}")
        
        command = [sys.executable, '-m', 'pip', 'install'] + install_list
        return self.run_pip_command(command)
    
    def check_dependencies(self) -> Tuple[str, str, int]:
        """Verifica las dependencias instaladas"""
        print("🔍 Verificando dependencias...")
        command = [sys.executable, '-m', 'pip', 'check']
        return self.run_pip_command(command)
    
    def resolve_conflicts(self):
        """Resuelve conflictos de dependencias automáticamente"""
        print("🚀 Iniciando resolución automática de dependencias...")
        
        # Primero, intentar instalar las versiones base
        base_versions = {
            'tensorflow': '2.15.0',
            'keras': '2.15.0', 
            'ml-dtypes': '0.3.1',
            'jax': '0.4.20',
            'jaxlib': '0.4.20',
            'transformers': '4.35.0'
        }
        
        print("📦 Instalando versiones base compatibles...")
        stdout, stderr, code = self.install_packages(base_versions)
        
        if code != 0:
            print(f"⚠️ Instalación inicial falló: {stderr}")
        
        # Iterativamente resolver conflictos
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration + 1
            print(f"\n🔄 Iteración {self.current_iteration}/{self.max_iterations}")
            
            # Verificar dependencias
            stdout, stderr, code = self.check_dependencies()
            
            if code == 0:
                print("✅ ¡Todas las dependencias son compatibles!")
                return True
            
            print(f"⚠️ Conflictos detectados:")
            print(stderr)
            
            # Parsear errores y extraer conflictos
            conflicts = self.parse_dependency_error(stderr)
            
            if not conflicts:
                print("❌ No se pudieron parsear los conflictos automáticamente")
                break
            
            # Resolver conflictos
            packages_to_update = {}
            
            for conflict in conflicts:
                required_package = conflict['required_package']
                version_spec = conflict['version_spec']
                
                compatible_version = self.extract_compatible_version(version_spec)
                
                if compatible_version:
                    packages_to_update[required_package] = compatible_version
                    print(f"🔧 {required_package}: {version_spec} -> {compatible_version}")
            
            if not packages_to_update:
                print("❌ No se encontraron versiones compatibles para resolver")
                break
            
            # Instalar versiones actualizadas
            stdout, stderr, code = self.install_packages(packages_to_update)
            
            if code != 0:
                print(f"⚠️ Error instalando actualizaciones: {stderr}")
        
        print(f"❌ No se pudo resolver automáticamente después de {self.max_iterations} iteraciones")
        return False
    
    def test_imports(self):
        """Prueba que las librerías se importen correctamente"""
        print("\n🧪 Probando imports...")
        
        test_packages = [
            ('tensorflow', 'import tensorflow as tf; print(f"TensorFlow: {tf.__version__}")'),
            ('keras', 'import keras; print(f"Keras: {keras.__version__}")'),
            ('ml_dtypes', 'import ml_dtypes; print(f"ml_dtypes: {getattr(ml_dtypes, \"__version__\", \"unknown\")}")'),
            ('jax', 'import jax; print(f"JAX: {jax.__version__}")'),
            ('transformers', 'import transformers; print(f"Transformers: {transformers.__version__}")')
        ]
        
        all_success = True
        
        for package_name, test_code in test_packages:
            try:
                result = subprocess.run([sys.executable, '-c', test_code], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"✅ {result.stdout.strip()}")
                else:
                    print(f"❌ {package_name}: {result.stderr.strip()}")
                    all_success = False
            except Exception as e:
                print(f"❌ {package_name}: Error al probar - {e}")
                all_success = False
        
        return all_success

def main():
    print("🔧 Script de Resolución Automática de Dependencias")
    print("=" * 60)
    
    resolver = DependencyResolver()
    
    # Resolver conflictos
    success = resolver.resolve_conflicts()
    
    if success:
        # Probar imports
        if resolver.test_imports():
            print("\n🎉 ¡Todas las dependencias instaladas y funcionando correctamente!")
        else:
            print("\n⚠️ Dependencias instaladas pero hay problemas con algunos imports")
    else:
        print("\n❌ No se pudieron resolver todos los conflictos automáticamente")
        print("\n📋 Recomendaciones manuales:")
        print("1. pip uninstall tensorflow keras ml-dtypes jax jaxlib transformers -y")
        print("2. pip install tensorflow==2.15.0 keras==2.15.0 ml-dtypes==0.3.1")
        print("3. pip install jax==0.4.20 jaxlib==0.4.20")
        print("4. pip install transformers==4.35.0")

if __name__ == "__main__":
    main()
