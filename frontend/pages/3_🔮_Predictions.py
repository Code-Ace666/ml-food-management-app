import streamlit as st
import datetime
import json
from frontend.app import inject_premium_css, api_get, api_post, render_sidebar_status

inject_premium_css()

st.markdown('<h1 class="gradient-text" style="font-size:3rem; margin-bottom:10px;">🔮 ML Demand Predictor & NGO Dispatch</h1>', unsafe_allow_html=True)
st.subheader("Forecast future meal demand plates, generate smart margins, and dispatch surplus to NGOs.")

# Initialize session state for predictions and donation responses
if "pred_results" not in st.session_state:
    st.session_state.pred_results = None
if "dispatch_results" not in st.session_state:
    st.session_state.dispatch_results = None

# Left column: input settings. Right column: predictions output.
col_input, col_output = st.columns([1, 1.3])

with col_input:
    st.markdown("### 🎛️ Forecast Configurations")
    
    # 1. Date selector
    tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)
    target_date = st.date_input("Target Forecast Date", value=tomorrow_date)
    date_str = target_date.strftime("%Y-%m-%d")
    
    # 2. Weather Auto lookup
    col_weather_btn, col_blank = st.columns([1.5, 1])
    with col_weather_btn:
        if st.button("🌦️ Auto-Detect Weather", help="Fetch forecasted weather variables for this date"):
            with st.spinner("Fetching forecast..."):
                w_info = api_get(f"/api/predictions/weather-auto?target_date={date_str}")
                if w_info:
                    st.session_state.w_detected = w_info
                    st.toast("Weather parameters updated successfully!", icon="✅")
                else:
                    st.toast("Could not fetch weather forecast. Using simulation fallback.", icon="⚠️")
                    
    # Retrieve pre-filled session values or defaults
    w_detected = st.session_state.get("w_detected", {})
    default_weather = w_detected.get("weather", "Sunny")
    default_temp = w_detected.get("temperature", 22.0)
    w_source = w_detected.get("source", "Default Simulator")
    
    if "w_detected" in st.session_state:
        st.caption(f"Weather fetched from: *{w_source}*")
        
    # Weather Dropdown
    weather_list = ["Sunny", "Cloudy", "Rainy", "Snowy"]
    w_index = weather_list.index(default_weather) if default_weather in weather_list else 0
    weather = st.selectbox("Forecasted Weather Condition", options=weather_list, index=w_index)
    
    # Temperature Slider
    temp = st.slider("Forecasted High Temp (°C)", min_value=-5.0, max_value=45.0, value=float(default_temp), step=0.5)
    
    # Holiday Checkbox
    # (Check if it's weekend, auto-suggest holiday)
    is_weekend = 1 if target_date.weekday() >= 5 else 0
    is_holiday = st.checkbox("Mark as National/Campus Holiday", value=False)
    is_holiday_int = 1 if is_holiday else 0
    
    # Event Selector
    events_list = ["None", "College Fest", "Sports Meet", "Corporate Conference", "Festive Celebrations"]
    event = st.selectbox("Ongoing Campus/Canteen Event", options=events_list, index=0)
    
    # Submit prediction
    st.markdown("---")
    if st.button("🔮 Run Demand Forecast", use_container_width=True):
        with st.spinner("Running ML inference models..."):
            payload = {
                "date": date_str,
                "temperature": temp,
                "weather": weather,
                "is_holiday": is_holiday_int,
                "event": event
            }
            results = api_post("/api/predictions/predict", data=payload)
            if results:
                st.session_state.pred_results = results
                st.session_state.dispatch_results = None # reset dispatch on new forecast
                st.success("ML Pipeline executed successfully!")
            else:
                st.error("Failed to run prediction. Verify the FastAPI backend is running and that your ML model is pre-trained in the Admin panel.")

