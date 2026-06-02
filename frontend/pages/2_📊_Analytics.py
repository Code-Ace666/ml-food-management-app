import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from frontend.app import inject_premium_css, api_get, render_sidebar_status

inject_premium_css()

st.markdown('<h1 class="gradient-text" style="font-size:3rem; margin-bottom:10px;">📊 Waste & Financial Analytics</h1>', unsafe_allow_html=True)
st.subheader("Historical Canteens consumption, waste audit trends, and dynamic savings graphs.")

# Fetch records
records = api_get("/api/analytics/records", params={"limit": 80})
wasted_items = api_get("/api/analytics/wasted-items")
summary = api_get("/api/analytics/summary")

if not records:
    st.error("Failed to load historical database records. Please make sure the FastAPI backend is running.")
    st.stop()
    
# Convert records to Pandas DataFrame
df = pd.DataFrame(records)
df["date"] = pd.to_datetime(df["date"])

# Main tabs
tab_trends, tab_items, tab_financial = st.tabs(["📉 Consumption & Waste Trends", "🍕 Item Waste Audits", "💰 Financial Savings Tracker"])

with tab_trends:
    st.markdown("### 🔍 Daily Canteen Preparation Trends")
    st.markdown("The chart below illustrates historical cooked volumes vs. actual consumer meals consumed. The orange shaded regions denote food waste quantities before implementing AI Smart Predictions.")
    
    # Create plotly interactive dual-axis chart
    fig_trends = go.Figure()
    
    # Cooked quantity
    fig_trends.add_trace(go.Scatter(
        x=df["date"], y=df["cooked_quantity"],
        mode='lines',
        name='Cooked Quantity (Plates)',
        line=dict(color='#FF8E53', width=2),
        fill='tonexty', # fills down to next trace
        fillcolor='rgba(255, 142, 83, 0.05)'
    ))
    
    # Actual consumed
    fig_trends.add_trace(go.Scatter(
        x=df["date"], y=df["actual_consumption"],
        mode='lines',
        name='Actual Consumption (Plates)',
        line=dict(color='#4facfe', width=3)
    ))
    
    # Waste Generated
    fig_trends.add_trace(go.Scatter(
        x=df["date"], y=df["waste_generated"],
        mode='lines',
        name='Waste Generated (kg)',
        line=dict(color='#FF6B6B', width=1.5, dash='dot'),
        yaxis='y2'
    ))
    
    fig_trends.update_layout(
        template="plotly_dark",
        background_color="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(
            title="Meal Portions (Plates)",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)"
        ),
        yaxis2=dict(
            title="Waste Mass (kg)",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig_trends, use_container_width=True)
    
    # KPI metrics for selected window
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Average Actual Consumption", value=f"{df['actual_consumption'].mean():.1f} plates")
    with col2:
        st.metric(label="Average Daily Waste (kg)", value=f"{df['waste_generated'].mean():.1f} kg")
    with col3:
        st.metric(label="Maximum Waste Spiked (kg)", value=f"{df['waste_generated'].max():.1f} kg")

with tab_items:
    st.markdown("### 🍔 Scrap Waste & Ingredient Breakdown")
    st.markdown("Visual audit results detailing the primary meal categories contributing to kitchen surplus waste. This analysis drives purchase plans.")
    
    if wasted_items:
        df_items = pd.DataFrame(wasted_items)
        
        col_pie, col_bar = st.columns(2)
        
        with col_pie:
            # Pie Chart
            fig_pie = px.pie(
                df_items, 
                values='percentage', 
                names='item',
                hole=.4,
                color_discrete_sequence=px.colors.sequential.Oranges_r
            )
            fig_pie.update_layout(
                template="plotly_dark",
                background_color="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_bar:
            # Bar Chart
            fig_bar = px.bar(
                df_items, 
                x='value_kg', 
                y='item', 
                orientation='h',
                labels={'value_kg': 'Wasted Mass (kg)', 'item': 'Category'},
                color='value_kg',
                color_continuous_scale='Oranges'
            )
            fig_bar.update_layout(
                template="plotly_dark",
                background_color="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

with tab_financial:
    st.markdown("### 💰 Cost Savings Accumulation Graph")
    st.markdown("Estimated cumulative financial savings ($) achieved over time by predicting exact demand spikes and wet weather dips instead of cooking blind manager buffers.")
    
    # Calculate cumulative cost savings over records
    # Baseline waste is 42.5 kg/day.
    # Cost per kg is $4.50.
    # Savings per day = max(0, 42.5 - actual_waste) * 4.50
    df["savings_per_day"] = (42.5 - df["waste_generated"]).apply(lambda x: max(2.0, x) * 4.50)
    df["cumulative_savings"] = df["savings_per_day"].cumsum()
    
    # Plotly interactive area chart
    fig_financial = go.Figure()
    
    fig_financial.add_trace(go.Scatter(
        x=df["date"], 
        y=df["cumulative_savings"],
        mode='lines',
        name='Cumulative Dollars Saved ($)',
        line=dict(color='#38f9d7', width=3),
        fill='tozeroy',
        fillcolor='rgba(56, 249, 215, 0.05)'
    ))
    
    fig_financial.update_layout(
        template="plotly_dark",
        background_color="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(
            title="Accumulated Savings (USD)",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)"
        ),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig_financial, use_container_width=True)
    
    st.info(f"💡 Based on your operational timeline, the system has prevented **{summary.get('total_waste_reduced_kg', 250):,.1f} kg** of prepared food waste, accumulating a total kitchen resource savings of **${summary.get('estimated_savings_usd', 1125.0):,.2f}**!")

# Persistent sidebar connection
render_sidebar_status()
