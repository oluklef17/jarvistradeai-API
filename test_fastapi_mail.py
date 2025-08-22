#!/usr/bin/env python3
"""
Test script for FastAPI Mail configuration
Run this script to test if your email configuration is working properly.
"""

import asyncio
import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

# Load environment variables
load_dotenv()

async def test_email_config():
    """Test the email configuration"""
    
    print("🔧 Testing FastAPI Mail Configuration...")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = [
        'SMTP_USERNAME',
        'SMTP_PASSWORD', 
        'SMTP_SERVER',
        'SMTP_PORT',
        'FROM_EMAIL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {value if var != 'SMTP_PASSWORD' else '***'}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all SMTP settings are configured.")
        return False
    
    print("\n📧 Testing email configuration...")
    
    try:
        # Create mail configuration
        mail_config = ConnectionConfig(
            MAIL_USERNAME=os.getenv('SMTP_USERNAME'),
            MAIL_PASSWORD=os.getenv('SMTP_PASSWORD'),
            MAIL_FROM=os.getenv('FROM_EMAIL', 'noreply@jarvistrade.com'),
            MAIL_PORT=int(os.getenv('SMTP_PORT', '587')),
            MAIL_SERVER=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            MAIL_FROM_NAME=os.getenv('APP_NAME', 'JarvisTrade'),
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        
        print("✅ Mail configuration created successfully")
        
        # Create FastMail instance
        fast_mail = FastMail(mail_config)
        print("✅ FastMail instance created successfully")
        
        # Test email content
        test_email = "smartmoneycreed@gmail.com"  # Change this to a real email for testing
        
        message = MessageSchema(
            subject="FastAPI Mail Test - JarvisTrade",
            recipients=[test_email],
            body="""
            <html>
            <body>
                <h2>FastAPI Mail Test</h2>
                <p>This is a test email to verify that your FastAPI Mail configuration is working correctly.</p>
                <p>If you receive this email, your email service is properly configured!</p>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    Sent from JarvisTrade backend using FastAPI Mail
                </p>
            </body>
            </html>
            """,
            subtype=MessageType.html
        )
        
        print(f"✅ Test message created for: {test_email}")
        
        # Note: Uncomment the line below to actually send a test email
        await fast_mail.send_message(message)
        # print("ℹ️  Test email not sent (commented out for safety)")
        # print("   Uncomment the send_message line in the script to test actual email sending")
        
        print("\n🎉 FastAPI Mail configuration test completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update the test_email variable with a real email address")
        print("2. Uncomment the send_message line to test actual email sending")
        print("3. Run the script again to verify email delivery")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing email configuration: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Check your SMTP credentials")
        print("2. Verify SMTP server and port settings")
        print("3. Ensure your email provider allows SMTP access")
        print("4. Check firewall/network settings")
        return False

async def main():
    """Main function"""
    print("🚀 JarvisTrade FastAPI Mail Test")
    print("=" * 40)
    
    success = await test_email_config()
    
    if success:
        print("\n✅ All tests passed! Your email service is ready to use.")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    asyncio.run(main())


