import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_paystack_integration():
    """Test Paystack integration"""
    
    # Test 1: Check if environment variables are set
    print("Testing Paystack configuration...")
    secret_key = os.getenv('PAYSTACK_SECRET_KEY')
    if not secret_key:
        print("❌ PAYSTACK_SECRET_KEY not found in environment variables")
        return False
    else:
        print("✅ PAYSTACK_SECRET_KEY is configured")
    
    # Test 2: Test Paystack API connection
    print("\nTesting Paystack API connection...")
    try:
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        # Test with a simple request to get bank list
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.paystack.co/bank", headers=headers) as response:
                if response.status == 200:
                    print("✅ Paystack API connection successful")
                else:
                    print(f"❌ Paystack API connection failed: {response.status}")
                    return False
            
    except Exception as e:
        print(f"❌ Paystack API connection error: {e}")
        return False
    
    # Test 3: Test checkout endpoint (requires authentication)
    print("\nTesting checkout endpoint...")
    try:
        # First, get a test token (you'd need to implement this)
        test_data = {
            "items": [
                {
                    "id": "test-1",
                    "name": "Test Product",
                    "price": 100,
                    "quantity": 1
                }
            ],
            "totalAmount": 108.00  # Including tax
        }
        
        # This would require a valid user token
        print("ℹ️  Checkout endpoint requires authentication - test manually")
        
    except Exception as e:
        print(f"❌ Checkout test error: {e}")
        return False
    
    print("\n🎉 Paystack integration tests completed!")
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_paystack_integration()) 