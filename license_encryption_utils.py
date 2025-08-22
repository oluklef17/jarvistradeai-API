"""
License File Encryption/Decryption Utilities
==========================================

This module provides comprehensive encryption and decryption utilities for the JarvisTrade
license file system. It includes both Python backend implementation and MQL4/MQL5
compatible decryption logic.

Features:
- XOR encryption with fixed key
- Base64 encoding for file storage
- JSON data serialization
- Cross-platform compatibility
- MQL4/MQL5 integration support

Usage:
    # Python Backend (Encryption)
    from license_encryption_utils import LicenseEncryption
    
    encryption = LicenseEncryption()
    encrypted_data = encryption.encrypt_license(license_data)
    
    # MQL4/MQL5 (Decryption)
    # Include the MQL4 functions in your EA
    # Use VerifyLicenseFile(license_id) in OnInit()
"""

import json
import base64
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class LicenseEncryption:
    """
    License file encryption and decryption utility class.
    
    Uses XOR encryption with fixed key and Base64 encoding.
    Compatible with MQL4/MQL5 decryption implementation.
    """
    
    # Encryption constants (must match MQL4/MQL5 implementation)
    MASTER_KEY = "JarvisTrade2024"
    
    # Fixed XOR key (32 bytes for encryption)
    XOR_KEY = b'JarvisTrade2024LicenseKey32Bytes!'
    
    def __init__(self):
        """Initialize the encryption utility."""
        pass
    
    def _xor_encrypt(self, data: bytes) -> bytes:
        """Encrypt data using XOR with fixed key."""
        result = bytearray()
        key_len = len(self.XOR_KEY)
        
        for i, byte in enumerate(data):
            result.append(byte ^ self.XOR_KEY[i % key_len])
        
        return bytes(result)
    
    def _xor_decrypt(self, data: bytes) -> bytes:
        """Decrypt data using XOR with fixed key (same as encrypt)."""
        return self._xor_encrypt(data)  # XOR is symmetric
    
    def encrypt_license(self, license_data: Dict[str, Any]) -> Optional[str]:
        """
        Encrypt license data and return base64-encoded string.
        
        Args:
            license_data: Dictionary containing license information
            
        Returns:
            Base64-encoded encrypted data or None if encryption fails
        """
        try:
            # Convert license data to JSON string
            json_data = json.dumps(license_data, separators=(',', ':'))
            plaintext = json_data.encode('utf-8')
            
            # XOR encrypt the data
            encrypted_bytes = self._xor_encrypt(plaintext)
            
            # Return base64-encoded encrypted data
            return base64.b64encode(encrypted_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"Error encrypting license data: {e}")
            return None
    
    def decrypt_license(self, encrypted_data: str) -> Optional[Dict[str, Any]]:
        """
        Decrypt license data from base64-encoded string.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted license data dictionary or None if decryption fails
        """
        try:
            # Decode base64 data
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # XOR decrypt the data
            decrypted_bytes = self._xor_decrypt(encrypted_bytes)
            
            # Parse JSON data
            json_data = decrypted_bytes.decode('utf-8')
            license_data = json.loads(json_data)
            
            return license_data
            
        except Exception as e:
            print(f"Error decrypting license data: {e}")
            return None


