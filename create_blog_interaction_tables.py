import sqlite3
import os

def create_blog_interaction_tables():
    """Create blog likes and comments tables"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create blog_likes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blog_likes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                blog_post_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (blog_post_id) REFERENCES blog_posts (id) ON DELETE CASCADE,
                UNIQUE(user_id, blog_post_id)
            )
        """)
        
        # Create blog_comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blog_comments (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                blog_post_id TEXT NOT NULL,
                parent_comment_id TEXT,
                content TEXT NOT NULL,
                is_approved BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (blog_post_id) REFERENCES blog_posts (id) ON DELETE CASCADE,
                FOREIGN KEY (parent_comment_id) REFERENCES blog_comments (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_likes_user_id ON blog_likes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_likes_post_id ON blog_likes(blog_post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_comments_user_id ON blog_comments(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_comments_post_id ON blog_comments(blog_post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_comments_parent_id ON blog_comments(parent_comment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_comments_approved ON blog_comments(is_approved)")
        
        conn.commit()
        print("✅ Blog interaction tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_blog_interaction_tables() 