import sqlite3
import os

def add_platform_index():
    """Add index on platform column for better query performance"""
    db_path = "jarvistrade.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if platform index already exists
        cursor.execute("PRAGMA index_list(products)")
        indexes = [index[1] for index in cursor.fetchall()]
        
        if 'idx_products_platform' in indexes:
            print("Platform index already exists!")
            return
        
        # Create index on platform column for better performance
        print("Creating index on platform column...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_platform ON products(platform)")
        
        # Commit changes
        conn.commit()
        print("Successfully created platform index!")
        
        # Show index information
        cursor.execute("PRAGMA index_info(idx_products_platform)")
        index_info = cursor.fetchall()
        print(f"Index created with {len(index_info)} columns")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_platform_index()