def create_license_data(
    product_name: str,
    license_id: str,
    accounts: List[Dict[str, str]],
    max_activations: int,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create license data structure for encryption.
    
    Args:
        product_name: Name of the product
        license_id: Unique license identifier
        accounts: List of authorized account dictionaries
        max_activations: Maximum number of allowed activations
        expiry_date: Optional expiry date (ISO format)
        
    Returns:
        License data dictionary ready for encryption
    """
    return {
        "product_name": product_name,
        "license_id": license_id,
        "max_activations": max_activations,
        "current_activations": len(accounts),
        "accounts": accounts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "expiry_date": expiry_date,
        "version": "1.0"
    }


def verify_account_in_license(
    license_data: Dict[str, Any],
    account_login: str,
    account_server: str
) -> bool:
    """
    Verify if an account is authorized in the license.
    
    Args:
        license_data: Decrypted license data
        account_login: Account login number
        account_server: Account server name
        
    Returns:
        True if account is authorized, False otherwise
    """
    try:
        accounts = license_data.get("accounts", [])
        
        for account in accounts:
            if (account.get("account_login") == account_login and
                account.get("account_server") == account_server):
                return True
        
        return False
        
    except Exception as e:
        print(f"Error verifying account: {e}")
        return False


def check_license_expiry(license_data: Dict[str, Any]) -> bool:
    """
    Check if license has expired.
    
    Args:
        license_data: Decrypted license data
        
    Returns:
        True if license is valid (not expired), False otherwise
    """
    try:
        expiry_date = license_data.get("expiry_date")
        
        if not expiry_date:
            # No expiry date means license is valid indefinitely
            return True
        
        # Parse expiry date
        expiry = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
        current = datetime.now(timezone.utc)
        
        return current < expiry
        
    except Exception as e:
        print(f"Error checking license expiry: {e}")
        return False


def get_license_info(license_data: Dict[str, Any]) -> str:
    """
    Get human-readable license information.
    
    Args:
        license_data: Decrypted license data
        
    Returns:
        Formatted license information string
    """
    try:
        info_lines = [
            f"Product: {license_data.get('product_name', 'Unknown')}",
            f"License ID: {license_data.get('license_id', 'Unknown')}",
            f"Max Activations: {license_data.get('max_activations', 0)}",
            f"Current Activations: {license_data.get('current_activations', 0)}",
            f"Generated: {license_data.get('generated_at', 'Unknown')}",
        ]
        
        expiry_date = license_data.get('expiry_date')
        if expiry_date:
            info_lines.append(f"Expires: {expiry_date}")
        else:
            info_lines.append("Expires: Never")
        
        accounts = license_data.get('accounts', [])
        if accounts:
            info_lines.append("\nAuthorized Accounts:")
            for i, account in enumerate(accounts, 1):
                info_lines.append(
                    f"  {i}. {account.get('account_login', 'Unknown')} @ "
                    f"{account.get('account_server', 'Unknown')} "
                    f"(Activated: {account.get('activated_at', 'Unknown')})"
                )
        
        return "\n".join(info_lines)
        
    except Exception as e:
        print(f"Error getting license info: {e}")
        return "Error reading license information"


# MQL4/MQL5 Compatible Decryption Functions
# =========================================

MQL4_DECRYPTION_FUNCTIONS = """
//+------------------------------------------------------------------+
//| License Decryption Functions for MQL4/MQL5
//+------------------------------------------------------------------+
#property copyright "JarvisTrade"
#property link      "https://jarvistrade.com"
#property version   "1.00"
#property strict

// License file constants (must match Python implementation)
#define LICENSE_MASTER_KEY "JarvisTrade2024"

// Fixed XOR key (32 bytes for encryption)
// These must match the Python implementation exactly
#define XOR_KEY_0 0x4a  // 'J'
#define XOR_KEY_1 0x61  // 'a'
#define XOR_KEY_2 0x72  // 'r'
#define XOR_KEY_3 0x76  // 'v'
#define XOR_KEY_4 0x69  // 'i'
#define XOR_KEY_5 0x73  // 's'
#define XOR_KEY_6 0x54  // 'T'
#define XOR_KEY_7 0x72  // 'r'
#define XOR_KEY_8 0x61  // 'a'
#define XOR_KEY_9 0x64  // 'd'
#define XOR_KEY_10 0x65 // 'e'
#define XOR_KEY_11 0x32 // '2'
#define XOR_KEY_12 0x30 // '0'
#define XOR_KEY_13 0x32 // '2'
#define XOR_KEY_14 0x34 // '4'
#define XOR_KEY_15 0x4c // 'L'
#define XOR_KEY_16 0x69 // 'i'
#define XOR_KEY_17 0x63 // 'c'
#define XOR_KEY_18 0x65 // 'e'
#define XOR_KEY_19 0x6e // 'n'
#define XOR_KEY_20 0x73 // 's'
#define XOR_KEY_21 0x65 // 'e'
#define XOR_KEY_22 0x4b // 'K'
#define XOR_KEY_23 0x65 // 'e'
#define XOR_KEY_24 0x79 // 'y'
#define XOR_KEY_25 0x33 // '3'
#define XOR_KEY_26 0x32 // '2'
#define XOR_KEY_27 0x42 // 'B'
#define XOR_KEY_28 0x79 // 'y'
#define XOR_KEY_29 0x74 // 't'
#define XOR_KEY_30 0x65 // 'e'
#define XOR_KEY_31 0x73 // 's'

//+------------------------------------------------------------------+
//| Global variables for license data                               |
//+------------------------------------------------------------------+
string g_license_product = "";
string g_license_id = "";
string g_license_accounts[10][2]; // [account_login, account_server]
int g_license_account_count = 0;

//+------------------------------------------------------------------+
//| License verification functions                                   |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Read and verify license file                                    |
//+------------------------------------------------------------------+
bool VerifyLicenseFile(string license_id)
{
   string license_file = license_id + ".lic";
   string file_path = "Files\\\\" + license_file;
   
   // Check if license file exists
   if(!FileIsExist(file_path))
   {
      Print("License file not found: ", file_path);
      return false;
   }
   
   // Read encrypted license data
   string encrypted_data = ReadLicenseFile(file_path);
   if(encrypted_data == "")
   {
      Print("Failed to read license file");
      return false;
   }
   
   // Decrypt license data
   string json_data = DecryptLicenseData(encrypted_data);
   if(json_data == "")
   {
      Print("Failed to decrypt license data");
      return false;
   }
   
   // Parse license data
   if(!ParseLicenseData(json_data))
   {
      Print("Failed to parse license data");
      return false;
   }
   
   // Verify current account
   if(!VerifyCurrentAccount())
   {
      Print("Current account not authorized in license");
      return false;
   }
   
   // Check expiry
   if(!CheckLicenseExpiry())
   {
      Print("License has expired");
      return false;
   }
   
   Print("License verified successfully");
   return true;
}

//+------------------------------------------------------------------+
//| Read license file content                                       |
//+------------------------------------------------------------------+
string ReadLicenseFile(string file_path)
{
   int file_handle = FileOpen(file_path, FILE_READ|FILE_TXT);
   if(file_handle == INVALID_HANDLE)
   {
      Print("Failed to open license file: ", file_path);
      return "";
   }
   
   string content = "";
   while(!FileIsEnding(file_handle))
   {
      content += FileReadString(file_handle);
   }
   
   FileClose(file_handle);
   return content;
}

//+------------------------------------------------------------------+
//| Base64 decode function                                          |
//+------------------------------------------------------------------+
string Base64Decode(string encoded)
{
   // Base64 character set
   string base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
   
   // Remove padding
   while(StringLen(encoded) > 0 && StringSubstr(encoded, StringLen(encoded) - 1, 1) == "=")
   {
      encoded = StringSubstr(encoded, 0, StringLen(encoded) - 1);
   }
   
   // Convert to bytes
   int len = StringLen(encoded);
   int output_len = (len * 3) / 4;
   uchar output[];
   ArrayResize(output, output_len);
   
   int j = 0;
   for(int i = 0; i < len; i += 4)
   {
      int sextet_a = StringFind(base64_chars, StringSubstr(encoded, i, 1));
      int sextet_b = StringFind(base64_chars, StringSubstr(encoded, i + 1, 1));
      int sextet_c = StringFind(base64_chars, StringSubstr(encoded, i + 2, 1));
      int sextet_d = StringFind(base64_chars, StringSubstr(encoded, i + 3, 1));
      
      if(sextet_a == -1 || sextet_b == -1) break;
      
      int triple = (sextet_a << 18) + (sextet_b << 12);
      
      if(sextet_c != -1)
      {
         triple += (sextet_c << 6);
         if(sextet_d != -1)
         {
            triple += sextet_d;
         }
      }
      
      if(j < output_len) output[j++] = (uchar)((triple >> 16) & 0xFF);
      if(j < output_len) output[j++] = (uchar)((triple >> 8) & 0xFF);
      if(j < output_len) output[j++] = (uchar)(triple & 0xFF);
   }
   
   // Convert bytes to string
   string result = "";
   for(int i = 0; i < ArraySize(output); i++)
   {
      result += CharToString(output[i]);
   }
   
   return result;
}

//+------------------------------------------------------------------+
//| XOR decrypt function                                            |
//+------------------------------------------------------------------+
string XORDecrypt(string encrypted_data)
{
   // Convert string to bytes
   int data_len = StringLen(encrypted_data);
   uchar data[];
   ArrayResize(data, data_len);
   
   for(int i = 0; i < data_len; i++)
   {
      data[i] = (uchar)StringGetCharacter(encrypted_data, i);
   }
   
   // Fixed XOR key (32 bytes)
   uchar key[32] = {
      XOR_KEY_0, XOR_KEY_1, XOR_KEY_2, XOR_KEY_3, XOR_KEY_4, XOR_KEY_5, XOR_KEY_6, XOR_KEY_7,
      XOR_KEY_8, XOR_KEY_9, XOR_KEY_10, XOR_KEY_11, XOR_KEY_12, XOR_KEY_13, XOR_KEY_14, XOR_KEY_15,
      XOR_KEY_16, XOR_KEY_17, XOR_KEY_18, XOR_KEY_19, XOR_KEY_20, XOR_KEY_21, XOR_KEY_22, XOR_KEY_23,
      XOR_KEY_24, XOR_KEY_25, XOR_KEY_26, XOR_KEY_27, XOR_KEY_28, XOR_KEY_29, XOR_KEY_30, XOR_KEY_31
   };
   
   // XOR decrypt data
   for(int i = 0; i < data_len; i++)
   {
      data[i] = data[i] ^ key[i % 32];
   }
   
   // Convert back to string
   string result = "";
   for(int i = 0; i < data_len; i++)
   {
      result += CharToString(data[i]);
   }
   
   return result;
}

//+------------------------------------------------------------------+
//| Decrypt license data using XOR + Base64                         |
//+------------------------------------------------------------------+
string DecryptLicenseData(string encrypted_data)
{
   // Decode base64
   string decoded = Base64Decode(encrypted_data);
   if(decoded == "") return "";
   
   // XOR decrypt
   string decrypted = XORDecrypt(decoded);
   
   return decrypted;
}

//+------------------------------------------------------------------+
//| Parse license JSON data                                         |
//+------------------------------------------------------------------+
bool ParseLicenseData(string json_data)
{
   // Parse JSON data and store in global variables
   // This is a simplified implementation
   
   // Extract product name
   int product_start = StringFind(json_data, "\\"product_name\\":\\"");
   if(product_start != -1)
   {
      product_start += 15;
      int product_end = StringFind(json_data, "\\"", product_start);
      if(product_end != -1)
      {
         g_license_product = StringSubstr(json_data, product_start, product_end - product_start);
      }
   }
   
   // Extract license ID
   int license_start = StringFind(json_data, "\\"license_id\\":\\"");
   if(license_start != -1)
   {
      license_start += 13;
      int license_end = StringFind(json_data, "\\"", license_start);
      if(license_end != -1)
      {
         g_license_id = StringSubstr(json_data, license_start, license_end - license_start);
      }
   }
   
   // Extract accounts array
   int accounts_start = StringFind(json_data, "\\"accounts\\":[");
   if(accounts_start != -1)
   {
      accounts_start += 11;
      int accounts_end = StringFind(json_data, "]", accounts_start);
      if(accounts_end != -1)
      {
         string accounts_json = StringSubstr(json_data, accounts_start, accounts_end - accounts_start);
         ParseAccountsArray(accounts_json);
      }
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Parse accounts array from JSON                                  |
//+------------------------------------------------------------------+
void ParseAccountsArray(string accounts_json)
{
   // Parse accounts array and store in global array
   // This is a simplified implementation
   
   int pos = 0;
   int account_count = 0;
   
   while(pos < StringLen(accounts_json) && account_count < 10)
   {
      // Find account login
      int login_start = StringFind(accounts_json, "\\"account_login\\":\\"", pos);
      if(login_start == -1) break;
      
      login_start += 16;
      int login_end = StringFind(accounts_json, "\\"", login_start);
      if(login_end == -1) break;
      
      string account_login = StringSubstr(accounts_json, login_start, login_end - login_start);
      
      // Find account server
      int server_start = StringFind(accounts_json, "\\"account_server\\":\\"", login_end);
      if(server_start == -1) break;
      
      server_start += 17;
      int server_end = StringFind(accounts_json, "\\"", server_start);
      if(server_end == -1) break;
      
      string account_server = StringSubstr(accounts_json, server_start, server_end - server_start);
      
      // Store account
      g_license_accounts[account_count][0] = account_login;
      g_license_accounts[account_count][1] = account_server;
      account_count++;
      
      pos = server_end;
   }
   
   g_license_account_count = account_count;
}

//+------------------------------------------------------------------+
//| Verify current account is in license                            |
//+------------------------------------------------------------------+
bool VerifyCurrentAccount()
{
   string current_login = IntegerToString(AccountNumber());
   string current_server = AccountServer();
   
   for(int i = 0; i < g_license_account_count; i++)
   {
      if(g_license_accounts[i][0] == current_login && 
         g_license_accounts[i][1] == current_server)
      {
         return true;
      }
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Check if license has expired                                    |
//+------------------------------------------------------------------+
bool CheckLicenseExpiry()
{
   // This is a simplified implementation
   // In production, you would parse the expiry_date from JSON
   // and compare with current time
   
   return true; // Assume valid for demo
}

//+------------------------------------------------------------------+
//| Example usage in EA                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   // Verify license before starting
   if(!VerifyLicenseFile("LIC-ABC12345"))
   {
      Print("License verification failed");
      return INIT_FAILED;
   }
   
   Print("License verified successfully. EA is now active.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                           |
//+------------------------------------------------------------------+
void OnTick()
{
   // Your EA logic here
   // License is already verified in OnInit()
}
"""


# Utility Functions
# ================

def generate_license_file_content(license_data: Dict[str, Any]) -> str:
    """
    Generate the content for a license file.
    
    Args:
        license_data: License data dictionary
        
    Returns:
        Encrypted license file content as string
    """
    encryption = LicenseEncryption()
    encrypted_data = encryption.encrypt_license(license_data)
    
    if not encrypted_data:
        raise ValueError("Failed to encrypt license data")
    
    return encrypted_data


def validate_license_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Validate and decrypt a license file.
    
    Args:
        file_path: Path to the license file
        
    Returns:
        Decrypted license data or None if validation fails
    """
    try:
        # Read the license file
        with open(file_path, 'r') as f:
            encrypted_data = f.read().strip()
        
        # Decrypt the data
        encryption = LicenseEncryption()
        license_data = encryption.decrypt_license(encrypted_data)
        
        return license_data
        
    except Exception as e:
        print(f"Error validating license file: {e}")
        return None


def test_encryption_decryption():
    """
    Test the encryption and decryption functionality.
    """
    print("Testing License Encryption/Decryption...")
    
    # Create test license data
    test_license = create_license_data(
        product_name="Test Trading Bot",
        license_id="LIC-TEST123",
        accounts=[
            {
                "account_login": "12345678",
                "account_server": "TestServer-Demo",
                "activated_at": "2024-01-15T10:30:00Z"
            }
        ],
        max_activations=3,
        expiry_date=None
    )
    
    print("Original license data:")
    print(json.dumps(test_license, indent=2))
    
    # Encrypt the license
    encryption = LicenseEncryption()
    encrypted_data = encryption.encrypt_license(test_license)
    
    if not encrypted_data:
        print("❌ Encryption failed")
        return False
    
    print(f"\nEncrypted data (base64): {encrypted_data[:50]}...")
    
    # Decrypt the license
    decrypted_data = encryption.decrypt_license(encrypted_data)
    
    if not decrypted_data:
        print("❌ Decryption failed")
        return False
    
    print("\nDecrypted license data:")
    print(json.dumps(decrypted_data, indent=2))
    
    # Verify the data matches
    if test_license == decrypted_data:
        print("✅ Encryption/Decryption test passed!")
        return True
    else:
        print("❌ Encryption/Decryption test failed!")
        return False


if __name__ == "__main__":
    # Run test if executed directly
    test_encryption_decryption() 