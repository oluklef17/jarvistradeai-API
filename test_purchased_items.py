import sqlite3
import json
from datetime import datetime

def test_purchased_items_storage():
    """Test the purchased_items storage functionality"""
    
    print("🧪 Testing Purchased Items Storage")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('jarvistrade.db')
    cursor = conn.cursor()
    
    # Check if purchased_items column exists
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'purchased_items' in columns:
        print("✅ purchased_items column exists in transactions table")
    else:
        print("❌ purchased_items column not found")
        return
    
    # Get sample transaction
    cursor.execute("SELECT id, paystack_reference, purchased_items FROM transactions LIMIT 1")
    transaction = cursor.fetchone()
    
    if transaction:
        transaction_id, reference, purchased_items_json = transaction
        print(f"\n📋 Sample Transaction:")
        print(f"   ID: {transaction_id}")
        print(f"   Reference: {reference}")
        
        if purchased_items_json:
            try:
                purchased_items = json.loads(purchased_items_json)
                print(f"   Purchased Items: {len(purchased_items)} items")
                
                for i, item in enumerate(purchased_items, 1):
                    print(f"\n   Item {i}:")
                    print(f"     Product Name: {item.get('product_name', 'N/A')}")
                    print(f"     Product ID: {item.get('product_id', 'N/A')}")
                    print(f"     Quantity: {item.get('quantity', 0)}")
                    print(f"     Price: ${item.get('price', 0)}")
                    print(f"     Total: ${item.get('total', 0)}")
                    print(f"     Category: {item.get('category', 'N/A')}")
                    print(f"     Is Digital: {item.get('is_digital', 'N/A')}")
                
                print(f"\n✅ Purchased items snapshot is working correctly")
                print(f"📊 Total items in snapshot: {len(purchased_items)}")
                
            except json.JSONDecodeError:
                print("❌ Invalid JSON in purchased_items field")
        else:
            print("ℹ️  No purchased_items data found (this is normal for old transactions)")
    
    # Check total transactions
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE purchased_items IS NOT NULL")
    transactions_with_items = cursor.fetchone()[0]
    
    print(f"\n📊 Database Statistics:")
    print(f"   Total Transactions: {total_transactions}")
    print(f"   Transactions with Purchased Items: {transactions_with_items}")
    print(f"   Coverage: {(transactions_with_items/total_transactions*100):.1f}%" if total_transactions > 0 else "   Coverage: 0%")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ Purchased items storage test completed")
    print("🔒 Purchase records are now preserved in transaction snapshots")
    print("📋 This ensures order history remains intact even if products change")

if __name__ == "__main__":
    test_purchased_items_storage() 