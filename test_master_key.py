#!/usr/bin/env python3
"""
Test script for master key signature calculation
"""

from license_encryption import LicenseSystem, create_license_data

def test_master_key_signature():
    """Test signature calculation with master key"""
    
    print("=== Testing Master Key Signature ===\n")
    
    # Test with different master keys
    test_cases = [
        ("JarvisTrade2024", "Default key"),
        ("CustomKey123", "Custom key"),
        ("AnotherKey456", "Another key")
    ]
    
    for master_key, description in test_cases:
        print(f"Testing with {description}: {master_key}")
        
        # Create license system with master key
        ls = LicenseSystem(master_key)
        
        # Create test data
        test_data = {
            "product_name": "Test Product",
            "license_id": "LIC-TEST123",
            "max_activations": 1,
            "current_activations": 0,
            "accounts": [],
            "generated_at": "2024-01-15T10:30:00",
            "expiry_date": None,
            "version": "1.0"
        }
        
        # Calculate signature
        signature = ls._calculate_signature(test_data)
        print(f"   Signature: {signature[:20]}...")
        
        # Verify signature
        test_data['signature'] = signature
        is_valid = ls._verify_signature(test_data)
        print(f"   Verification: {'✓ Pass' if is_valid else '✗ Fail'}")
        
        # Test with different data (should produce different signature)
        test_data2 = test_data.copy()
        test_data2['product_name'] = "Different Product"
        signature2 = ls._calculate_signature(test_data2)
        print(f"   Different data signature: {signature2[:20]}...")
        
        if signature != signature2:
            print("   ✓ Different data produces different signature")
        else:
            print("   ✗ Different data produces same signature")
        
        print()
    
    # Test creating and reading license file
    print("=== Testing License File Creation ===\n")
    
    ls = LicenseSystem("JarvisTrade2024")
    license_data = create_license_data(
        product_name="Advanced Trading Bot",
        license_id="LIC-MASTER123",
        accounts=[
            {"account_login": "123456", "account_server": "MetaQuotes-Demo"}
        ],
        max_activations=2
    )
    
    # Create license file
    success = ls.create_license_file(license_data, "LIC-MASTER123")
    if success:
        print("✓ License file created successfully")
        
        # Read and verify license file
        read_data = ls.read_license_file("LIC-MASTER123")
        if read_data:
            print("✓ License file read and verified successfully")
            print(f"   Product: {read_data['product_name']}")
            print(f"   License ID: {read_data['license_id']}")
            print(f"   Max Activations: {read_data['max_activations']}")
        else:
            print("✗ Failed to read license file")
    else:
        print("✗ Failed to create license file")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_master_key_signature() 