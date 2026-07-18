import sqlite3
conn = sqlite3.connect(r'C:\Apps\steam-price-tracker\app\data\steam_tracker.db')
cursor = conn.cursor()

cursor.execute('SELECT id, market_hash_name, item_type, gear_type, gear_level, is_equipped, quantity, removed_at FROM tracked_items WHERE removed_at IS NULL AND item_type = "GEAR" ORDER BY market_hash_name')
for row in cursor.fetchall():
    print(row)
conn.close()