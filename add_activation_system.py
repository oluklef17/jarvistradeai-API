import sqlite3
import json
from datetime import datetime

def add_activation_system():
    """Add activation system fields and tables to the database"""
    conn = sqlite3.connect('jarvistrade.db')
    cursor = conn.cursor()
    
    try:
        # Add max_activations column to products table
        cursor.execute("""
            ALTER TABLE products 
            ADD COLUMN max_activations INTEGER DEFAULT 1
        """)
        print("✅ Added max_activations column to products table")
        
        # Create user_product_activations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_product_activations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                transaction_id TEXT NOT NULL,
                terminal_id TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        """)
        print("✅ Created user_product_activations table")
        
        # Create index for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_product_activations_user_product 
            ON user_product_activations (user_id, product_id)
        """)
        print("✅ Created index on user_product_activations")
        
        # Create index for terminal lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_product_activations_terminal 
            ON user_product_activations (terminal_id)
        """)
        print("✅ Created index on terminal_id")
        
        conn.commit()
        print("✅ Activation system migration completed successfully")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_activation_system() 