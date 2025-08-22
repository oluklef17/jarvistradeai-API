import json
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

class LicenseEncryption:
    """License encryption/decryption system compatible with MQL4/MQL5"""
    
    # Fixed AES key (32 bytes for AES-256) - truncated to exactly 32 bytes
    AES_KEY = b'JarvisTrade2024LicenseKey32Bytes'
    # Fixed IV (16 bytes for AES) - truncated to exactly 16 bytes
    AES_IV = b'JarvisTrade2024I'
    # HMAC key for signature (32 bytes)
    HMAC_KEY = b'JarvisTrade2024HMACKey32Bytes!'
    
    def __init__(self, master_key="JarvisTrade2024"):
        """Initialize with master key (kept for compatibility)"""
        self.master_key = master_key
    
    def _calculate_signature(self, license_data: dict) -> str:
        """Calculate HMAC-SHA256 signature of license data"""
        # Create a copy without signature field
        data_for_signature = license_data.copy()
        if 'signature' in data_for_signature:
            del data_for_signature['signature']
        
        # Convert to JSON string
        json_data = json.dumps(data_for_signature, separators=(',', ':'))
        
        # Calculate HMAC-SHA256
        signature = hmac.new(
            self.HMAC_KEY,
            json_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _verify_signature(self, license_data: dict) -> bool:
        """Verify HMAC-SHA256 signature of license data"""
        if 'signature' not in license_data:
            return False
        
        stored_signature = license_data['signature']
        calculated_signature = self._calculate_signature(license_data)
        
        return hmac.compare_digest(stored_signature, calculated_signature)
    
    def _aes_encrypt(self, data: bytes) -> bytes:
        """Encrypt data using AES-256-CBC"""
        cipher = Cipher(
            algorithms.AES(self.AES_KEY),
            modes.CBC(self.AES_IV),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Add PKCS7 padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        return encrypted_data
    
    def _aes_decrypt(self, data: bytes) -> bytes:
        """Decrypt data using AES-256-CBC"""
        cipher = Cipher(
            algorithms.AES(self.AES_KEY),
            modes.CBC(self.AES_IV),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        decrypted_data = decryptor.update(data) + decryptor.finalize()
        
        # Remove PKCS7 padding
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()
        
        return unpadded_data
    
    def encrypt_license(self, license_data):
        """Encrypt license data with signature"""
        try:
            # Add signature to license data
            license_data['signature'] = self._calculate_signature(license_data)
            
            # Convert to JSON string
            json_data = json.dumps(license_data, separators=(',', ':'))
            plaintext = json_data.encode('utf-8')
            
            # AES encrypt the data
            encrypted_bytes = self._aes_encrypt(plaintext)
            
            # Return base64-encoded encrypted data
            return base64.b64encode(encrypted_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return None
    
    def decrypt_license(self, encrypted_data):
        """Decrypt license data and verify signature"""
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # AES decrypt the data
            decrypted_bytes = self._aes_decrypt(encrypted_bytes)
            
            # Parse JSON data
            json_data = decrypted_bytes.decode('utf-8')
            license_data = json.loads(json_data)
            
            # Verify signature
            if not self._verify_signature(license_data):
                print("Signature verification failed")
                return None
            
            # Remove signature from returned data
            if 'signature' in license_data:
                del license_data['signature']
            
            return license_data
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

def create_license_data(product_name, license_id, accounts, max_activations, expiry_date=None):
    """Create license data structure"""
    return {
        "product_name": product_name,
        "license_id": license_id,
        "max_activations": max_activations,
        "current_activations": len(accounts),
        "accounts": accounts,
        "generated_at": datetime.utcnow().isoformat(),
        "expiry_date": expiry_date.isoformat() if expiry_date else None,
        "version": "1.0"
    }

def verify_account_in_license(license_data, account_login, account_server):
    """Verify if account is authorized in license"""
    if not license_data or "accounts" not in license_data:
        return False
    
    # Check if account exists in license
    for account in license_data["accounts"]:
        if (account.get("account_login") == str(account_login) and 
            account.get("account_server") == str(account_server)):
            return True
    
    return False

def check_license_expiry(license_data):
    """Check if license has expired"""
    if not license_data or "expiry_date" not in license_data:
        return True  # No expiry date means valid
    
    try:
        expiry_date = datetime.fromisoformat(license_data["expiry_date"])
        return datetime.utcnow() < expiry_date
    except:
        return True  # If parsing fails, assume valid

def get_license_info(license_data):
    """Get human-readable license information"""
    if not license_data:
        return "Invalid license"
    
    info = f"Product: {license_data.get('product_name', 'Unknown')}\n"
    info += f"License ID: {license_data.get('license_id', 'Unknown')}\n"
    info += f"Activations: {license_data.get('current_activations', 0)}/{license_data.get('max_activations', 0)}\n"
    
    if license_data.get("expiry_date"):
        info += f"Expires: {license_data['expiry_date']}\n"
    else:
        info += "No expiry date\n"
    
    info += f"Generated: {license_data.get('generated_at', 'Unknown')}\n"
    info += f"Accounts: {len(license_data.get('accounts', []))}\n"
    
    return info 
