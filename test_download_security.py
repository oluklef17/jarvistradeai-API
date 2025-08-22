import os
import sys
from datetime import datetime, timedelta
from database import SessionLocal
from models_mysql import Product, User, DownloadToken
from payment_service import PaymentService

def test_download_security_options():
    """Test different download security configurations"""
    try:
        db = SessionLocal()
        
        # Get a test user
        user = db.query(User).first()
        if not user:
            print("No users found in database")
            return
        
        print("🔒 Download Security Configuration Test")
        print("=" * 50)
        
        # Test different security configurations
        security_configs = [
            {
                "name": "Single-Use (Maximum Security)",
                "max_downloads": 1,
                "is_single_use": True,
                "description": "One download only, highest security"
            },
            {
                "name": "Limited Downloads (Balanced)",
                "max_downloads": 3,
                "is_single_use": False,
                "description": "3 downloads allowed, good balance"
            },
            {
                "name": "Multiple Downloads (User-Friendly)",
                "max_downloads": 5,
                "is_single_use": False,
                "description": "5 downloads allowed, user-friendly"
            }
        ]
        
        for i, config in enumerate(security_configs, 1):
            print(f"\n{i}. {config['name']}")
            print(f"   Description: {config['description']}")
            print(f"   Max Downloads: {config['max_downloads']}")
            print(f"   Single Use: {config['is_single_use']}")
            
            # Create a test token
            token_string = "test_token_" + str(i)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            test_token = DownloadToken(
                user_id=user.id,
                product_id=None,
                transaction_id="test_transaction",
                token=token_string,
                is_single_use=config['is_single_use'],
                expires_at=expires_at,
                file_path="/test/path.zip",
                download_count=0,
                max_downloads=config['max_downloads']
            )
            
            # Simulate download attempts
            payment_service = PaymentService()
            
            for attempt in range(config['max_downloads'] + 1):
                result = payment_service.validate_download_token(
                    db, token_string, "127.0.0.1", "Test Browser"
                )
                
                if result["success"]:
                    remaining = result.get("downloads_remaining", 0)
                    print(f"   ✓ Download {attempt + 1}: Success (Remaining: {remaining})")
                else:
                    print(f"   ✗ Download {attempt + 1}: {result['error']}")
                    break
            
            # Clean up test token
            db.query(DownloadToken).filter(DownloadToken.token == token_string).delete()
            db.commit()
        
        print("\n" + "=" * 50)
        print("📋 Security Recommendations:")
        print("1. For high-value products: Use Single-Use (1 download)")
        print("2. For standard products: Use Limited Downloads (3 downloads)")
        print("3. For user-friendly experience: Use Multiple Downloads (5 downloads)")
        print("4. Always set reasonable expiry times (24-48 hours)")
        print("5. Monitor download logs for suspicious activity")
        
        print("\n🔧 Environment Variables:")
        print("MAX_DOWNLOADS_PER_TOKEN=3")
        print("ENABLE_SINGLE_USE_TOKENS=false")
        print("DOWNLOAD_TOKEN_EXPIRY_HOURS=24")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_download_security_options() 