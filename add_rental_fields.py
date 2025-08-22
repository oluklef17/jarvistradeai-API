#!/usr/bin/env python3
"""
Database migration script to add rental fields to existing tables.
This script adds rental functionality to the JarvisTrade system.
"""

import sqlite3
import os
from datetime import datetime

def add_rental_fields():
    """Add rental fields to the database tables"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting rental fields migration...")
        
        # Check if rental fields already exist
        cursor.execute("PRAGMA table_info(products)")
        product_columns = [column[1] for column in cursor.fetchall()]
        
        # Add rental fields to products table
        if "has_rental_option" not in product_columns:
            print("Adding has_rental_option column to products table...")
            cursor.execute("ALTER TABLE products ADD COLUMN has_rental_option BOOLEAN DEFAULT 0")
        
        if "rental_price" not in product_columns:
            print("Adding rental_price column to products table...")
            cursor.execute("ALTER TABLE products ADD COLUMN rental_price REAL")
        
        if "rental_duration_days" not in product_columns:
            print("Adding rental_duration_days column to products table...")
            cursor.execute("ALTER TABLE products ADD COLUMN rental_duration_days INTEGER DEFAULT 30")
        
        # Check licenses table
        cursor.execute("PRAGMA table_info(licenses)")
        license_columns = [column[1] for column in cursor.fetchall()]
        
        # Add rental fields to licenses table
        if "expires_at" not in license_columns:
            print("Adding expires_at column to licenses table...")
            cursor.execute("ALTER TABLE licenses ADD COLUMN expires_at DATETIME")
        
        if "is_rental" not in license_columns:
            print("Adding is_rental column to licenses table...")
            cursor.execute("ALTER TABLE licenses ADD COLUMN is_rental BOOLEAN DEFAULT 0")
        
        # Check order_items table
        cursor.execute("PRAGMA table_info(order_items)")
        order_item_columns = [column[1] for column in cursor.fetchall()]
        
        # Add rental fields to order_items table
        if "is_rental" not in order_item_columns:
            print("Adding is_rental column to order_items table...")
            cursor.execute("ALTER TABLE order_items ADD COLUMN is_rental BOOLEAN DEFAULT 0")
        
        if "rental_duration_days" not in order_item_columns:
            print("Adding rental_duration_days column to order_items table...")
            cursor.execute("ALTER TABLE order_items ADD COLUMN rental_duration_days INTEGER")
        
        # Commit changes
        conn.commit()
        print("✅ Rental fields migration completed successfully!")
        
        # Verify the changes
        print("\nVerifying migration...")
        
        # Check products table
        cursor.execute("PRAGMA table_info(products)")
        product_columns = [column[1] for column in cursor.fetchall()]
        rental_fields = ["has_rental_option", "rental_price", "rental_duration_days"]
        
        for field in rental_fields:
            if field in product_columns:
                print(f"✅ {field} column exists in products table")
            else:
                print(f"❌ {field} column missing from products table")
        
        # Check licenses table
        cursor.execute("PRAGMA table_info(licenses)")
        license_columns = [column[1] for column in cursor.fetchall()]
        license_rental_fields = ["expires_at", "is_rental"]
        
        for field in license_rental_fields:
            if field in license_columns:
                print(f"✅ {field} column exists in licenses table")
            else:
                print(f"❌ {field} column missing from licenses table")
        
        # Check order_items table
        cursor.execute("PRAGMA table_info(order_items)")
        order_item_columns = [column[1] for column in cursor.fetchall()]
        order_item_rental_fields = ["is_rental", "rental_duration_days"]
        
        for field in order_item_rental_fields:
            if field in order_item_columns:
                print(f"✅ {field} column exists in order_items table")
            else:
                print(f"❌ {field} column missing from order_items table")
        
        print(f"\nMigration completed at {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_rental_fields()
