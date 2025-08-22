import sqlite3
import uuid
from datetime import datetime

def create_notifications_table():
    """Create notifications table in the database"""
    conn = sqlite3.connect('jarvistrade.db')
    cursor = conn.cursor()
    
    try:
        # Create notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id 
            ON notifications (user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
            ON notifications (created_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notifications_is_read 
            ON notifications (is_read)
        ''')
        
        conn.commit()
        print("✅ Notifications table created successfully!")
        
        # Add some sample notifications for testing
        sample_notifications = [
            {
                'id': str(uuid.uuid4()),
                'user_id': '1',  # Assuming admin user ID is 1
                'title': 'Welcome to JarvisTrade!',
                'message': 'Thank you for joining our platform. Explore our premium trading tools and services.',
                'type': 'info',
                'is_read': False,
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': str(uuid.uuid4()),
                'user_id': '1',
                'title': 'System Update',
                'message': 'We have added new features including real-time notifications and improved user experience.',
                'type': 'system',
                'is_read': False,
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        for notification in sample_notifications:
            cursor.execute('''
                INSERT OR IGNORE INTO notifications 
                (id, user_id, title, message, type, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                notification['id'],
                notification['user_id'],
                notification['title'],
                notification['message'],
                notification['type'],
                notification['is_read'],
                notification['created_at']
            ))
        
        conn.commit()
        print("✅ Sample notifications added successfully!")
        
    except Exception as e:
        print(f"❌ Error creating notifications table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_notifications_table() 