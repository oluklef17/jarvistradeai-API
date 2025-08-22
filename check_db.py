import sqlite3

conn = sqlite3.connect('jarvistrade.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [table[0] for table in tables])

# Check transactions
cursor.execute("SELECT COUNT(*) FROM transactions")
total_transactions = cursor.fetchone()[0]
print(f"Total transactions: {total_transactions}")

# Check order_items
cursor.execute("SELECT COUNT(*) FROM order_items")
total_order_items = cursor.fetchone()[0]
print(f"Total order_items: {total_order_items}")

# Check downloads
cursor.execute("SELECT COUNT(*) FROM download_logs")
total_downloads = cursor.fetchone()[0]
print(f"Total downloads: {total_downloads}")

# Check for specific user
user_id = "ec808922-3016-44b4-ad4a-748f8fd52d41"
cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))
user_transactions = cursor.fetchone()[0]
print(f"User transactions: {user_transactions}")

cursor.execute("SELECT COUNT(*) FROM download_logs WHERE user_id = ?", (user_id,))
user_downloads = cursor.fetchone()[0]
print(f"User downloads: {user_downloads}")

# Check all transactions for this user
cursor.execute("""
    SELECT id, status, created_at, amount, paystack_reference
    FROM transactions
    WHERE user_id = ?
    LIMIT 5
""", (user_id,))
transactions = cursor.fetchall()
print(f"\nUser transactions:")
for t in transactions:
    print(f"  {t}")

# Check all order_items
cursor.execute("SELECT transaction_id, product_id, price, quantity FROM order_items LIMIT 5")
order_items = cursor.fetchall()
print(f"\nAll order_items:")
for oi in order_items:
    print(f"  {oi}")

# Check downloads with product info
cursor.execute("""
    SELECT dl.id, dl.product_id, dl.download_time, p.name
    FROM download_logs dl
    LEFT JOIN products p ON dl.product_id = p.id
    WHERE dl.user_id = ?
    LIMIT 5
""", (user_id,))
downloads = cursor.fetchall()
print(f"\nUser downloads with product names:")
for d in downloads:
    print(f"  {d}")

conn.close() 