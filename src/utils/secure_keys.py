"""
Secure API Key Management System
Encripta y protege las claves API usando Fernet (AES 128 en modo CBC)
"""

import os
import base64
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass

logger = logging.getLogger(__name__)

class SecureKeyManager:
    """Gestor seguro de claves API con encriptación AES."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.encrypted_file = self.config_dir / "encrypted_keys.dat"
        self.salt_file = self.config_dir / "key.salt"
        
        self._fernet = None
        self._master_key = None
        
        # Crear archivos .gitignore para proteger claves
        self._create_gitignore()
    
    def _create_gitignore(self):
        """Crea .gitignore para proteger archivos de claves."""
        gitignore_path = self.config_dir / ".gitignore"
        
        gitignore_content = """
# Encrypted API Keys - NEVER COMMIT
encrypted_keys.dat
key.salt
*.key
*.secret

# Configuration with sensitive data
*_config.json
*_secrets.json
        """.strip()
        
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        logger.info(f"[OK] Created .gitignore for key protection at {gitignore_path}")
    
    def _generate_salt(self) -> bytes:
        """Genera salt aleatorio para la derivación de claves."""
        salt = os.urandom(16)
        with open(self.salt_file, 'wb') as f:
            f.write(salt)
        return salt
    
    def _load_salt(self) -> bytes:
        """Carga el salt existente o genera uno nuevo."""
        if self.salt_file.exists():
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            return self._generate_salt()
    
    def _derive_key(self, password: str) -> bytes:
        """Deriva una clave de encriptación del password usando PBKDF2."""
        salt = self._load_salt()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # 100k iteraciones para seguridad
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _get_fernet(self, password: str = None) -> Fernet:
        """Obtiene instancia de Fernet para encriptación."""
        if self._fernet is None:
            if password is None:
                password = self._get_master_password()
            
            key = self._derive_key(password)
            self._fernet = Fernet(key)
        
        return self._fernet
    
    def _get_master_password(self) -> str:
        """Obtiene la contraseña maestra del usuario."""
        if self._master_key is None:
            # Intentar obtener de variable de entorno primero
            env_password = os.getenv('RISKMAP_MASTER_KEY')
            if env_password:
                self._master_key = env_password
                logger.info("[OK] Master password loaded from environment variable")
            else:
                # Solicitar al usuario
                print("\n🔐 SECURE KEY MANAGER")
                print("=====================================")
                if self.encrypted_file.exists():
                    print("🔓 Enter master password to decrypt API keys:")
                else:
                    print("🔒 Create master password to encrypt API keys:")
                    print("💡 Tip: Set RISKMAP_MASTER_KEY environment variable to avoid prompts")
                
                self._master_key = getpass.getpass("Master Password: ")
                
                if not self.encrypted_file.exists():
                    confirm = getpass.getpass("Confirm Password: ")
                    if self._master_key != confirm:
                        raise ValueError("[ERROR] Passwords do not match!")
                    print("[OK] Master password set successfully")
        
        return self._master_key
    
    def encrypt_and_save_keys(self, api_keys: Dict[str, str], password: str = None) -> bool:
        """Encripta y guarda las claves API."""
        try:
            fernet = self._get_fernet(password)
            
            # Serializar las claves
            keys_json = json.dumps(api_keys, indent=2)
            
            # Encriptar
            encrypted_data = fernet.encrypt(keys_json.encode())
            
            # Guardar archivo encriptado
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info(f"[OK] {len(api_keys)} API keys encrypted and saved securely")
            print(f"🔒 API keys encrypted and saved to: {self.encrypted_file}")
            
            # Mostrar claves enmascaradas para confirmación
            print("\n📋 Saved keys (masked):")
            for key_name, key_value in api_keys.items():
                masked_key = f"{key_value[:8]}...{key_value[-4:]}" if len(key_value) > 12 else "***masked***"
                print(f"  {key_name}: {masked_key}")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error encrypting keys: {e}")
            return False
    
    def load_and_decrypt_keys(self, password: str = None) -> Dict[str, str]:
        """Carga y desencripta las claves API."""
        try:
            if not self.encrypted_file.exists():
                logger.warning("[WARN] No encrypted keys file found")
                return {}
            
            fernet = self._get_fernet(password)
            
            # Leer archivo encriptado
            with open(self.encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Desencriptar
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Deserializar
            api_keys = json.loads(decrypted_data.decode())
            
            logger.info(f"[OK] {len(api_keys)} API keys decrypted successfully")
            return api_keys
            
        except Exception as e:
            logger.error(f"[ERROR] Error decrypting keys: {e}")
            print("[ERROR] Failed to decrypt keys. Check your master password.")
            return {}
    
    def add_or_update_key(self, key_name: str, key_value: str, password: str = None) -> bool:
        """Añade o actualiza una clave específica."""
        try:
            # Cargar claves existentes
            existing_keys = self.load_and_decrypt_keys(password)
            
            # Actualizar/añadir nueva clave
            existing_keys[key_name] = key_value
            
            # Guardar de nuevo
            success = self.encrypt_and_save_keys(existing_keys, password)
            
            if success:
                action = "updated" if key_name in existing_keys else "added"
                print(f"[OK] API key '{key_name}' {action} successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"[ERROR] Error adding/updating key {key_name}: {e}")
            return False
    
    def get_key(self, key_name: str, password: str = None) -> Optional[str]:
        """Obtiene una clave específica."""
        try:
            api_keys = self.load_and_decrypt_keys(password)
            return api_keys.get(key_name)
        except Exception as e:
            logger.error(f"[ERROR] Error getting key {key_name}: {e}")
            return None
    
    def list_keys(self, password: str = None) -> Dict[str, str]:
        """Lista todas las claves (enmascaradas)."""
        try:
            api_keys = self.load_and_decrypt_keys(password)
            
            masked_keys = {}
            for key_name, key_value in api_keys.items():
                if len(key_value) > 12:
                    masked_keys[key_name] = f"{key_value[:8]}...{key_value[-4:]}"
                else:
                    masked_keys[key_name] = "***masked***"
            
            return masked_keys
            
        except Exception as e:
            logger.error(f"[ERROR] Error listing keys: {e}")
            return {}
    
    def delete_key(self, key_name: str, password: str = None) -> bool:
        """Elimina una clave específica."""
        try:
            api_keys = self.load_and_decrypt_keys(password)
            
            if key_name not in api_keys:
                print(f"[WARN] Key '{key_name}' not found")
                return False
            
            del api_keys[key_name]
            
            success = self.encrypt_and_save_keys(api_keys, password)
            
            if success:
                print(f"[OK] API key '{key_name}' deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"[ERROR] Error deleting key {key_name}: {e}")
            return False
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """Cambia la contraseña maestra."""
        try:
            # Cargar claves con contraseña actual
            api_keys = self.load_and_decrypt_keys(old_password)
            
            if not api_keys:
                print("[ERROR] Failed to decrypt with old password")
                return False
            
            # Regenerar salt para nueva contraseña
            self._generate_salt()
            self._fernet = None  # Reset Fernet instance
            
            # Guardar con nueva contraseña
            success = self.encrypt_and_save_keys(api_keys, new_password)
            
            if success:
                self._master_key = new_password
                print("[OK] Master password changed successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"[ERROR] Error changing master password: {e}")
            return False


def setup_api_keys_interactive():
    """Setup interactivo para configurar claves API de forma segura."""
    print("\n🔐 SECURE API KEYS SETUP")
    print("=" * 50)
    print("This wizard will help you securely encrypt and store your API keys.")
    print("Keys will be encrypted with AES-128 and stored locally.")
    print()
    
    key_manager = SecureKeyManager()
    
    # Claves requeridas para el sistema
    required_keys = {
        'NEWSAPI_KEY': {
            'description': 'NewsAPI.org API Key',
            'url': 'https://newsapi.org/register',
            'example': 'a1b2c3d4e5f6...',
            'required': True
        },
        'OPENAI_API_KEY': {
            'description': 'OpenAI API Key (for advanced NLP)',
            'url': 'https://platform.openai.com/api-keys',
            'example': 'sk-...',
            'required': False
        },
        'GOOGLE_TRANSLATE_KEY': {
            'description': 'Google Cloud Translation API Key',
            'url': 'https://cloud.google.com/translate/docs/setup',
            'example': 'AIza...',
            'required': False
        }
    }
    
    api_keys = {}
    
    for key_name, key_info in required_keys.items():
        print(f"\n📋 {key_info['description']}")
        print(f"   Get it at: {key_info['url']}")
        print(f"   Example: {key_info['example']}")
        
        if key_info['required']:
            print("   Status: REQUIRED")
        else:
            print("   Status: Optional")
        
        while True:
            if key_info['required']:
                key_value = getpass.getpass(f"Enter {key_name}: ").strip()
                if not key_value:
                    print("[ERROR] This key is required. Please enter a valid value.")
                    continue
            else:
                key_value = getpass.getpass(f"Enter {key_name} (optional, press Enter to skip): ").strip()
                if not key_value:
                    print(f"⏭️ Skipping {key_name}")
                    break
            
            # Validación básica
            if key_name == 'NEWSAPI_KEY' and len(key_value) < 30:
                print("[ERROR] NewsAPI key seems too short. Please check.")
                continue
            elif key_name == 'OPENAI_API_KEY' and not key_value.startswith('sk-'):
                print("[ERROR] OpenAI key should start with 'sk-'. Please check.")
                continue
            elif key_name == 'GOOGLE_TRANSLATE_KEY' and not (key_value.startswith('AIza') or len(key_value) > 30):
                print("[ERROR] Google Translate key format seems incorrect. Please check.")
                continue
            
            api_keys[key_name] = key_value
            print(f"[OK] {key_name} added")
            break
    
    if not api_keys:
        print("\n[WARN] No API keys provided. Setup cancelled.")
        return False
    
    # Guardar claves encriptadas
    print(f"\n[SAVE] Saving {len(api_keys)} API keys...")
    success = key_manager.encrypt_and_save_keys(api_keys)
    
    if success:
        print("\n🎉 API keys setup completed successfully!")
        print("\n[NOTES] Next steps:")
        print("1. Set RISKMAP_MASTER_KEY environment variable to avoid password prompts")
        print("2. Run 'python main.py --status' to verify system configuration")
        print("3. Run 'python main.py --full-pipeline' to start data collection")
        print("\n🔒 Your API keys are now securely encrypted and protected.")
    else:
        print("\n[ERROR] Failed to save API keys. Please try again.")
    
    return success


if __name__ == "__main__":
    # Permitir ejecución directa para setup de claves
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_api_keys_interactive()
    else:
        print("Usage: python secure_keys.py setup")
