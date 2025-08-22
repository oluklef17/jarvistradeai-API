#!/usr/bin/env python3
"""
Script to add slug field to existing products and generate slugs for them.
This script should be run after adding the slug column to the Product model.
"""

import sqlite3
import re
import os
from pathlib import Path

def generate_slug(name):
    """Generate a URL-friendly slug from a product name."""
    if not name:
        return ""
    
    # Convert to lowercase and replace special characters
    slug = name.lower()
    
    # Replace special characters with spaces
    slug = re.sub(r'[^a-z0-9\s-]', ' ', slug)
    
    # Replace multiple spaces with single space
    slug = re.sub(r'\s+', ' ', slug)
    
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure slug is not empty
    if not slug:
        slug = "product"
    
    return slug

def ensure_unique_slug(cursor, slug, product_id, counter=0):
    """Ensure slug is unique by adding a number suffix if needed."""
    if counter == 0:
        test_slug = slug
    else:
        test_slug = f"{slug}-{counter}"
    
    # Check if slug exists for other products
    cursor.execute(
        "SELECT id FROM products WHERE slug = ? AND id != ?",
        (test_slug, product_id)
    )
    
    if cursor.fetchone():
        return ensure_unique_slug(cursor, slug, product_id, counter + 1)
    
    return test_slug

def add_slug_field():
    """Add slug field to products table and populate it for existing products."""
    db_path = "jarvistrade.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if slug column already exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'slug' not in columns:
            print("Adding slug column to products table...")
            cursor.execute("ALTER TABLE products ADD COLUMN slug TEXT")
            print("✓ Slug column added successfully")
        else:
            print("✓ Slug column already exists")
        
        # Get all products that don't have a slug
        cursor.execute("SELECT id, name FROM products WHERE slug IS NULL OR slug = ''")
        products_without_slug = cursor.fetchall()
        
        if not products_without_slug:
            print("✓ All products already have slugs")
            return
        
        print(f"Found {len(products_without_slug)} products without slugs. Generating slugs...")
        
        updated_count = 0
        for product_id, name in products_without_slug:
            if name:
                # Generate base slug
                base_slug = generate_slug(name)
                
                # Ensure uniqueness
                unique_slug = ensure_unique_slug(cursor, base_slug, product_id)
                
                # Update the product
                cursor.execute(
                    "UPDATE products SET slug = ? WHERE id = ?",
                    (unique_slug, product_id)
                )
                
                print(f"  {name} → {unique_slug}")
                updated_count += 1
        
        # Commit changes
        conn.commit()
        print(f"✓ Successfully updated {updated_count} products with slugs")
        
        # Create index on slug column for better performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug)")
            print("✓ Slug index created/verified")
        except Exception as e:
            print(f"Warning: Could not create slug index: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Adding slug field to products table...")
    add_slug_field()
    print("Done!")
