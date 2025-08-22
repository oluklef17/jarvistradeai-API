import sqlite3
import os
from datetime import datetime

def fix_exchange_rates_datetime():
    """Fix datetime fields in existing exchange rate records"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Update existing records with proper datetime values
        current_time = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE exchange_rates 
            SET created_at = ?, updated_at = ?
            WHERE created_at IS NULL OR updated_at IS NULL
        """, (current_time, current_time))
        
        updated_count = cursor.rowcount
        print(f"Updated {updated_count} exchange rate records with proper datetime values")
        
        # Commit the changes
        conn.commit()
        print("Successfully fixed exchange rates datetime fields")
        
    except Exception as e:
        print(f"Error fixing exchange rates datetime: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_exchange_rates_datetime() 