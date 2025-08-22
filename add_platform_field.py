import sqlite3
import os

def add_platform_field():
    """Add platform field to products table"""
    db_path = "jarvistrade.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if platform column already exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'platform' in columns:
            print("Platform column already exists!")
            return
        
        # Add platform column with default value MT4
        print("Adding platform column to products table...")
        cursor.execute("ALTER TABLE products ADD COLUMN platform TEXT DEFAULT 'MT4'")
        
        # Update existing products to have MT4 as default platform
        print("Updating existing products to have MT4 as default platform...")
        cursor.execute("UPDATE products SET platform = 'MT4' WHERE platform IS NULL")
        
        # Create index on platform column for better performance
        print("Creating index on platform column...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_platform ON products(platform)")
        
        # Commit changes
        conn.commit()
        print("Successfully added platform field to products table!")
        
        # Show some statistics
        cursor.execute("SELECT platform, COUNT(*) FROM products GROUP BY platform")
        platform_counts = cursor.fetchall()
        print("\nPlatform distribution:")
        for platform, count in platform_counts:
            print(f"  {platform}: {count} products")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_platform_field()
