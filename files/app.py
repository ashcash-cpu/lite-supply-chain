import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="Supply Chain Monitor", page_icon="📦", layout="centered")

st.title("📦 Supply Chain Monitor")
st.markdown("Track your inventory and get early warnings before stockouts occur.")
st.divider()

col1, col2 = st.columns(2)

with col1:
    product_name = st.text_input("Product Name", value="Product A")
    current_stock = st.number_input("Current Stock (units)", min_value=0, value=100, step=1)

with col2:
    avg_daily_usage = st.number_input("Average Daily Usage (units/day)", min_value=0.1, value=10.0, step=0.5, format="%.1f")

st.divider()

if avg_daily_usage > 0:
    days_of_cover = current_stock / avg_daily_usage
    stockout_date = date.today() + timedelta(days=days_of_cover)

    st.subheader(f"📊 Results for **{product_name}**")

    m1, m2, m3 = st.columns(3)
    m1.metric("Current Stock", f"{current_stock:,} units")
    m2.metric("Days of Cover", f"{days_of_cover:.1f} days")
    m3.metric("Estimated Stockout Date", stockout_date.strftime("%b %d, %Y"))

    st.divider()

    if days_of_cover < 7:
        st.error(
            f"🚨 **CRITICAL STOCK WARNING** — *{product_name}* will run out in "
            f"**{days_of_cover:.1f} days** (by **{stockout_date.strftime('%B %d, %Y')}**). "
            f"Immediate replenishment action required!",
            icon="🚨"
        )
    elif days_of_cover < 14:
        st.warning(
            f"⚠️ **Low Stock Alert** — *{product_name}* has only **{days_of_cover:.1f} days** "
            f"of cover remaining. Consider placing a replenishment order soon.",
            icon="⚠️"
        )
    else:
        st.success(
            f"✅ **Stock Levels Healthy** — *{product_name}* has **{days_of_cover:.1f} days** "
            f"of cover. No immediate action required.",
            icon="✅"
        )

    with st.expander("📈 View Inventory Depletion Forecast"):
        import pandas as pd

        forecast_days = min(int(days_of_cover) + 1, 60)
        forecast_data = pd.DataFrame({
            "Date": [date.today() + timedelta(days=i) for i in range(forecast_days)],
            "Projected Stock": [max(current_stock - avg_daily_usage * i, 0) for i in range(forecast_days)]
        }).set_index("Date")

        st.line_chart(forecast_data, color="#FF4B4B")
        st.caption("Projected stock levels assuming constant daily usage.")
