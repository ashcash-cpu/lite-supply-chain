import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ── Database setup ─────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "supply_chain.db"
SAFETY_STOCK = 5
DOC_WINDOW_DAYS = 30


def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS products
                   (id INTEGER PRIMARY KEY, name TEXT, sku TEXT, stock INTEGER, price REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT,
                    change_amount INTEGER,
                    timestamp TEXT DEFAULT (datetime('now', 'localtime')))''')
    conn.execute("INSERT OR IGNORE INTO products VALUES (1, 'Cargo Drone', 'DRN-01', 15, 1200.0)")
    conn.execute("INSERT OR IGNORE INTO products VALUES (2, 'Battery Pack', 'BAT-99', 5, 150.0)")
    conn.commit()
    conn.close()


def read_inventory():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transactions():
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT product_name, change_amount, timestamp FROM transactions ORDER BY id DESC LIMIT 50'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_transaction(conn, product_id: int, change_amount: int):
    product_name = conn.execute(
        'SELECT name FROM products WHERE id = ?', (product_id,)
    ).fetchone()['name']
    conn.execute(
        'INSERT INTO transactions (product_name, change_amount) VALUES (?, ?)',
        (product_name, change_amount)
    )


def update_stock(product_id: int, adjustment: int):
    conn = get_db_connection()
    conn.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (adjustment, product_id))
    log_transaction(conn, product_id, adjustment)
    conn.commit()
    conn.close()


def restock(product_id: int, quantity: int):
    conn = get_db_connection()
    conn.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (quantity, product_id))
    log_transaction(conn, product_id, quantity)
    conn.commit()
    conn.close()


# ── App ────────────────────────────────────────────────────────────────────────
init_db()

st.set_page_config(page_title="Lite Inventory Dashboard", layout="wide")


def check_password():
    st.markdown(
        """
        <style>
        .login-container { max-width: 400px; margin: 10vh auto; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.title("🔒 Inventory Dashboard")
        st.markdown("Please enter your password to continue.")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        if st.button("Login", use_container_width=True, type="primary"):
            if password == st.secrets["password"]:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


if not st.session_state.get("authenticated"):
    check_password()

st.title("📦 Lite Inventory Dashboard")

# ── Shared data (fetched once, used across both tabs) ─────────────────────────
inventory     = read_inventory()
transactions  = get_transactions()
product_names = [p["name"] for p in inventory]

total_value     = sum(p["stock"] * p["price"] for p in inventory)
low_stock_count = sum(1 for p in inventory if p["stock"] < SAFETY_STOCK)

sales_by_product = {}
for tx in transactions:
    if tx["change_amount"] < 0:
        name = tx["product_name"]
        sales_by_product[name] = sales_by_product.get(name, 0) + abs(tx["change_amount"])

# ── KPI Header (always visible) ───────────────────────────────────────────────
kpi_col1, kpi_col2 = st.columns(2)
kpi_col1.metric("💰 Total Inventory Value", f"${total_value:,.2f}")
kpi_col2.metric("⚠️ Low Stock Items", low_stock_count)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_dashboard, tab_analytics = st.tabs(["📋 Dashboard", "📊 Analytics"])

# ════════════════════════════════════════════════════════════════════════════════
with tab_dashboard:

    # ── Inventory Table ───────────────────────────────────────────────────────
    st.subheader("Current Stock Status")

    def days_of_cover(product_name, stock):
        avg_daily = sales_by_product.get(product_name, 0) / DOC_WINDOW_DAYS
        return "∞" if avg_daily == 0 else round(stock / avg_daily, 1)

    df = pd.DataFrame(inventory)
    df["days_of_cover"] = df.apply(lambda r: days_of_cover(r["name"], r["stock"]), axis=1)

    def highlight_low_stock(row):
        if row["stock"] < SAFETY_STOCK:
            return ["background-color: #ffcccc; color: #7b1c1c"] * len(row)
        return [""] * len(row)

    st.dataframe(df.style.apply(highlight_low_stock, axis=1), use_container_width=True)

    st.divider()

    # ── Transactions: Log a Sale | Restock ───────────────────────────────────
    col_sale, col_restock = st.columns(2)

    with col_sale:
        st.subheader("🛒 Log a Sale")
        sale_product = st.selectbox("Product", product_names, key="sale_product")
        sale_qty = st.number_input("Quantity Sold", min_value=1, value=1, key="sale_qty")
        if st.button("Record Sale", use_container_width=True):
            p_id = next(p["id"] for p in inventory if p["name"] == sale_product)
            update_stock(p_id, -sale_qty)
            st.success(f"Sale recorded: -{sale_qty} {sale_product}")
            st.rerun()

    with col_restock:
        st.subheader("📥 Restock")
        restock_product = st.selectbox("Product", product_names, key="restock_product")
        restock_qty = st.number_input("Quantity to Add", min_value=1, value=1, key="restock_qty")
        if st.button("Restock", use_container_width=True):
            p_id = next(p["id"] for p in inventory if p["name"] == restock_product)
            restock(p_id, restock_qty)
            st.success(f"Restocked: +{restock_qty} {restock_product}")
            st.rerun()

    st.divider()

    # ── Recent Activity ───────────────────────────────────────────────────────
    st.subheader("🕒 Recent Activity")

    if transactions:
        tx_df = pd.DataFrame(transactions)
        tx_df.columns = ["Product", "Change", "Timestamp"]

        def style_change(val):
            return "color: #c0392b" if val < 0 else "color: #27ae60"

        st.dataframe(
            tx_df.style.applymap(style_change, subset=["Change"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No transactions recorded yet.")

# ════════════════════════════════════════════════════════════════════════════════
with tab_analytics:
    st.subheader("📊 Analytics")

    chart_col1, chart_col2 = st.columns(2)

    # ── Pie: Inventory Value by Product ──────────────────────────────────────
    with chart_col1:
        st.markdown("**Inventory Value by Product**")
        value_df = pd.DataFrame({
            "Product": [p["name"] for p in inventory],
            "Value":   [p["stock"] * p["price"] for p in inventory],
        })
        fig_pie = px.pie(
            value_df,
            names="Product",
            values="Value",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_pie.update_traces(textinfo="label+percent", hovertemplate="%{label}: $%{value:,.2f}")
        fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Bar: Units Sold by Product ────────────────────────────────────────────
    with chart_col2:
        PERIOD_OPTIONS = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All time": None}
        period_label = st.selectbox("Time period", list(PERIOD_OPTIONS.keys()), index=1, key="sales_period")
        days = PERIOD_OPTIONS[period_label]

        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days) if days else pd.Timestamp.min

        filtered_sales = {}
        for tx in transactions:
            if tx["change_amount"] < 0 and pd.Timestamp(tx["timestamp"]) >= cutoff:
                name = tx["product_name"]
                filtered_sales[name] = filtered_sales.get(name, 0) + abs(tx["change_amount"])

        st.markdown(f"**Total Units Sold — {period_label}**")
        if filtered_sales:
            sales_df = pd.DataFrame(
                filtered_sales.items(), columns=["Product", "Units Sold"]
            ).sort_values("Units Sold", ascending=False)
            fig_bar = px.bar(
                sales_df,
                x="Product",
                y="Units Sold",
                color="Product",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                text="Units Sold",
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(
                showlegend=False,
                xaxis_title=None,
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info(f"No sales recorded in the {period_label.lower()}.")
