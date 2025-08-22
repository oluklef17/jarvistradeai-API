#!/usr/bin/env python3

import aiohttp
import asyncio
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@jarvistrade.com"
ADMIN_PASSWORD = "admin123"

async def login() -> str:
    """Login and get access token"""
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE_URL}/api/auth/login", json=login_data) as response:
            response.raise_for_status()
            data = await response.json()
            return data["access_token"]

async def create_product(token: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new product"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE_URL}/api/products", json=product_data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

async def main():
    """Main function to add sample products"""
    
    # Sample products data
    sample_products = [
        {
            "name": "Advanced Trading Bot Pro",
            "description": "Professional automated trading bot with advanced algorithms and risk management features. Includes backtesting, optimization, and real-time monitoring capabilities.",
            "short_description": "Professional automated trading bot with advanced algorithms",
            "price": 199.99,
            "original_price": 299.99,
            "category": "Development",
            "tags": ["bot", "automation", "trading", "MT4", "MT5"],
            "is_active": True,
            "is_featured": True,
            "stock": 50,
            "sku": "BOT-PRO-001",
            "weight": 0.1,
            "dimensions": "Digital Download",
            "requirements": "MT4/MT5 platform, minimum deposit $500, basic trading knowledge",
            "features": [
                "Advanced algorithm implementation",
                "Risk management system",
                "Backtesting capabilities",
                "Real-time monitoring",
                "Customizable parameters",
                "24/7 support"
            ],
            "changelog": "v2.1.0 - Added new risk management features\nv2.0.0 - Complete rewrite with improved algorithms",
            "images": [
                "https://via.placeholder.com/400x300?text=Bot+Interface",
                "https://via.placeholder.com/400x300?text=Dashboard"
            ]
        },
        {
            "name": "Premium Chart Analysis Suite",
            "description": "Comprehensive chart analysis toolkit with advanced indicators, pattern recognition, and market structure analysis. Perfect for professional traders.",
            "short_description": "Comprehensive chart analysis toolkit with advanced indicators",
            "price": 89.99,
            "original_price": 129.99,
            "category": "Premium Tools",
            "tags": ["charts", "analysis", "indicators", "patterns", "MT4"],
            "is_active": True,
            "is_featured": False,
            "stock": 100,
            "sku": "CHART-SUITE-002",
            "weight": 0.05,
            "dimensions": "Digital Download",
            "requirements": "MT4 platform, intermediate trading knowledge",
            "features": [
                "Advanced chart indicators",
                "Pattern recognition",
                "Market structure analysis",
                "Custom drawing tools",
                "Multiple timeframe analysis",
                "Export capabilities"
            ],
            "changelog": "v1.5.0 - Added new pattern recognition algorithms\nv1.4.0 - Enhanced drawing tools",
            "images": [
                "https://via.placeholder.com/400x300?text=Chart+Analysis",
                "https://via.placeholder.com/400x300?text=Indicators"
            ]
        },
        {
            "name": "Risk Management Masterclass",
            "description": "Comprehensive course on risk management strategies for traders. Learn position sizing, stop-loss techniques, and portfolio management.",
            "short_description": "Comprehensive course on risk management strategies",
            "price": 149.99,
            "category": "Education",
            "tags": ["education", "risk management", "course", "trading"],
            "is_active": True,
            "is_featured": True,
            "stock": 200,
            "sku": "EDU-RISK-003",
            "weight": 0.0,
            "dimensions": "Digital Course",
            "requirements": "Basic trading knowledge, willingness to learn",
            "features": [
                "10+ hours of video content",
                "Interactive exercises",
                "Risk assessment tools",
                "Portfolio templates",
                "Lifetime access",
                "Certificate of completion"
            ],
            "changelog": "v1.2.0 - Added new case studies\nv1.1.0 - Enhanced interactive exercises",
            "images": [
                "https://via.placeholder.com/400x300?text=Course+Preview",
                "https://via.placeholder.com/400x300?text=Risk+Management"
            ]
        }
    ]
    
    try:
        print("Logging in...")
        token = await login()
        print(f"Successfully logged in with token: {token[:20]}...")
        
        for i, product_data in enumerate(sample_products, 1):
            print(f"\nCreating product {i}/{len(sample_products)}: {product_data['name']}")
            
            try:
                result = await create_product(token, product_data)
                print(f"✅ Successfully created: {result['name']} (ID: {result['id']})")
            except aiohttp.ClientError as e:
                print(f"❌ Failed to create product: {e}")
        
        print(f"\n🎉 Completed! Added {len(sample_products)} products.")
        
    except aiohttp.ClientError as e:
        print(f"❌ Login failed: {e}")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 