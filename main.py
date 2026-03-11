from fastapi import FastAPI
import sqlite3

app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect('supply_chain.db')
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn

def log_transaction(conn, product_id: int, change_amount: int):
    product_name = conn.execute(
        'SELECT name FROM products WHERE id = ?', (product_id,)
    ).fetchone()['name']
    conn.execute(
        'INSERT INTO transactions (product_name, change_amount) VALUES (?, ?)',
        (product_name, change_amount)
    )

@app.get("/inventory")
def read_inventory():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return [dict(item) for item in items]

@app.post("/update_stock/{product_id}")
def update_stock(product_id: int, adjustment: int):
    conn = get_db_connection()
    conn.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (adjustment, product_id))
    log_transaction(conn, product_id, adjustment)
    conn.commit()
    conn.close()
    return {"message": "Stock updated successfully"}

@app.post("/restock/{product_id}")
def restock(product_id: int, quantity: int):
    conn = get_db_connection()
    conn.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (quantity, product_id))
    log_transaction(conn, product_id, quantity)
    conn.commit()
    conn.close()
    return {"message": "Restock successful"}

@app.get("/transactions")
def get_transactions():
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT product_name, change_amount, timestamp FROM transactions ORDER BY id DESC LIMIT 50'
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
