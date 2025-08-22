import sqlite3
import os

def add_file_path_column():
    """Add file_path column to download_tokens table"""
    try:
        # Connect to the database
        conn = sqlite3.connect('jarvistrade.db')
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(download_tokens)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'file_path' not in columns:
            # Add the file_path column
            cursor.execute("ALTER TABLE download_tokens ADD COLUMN file_path TEXT")
            print("Added file_path column to download_tokens table")
        else:
            print("file_path column already exists")
        
        # Commit the changes
        conn.commit()
        conn.close()
        print("Database schema updated successfully")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")

if __name__ == "__main__":
    add_file_path_column() 