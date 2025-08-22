import sqlite3
import os

def update_blog_posts_table():
    """Add new columns to blog_posts table for media and interaction counts"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add new columns to blog_posts table
        new_columns = [
            "youtube_links TEXT",
            "attached_files TEXT", 
            "gallery_images TEXT",
            "like_count INTEGER DEFAULT 0",
            "comment_count INTEGER DEFAULT 0"
        ]
        
        for column_def in new_columns:
            column_name = column_def.split()[0]
            try:
                cursor.execute(f"ALTER TABLE blog_posts ADD COLUMN {column_def}")
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"ℹ️  Column {column_name} already exists")
                else:
                    print(f"❌ Error adding column {column_name}: {e}")
        
        conn.commit()
        print("✅ Blog posts table updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_blog_posts_table() 