import sqlite3
import json

def add_notification_preferences():
    """Add notification preferences columns to users table"""
    conn = sqlite3.connect('jarvistrade.db')
    cursor = conn.cursor()

    try:
        # Add notification preferences columns
        cursor.execute('''
            ALTER TABLE users ADD COLUMN notification_preferences TEXT 
            DEFAULT '{"info": true, "success": true, "warning": true, "error": true, "payment": true, "order": true, "system": true, "update": true, "review_prompt": true}'
        ''')

        cursor.execute('''
            ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE
        ''')

        cursor.execute('''
            ALTER TABLE users ADD COLUMN push_notifications BOOLEAN DEFAULT TRUE
        ''')

        conn.commit()
        print("✅ Notification preferences columns added successfully!")

        # Update existing users with default preferences
        default_preferences = {
            "info": True,
            "success": True,
            "warning": True,
            "error": True,
            "payment": True,
            "order": True,
            "system": True,
            "update": True,
            "review_prompt": True
        }

        cursor.execute('''
            UPDATE users SET 
            notification_preferences = ?,
            email_notifications = TRUE,
            push_notifications = TRUE
            WHERE notification_preferences IS NULL
        ''', (json.dumps(default_preferences),))

        conn.commit()
        print("✅ Default notification preferences applied to existing users!")

    except Exception as e:
        print(f"❌ Error adding notification preferences: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_notification_preferences() 