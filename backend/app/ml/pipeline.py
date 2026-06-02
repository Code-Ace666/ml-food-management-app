import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

from backend.app.config import MODELS_DIR, logger
from backend.app.ml.features import prepare_training_features

# Paths for serialized models
MODEL_PATH = MODELS_DIR / "best_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata.json"

def train_and_select_best_model(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Trains Linear Regression, Random Forest, and XGBoost regressor models,
    compares their performance using a chronological train/test split,
    selects the best model, and serializes all pipeline artifacts.
    """
    logger.info("Initializing Model Training Pipeline...")
    
    # 1. Feature Engineering
    X, y = prepare_training_features(df)
    
    # 2. Chronological Train-Test Split (80% Train, 20% Test)
    # We do NOT shuffle because this is a time-series dataset.
    split_idx = int(len(X) * 0.8)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    logger.info(f"Split data chronologically: Train shape={X_train.shape}, Test shape={X_test.shape}")
    
    # 3. Fit StandardScaler on features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Track metrics
    models_evaluation = {}
    trained_models = {}
    
    # --- MODEL 1: Linear Regression ---
    lr = LinearRegression()
    lr.fit(X_train_scaled, y_train)
    y_pred_lr = lr.predict(X_test_scaled)
    
    models_evaluation["Linear Regression"] = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_lr))),
        "mae": float(mean_absolute_error(y_test, y_pred_lr)),
        "r2": float(r2_score(y_test, y_pred_lr))
    }
    trained_models["Linear Regression"] = lr
    
    # --- MODEL 2: Random Forest Regressor ---
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X_train_scaled, y_train)
    y_pred_rf = rf.predict(X_test_scaled)
    
    models_evaluation["Random Forest"] = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_rf))),
        "mae": float(mean_absolute_error(y_test, y_pred_rf)),
        "r2": float(r2_score(y_test, y_pred_rf))
    }
    trained_models["Random Forest"] = rf
    
    # --- MODEL 3: XGBoost Regressor ---
    xg_reg = xgb.XGBRegressor(
        objective='reg:squarederror', 
        n_estimators=100, 
        max_depth=5, 
        learning_rate=0.08, 
        random_state=42
    )
    xg_reg.fit(X_train_scaled, y_train)
    y_pred_xgb = xg_reg.predict(X_test_scaled)
    
    models_evaluation["XGBoost"] = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_xgb))),
        "mae": float(mean_absolute_error(y_test, y_pred_xgb)),
        "r2": float(r2_score(y_test, y_pred_xgb))
    }
    trained_models["XGBoost"] = xg_reg
    
    # 4. Auto-select best model (based on lowest RMSE)
    best_model_name = min(models_evaluation, key=lambda k: models_evaluation[k]["rmse"])
    best_model = trained_models[best_model_name]
    best_metrics = models_evaluation[best_model_name]
    
    logger.info(f"Auto-selected Best Model: {best_model_name}")
    logger.info(f"Performance: RMSE={best_metrics['rmse']:.3f}, MAE={best_metrics['mae']:.3f}, R²={best_metrics['r2']:.3f}")
    
    # 5. Serialize best model, scaler, and metadata
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    
    # Features names order
    feature_columns = list(X.columns)
    
    metadata = {
        "best_model_name": best_model_name,
        "feature_columns": feature_columns,
        "metrics": models_evaluation,
        "trained_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_samples": len(df)
    }
    
    joblib.dump(metadata, METADATA_PATH)
    logger.info("Successfully saved best model, scaler, and metadata to model storage.")
    
    return metadata

def load_pipeline() -> Tuple[Any, StandardScaler, Dict[str, Any]]:
    """
    Loads serialized ML models, scalers, and metadata from storage.
    If models do not exist, returns None.
    """
    if not (MODEL_PATH.exists() and SCALER_PATH.exists() and METADATA_PATH.exists()):
        logger.warning("ML pipeline files not found in models_store. Pipeline needs to be trained.")
        return None, None, None
        
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        metadata = joblib.load(METADATA_PATH)
        return model, scaler, metadata
    except Exception as e:
        logger.error(f"Error loading saved ML pipeline: {e}")
        return None, None, None

def run_predictions(inference_features: pd.DataFrame) -> Tuple[int, str]:
    """
    Loads saved model and runs demand plate inference.
    Aligns and scales inputs to ensure matching features list.
    """
    model, scaler, metadata = load_pipeline()
    if model is None:
        raise FileNotFoundError("Model pipeline not trained. Please train the model first.")
        
    # Get expected features order
    expected_features = metadata["feature_columns"]
    
    # Re-order/fill missing columns in inference dataframe
    inference_ready = pd.DataFrame(index=inference_features.index)
    for col in expected_features:
        if col in inference_features.columns:
            inference_ready[col] = inference_features[col]
        else:
            # Fallback for missing category column
            inference_ready[col] = 0
            
    # Scale features
    scaled_features = scaler.transform(inference_ready)
    
    # Run prediction
    predicted_plates = model.predict(scaled_features)[0]
    
    # Enforce minimum lower bound
    predicted_plates = max(10, int(round(predicted_plates)))
    
    return predicted_plates, metadata["best_model_name"]
