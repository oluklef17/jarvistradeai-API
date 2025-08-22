#!/usr/bin/env python3
"""
Script to add the reviews table to the existing database
"""

import sqlite3
import os

def create_reviews_table():
    """Create the reviews table in the database"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create the reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comment TEXT NOT NULL,
                is_verified_purchase BOOLEAN DEFAULT 0,
                is_approved BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews (product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews (created_at)")
        
        # Commit the changes
        conn.commit()
        print("✅ Reviews table created successfully!")
        
        # Show table structure
        cursor.execute("PRAGMA table_info(reviews)")
        columns = cursor.fetchall()
        print("\n📋 Reviews table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ Error creating reviews table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_reviews_table() 