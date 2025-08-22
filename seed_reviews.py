#!/usr/bin/env python3
"""
Script to add sample reviews to the database for testing
"""

import sqlite3
import os
import uuid
from datetime import datetime

def seed_reviews():
    """Add sample reviews to the database"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get existing users and products
        cursor.execute("SELECT id, name FROM users LIMIT 5")
        users = cursor.fetchall()
        
        cursor.execute("SELECT id, name FROM products LIMIT 5")
        products = cursor.fetchall()
        
        if not users or not products:
            print("❌ No users or products found in database!")
            return
        
        print(f"Found {len(users)} users and {len(products)} products")
        
        # Sample reviews data
        sample_reviews = [
            {
                "rating": 5,
                "comment": "Excellent trading bot! The automated strategies are incredibly effective. I've seen a 25% increase in my trading performance since using this tool. Highly recommended for serious traders.",
                "is_verified_purchase": True
            },
            {
                "rating": 4,
                "comment": "Great indicator package. The signals are accurate and the interface is user-friendly. Would definitely recommend to other traders.",
                "is_verified_purchase": True
            },
            {
                "rating": 5,
                "comment": "Outstanding risk management toolkit. The position sizing calculator and stop-loss features have saved me from significant losses. Worth every penny!",
                "is_verified_purchase": True
            },
            {
                "rating": 4,
                "comment": "Solid analysis tools. The market scanning capabilities are impressive and help me identify opportunities I would have missed otherwise.",
                "is_verified_purchase": False
            },
            {
                "rating": 5,
                "comment": "Premium quality indicators. The custom alerts and real-time notifications work perfectly. This has become an essential part of my trading routine.",
                "is_verified_purchase": True
            },
            {
                "rating": 3,
                "comment": "Good product overall, but could use some improvements in the user interface. The functionality is solid though.",
                "is_verified_purchase": False
            },
            {
                "rating": 5,
                "comment": "Amazing educational content! The tutorials and guides are comprehensive and easy to follow. Perfect for both beginners and experienced traders.",
                "is_verified_purchase": True
            },
            {
                "rating": 4,
                "comment": "Reliable trading bot with good performance. The backtesting results were impressive and the live trading matches expectations.",
                "is_verified_purchase": True
            }
        ]
        
        # Insert sample reviews
        reviews_added = 0
        for i, product in enumerate(products):
            # Add 2-3 reviews per product
            for j in range(min(3, len(sample_reviews) - i * 2)):
                review_data = sample_reviews[i * 2 + j]
                user = users[i % len(users)]
                
                cursor.execute("""
                    INSERT INTO reviews (
                        id, user_id, product_id, rating, comment, 
                        is_verified_purchase, is_approved, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    user[0],
                    product[0],
                    review_data["rating"],
                    review_data["comment"],
                    review_data["is_verified_purchase"],
                    True,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                reviews_added += 1
        
        # Update product ratings
        cursor.execute("""
            UPDATE products 
            SET rating = (
                SELECT ROUND(AVG(rating), 1)
                FROM reviews 
                WHERE reviews.product_id = products.id 
                AND reviews.is_approved = 1
            )
        """)
        
        # Commit the changes
        conn.commit()
        print(f"✅ Successfully added {reviews_added} sample reviews!")
        
        # Show some statistics
        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_reviews = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(rating) FROM reviews WHERE is_approved = 1")
        avg_rating = cursor.fetchone()[0]
        
        print(f"📊 Total reviews: {total_reviews}")
        print(f"📊 Average rating: {avg_rating:.1f}")
        
        # Show some sample reviews
        cursor.execute("""
            SELECT r.comment, r.rating, u.name, p.name 
            FROM reviews r 
            JOIN users u ON r.user_id = u.id 
            JOIN products p ON r.product_id = p.id 
            LIMIT 3
        """)
        sample_reviews = cursor.fetchall()
        
        print("\n📝 Sample reviews:")
        for review in sample_reviews:
            print(f"  - {review[2]} rated {review[3]} {review[1]}/5 stars")
            print(f"    \"{review[0][:50]}...\"")
            print()
            
    except Exception as e:
        print(f"❌ Error seeding reviews: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_reviews() 