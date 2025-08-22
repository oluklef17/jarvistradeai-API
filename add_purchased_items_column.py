import sqlite3
import os

def add_purchased_items_column():
    """Add purchased_items column to transactions table"""
    conn = sqlite3.connect('jarvistrade.db')
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'purchased_items' not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN purchased_items TEXT")
        print("✅ Added purchased_items column to transactions table")
    else:
        print("ℹ️  purchased_items column already exists")
    
    conn.commit()
    conn.close()
    print("✅ Database schema updated successfully")

def populate_existing_transactions():
    """Populate purchased_items for existing transactions based on order_items"""
    conn = sqlite3.connect('jarvistrade.db')
    cursor = conn.cursor()
    
    # Get all transactions
    cursor.execute("SELECT id FROM transactions")
    transactions = cursor.fetchall()
    
    populated_count = 0
    
    for (transaction_id,) in transactions:
        # Get order items for this transaction
        cursor.execute("""
            SELECT oi.product_id, oi.quantity, oi.price, p.name, p.category, p.image
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.transaction_id = ?
        """, (transaction_id,))
        
        items = cursor.fetchall()
        
        if items:
            # Format items as JSON
            purchased_items = []
            for item in items:
                product_id, quantity, price, name, category, image = item
                purchased_items.append({
                    "product_id": product_id,
                    "product_name": name or "Unknown Product",
                    "quantity": quantity,
                    "price": price,
                    "total": quantity * price,
                    "category": category,
                    "image": image
                })
            
            # Update transaction with purchased_items
            import json
            cursor.execute(
                "UPDATE transactions SET purchased_items = ? WHERE id = ?",
                (json.dumps(purchased_items), transaction_id)
            )
            populated_count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Populated purchased_items for {populated_count} existing transactions")

if __name__ == "__main__":
    print("🔄 Adding purchased_items column to transactions table...")
    add_purchased_items_column()
    
    print("\n🔄 Populating existing transactions with purchased items data...")
    populate_existing_transactions()
    
    print("\n✅ Migration completed successfully!")
    print("📋 The purchased_items field now stores a complete snapshot of what was purchased")
    print("🔒 This ensures purchase records are preserved even if products are modified/deleted") 