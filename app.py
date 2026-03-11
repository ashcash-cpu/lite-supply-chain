import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Supply Chain Shortage Predictor", layout="centered")

st.title("📦 SKU Shortage Predictor")
st.write("Calculate your 'Days of Cover' and see when you'll hit a stockout.")

# User Inputs
col1, col2 = st.columns(2)
with col1:
    current_stock = st.number_input("Current Inventory (Units)", min_value=0, value=500)
    lead_time = st.number_input("Supplier Lead Time (Days)", min_value=1, value=14)

with col2:
    daily_demand = st.number_input("Average Daily Demand (Units)", min_value=0.1, value=25.0)
    safety_stock = st.number_input("Safety Stock Level", min_value=0, value=100)

# Calculations
days_of_cover = current_stock / daily_demand
stockout_date = datetime.now() + timedelta(days=days_of_cover)

st.divider()

# Dashboard Results
st.subheader(f"Results for SKU")
st.metric("Days of Cover", f"{days_of_cover:.1f} Days")

if days_of_cover < lead_time:
    st.error(f"⚠️ RISK: Stockout expected on {stockout_date.strftime('%Y-%m-%d')}")
    st.write(f"You will run out **BEFORE** a new order can arrive (Lead time is {lead_time} days).")
elif days_of_cover < (lead_time + 7):
    st.warning(f"🕒 CAUTION: Stockout expected on {stockout_date.strftime('%Y-%m-%d')}")
else:
    st.success(f"✅ Healthy: Stockout not expected until {stockout_date.strftime('%Y-%m-%d')}")

# Agent Action (Simulation)
if st.button("Draft Expedite Email"):
    st.info("Drafting email via Claude...")
    email_body = f"""
    Subject: URGENT: Expedite Request for SKU
    
    Hi Supplier Team,
    
    Our records show a projected stockout on {stockout_date.strftime('%Y-%m-%d')}. 
    Based on our lead time of {lead_time} days, we need to expedite our current PO.
    
    Please advise on the earliest possible ship date.
    """
    st.text_area("Email Draft:", value=email_body, height=200)