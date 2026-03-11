import sqlite3

# This line creates the 'supply_chain.db' file automatically!
conn = sqlite3.connect('supply_chain.db')
cursor = conn.cursor()

# Create the tables
cursor.execute('''CREATE TABLE IF NOT EXISTS products
               (id INTEGER PRIMARY KEY, name TEXT, sku TEXT, stock INTEGER, price REAL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT,
                change_amount INTEGER,
                timestamp TEXT DEFAULT (datetime('now', 'localtime')))''')

# Add some starter inventory
cursor.execute("INSERT OR IGNORE INTO products VALUES (1, 'Cargo Drone', 'DRN-01', 15, 1200.0)")
cursor.execute("INSERT OR IGNORE INTO products VALUES (2, 'Battery Pack', 'BAT-99', 5, 150.0)")

conn.commit()
conn.close()
print("Success! Database initialized and 'supply_chain.db' created.")