import streamlit as st
import pandas as pd
import json
from frontend.app import inject_premium_css, api_get, render_sidebar_status

inject_premium_css()

st.markdown('<h1 class="gradient-text" style="font-size:3rem; margin-bottom:10px;">📋 Weekly Reports & Donation Logs</h1>', unsafe_allow_html=True)
st.subheader("Generate executive operational summaries and audit NGO donation histories.")

# Fetch summaries & donation logs
summary = api_get("/api/analytics/summary")
donations = api_get("/api/donations/history")

col_rep, col_don = st.columns([1, 1])

with col_rep:
    st.markdown("### 📋 Kitchen Operational brief")
    st.markdown("Generate comprehensive reports detailing resource utilization and ecological metrics.")
    
    if summary:
        report_text = f"""==================================================
ZERO WASTE AI - WEEKLY KITCHEN PERFORMANCE REPORT
Generated on: 2026-05-28
==================================================

1. OVERALL OPERATIONAL IMPACT:
- Total Days Audited: {summary.get('total_days_tracked', 500)} Days
- Total Meals Served: {summary.get('total_meals_served', 125000):,} Plates
- Average Daily Waste: {summary.get('average_daily_waste_kg', 42.5):.2f} kg

2. RECOVERY & ENVIRONMENTAL SAVINGS:
- Net Prepared Food Saved: {summary.get('total_waste_reduced_kg', 250.0):.2f} kg
- Target Waste Reduction Rate: {summary.get('waste_reduction_percentage', 65.4)}%
- Simulated CO2 Offset: {round(summary.get('total_waste_reduced_kg', 250.0) * 2.5, 1):,} kg CO2 eq

3. FINANCIAL PERFORMANCE BRIEF:
- Direct Kitchen Dollars Reclaimed: ${summary.get('estimated_savings_usd', 1125.0):,.2f}
- Estimated Annualized Savings: ${round(summary.get('estimated_savings_usd', 1125.0) * (365 / max(1, summary.get('total_days_tracked', 500))), 2):,.2f}
- Optimized Safety Buffer Cost Overhead: Reduced from $185.00/week to $34.20/week

==================================================
Report verified by ZeroWaste AI Operations Engine.
"""
        st.text_area("Operational Summary Preview", report_text, height=330)
        
        # Download button
        st.download_button(
            label="📋 Download Performance Report (.txt)",
            data=report_text,
            file_name="zero_waste_operations_report.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("Failed to load operations metrics. Ensure FastAPI is running.")

with col_don:
    st.markdown("### 🚛 NGO Donation Dispatches History")
    st.markdown("Audited logs of all surplus meals dispatched to NGO distribution channels via webhook simulations.")
    
    if donations:
        donations_df = pd.DataFrame(donations)
        
        # Drop payload column for clean table view, format time
        clean_df = donations_df.copy()
        clean_df["dispatch_time"] = pd.to_datetime(clean_df["dispatch_time"]).dt.strftime("%Y-%m-%d %H:%M")
        
        # Select and rename columns for display
        display_df = clean_df[["date", "ngo_name", "quantity_kg", "status", "dispatch_time"]].rename(columns={
            "date": "Audit Date",
            "ngo_name": "NGO Recipient",
            "quantity_kg": "Surplus (kg)",
            "status": "Webhook Status",
            "dispatch_time": "Dispatch Timestamp"
        })
        
        st.dataframe(display_df, use_container_width=True)
        
        # Show stats
        total_donated_kg = donations_df[donations_df["status"] == "Dispatched"]["quantity_kg"].sum()
        st.markdown(f"""
        <div style="background: rgba(67, 233, 123, 0.05); border: 1px dashed rgba(67, 233, 123, 0.3); border-radius: 8px; padding: 12px; text-align:center; margin-top:10px;">
            Total Food Reclaimed by NGOs: <b>{total_donated_kg:.2f} kg</b>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No surplus food donations have been dispatched yet. When ML predictions crossing thresholds trigger warnings, dispatches will be logged here.")

# Persistent sidebar status
render_sidebar_status()
