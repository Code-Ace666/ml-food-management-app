from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pandas as pd

from backend.app.database import get_db
from backend.app.models.sql_models import ConsumptionRecord
from backend.app.models.schemas import PredictionRequest, PredictionResponse, IngredientEstimate
from backend.app.config import get_ingredients_config, logger
from backend.app.ml.features import prepare_inference_features
from backend.app.ml.pipeline import run_predictions, load_pipeline
from backend.app.utils.weather import get_weather_forecast

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.post("/predict", response_model=PredictionResponse)
def predict_daily_demand(request: PredictionRequest, db: Session = Depends(get_db)):
    """
    Predicts food plate demand, suggests cooking quantities, estimates raw
    ingredient portions, and calculates potential waste for a specific date.
    """
    try:
        # Validate date format
        target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
    # Check if we have trained model
    model, scaler, metadata = load_pipeline()
    if model is None:
        raise HTTPException(
            status_code=400, 
            detail="Machine learning model has not been trained. Go to Admin to trigger model training."
        )
        
    # Fetch last 15 days of historical records from database for lag/rolling features
    history_records = db.query(ConsumptionRecord)\
        .filter(ConsumptionRecord.date < target_date)\
        .order_by(ConsumptionRecord.date.desc())\
        .limit(15)\
        .all()
        
    if len(history_records) < 7:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient history in database. Need at least 7 days of consumption history to compute lag features. Currently have {len(history_records)}."
        )
        
    # Convert records to dictionary lists chronologically
    historical_data = []
    for r in reversed(history_records):
        historical_data.append({
            "date": r.date.strftime("%Y-%m-%d"),
            "actual_consumption": r.actual_consumption
        })
        
    # Prepare inference record
    inference_record = {
        "date": request.date,
        "temperature": request.temperature,
        "weather": request.weather,
        "is_holiday": request.is_holiday,
        "event": request.event
    }
    
    # 1. Feature Engineering for Inference
    try:
        inference_features = prepare_inference_features(inference_record, historical_data)
    except Exception as e:
        logger.error(f"Feature engineering failed during inference: {e}")
        raise HTTPException(status_code=500, detail=f"Inference feature engineering failed: {str(e)}")
        
    # 2. Run prediction
    try:
        predicted_plates, model_name = run_predictions(inference_features)
    except Exception as e:
        logger.error(f"Inference calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference model execution failed: {str(e)}")
        
    # 3. Dynamic Optimization Logic
    # Heuristic for suggested cooking quantity: predicted plates + safety buffer.
    # We add 8% of predicted plates (or minimum 8 plates) to avoid running out of food,
    # which is significantly smaller than the historical 20-30% blind buffer.
    safety_buffer_plates = max(8, int(round(predicted_plates * 0.08)))
    suggested_cooking = predicted_plates + safety_buffer_plates
    
    # Estimated waste (if actual demand matches predicted, the only waste is the safety buffer.
    # Standard plate waste weight average = 0.40 kg)
    estimated_waste_kg = round(safety_buffer_plates * 0.40, 2)
    
    # 4. Resolve Raw Ingredients Portions
    portions_config = get_ingredients_config()
    ingredient_estimates = []
    
    for key, item in portions_config.items():
        # Portion calculation: suggested plates * portion size per meal
        total_amount = suggested_cooking * item["portion_size"]
        
        # Convert scale to kilograms/liters if size is substantial
        if item["unit"] == "g" and total_amount >= 1000:
            converted_amount = round(total_amount / 1000.0, 2)
            display_unit = "kg"
        elif item["unit"] == "ml" and total_amount >= 1000:
            converted_amount = round(total_amount / 1000.0, 2)
            display_unit = "L"
        else:
            converted_amount = round(total_amount, 2)
            display_unit = item["unit"]
            
        ingredient_estimates.append(
            IngredientEstimate(
                name=item["name"],
                amount=converted_amount,
                unit=display_unit
            )
        )
        
    return PredictionResponse(
        predicted_consumption_plates=predicted_plates,
        estimated_waste_kg=estimated_waste_kg,
        suggested_cooking_plates=suggested_cooking,
        model_used=model_name,
        active_portions=portions_config,
        ingredient_estimates=ingredient_estimates
    )

@router.get("/weather-auto")
def fetch_weather_recommendation(target_date: str):
    """
    Utility endpoint to auto-retrieve temperature and weather estimates
    for a future target date.
    """
    try:
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
    weather_info = get_weather_forecast(target_date)
    return weather_info
