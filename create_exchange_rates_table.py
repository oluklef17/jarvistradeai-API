import sqlite3
import os
from datetime import datetime

def create_exchange_rates_table():
    """Create the exchange_rates table and add default rates"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create exchange_rates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id TEXT PRIMARY KEY,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_currency, to_currency)
            )
        """)
        print("Created exchange_rates table")
        
        # Add default exchange rates
        default_rates = [
            ("USD", "NGN", 1500.0),  # 1 USD = 1500 NGN
            ("USD", "EUR", 0.85),    # 1 USD = 0.85 EUR
            ("USD", "GBP", 0.73),    # 1 USD = 0.73 GBP
        ]
        
        current_time = datetime.now().isoformat()
        
        for from_curr, to_curr, rate in default_rates:
            try:
                cursor.execute("""
                    INSERT INTO exchange_rates (id, from_currency, to_currency, rate, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"{from_curr}_{to_curr}", from_curr, to_curr, rate, True, current_time, current_time))
                print(f"Added exchange rate: {from_curr} to {to_curr} = {rate}")
            except sqlite3.IntegrityError:
                print(f"Exchange rate {from_curr} to {to_curr} already exists")
        
        # Commit the changes
        conn.commit()
        print("Successfully created exchange_rates table with default rates")
        
    except Exception as e:
        print(f"Error creating exchange_rates table: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_exchange_rates_table() 