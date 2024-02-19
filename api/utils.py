from cryptography.fernet import Fernet
import os
import json
upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(upper_dir + "/trade_core_config.json") as f:
    config = json.load(f)

node = config['node']
key = config['node_settings'][node]['encryption_key'].encode()

# Initialize Fernet with your key
# In a real application, load this key from a secure location
fernet = Fernet(key)

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data."""
    return fernet.encrypt(data)

def decrypt_data(encrypted_data: bytes) -> bytes:
    """Decrypt data."""
    return fernet.decrypt(encrypted_data)