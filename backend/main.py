import sys
from pathlib import Path

# Add project root directory to sys.path to allow absolute imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import pandas as pd

from backend.app.config import settings, logger
from backend.app.database import init_db, SessionLocal
from backend.app.models.sql_models import ConsumptionRecord
from backend.app.ml.pipeline import load_pipeline, train_and_select_best_model
from backend.app.api import predictions, analytics, donations, inventory, admin

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="AI + ML Smart Food Waste Management System",
    description="REST API powering food consumption prediction, waste analytics, raw portion estimation, and NGO donations dispatches.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to Streamlit origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router)
app.include_router(analytics.router)
app.include_router(donations.router)
app.include_router(inventory.router)
app.include_router(admin.router)

@app.on_event("startup")
def on_startup():
    """
    Startup handler. Performs database checks, table configurations,
    synthetic data population, and ensures ML models are pre-trained.
    """
    logger.info("Starting up Smart Food Waste Management System API...")
    
    # 1. Initialize SQLite Database & populate sample data if empty
    init_db()
    
    # 2. Verify and pre-train machine learning models automatically
    model, _, _ = load_pipeline()
    if model is None:
        logger.info("No pre-trained ML models found. Automatically training pipeline models on initial historical data...")
        db = SessionLocal()
        try:
            records = db.query(ConsumptionRecord).order_by(ConsumptionRecord.date.asc()).all()
            if records:
                data = [r.to_dict() for r in records]
                df = pd.DataFrame(data)
                train_and_select_best_model(df)
                logger.info("Initial ML pipeline trained and serialized successfully.")
            else:
                logger.error("Cannot pre-train ML model. Database contains zero records.")
        except Exception as e:
            logger.error(f"Automatic startup model training failed: {e}")
        finally:
            db.close()
    else:
        logger.info("Existing ML model pipeline loaded successfully.")

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    """
    Captures unhandled exceptions globally and outputs formatted errors.
    """
    logger.error(f"Global unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the technical administrator."}
    )

@app.get("/")
def read_root():
    """
    Root endpoint indicating API service health status.
    """
    return {
        "status": "online",
        "service": "AI + ML Smart Food Waste Management System API",
        "docs_url": "/docs",
        "environment": settings.APP_ENV
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=True
    )
