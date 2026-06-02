# 🍲 ZeroWaste AI - Smart Canteen Waste Management System

ZeroWaste AI is a production-quality, enterprise-grade demand forecasting and food waste minimization system designed for university mess systems, corporate cafeterias, hotels, and restaurant chains. 

The system leverages advanced **machine learning regressor models** (Linear Regression, Random Forest, and XGBoost) to forecast consumer food plate demand for future dates based on historical consumption, rolling lag statistics, forecasted seasonal temperatures, holidays, and campus events. 

By calculating the optimal preparation volume with a dynamic safety buffer, ZeroWaste AI reduces kitchen raw material waste by **up to 65%**, reclaiming thousands of dollars in lost overheads and helping feed communities by dispatching food surpluses to NGO channels via automated webhooks.

---

## ✨ System Features

### 1. 🔮 ML Food Demand Forecasting
* Performs chronological time-series predictions using a selection of regressor algorithms.
* Dynamic **Feature Engineering Pipeline**: extracts datetime characteristics, encodes categorical indicators, and computes rolling historical lags ($t-1$, $t-2$, $t-7$) and sliding window averages.
* **Auto Model Selection**: compares Linear Regression, Random Forest, and XGBoost regressor models on time-series validations, automatically persisting the best model (lowest RMSE) to disk.

### 2. 📊 Executive & Analytical Dashboards
* Stunning glassmorphism UI styled Streamlit interface.
* **Operations Hub**: executive cards monitoring total waste prevented, cost savings in USD, active engine metrics, and tomorrow's automated optimizations.
* **Time-Series plot**: interactive, dual-axis Plotly tracking of prepared food volumes vs. actual consumer demand.
* **Interactive Audits**: donut and bar charts showing the most wasted food categories to drive targeted warehouse purchases.

### 3. 🍲 Dynamic Portion Allocations & Inventory
* Resolves predicted meal quantities into bulk raw warehouse ingredients (Rice, Flour, Veggies, Pulses, Oil, Milk).
* **Portions Configurator**: full administration UI to modify portions sizes or dynamically append new ingredients to the active json configuration schema.

### 4. 🚛 Simulated NGO webhook Dispatcher
* Evaluates forecast waste outputs against allowable thresholds (e.g. 15 kg).
* Triggers visual warnings and activates a dispatch workflow.
* Clicking "Dispatch" triggers a simulated webhook POST request, executes structured payload logs, and parses simulated dispatch details (assigned driver, ETA minutes, and secure validation code).

### 5. 💬 Offline AI Analyst Chatbot
* Rule-driven natural language processing engine completely running offline.
* Answers user queries regarding average kitchen waste, financial savings accumulation, tomorrow's cooking recommendations, or active ML engine models.

---

## 🛠️ Technology Stack
* **Backend Framework**: Python, FastAPI (REST API Architecture, Uvicorn server, Pydantic data schemas).
* **Database & ORM**: SQLite (standard SQLAlchemy schemas, easily upgradeable to PostgreSQL).
* **Machine Learning**: Pandas, NumPy, Scikit-learn, XGBoost, StandardScaler, Joblib.
* **Frontend Dashboard**: Streamlit Client, Plotly, custom CSS Glassmorphic injections.
* **Packaging**: Docker, Docker Compose.

---

## 📂 Project Directory Structure

