import sqlite3
import aiohttp
import asyncio

# Check database for transactions
conn = sqlite3.connect('jarvistrade.db')
cursor = conn.cursor()

cursor.execute("SELECT paystack_reference, status, amount, created_at FROM transactions ORDER BY created_at DESC LIMIT 5")
transactions = cursor.fetchall()

print("Recent transactions:")
for t in transactions:
    print(f"  Reference: {t[0]}, Status: {t[1]}, Amount: {t[2]}, Created: {t[3]}")

conn.close()

async def test_status_endpoint():
    # Test the status endpoint
    if transactions:
        reference = transactions[0][0]
        print(f"\nTesting status endpoint for reference: {reference}")
        
        # Login first
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8000/api/auth/login', 
                                     json={'email': 'admin@jarvistrade.com', 'password': 'admin123'}) as login_response:
                
                if login_response.status == 200:
                    login_data = await login_response.json()
                    token = login_data['access_token']
                    
                    # Test status endpoint
                    async with session.get(f'http://localhost:8000/api/payment/status/{reference}',
                                         headers={'Authorization': f'Bearer {token}'}) as status_response:
                        
                        print(f"Status endpoint response: {status_response.status}")
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            print(f"Status data: {status_data}")
                        else:
                            error_text = await status_response.text()
                            print(f"Error: {error_text}")
                else:
                    print("Login failed")
    else:
        print("No transactions found in database")

# Run the async test
if __name__ == "__main__":
    asyncio.run(test_status_endpoint()) 