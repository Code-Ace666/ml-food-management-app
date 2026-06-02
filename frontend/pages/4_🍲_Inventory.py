import streamlit as st
import pandas as pd
from frontend.app import inject_premium_css, api_get, api_post, render_sidebar_status

inject_premium_css()

st.markdown('<h1 class="gradient-text" style="font-size:3rem; margin-bottom:10px;">🍲 Dynamic Inventory Estimations</h1>', unsafe_allow_html=True)
st.subheader("Guided raw material calculations & Portions Configurator.")

# Fetch active configurations
portions = api_get("/api/inventory/portions")

if portions is None:
    st.error("Failed to load portions configuration. Verify the FastAPI backend is running.")
    st.stop()
    
# Layout: Left column is the inventory estimator. Right column is the portions configurator.
col_est, col_cfg = st.columns([1, 1])

with col_est:
    st.markdown("### 🧮 Ingredient portions Estimator")
    st.markdown("Compute exact bulk raw material weight requirements based on meal counts.")
    
    # Retrieve suggested plate count from predictions if available
    pred_res = st.session_state.get("pred_results")
    suggested_plates = 350 # fallback default
    if pred_res:
        suggested_plates = pred_res.get("suggested_cooking_plates", 350)
        st.success(f"Loaded suggested plates from ML forecast: **{suggested_plates} plates**")
        
    plates = st.number_input("Target Meal Portion (Plates)", min_value=1, max_value=2000, value=suggested_plates, step=10)
    
    # Compute estimates
    est_results = api_post(f"/api/inventory/estimate?plates={plates}")
    
    if est_results:
        st.markdown(f"#### Bulk shopping list for {plates} plates:")
        
        estimates = est_results.get("estimates", {})
        
        # Display as metric grid
        for key, value in estimates.items():
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight:600; color:#4facfe;">{value.get('name')}</span>
                <span style="font-size:1.15rem; font-weight:700; color:#43e97b;">{value.get('display_amount')} {value.get('display_unit')}</span>
            </div>
            """, unsafe_allow_html=True)
            
        # Kitchen hint card
        st.markdown("""
        <div style="background-color:rgba(79, 172, 254, 0.05); border:1px dashed rgba(79, 172, 254, 0.3); border-radius:8px; padding:15px; margin-top:15px;">
            <p style="font-size:0.85rem; line-height:1.4; margin:0; color:#a0aec0;">
                💡 <b>Prep Station Hint</b>: Portions are calculated exactly from the portion configuration schemas on the right. 
                Keep raw inventory packed until kitchen scales align with optimal thresholds.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
with col_cfg:
    st.markdown("### ⚙️ Portion Sizes Manager")
    st.markdown("Modify standard canteen serving sizes or add new raw ingredients to the configuration schema database.")
    
    # Render portion config inputs
    updated_portions = {}
    
    st.markdown("#### Configure Serving Portions:")
    
    # Form for updating portions
    with st.form("portions_form"):
        # Loop through existing config
        for key, val in portions.items():
            col_name, col_size, col_unit = st.columns([2, 1, 1])
            with col_name:
                item_name = st.text_input("Name", value=val["name"], key=f"name_{key}")
            with col_size:
                item_size = st.number_input("Per Plate", value=float(val["portion_size"]), key=f"size_{key}")
            with col_unit:
                item_unit = st.text_input("Unit", value=val["unit"], key=f"unit_{key}")
                
            updated_portions[key] = {
                "name": item_name,
                "portion_size": item_size,
                "unit": item_unit
            }
            
        # Add dynamic ingredient addition widget
        st.markdown("---")
        st.markdown("#### ➕ Add New Canteen Ingredient")
        
        new_key = st.text_input("Unique Key (e.g. chicken, butter, spices)", value="")
        col_new_name, col_new_size, col_new_unit = st.columns([2, 1, 1])
        with col_new_name:
            new_name = st.text_input("Ingredient Display Name", value="")
        with col_new_size:
            new_size = st.number_input("Serving Size per Plate", min_value=0.0, value=0.0)
        with col_new_unit:
            new_unit = st.text_input("Serving Unit (g/ml)", value="g")
            
        # Form submit button
        submit_btn = st.form_submit_button("💾 Save Configurations")
        
        if submit_btn:
            # Process add new ingredient
            if new_key:
                clean_key = new_key.lower().strip().replace(" ", "_")
                if not new_name:
                    st.error("Please supply a display name for the new ingredient.")
                    st.stop()
                updated_portions[clean_key] = {
                    "name": new_name.strip(),
                    "portion_size": float(new_size),
                    "unit": new_unit.strip()
                }
                
            # Call API to update portions config
            res = api_post("/api/inventory/portions/update", data=updated_portions)
            if res and res.get("status") == "success":
                st.toast("Canteens portions updated successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Failed to update portion sizes configuration.")

# Persistent sidebar status
render_sidebar_status()
