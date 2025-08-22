#!/usr/bin/env python3
"""
Test Script for Email Functionality

This script tests the email service functions to ensure they work correctly.
Run this after setting up your environment variables.

Usage:
    python test_email_functionality.py
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'SMTP_SERVER',
        'SMTP_PORT', 
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'FROM_EMAIL',
        'APP_NAME',
        'FRONTEND_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {value}")
        else:
            print(f"  ✗ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ All required environment variables are set")
    return True

def test_email_service_import():
    """Test if email service can be imported"""
    print("\n🔍 Testing email service import...")
    
    try:
        from email_service import email_service
        print("✅ Email service imported successfully")
        return email_service
    except ImportError as e:
        print(f"❌ Failed to import email service: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error importing email service: {e}")
        return None

def test_welcome_email(email_service):
    """Test welcome email functionality"""
    print("\n🔍 Testing welcome email...")
    
    try:
        test_email = "test@example.com"
        test_name = "Test User"
        verification_url = "https://example.com/verify?token=test123"
        
        result = email_service.send_welcome_email(
            user_email=test_email,
            user_name=test_name,
            verification_url=verification_url
        )
        
        if result:
            print("✅ Welcome email sent successfully")
        else:
            print("⚠️  Welcome email would be sent (SMTP not configured)")
            
        return result
        
    except Exception as e:
        print(f"❌ Error testing welcome email: {e}")
        return False

def test_password_reset_email(email_service):
    """Test password reset email functionality"""
    print("\n🔍 Testing password reset email...")
    
    try:
        test_email = "test@example.com"
        test_name = "Test User"
        reset_url = "https://example.com/reset?token=test123"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        result = email_service.send_password_reset_email(
            user_email=test_email,
            user_name=test_name,
            reset_url=reset_url,
            expires_at=expires_at
        )
        
        if result:
            print("✅ Password reset email sent successfully")
        else:
            print("⚠️  Password reset email would be sent (SMTP not configured)")
            
        return result
        
    except Exception as e:
        print(f"❌ Error testing password reset email: {e}")
        return False

def test_email_verification_email(email_service):
    """Test email verification email functionality"""
    print("\n🔍 Testing email verification email...")
    
    try:
        test_email = "test@example.com"
        test_name = "Test User"
        verification_url = "https://example.com/verify?token=test123"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        result = email_service.send_email_verification_email(
            user_email=test_email,
            user_name=test_name,
            verification_url=verification_url,
            expires_at=expires_at
        )
        
        if result:
            print("✅ Email verification email sent successfully")
        else:
            print("⚠️  Email verification email would be sent (SMTP not configured)")
            
        return result
        
    except Exception as e:
        print(f"❌ Error testing email verification email: {e}")
        return False

def test_smtp_connection():
    """Test SMTP connection"""
    print("\n🔍 Testing SMTP connection...")
    
    try:
        import smtplib
        
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not all([smtp_server, smtp_username, smtp_password]):
            print("⚠️  SMTP credentials not complete, skipping connection test")
            return False
        
        print(f"  Connecting to {smtp_server}:{smtp_port}...")
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print("  Authenticating...")
        server.login(smtp_username, smtp_password)
        
        print("✅ SMTP connection successful")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP authentication failed - check username and password")
        return False
    except smtplib.SMTPConnectError:
        print("❌ SMTP connection failed - check server and port")
        return False
    except Exception as e:
        print(f"❌ SMTP test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Email Functionality Test Suite")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test environment variables
    if not test_environment_variables():
        print("\n❌ Environment setup incomplete. Please fix the issues above.")
        sys.exit(1)
    
    # Test SMTP connection
    smtp_ok = test_smtp_connection()
    
    # Test email service import
    email_service = test_email_service_import()
    if not email_service:
        print("\n❌ Email service not available. Please check the errors above.")
        sys.exit(1)
    
    # Test email functions
    print("\n" + "=" * 40)
    print("Testing Email Functions")
    print("=" * 40)
    
    welcome_ok = test_welcome_email(email_service)
    reset_ok = test_password_reset_email(email_service)
    verify_ok = test_email_verification_email(email_service)
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Summary")
    print("=" * 40)
    
    tests = [
        ("Environment Variables", True),
        ("SMTP Connection", smtp_ok),
        ("Welcome Email", welcome_ok),
        ("Password Reset Email", reset_ok),
        ("Email Verification Email", verify_ok)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Email functionality is working correctly.")
        print("\nNext steps:")
        print("1. Test the API endpoints")
        print("2. Verify email delivery")
        print("3. Test the forgot password flow")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
        
        if not smtp_ok:
            print("\nSMTP Issues:")
            print("- Verify your SMTP credentials")
            print("- Check if 2FA is enabled (for Gmail)")
            print("- Verify firewall/network settings")
            print("- Check email provider's sending limits")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
