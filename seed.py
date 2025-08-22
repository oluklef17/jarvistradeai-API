#!/usr/bin/env python3

import asyncio
from sqlalchemy.orm import Session
from database import engine, get_db
from models_mysql import Base, User, Product
from auth import get_password_hash
import json
import os

# Create tables
Base.metadata.create_all(bind=engine)

def seed_database():
    db = next(get_db())
    
    # Create admin user if it doesn't exist
    admin_user = db.query(User).filter(User.email == "admin@jarvistrade.com").first()
    if not admin_user:
        admin_user = User(
            email="admin@jarvistrade.com",
            name="Admin User",
            hashed_password=get_password_hash("admin123"),
            is_client=True,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("Admin user created")
    
    # Create digital products directory
    digital_products_dir = "./digital_products"
    if not os.path.exists(digital_products_dir):
        os.makedirs(digital_products_dir)
        print(f"Created directory: {digital_products_dir}")
    
    # Create sample digital files
    sample_files = [
        {
            "name": "Advanced Trading Bot",
            "filename": "advanced_trading_bot.zip",
            "content": "This is a sample digital product file for testing downloads."
        },
        {
            "name": "Premium Indicator Pack",
            "filename": "premium_indicators.zip", 
            "content": "This is a sample indicator pack for testing downloads."
        },
        {
            "name": "Risk Management Toolkit",
            "filename": "risk_management_toolkit.zip",
            "content": "This is a sample risk management toolkit for testing downloads."
        }
    ]
    
    for file_info in sample_files:
        file_path = os.path.join(digital_products_dir, file_info["filename"])
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(file_info["content"])
            print(f"Created sample file: {file_path}")
    
    # Create digital products
    digital_products = [
        {
            "name": "Advanced Trading Bot",
            "description": "A sophisticated algorithmic trading bot with advanced features for automated trading strategies.",
            "short_description": "Professional trading automation",
            "price": 299.99,
            "category": "trading-bot",
            "image": "/products/bot1.png",
            "tags": json.dumps(["automation", "algorithmic", "professional"]),
            "features": json.dumps(["Real-time monitoring", "Risk management", "Backtesting", "Multiple strategies"]),
            "images": json.dumps(["/products/bot1.png", "/products/bot2.png"]),
            "rating": 0.0,
            "total_reviews": 0,
            "is_active": True,
            "is_featured": True,
            "is_digital": True,
            "file_path": os.path.join(digital_products_dir, "advanced_trading_bot.zip"),
            "file_size": 1024 * 1024 * 5,  # 5MB
            "download_count": 0,
            "youtube_demo_link": "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "test_download_link": "https://example.com/test/advanced-trading-bot-demo.zip",
            "user_id": admin_user.id
        },
        {
            "name": "Premium Indicator Pack",
            "description": "A comprehensive collection of technical indicators for advanced market analysis.",
            "short_description": "Professional technical analysis tools",
            "price": 149.99,
            "category": "indicator",
            "image": "/products/indicator1.png",
            "tags": json.dumps(["technical analysis", "indicators", "professional"]),
            "features": json.dumps(["50+ indicators", "Customizable", "Real-time alerts", "Documentation"]),
            "images": json.dumps(["/products/indicator1.png", "/products/indicator2.png"]),
            "rating": 0.0,
            "total_reviews": 0,
            "is_active": True,
            "is_featured": True,
            "is_digital": True,
            "file_path": os.path.join(digital_products_dir, "premium_indicators.zip"),
            "file_size": 1024 * 1024 * 3,  # 3MB
            "download_count": 0,
            "youtube_demo_link": "https://www.youtube.com/embed/9bZkp7q19f0",
            "test_download_link": "https://example.com/test/premium-indicators-demo.zip",
            "user_id": admin_user.id
        },
        {
            "name": "Risk Management Toolkit",
            "description": "Complete risk management solution with position sizing and portfolio protection tools.",
            "short_description": "Professional risk management",
            "price": 199.99,
            "category": "risk-management",
            "image": "/products/risk1.png",
            "tags": json.dumps(["risk management", "portfolio", "protection"]),
            "features": json.dumps(["Position sizing", "Stop-loss automation", "Portfolio monitoring", "Risk reports"]),
            "images": json.dumps(["/products/risk1.png", "/products/risk2.png"]),
            "rating": 0.0,
            "total_reviews": 0,
            "is_active": True,
            "is_featured": False,
            "is_digital": True,
            "file_path": os.path.join(digital_products_dir, "risk_management_toolkit.zip"),
            "file_size": 1024 * 1024 * 4,  # 4MB
            "download_count": 0,
            "youtube_demo_link": "https://www.youtube.com/embed/jNQXAC9IVRw",
            "test_download_link": "https://example.com/test/risk-management-demo.zip",
            "user_id": admin_user.id
        }
    ]
    
    # Add digital products to database
    for product_data in digital_products:
        existing_product = db.query(Product).filter(Product.name == product_data["name"]).first()
        if not existing_product:
            product = Product(**product_data)
            db.add(product)
            print(f"Added digital product: {product_data['name']}")
    
    # Create regular products (non-digital)
    regular_products = [
        {
            "name": "Trading Strategy Guide",
            "description": "Comprehensive guide to developing profitable trading strategies.",
            "short_description": "Learn professional trading strategies",
            "price": 79.99,
            "category": "education",
            "image": "/products/guide1.png",
            "tags": json.dumps(["education", "strategy", "guide"]),
            "features": json.dumps(["Step-by-step tutorials", "Case studies", "Video content", "Community access"]),
            "images": json.dumps(["/products/guide1.png"]),
            "rating": 0.0,
            "total_reviews": 0,
            "is_active": True,
            "is_featured": False,
            "is_digital": False,
            "file_path": None,
            "file_size": None,
            "download_count": 0,
            "youtube_demo_link": "https://www.youtube.com/embed/kJQP7kiw5Fk",
            "test_download_link": None,
            "user_id": admin_user.id
        },
        {
            "name": "Market Analysis Tool",
            "description": "Advanced market analysis software for professional traders.",
            "short_description": "Professional market analysis",
            "price": 399.99,
            "category": "analysis-tool",
            "image": "/products/analysis1.png",
            "tags": json.dumps(["analysis", "professional", "software"]),
            "features": json.dumps(["Real-time data", "Advanced charts", "News integration", "API access"]),
            "images": json.dumps(["/products/analysis1.png"]),
            "rating": 0.0,
            "total_reviews": 0,
            "is_active": True,
            "is_featured": True,
            "is_digital": False,
            "file_path": None,
            "file_size": None,
            "download_count": 0,
            "youtube_demo_link": "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "test_download_link": None,
            "user_id": admin_user.id
        }
    ]
    
    # Add regular products to database
    for product_data in regular_products:
        existing_product = db.query(Product).filter(Product.name == product_data["name"]).first()
        if not existing_product:
            product = Product(**product_data)
            db.add(product)
            print(f"Added regular product: {product_data['name']}")
    
    db.commit()
    print("Database seeding completed!")

if __name__ == "__main__":
    seed_database() 