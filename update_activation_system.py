import sqlite3
import json
import uuid
from datetime import datetime

def generate_license_id():
    """Generate a user-friendly license ID"""
    return f"LIC-{uuid.uuid4().hex[:8].upper()}"

def update_activation_system():
    """Update activation system to use licenses and account logins"""
    conn = sqlite3.connect('jarvistrade.db')
    cursor = conn.cursor()
    
    try:
        # Create licenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id TEXT PRIMARY KEY,
                license_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                transaction_id TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        """)
        print("✅ Created licenses table")
        
        # Update user_product_activations table
        cursor.execute("""
            DROP TABLE IF EXISTS user_product_activations
        """)
        
        cursor.execute("""
            CREATE TABLE user_product_activations (
                id TEXT PRIMARY KEY,
                license_id TEXT NOT NULL,
                account_login TEXT NOT NULL,
                account_server TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (license_id) REFERENCES licenses (id)
            )
        """)
        print("✅ Updated user_product_activations table")
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_licenses_user_product 
            ON licenses (user_id, product_id)
        """)
        print("✅ Created index on licenses")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_licenses_license_id 
            ON licenses (license_id)
        """)
        print("✅ Created index on license_id")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activations_license 
            ON user_product_activations (license_id)
        """)
        print("✅ Created index on activations license_id")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activations_account 
            ON user_product_activations (account_login, account_server)
        """)
        print("✅ Created index on account login/server")
        
        # Create licenses for existing successful transactions
        cursor.execute("""
            SELECT DISTINCT t.id, t.user_id, oi.product_id, t.paystack_reference
            FROM transactions t
            JOIN order_items oi ON t.id = oi.transaction_id
            WHERE t.status = 'success'
        """)
        
        existing_transactions = cursor.fetchall()
        licenses_created = 0
        
        for transaction_id, user_id, product_id, paystack_ref in existing_transactions:
            license_id = generate_license_id()
            
            cursor.execute("""
                INSERT INTO licenses (id, license_id, user_id, product_id, transaction_id, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (str(uuid.uuid4()), license_id, user_id, product_id, transaction_id))
            
            licenses_created += 1
        
        print(f"✅ Created {licenses_created} licenses for existing transactions")
        
        conn.commit()
        print("✅ Activation system migration completed successfully")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_activation_system() 