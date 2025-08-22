import sqlite3
import os

def create_blog_table():
    """Create the blog_posts table in the database"""
    
    # Connect to the database
    conn = sqlite3.connect('jarvistrade.db')
    cursor = conn.cursor()
    
    # Create blog_posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT NOT NULL,
            featured_image TEXT,
            author_id TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            is_featured BOOLEAN DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            tags TEXT,
            meta_title TEXT,
            meta_description TEXT,
            published_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts (slug)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_author ON blog_posts (author_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts (published_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_blog_posts_featured ON blog_posts (is_featured)')
    
    # Commit the changes
    conn.commit()
    conn.close()
    
    print("Blog posts table created successfully!")

if __name__ == "__main__":
    create_blog_table() 