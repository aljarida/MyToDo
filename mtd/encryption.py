import base64
import hashlib
import os
from typing import Optional
from dotenv import load_dotenv

from cryptography.fernet import Fernet

from .paths import get_encrypted_file_path, SCRIPT_DIR 

def get_encryption_key() -> Optional[bytes]:
    """Get encryption key from password in .env file. Returns None if password not set."""
    load_dotenv(dotenv_path=os.path.join(SCRIPT_DIR, '.env'))

    password = os.getenv('MTD_ENCRYPTION_PASSWORD')
    if not password:
        return None

    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_file(file_path: str) -> None:
    """Encrypt a file and save it in the encrypted directory."""
    key = get_encryption_key()
    if not key:
        print("Could not find encryption key.")
        return None
    
    with open(file_path, 'rb') as f:
        plaintext = f.read()

    assert plaintext is not None
    
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plaintext)
    
    encrypted_path = get_encrypted_file_path(file_path)
    os.makedirs(os.path.dirname(encrypted_path), exist_ok=True)
    with open(encrypted_path, 'wb') as f:
        f.write(encrypted)


def encrypt_file_if_enabled(file_path: str) -> None:
    """Encrypt a file if encryption password is set in .env file."""
    if get_encryption_key() is not None:
        encrypt_file(file_path)


def decrypt_file(file_path: str) -> bool:
    """Decrypt a file and write it to the plaintext location. Returns True if successful, False otherwise."""
    key = get_encryption_key()
    if key is None:
        return False
    
    encrypted_path = get_encrypted_file_path(file_path)
    if not os.path.exists(encrypted_path):
        return False
    
    try:
        with open(encrypted_path, 'rb') as f:
            encrypted = f.read()
        
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted)
        
        with open(file_path, 'wb') as f:
            f.write(decrypted)
        
        return True
    except Exception:
        return False

