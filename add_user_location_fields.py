import sqlite3
import os

def add_user_location_fields():
    """Add location fields to the users table"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add country field if it doesn't exist
        if 'country' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN country TEXT DEFAULT 'US'")
            print("Added 'country' column to users table")
        
        # Add currency field if it doesn't exist
        if 'currency' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'USD'")
            print("Added 'currency' column to users table")
        
        # Add currency_symbol field if it doesn't exist
        if 'currency_symbol' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN currency_symbol TEXT DEFAULT '$'")
            print("Added 'currency_symbol' column to users table")
        
        # Commit the changes
        conn.commit()
        print("Successfully added location fields to users table")
        
    except Exception as e:
        print(f"Error adding location fields: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    add_user_location_fields() 