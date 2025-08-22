import sqlite3
import os

def add_original_price_column():
    """Add original_price column to products table"""
    
    # Get the database path
    db_path = "jarvistrade.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "original_price" in columns:
            print("Column 'original_price' already exists in products table")
            return
        
        # Add the original_price column
        cursor.execute("ALTER TABLE products ADD COLUMN original_price REAL")
        
        # Update existing products to set original_price = price (no discount initially)
        cursor.execute("UPDATE products SET original_price = price WHERE original_price IS NULL")
        
        # Commit the changes
        conn.commit()
        
        print("Successfully added 'original_price' column to products table")
        print("Existing products updated with original_price = price")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in products table: {columns}")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_original_price_column()
