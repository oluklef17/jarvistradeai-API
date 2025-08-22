import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login', 
                        json={'email': 'admin@jarvistrade.com', 'password': 'admin123'})
token = response.json()['access_token']

# Test review creation
product_id = "4c622151-83f6-44ff-b973-9f58f76abfbf"  # Advanced Trading Bot
review_data = {
    "rating": 5,
    "comment": "This is a test review for the dashboard activity log."
}

response = requests.post(f'http://localhost:8000/api/products/{product_id}/reviews', 
                        json=review_data,
                        headers={'Authorization': f'Bearer {token}'})

print(f"Review creation status: {response.status_code}")
if response.status_code == 200:
    print("Review created successfully!")
    print(response.json())
else:
    print(f"Error: {response.text}") 