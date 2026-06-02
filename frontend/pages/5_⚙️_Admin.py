import streamlit as st
import pandas as pd
from datetime import date
from frontend.app import inject_premium_css, api_get, api_post, render_sidebar_status

inject_premium_css()

st.markdown('<h1 class="gradient-text" style="font-size:3rem; margin-bottom:10px;">⚙️ Administrative Operations</h1>', unsafe_allow_html=True)
st.subheader("Manage ML pipelines, log consumption entries, and import CSV logs.")

model_info = api_get("/api/admin/model-info")

tab_ml, tab_log, tab_upload = st.tabs(["🤖 ML Engine & Retraining", "📝 Manual Canteen Log", "📤 Batch CSV Data Upload"])

with tab_ml:
    st.markdown("### 🤖 Predictive Engine Controls")
    st.markdown("The system automatically checks historical canteens logs on startup and selects the best regression model. You can manually re-trigger a pipeline training loop below.")
    
    # Render active model details
    if model_info and model_info.get("trained"):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Active ML Engine", model_info.get("best_model"))
        with col_m2:
            st.metric("Dataset Size", f"{model_info.get('dataset_samples')} daily logs")
        with col_m3:
            st.metric("Last Retrained", model_info.get("trained_date")[:16])
            
        # Model Comparison Table
        st.markdown("#### Model Performance Benchmarks:")
        metrics = model_info.get("metrics", {})
        
        metrics_rows = []
        for m_name, vals in metrics.items():
            metrics_rows.append({
                "Model Engine": m_name,
                "RMSE (Root Mean Square Error)": f"{vals.get('rmse'):.3f} plates",
                "MAE (Mean Absolute Error)": f"{vals.get('mae'):.3f} plates",
                "R² (Coefficient of Determination)": f"{vals.get('r2'):.4f}"
            })
        st.table(pd.DataFrame(metrics_rows))
    else:
        st.warning("⚠️ No machine learning models have been trained yet. Click the Retrain button below to initialize the pipeline.")
        
    # Retrain button
    if st.button("🔄 Trigger ML Pipeline Retraining", type="primary", use_container_width=True):
        with st.spinner("Executing time-series splits, Standard Scaling, and fitting Linear Regression, Random Forest, and XGBoost models..."):
            retrain_res = api_post("/api/admin/retrain")
            if retrain_res and retrain_res.get("status") == "success":
                st.toast("Model retrained successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Failed to retrain pipeline models. Verify database connection is open.")

with tab_log:
    st.markdown("### 📝 Manual Daily Audit Entry")
    st.markdown("Cafeteria operational managers can manually log actual daily preparation metrics here to update databases and features.")
    
    with st.form("manual_entry_form"):
        col_log1, col_log2 = st.columns(2)
        with col_log1:
            log_date = st.date_input("Audit Date", value=date.today())
            visitors = st.number_input("Total Visitors (Eaten + Turned Away)", min_value=0, value=300)
            cooked = st.number_input("Meals Prepared (Plates)", min_value=0, value=320)
            consumed = st.number_input("Actual Consumption (Plates eaten)", min_value=0, value=290)
            
        with col_log2:
            temp = st.slider("Temperature (°C)", min_value=-5.0, max_value=45.0, value=23.0)
            weather = st.selectbox("Weather", options=["Sunny", "Cloudy", "Rainy", "Snowy"])
            is_holiday = st.checkbox("Was it a holiday?")
            event = st.selectbox("Ongoing Campus Event", options=["None", "College Fest", "Sports Meet", "Corporate Conference", "Festive Celebrations"])
            
        # Form submit
        log_submit = st.form_submit_button("💾 Save Audit Entry")
        
        if log_submit:
            if consumed > cooked:
                st.error("Actual plates consumed cannot exceed prepared plate counts!")
                st.stop()
                
            # Compute waste: plates remaining * average waste weight coefficient (0.45kg) + noise buffer
            rem_plates = cooked - consumed
            waste_mass = round(rem_plates * 0.45 + 1.2, 2)
            
            payload = {
                "date": log_date.strftime("%Y-%m-%d"),
                "day_of_week": log_date.strftime("%A"),
                "temperature": float(temp),
                "weather": weather,
                "is_holiday": 1 if is_holiday else 0,
                "event": event,
                "visitors": int(visitors),
                "cooked_quantity": int(cooked),
                "actual_consumption": int(consumed),
                "waste_generated": float(waste_mass)
            }
            
            res = api_post("/api/admin/add-record", data=payload)
            if res and res.get("status") == "success":
                st.success(f"Successfully saved daily log for {log_date}!")
                st.toast("Database record ingestion success!", icon="✅")
            else:
                st.error("Failed to insert daily record.")

with tab_upload:
    st.markdown("### 📤 Batch Ingest Canteens Data CSV")
    st.markdown("Import a custom historical dataset CSV to batch update operations. This completely updates database tables and automatically triggers ML pipeline retraining.")
    
    # Template download help
    with st.expander("🛠️ View CSV Ingest Layout Structure Guide"):
        st.markdown("""
        Your CSV file must contain the following columns exactly (case sensitive):
        * `date` (YYYY-MM-DD)
        * `temperature` (Celsius floats)
        * `weather` (Sunny, Cloudy, Rainy, Snowy)
        * `is_holiday` (0 or 1)
        * `event` (None, College Fest, Sports Meet, Corporate Conference, Festive Celebrations)
        * `visitors` (integers)
        * `cooked_quantity` (integers)
        * `actual_consumption` (integers)
        * `waste_generated` (kilograms floats)
        """)
        
    uploaded_file = st.file_uploader("Select Canteens CSV logs file...", type=["csv"])
    
    if uploaded_file is not None:
        if st.button("📤 Ingest CSV & Train Models", use_container_width=True):
            with st.spinner("Processing file, rebuilding SQLite database tables, and executing ML model pipelines..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                res = api_post("/api/admin/upload-csv", files=files)
                
                if res and res.get("status") == "success":
                    st.success(res.get("message"))
                    st.toast("Batch ingestion complete!", icon="✅")
                    st.rerun()
                else:
                    st.error("CSV import failed. Please verify format guidelines.")

# Persistent sidebar status
render_sidebar_status()