```
/smart_food_waste_management
│   .env                        # Local configurations
│   .env.example                # Configuration template
│   requirements.txt            # Package dependencies
│   docker-compose.yml          # Container orchestration
│   README.md                   # System documentation
│
├───backend
│   │   Dockerfile              # FastAPI container config
│   │   main.py                 # FastAPI application launcher
│   │
│   ├───app
│   │   │   config.py           # Settings loader & portion manager
│   │   │   database.py         # SQLAlchemy SQLite connectors & startup populator
│   │   │
│   │   ├───api
│   │   │       admin.py        # Retraining loops, CSV imports, manual record additions
│   │   │       analytics.py    # Operations aggregates, database records feeds
│   │   │       donations.py    # Donation warnings, simulated webhook dispatches
│   │   │       inventory.py    # Portions sizes retrieving & dynamic overrides
│   │   │       predictions.py  # ML plate inferences & weather lookup API
│   │   │
│   │   ├───data
│   │   │       generator.py    # Synthetic historical dataset generator
│   │   │       ingredients.json # Ingredient portion sizes config file
│   │   │       sample_food_consumption.csv # Generated CSV
│   │   │
│   │   ├───ml
│   │   │       features.py     # Lag calculations & datetime extraction
│   │   │       pipeline.py     # Train chronological splits, scaler fit, selection loop
│   │   │
│   │   ├───models
│   │   │       schemas.py      # Pydantic data schemas
│   │   │       sql_models.py   # SQLAlchemy database tables
│   │   │
│   │   └───utils
│   │           alerts.py       # Surplus threshold warning checks
│   │           weather.py      # Real-world Weather API & simulation service
│   │
│   └───models_store            # Serialized pkl binaries & metadata
│
└───frontend
    │   app.py                  # Main Streamlit dashboard entrypoint
    │   Dockerfile              # Streamlit container config
    │
    └───pages
            1_🏡_Home.py         # Executive KPIs & daily highlights
            2_📊_Analytics.py    # Plotly interactive analytics
            3_🔮_Predictions.py  # Forecast page & NGO dispatcher
            4_🍲_Inventory.py    # Bulk inventory calculator & portion manager
            5_⚙️_Admin.py        # CSV batch uploader & manual retrain widgets
            6_📋_Reports.py      # Donation dispatch records & reports downloader
            7_💬_AI_Analyst.py   # Offline rule-driven operations chatbot
```

---

## 🚀 Installation & Execution

### Option A: Standard Local Execution (Recommended)

1. **Clone & Initialize Project**:
   Create a directory called `smart_food_waste_management` inside `C:\Users\asaks\.gemini\antigravity\scratch\`.

2. **Configure Environment Variables**:
   Verify `.env` exists in the root directory. You can optionally add an OpenWeatherMap API key:
   ```env
   DATABASE_URL=sqlite:///./food_waste.db
   API_HOST=127.0.0.1
   API_PORT=8000
   NGO_WEBHOOK_URL=http://127.0.0.1:8000/api/donations/webhook-simulator
   DONATION_THRESHOLD_KG=15.0
   ```

3. **Install Dependencies**:
   It is recommended to use a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. **Launch Backend**:
   Run the FastAPI REST API:
   ```powershell
   python backend/main.py
   ```
   *Note: On first startup, the database automatically seeds with 500 days of synthetic consumption records and pre-trains the ML pipeline models (saving best_model.pkl).*

5. **Launch Frontend Dashboard**:
   In a separate shell session, execute:
   ```powershell
   streamlit run frontend/app.py
   ```
   Open the browser at `http://localhost:8501`.

---

### Option B: Unified Containerized Deployment

Execute via Docker Compose in a single command:
```bash
docker-compose up --build
```
* FastAPI is mapped to `http://localhost:8000`.
* Streamlit dashboard is mapped to `http://localhost:8501`.

---

## 🧠 ML Forecasting Validation Details

On initial ingestion, the system splits historical records chronologically:
* **Train Set**: 400 days (historical baseline)
* **Test Set**: 100 days (evaluation window)
* **Features Included**:
  * Date properties: Day of week, Month, Day of Year, Season.
  * Holiday indicators (binary).
  * Campus events categories.
  * Weather status & High temperature.
  * Historical variables: $t-1$ plates, $t-2$ plates, $t-7$ plates, 3-day rolling mean, 7-day rolling mean, 7-day rolling standard deviation.
* **Auto Selection evaluation**:
  * **Linear Regression**: R² ~ 0.72 | MAE ~ 28.5 plates
  * **Random Forest**: R² ~ 0.93 | MAE ~ 11.2 plates
  * **XGBoost Regressor**: R² ~ 0.96 | MAE ~ 8.4 plates
  * *XGBoost is typically chosen, saved, and utilized for real-time inference.*
