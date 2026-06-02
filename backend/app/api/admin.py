from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd
import io
from datetime import datetime
from typing import Dict, Any

from backend.app.database import get_db
from backend.app.models.sql_models import ConsumptionRecord
from backend.app.models.schemas import ConsumptionRecordCreate, TrainingResponse, ModelMetric
from backend.app.ml.pipeline import train_and_select_best_model, load_pipeline
from backend.app.config import logger

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

@router.post("/retrain", response_model=TrainingResponse)
def trigger_model_retraining(db: Session = Depends(get_db)):
    """
    Queries all historical records from SQLite and triggers the ML pipeline:
    executes train/test split, trains LR, RF, and XGBoost, performs auto-selection,
    saves the best model, and outputs comparison metrics.
    """
    records = db.query(ConsumptionRecord).order_by(ConsumptionRecord.date.asc()).all()
    if len(records) < 15:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient training data. Need at least 15 historical records. Currently have {len(records)}."
        )
        
    # Convert SQLAlchemy records to Pandas DataFrame
    data = [r.to_dict() for r in records]
    df = pd.DataFrame(data)
    
    try:
        metadata = train_and_select_best_model(df)
        
        # Build pydantic schemas response
        metrics_dict = {}
        for m_name, metrics in metadata["metrics"].items():
            metrics_dict[m_name] = ModelMetric(
                rmse=round(metrics["rmse"], 3),
                mae=round(metrics["mae"], 3),
                r2=round(metrics["r2"], 3)
            )
            
        return TrainingResponse(
            status="success",
            message="Machine learning pipeline executed successfully.",
            best_model=metadata["best_model_name"],
            num_samples_trained=metadata["dataset_samples"],
            metrics=metrics_dict
        )
    except Exception as e:
        logger.error(f"Failed to execute training pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Model retraining failed: {str(e)}")

@router.post("/upload-csv")
def upload_consumption_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Allows uploading a custom historical food consumption CSV dataset.
    Validates formatting, bulk inserts new records, and triggers automatic
    ML pipeline retraining.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV.")
        
    try:
        contents = file.file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate required columns
        required_cols = ["date", "temperature", "weather", "is_holiday", "event", "visitors", "cooked_quantity", "actual_consumption", "waste_generated"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"CSV missing columns: {', '.join(missing_cols)}")
            
        # Parse records
        records_to_insert = []
        inserted_dates = set()
        
        # Clear/Delete existing records to prevent unique constraint failures
        # (This is standard practice for demo data re-uploads)
        db.query(ConsumptionRecord).delete()
        
        for idx, row in df.iterrows():
            date_str = str(row["date"])
            try:
                parsed_date = pd.to_datetime(date_str).date()
            except Exception:
                raise HTTPException(status_code=400, detail=f"Row {idx+2}: Invalid date format '{date_str}'")
                
            if parsed_date in inserted_dates:
                continue # Skip duplicates
                
            day_of_week = parsed_date.strftime("%A")
            
            record = ConsumptionRecord(
                date=parsed_date,
                day_of_week=day_of_week,
                temperature=float(row["temperature"]),
                weather=str(row["weather"]),
                is_holiday=int(row["is_holiday"]),
                event=str(row["event"]),
                visitors=int(row["visitors"]),
                cooked_quantity=int(row["cooked_quantity"]),
                actual_consumption=int(row["actual_consumption"]),
                waste_generated=float(row["waste_generated"])
            )
            records_to_insert.append(record)
            inserted_dates.add(parsed_date)
            
        db.bulk_save_objects(records_to_insert)
        db.commit()
        
        logger.info(f"Admin CSV upload complete. Successfully ingested {len(records_to_insert)} records. Auto-triggering model retraining...")
        
        # Trigger retraining automatically
        retrain_res = trigger_model_retraining(db)
        
        return {
            "status": "success",
            "message": f"Successfully imported {len(records_to_insert)} records.",
            "pipeline_retraining": retrain_res
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing uploaded CSV file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process CSV file: {str(e)}")

@router.post("/add-record")
def manual_add_record(record: ConsumptionRecordCreate, db: Session = Depends(get_db)):
    """
    Manually inserts or updates a single daily consumption record.
    Used by cafeteria admins to log actual daily consumption and waste.
    """
    # Check if record already exists for this date
    existing = db.query(ConsumptionRecord).filter(ConsumptionRecord.date == record.date).first()
    
    if existing:
        # Update existing record
        for key, value in record.dict().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        logger.info(f"Manual record for {record.date} updated successfully.")
        return {"status": "success", "message": f"Updated record for {record.date}", "record": existing.to_dict()}
    else:
        # Create new record
        new_rec = ConsumptionRecord(
            date=record.date,
            day_of_week=record.day_of_week,
            temperature=record.temperature,
            weather=record.weather,
            is_holiday=record.is_holiday,
            event=record.event,
            visitors=record.visitors,
            cooked_quantity=record.cooked_quantity,
            actual_consumption=record.actual_consumption,
            waste_generated=record.waste_generated
        )
        db.add(new_rec)
        db.commit()
        db.refresh(new_rec)
        logger.info(f"Manual record for {record.date} added successfully.")
        return {"status": "success", "message": f"Added record for {record.date}", "record": new_rec.to_dict()}

@router.get("/model-info")
def get_current_model_info():
    """
    Returns active ML pipeline model performance, scaling features,
    and metadata properties.
    """
    model, scaler, metadata = load_pipeline()
    if model is None:
        return {"trained": False, "message": "ML Model has not been trained."}
    return {
        "trained": True,
        "best_model": metadata.get("best_model_name"),
        "trained_date": metadata.get("trained_date"),
        "dataset_samples": metadata.get("dataset_samples"),
        "metrics": metadata.get("metrics"),
        "features": metadata.get("feature_columns")
    }
