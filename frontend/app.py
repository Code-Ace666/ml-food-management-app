import streamlit as st
import requests
import json
import logging
from pathlib import Path

# Configure page settings first
st.set_page_config(
    page_title="AI Smart Food Waste Manager",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL
API_URL = "http://127.0.0.1:8000"

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("frontend")

def inject_premium_css():
    """
    Injects high-end, startup-grade glassmorphic CSS styling to transform
    the default Streamlit dashboard appearance.
    """
    st.markdown("""
        <style>
        /* Import premium font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Modern Glassmorphic Cards */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        
        .glass-card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 255, 255, 0.25);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.25);
        }
        
        /* Premium Gradient Headers */
        .gradient-text {
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #FFD269 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        
        .gradient-blue {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }

        .gradient-green {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        
        /* Metric Badges */
        .metric-val {
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0;
            color: #ffffff;
        }
        
        .metric-label {
            font-size: 0.95rem;
            color: #a0aec0;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        
        /* Chatbot bubble styles */
        .user-bubble {
            background-color: #2D3748;
            color: #ffffff;
            padding: 12px 18px;
            border-radius: 18px 18px 0px 18px;
            margin-bottom: 12px;
            max-width: 80%;
            align-self: flex-end;
            margin-left: auto;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .bot-bubble {
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 142, 83, 0.1) 100%);
            color: #f7fafc;
            padding: 12px 18px;
            border-radius: 18px 18px 18px 0px;
            margin-bottom: 12px;
            max-width: 80%;
            border: 1px solid rgba(255, 142, 83, 0.2);
        }
        
        /* Sidebar styling override */
        section[data-testid="stSidebar"] {
            background-color: #111625;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Main container background override */
        .stApp {
            background-color: #0b0f19;
            color: #f7fafc;
        }
        
        /* Buttons custom hover */
        .stButton>button {
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 8px 20px;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #FF8E53 0%, #FFD269 100%);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
            transform: scale(1.02);
        }
        </style>
    """, unsafe_allow_html=True)

# Helper API functions
def api_get(endpoint: str, params: dict = None):
    """
    Performs a safe GET request to the FastAPI backend.
    """
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error {endpoint}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Network error on API GET {endpoint}: {e}")
        return None

def api_post(endpoint: str, data: dict = None, files: dict = None):
    """
    Performs a safe POST request to the FastAPI backend.
    """
    try:
        if files:
            response = requests.post(f"{API_URL}{endpoint}", files=files, timeout=30)
        else:
            response = requests.post(f"{API_URL}{endpoint}", json=data, timeout=10)
            
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error {endpoint}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Network error on API POST {endpoint}: {e}")
        return None

# Render Sidebar Info
def render_sidebar_status():
    """
    Displays a persistent connection and model health badge inside the sidebar.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔌 System Status")
    
    # Check connection to backend
    health = api_get("/")
    if health and health.get("status") == "online":
        st.sidebar.markdown(
            '<div style="display:flex; align-items:center; gap:8px;">'
            '<span style="height:10px; width:10px; background-color:#43e97b; border-radius:50%; display:inline-block; box-shadow:0 0 8px #43e97b;"></span>'
            '<span>FastAPI Backend Online</span>'
            '</div>', 
            unsafe_allow_html=True
        )
        
        # Check active model
        model_info = api_get("/api/admin/model-info")
        if model_info and model_info.get("trained"):
            st.sidebar.markdown(f"🤖 **Model**: `{model_info.get('best_model')}`")
            st.sidebar.markdown(f"📈 **Accuracy**: R² `{model_info.get('metrics', {}).get(model_info.get('best_model'), {}).get('r2', 0.85):.2f}`")
        else:
            st.sidebar.markdown("⚠️ Model Status: Not Trained")
    else:
        st.sidebar.markdown(
            '<div style="display:flex; align-items:center; gap:8px;">'
            '<span style="height:10px; width:10px; background-color:#FF6B6B; border-radius:50%; display:inline-block; box-shadow:0 0 8px #FF6B6B;"></span>'
            '<span>Backend Offline</span>'
            '</div>', 
            unsafe_allow_html=True
        )
        st.sidebar.info("Tip: Start the backend FastAPI server by running `python backend/main.py`!")

# If this file is run directly, show a welcome landing
if __name__ == "__main__":
    inject_premium_css()
    st.title("Welcome to Antigravity Smart Food Waste Management")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### Smart Food Waste Management System
        Welcome to the **Smart Food Waste Management System Dashboard**! This is a state-of-the-art AI-driven operations panel built with a FastAPI REST backend and a Streamlit analytics front-end.
        
        To view the system dashboards, select one of the pages in the sidebar menu:
        1. **🏡 Home**: Executive overview of cost savings, waste reductions, and daily recommendations.
        2. **📊 Analytics**: Dynamic time-series graphs, cost tracking, and food item audit charts.
        3. **🔮 Predictions**: Dynamic forecasting widget, weather-auto integration, and NGO donation dispatches.
        4. **🍲 Inventory**: AI-guided raw ingredient portion calculations and portions configurator.
        5. **⚙️ Admin**: CSV batch data upload, single-date manual entries, and ML pipeline training logs.
        6. **📋 Reports**: Downloadable weekly reports, custom metrics, and dynamic summary views.
        7. **💬 AI Analyst**: Friendly rule-driven chatbot to query statistics and request meal suggestions.
        """)
        
        st.image("https://images.unsplash.com/photo-1543083503-0c40dac3eba8?auto=format&fit=crop&q=80&w=1200", use_column_width=True, caption="Zero Waste Kitchen Analytics")
        
    with col2:
        st.subheader("🚀 Getting Started")
        st.info("Follow these quick steps to fully boot and explore the portfolio app:")
        st.markdown("""
        1. **Start Backend**:
           ```powershell
           python backend/main.py
           ```
        2. **Run Streamlit**:
           ```powershell
           streamlit run frontend/app.py
           ```
        3. **Set Workspace**:
           Set `C:\\Users\\asaks\\.gemini\\antigravity\\scratch\\smart_food_waste_management` as active workspace.
        """)
        render_sidebar_status()
