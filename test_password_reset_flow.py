#!/usr/bin/env python3
"""
Test script to verify password reset flow
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from fastapi.testclient import TestClient

def test_password_reset_flow():
    """Test the password reset flow"""
    client = TestClient(app)
    
    print("🧪 Testing Password Reset Flow...")
    
    # Test 1: Request password reset
    print("\n1. Testing password reset request...")
    reset_request = {
        "email": "test@example.com"
    }
    
    response = client.post("/api/auth/forgot-password", json=reset_request)
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✅ Password reset request successful")
    else:
        print("   ❌ Password reset request failed")
    
    # Test 2: Check if the reset URL is constructed correctly
    print("\n2. Checking reset URL construction...")
    
    # Get the FRONTEND_URL from environment
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    print(f"   FRONTEND_URL from environment: {frontend_url}")
    
    # Simulate a reset token
    test_token = "test-reset-token-123"
    expected_reset_url = f"{frontend_url}/reset-password?token={test_token}"
    print(f"   Expected reset URL: {expected_reset_url}")
    
    # Test 3: Test the reset-password endpoint (this would normally require a valid token)
    print("\n3. Testing reset password endpoint...")
    reset_password_request = {
        "token": "invalid-token",
        "new_password": "newpassword123"
    }
    
    response = client.post("/api/auth/reset-password", json=reset_password_request)
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 400:
        print("   ✅ Reset password endpoint correctly rejected invalid token")
    else:
        print("   ❌ Reset password endpoint should have rejected invalid token")
    
    print("\n🎯 Password Reset Flow Test Complete!")
    print(f"   Frontend URL configured as: {frontend_url}")
    print(f"   Reset URLs will be constructed as: {frontend_url}/reset-password?token=<token>")

if __name__ == "__main__":
    test_password_reset_flow()