with col_output:
    st.markdown("### 📊 AI Forecasting Results")
    
    pred_res = st.session_state.pred_results
    
    if pred_res is None:
        st.info("Configure variables on the left panel and click 'Run Demand Forecast' to view AI model outputs.")
    else:
        # Display main results
        plates = pred_res.get("predicted_consumption_plates")
        cooked = pred_res.get("suggested_cooking_plates")
        waste = pred_res.get("estimated_waste_kg")
        engine = pred_res.get("model_used")
        
        # 1. Output KPI cards
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.markdown(f"""
                <div class="glass-card" style="padding:15px; text-align:center;">
                    <p class="metric-label" style="font-size:0.8rem;">🎯 Predicted Plates</p>
                    <p class="metric-val" style="color: #4facfe; font-size:1.8rem;">{plates}</p>
                    <p style="font-size:0.75rem; color:#a0aec0; margin:0;">Target Consumption</p>
                </div>
            """, unsafe_allow_html=True)
        with col_res2:
            st.markdown(f"""
                <div class="glass-card" style="padding:15px; text-align:center;">
                    <p class="metric-label" style="font-size:0.8rem;">🥘 Cooking Guide</p>
                    <p class="metric-val" style="color: #43e97b; font-size:1.8rem;">{cooked}</p>
                    <p style="font-size:0.75rem; color:#a0aec0; margin:0;">With +8% Safety Margin</p>
                </div>
            """, unsafe_allow_html=True)
        with col_res3:
            st.markdown(f"""
                <div class="glass-card" style="padding:15px; text-align:center;">
                    <p class="metric-label" style="font-size:0.8rem;">🗑️ Est. Scrap Waste</p>
                    <p class="metric-val" style="color: #FF6B6B; font-size:1.8rem;">{waste:.2f} kg</p>
                    <p style="font-size:0.75rem; color:#a0aec0; margin:0;">Minimized leftover volume</p>
                </div>
            """, unsafe_allow_html=True)
            
        # 2. Recommendation Engine block
        st.markdown("#### 💡 AI Suggested Kitchen Instructions")
        
        rec_texts = []
        if is_holiday:
            rec_texts.append("Holiday attendance drop. Limit prepared food stations to a single counter.")
        if weather in ["Rainy", "Snowy"]:
            rec_texts.append(f"Expected attendance drop due to wet conditions. Slice vegetable prep by 15%.")
        if event != "None":
            rec_texts.append(f"Demand surge expected due to {event}. Ensure buffer is loaded.")
        else:
            rec_texts.append("No active weather shocks or holidays. Prepare normal base portions.")
            
        rec_texts.append(f"Model Engine Used: `{engine}`.")
        
        bullets = "".join([f"<li>{r}</li>" for r in rec_texts])
        st.markdown(f"""
        <div style="background-color:#111625; padding:15px; border-radius:8px; border:1px solid rgba(255,255,255,0.05); margin-bottom:20px;">
            <ul style="margin:0; padding-left:20px; font-size:0.9rem; line-height:1.5;">
                {bullets}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. NGO Donation Alerts Integration
        st.markdown("#### 🚛 NGO Donation Management")
        
        # Call Backend to get donation alert status
        alert_res = api_get(f"/api/donations/alert?date={date_str}&predicted_waste_kg={waste}")
        
        if alert_res:
            is_triggered = alert_res.get("is_triggered", False)
            
            if not is_triggered:
                st.success("🌱 Estimated waste levels are low. No NGO donation dispatch is necessary for this date.")
            else:
                st.markdown(f"""
                <div style="background-color:rgba(255, 107, 107, 0.1); border:1px solid rgba(255, 107, 107, 0.3); border-radius:8px; padding:15px; margin-bottom:15px;">
                    <p style="font-weight:700; color:#FF6B6B; margin:0 0 5px 0;">🚨 Food Surplus Warning (Threshold Crossed)</p>
                    <p style="font-size:0.85rem; margin:0; line-height:1.4;">
                        Predicted waste ({waste:.2f} kg) exceeds the system threshold of 15.0 kg.
                        Pre-dispatch webhook triggers are active. Select an NGO partner to request collection dispatch.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Dispatch Select Form
                ngos = alert_res.get("suggested_ngos", ["Robin Hood Army", "Food Share Rescue", "Zero Waste Center"])
                selected_ngo = st.selectbox("Select Partner NGO", options=ngos)
                
                # Dispatch button
                if st.session_state.dispatch_results is None:
                    if st.button("🚛 Dispatch Collection Webhook", type="primary", use_container_width=True):
                        with st.spinner("Executing simulated webhook dispatch..."):
                            dispatch_payload = {
                                "date": date_str,
                                "quantity_kg": float(waste),
                                "ngo_name": selected_ngo
                            }
                            dispatch_res = api_post("/api/donations/dispatch", data=dispatch_payload)
                            if dispatch_res:
                                st.session_state.dispatch_results = dispatch_res
                                st.rerun()
                            else:
                                st.error("Webhook dispatch failed. Please retry.")
                else:
                    # Render dispatch success card
                    d_res = st.session_state.dispatch_results
                    p_load = json.loads(d_res.get("response_payload", "{}"))
                    
                    st.markdown(f"""
                    <div style="background-color:rgba(67, 233, 123, 0.1); border:1px solid rgba(67, 233, 123, 0.4); border-radius:8px; padding:20px; margin-top:10px;">
                        <h5 style="color:#43e97b; margin:0 0 8px 0;">🚀 Webhook Ingest Completed!</h5>
                        <p style="font-size:0.9rem; margin:0 0 10px 0; line-height:1.4;">
                            Donation dispatched successfully to <b>{d_res.get('ngo_name')}</b>.
                            The mock NGO webhook simulator accepted the payload.
                        </p>
                        <ul style="font-size:0.85rem; padding-left:20px; margin:0; line-height:1.4;">
                            <li><b>Assigned Driver</b>: {p_load.get('assigned_driver', 'Marcus Vance')}</li>
                            <li><b>Driver ETA</b>: {p_load.get('eta_minutes', 30)} minutes</li>
                            <li><b>Pickup Verification Token</b>: <code style="color:#38f9d7;">{p_load.get('security_verification_code', 'N/A')}</code></li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show payload details in expander
                    with st.expander("🛠️ View raw Webhook REST Ingest Payload"):
                        st.code(json.dumps(p_load, indent=2), language="json")

# Persistent sidebar status
render_sidebar_status()
