#!/usr/bin/env python3
"""
Test script for purchased products endpoints
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def test_purchased_products_endpoints():
    """Test the purchased products endpoints"""
    
    print("=== Testing Purchased Products Endpoints ===\n")
    
    # First, try to get purchased products without authentication
    print("1. Testing without authentication...")
    try:
        response = requests.get(f"{BASE_URL}/api/users/me/purchased-products")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Correctly requires authentication")
        else:
            print("   ⚠ Unexpected status code")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test generate download token endpoint
    print("\n2. Testing generate download token endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/api/users/me/products/test-product-id/generate-download-token")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Correctly requires authentication")
        else:
            print("   ⚠ Unexpected status code")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n=== Test completed ===")
    print("Note: These endpoints require authentication to work properly.")
    print("To test with authentication, you would need to:")
    print("1. Login to get an access token")
    print("2. Use the token in the Authorization header")
    print("3. Test with actual user data")

if __name__ == "__main__":
    test_purchased_products_endpoints() 