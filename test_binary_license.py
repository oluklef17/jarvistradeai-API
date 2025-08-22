#!/usr/bin/env python3
"""
Test script for the new binary license system
"""

import os
import sys
import json
from license_encryption import LicenseSystem, create_license_data, get_license_info

def test_binary_license_system():
    """Test the binary license system"""
    
    print("=== Testing Binary License System ===\n")
    
    # Initialize license system
    license_system = LicenseSystem()
    
    # Create test license data
    license_data = create_license_data(
        product_name="Advanced Trading Bot",
        license_id="LIC-TEST123",
        accounts=[
            {"account_login": "123456", "account_server": "MetaQuotes-Demo"},
            {"account_login": "789012", "account_server": "MetaQuotes-Live"}
        ],
        max_activations=3
    )
    
    print("1. Created license data:")
    print(f"   Product: {license_data['product_name']}")
    print(f"   License ID: {license_data['license_id']}")
    print(f"   Max Activations: {license_data['max_activations']}")
    print(f"   Current Activations: {license_data['current_activations']}")
    print(f"   Accounts: {len(license_data['accounts'])}")
    print()
    
    # Create license file
    print("2. Creating license file...")
    success = license_system.create_license_file(license_data, "LIC-TEST123")
    
    if success:
        print("   ✓ License file created successfully")
        
        # Check if file exists and is binary
        if os.path.exists("LIC-TEST123.lic"):
            file_size = os.path.getsize("LIC-TEST123.lic")
            print(f"   ✓ File size: {file_size} bytes")
            
            # Try to read as text to show it's not plain text
            try:
                with open("LIC-TEST123.lic", "r") as f:
                    content = f.read()
                    if content.isprintable():
                        print("   ⚠ File appears to be readable text")
                    else:
                        print("   ✓ File is in binary format (not readable)")
            except UnicodeDecodeError:
                print("   ✓ File is in binary format (not readable)")
        else:
            print("   ✗ License file not found")
            return False
    else:
        print("   ✗ Failed to create license file")
        return False
    
    print()
    
    # Read and verify license file
    print("3. Reading and verifying license file...")
    read_license_data = license_system.read_license_file("LIC-TEST123")
    
    if read_license_data:
        print("   ✓ License file read successfully")
        print("   ✓ Signature verification passed")
        print()
        
        print("4. License information:")
        print(get_license_info(read_license_data))
        
        # Verify the data matches
        if (read_license_data['product_name'] == license_data['product_name'] and
            read_license_data['license_id'] == license_data['license_id'] and
            read_license_data['max_activations'] == license_data['max_activations']):
            print("   ✓ License data integrity verified")
        else:
            print("   ✗ License data integrity check failed")
            return False
    else:
        print("   ✗ Failed to read license file")
        return False
    
    print()
    
    # Test with invalid signature
    print("5. Testing signature verification...")
    
    # Create a license with invalid signature by manually creating the file
    invalid_license_data = license_data.copy()
    invalid_license_data['signature'] = "invalid_signature"
    
    # Manually create the file with invalid signature (bypass the create_license_file method)
    json_data = json.dumps(invalid_license_data, separators=(',', ':'))
    hex_string = license_system._encode_to_hex(json_data)
    
    with open("LIC-INVALID.lic", "w") as f:
        f.write(hex_string)
    
    # Try to read it (should fail)
    invalid_result = license_system.read_license_file("LIC-INVALID")
    if invalid_result is None:
        print("   ✓ Invalid signature correctly rejected")
    else:
        print("   ✗ Invalid signature was not rejected")
        return False
    
    # Clean up test files
    print()
    print("6. Cleaning up test files...")
    
    for filename in ["LIC-TEST123.lic", "LIC-INVALID.lic"]:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"   ✓ Removed {filename}")
    
    print()
    print("=== All tests passed! ===")
    return True

def test_signature_calculation():
    """Test signature calculation consistency"""
    
    print("\n=== Testing Signature Calculation ===\n")
    
    license_system = LicenseSystem()
    
    # Create test data
    test_data = {
        "product_name": "Test Product",
        "license_id": "TEST-123",
        "max_activations": 1,
        "current_activations": 0,
        "accounts": [],
        "generated_at": "2024-01-15T10:30:00",
        "expiry_date": None,
        "version": "1.0"
    }
    
    # Calculate signature
    signature1 = license_system._calculate_signature(test_data)
    print(f"1. Calculated signature: {signature1}")
    
    # Calculate again (should be identical)
    signature2 = license_system._calculate_signature(test_data)
    print(f"2. Calculated signature: {signature2}")
    
    if signature1 == signature2:
        print("   ✓ Signature calculation is consistent")
    else:
        print("   ✗ Signature calculation is inconsistent")
        return False
    
    # Test with different data
    test_data2 = test_data.copy()
    test_data2["product_name"] = "Different Product"
    
    signature3 = license_system._calculate_signature(test_data2)
    print(f"3. Different data signature: {signature3}")
    
    if signature1 != signature3:
        print("   ✓ Different data produces different signature")
    else:
        print("   ✗ Different data produces same signature")
        return False
    
    print("   ✓ Signature calculation tests passed")
    return True

def test_hex_encoding():
    """Test hex encoding/decoding"""
    
    print("\n=== Testing Hex Encoding ===\n")
    
    license_system = LicenseSystem()
    
    # Test data
    test_json = '{"test":"data","number":123}'
    
    # Encode to hex
    binary_data = license_system._encode_to_hex(test_json)
    print(f"1. Original JSON: {test_json}")
    print(f"2. Hex-encoded data length: {len(binary_data)} bytes")
    
    # Check if it's not readable
    try:
        binary_str = binary_data.decode('utf-8')
        if binary_str.isprintable():
            print("   ⚠ Hex-encoded data appears readable")
        else:
            print("   ✓ Hex-encoded data is not readable")
    except UnicodeDecodeError:
        print("   ✓ Hex-encoded data is not readable (contains non-UTF8 bytes)")
    
    # Decode back
    decoded_json = license_system._decode_from_hex(binary_data)
    print(f"3. Decoded JSON: {decoded_json}")
    
    if decoded_json == test_json:
        print("   ✓ Hex encoding/decoding works correctly")
    else:
        print("   ✗ Hex encoding/decoding failed")
        return False
    
    return True

if __name__ == "__main__":
    print("Binary License System Test Suite")
    print("=" * 40)
    
    # Run all tests
    tests = [
        test_binary_license_system,
        test_signature_calculation,
        test_hex_encoding
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"   ✗ Test failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1) 