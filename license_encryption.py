import json
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LicenseSystem:
    """License system using hex encoding with SHA256 signature for integrity"""
    
    def __init__(self, master_key=None):
        """Initialize with master key from environment or provided key"""
        if master_key is None:
            # Load from environment variable
            master_key = os.getenv('LICENSE_MASTER_KEY', 'JarvisTrade2024')
        
        self.master_key = master_key
    
    def _calculate_signature(self, license_data: dict) -> str:
        """Calculate SHA256 signature of license data using master key"""
        # Create a copy without signature field
        data_for_signature = license_data.copy()
        if 'signature' in data_for_signature:
            del data_for_signature['signature']
        
        # Convert to JSON string with consistent formatting
        json_data = json.dumps(data_for_signature, separators=(',', ':'))
        
        # Create HMAC-SHA256 using master key
        key_bytes = self.master_key.encode('utf-8')
        data_bytes = json_data.encode('utf-8')
        
        # Calculate HMAC-SHA256
        signature = hmac.new(key_bytes, data_bytes, hashlib.sha256).hexdigest()
        
        return signature
    
    def _verify_signature(self, license_data: dict) -> bool:
        """Verify SHA256 signature of license data using master key"""
        if 'signature' not in license_data:
            return False
        
        stored_signature = license_data['signature']
        calculated_signature = self._calculate_signature(license_data)
        
        return stored_signature == calculated_signature
    
    def _encode_to_hex(self, json_data: str) -> str:
        """Convert JSON string to hex-encoded string"""
        # Convert string to bytes using UTF-8 encoding
        utf8_bytes = json_data.encode('utf-8')
        
        # Convert to hex string
        hex_string = utf8_bytes.hex()
        
        return hex_string
    
    def _decode_from_hex(self, hex_string: str) -> str:
        """Convert hex-encoded string back to JSON string"""
        # Convert hex string back to bytes
        utf8_bytes = bytes.fromhex(hex_string)
        
        # Convert back to string
        return utf8_bytes.decode('utf-8')
    
    def create_license_file(self, license_data: dict, license_id: str) -> bool:
        """Create license file with hex encoding and signature"""
        try:
            # Add signature to license data
            license_data['signature'] = self._calculate_signature(license_data)
            
            # Convert to JSON string
            json_data = json.dumps(license_data, separators=(',', ':'))
            
            # Convert to hex-encoded string
            hex_string = self._encode_to_hex(json_data)
            
            # Write hex string to file
            filename = f"{license_id}.lic"
            with open(filename, "w") as f:
                f.write(hex_string)
            
            print(f"License file created: {filename}")
            return True
            
        except Exception as e:
            print(f"Error creating license file: {e}")
            return False
    
    def read_license_file(self, license_id: str) -> dict:
        """Read and verify license file"""
        try:
            # Read hex string from file
            filename = f"{license_id}.lic"
            with open(filename, "r") as f:
                hex_string = f.read().strip()
            
            # Decode from hex-encoded string
            json_data = self._decode_from_hex(hex_string)
            
            # Parse JSON data
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
            print(f"Error reading license file: {e}")
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

# For backward compatibility, create aliases
LicenseEncryption = LicenseSystem 
