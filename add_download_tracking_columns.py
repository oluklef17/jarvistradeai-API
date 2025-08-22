import sqlite3
import os

def add_download_tracking_columns():
    """Add download tracking columns to download_tokens table"""
    try:
        # Connect to the database
        conn = sqlite3.connect('jarvistrade.db')
        cursor = conn.cursor()
        
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(download_tokens)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add download_count column if it doesn't exist
        if 'download_count' not in columns:
            cursor.execute("ALTER TABLE download_tokens ADD COLUMN download_count INTEGER DEFAULT 0")
            print("Added download_count column to download_tokens table")
        else:
            print("download_count column already exists")
        
        # Add max_downloads column if it doesn't exist
        if 'max_downloads' not in columns:
            cursor.execute("ALTER TABLE download_tokens ADD COLUMN max_downloads INTEGER DEFAULT 1")
            print("Added max_downloads column to download_tokens table")
        else:
            print("max_downloads column already exists")
        
        # Commit the changes
        conn.commit()
        conn.close()
        print("Database schema updated successfully")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")

if __name__ == "__main__":
    add_download_tracking_columns() 