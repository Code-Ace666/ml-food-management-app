import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, Any, List, Tuple

# Definitions of expected columns
WEATHER_CATEGORIES = ["Sunny", "Cloudy", "Rainy", "Snowy"]
EVENT_CATEGORIES = ["None", "College Fest", "Sports Meet", "Corporate Conference", "Festive Celebrations"]

def extract_datetime_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts high-value time-based features from the date column.
    """
    df = df.copy()
    # Convert to datetime if it's not already
    df["date_parsed"] = pd.to_datetime(df["date"])
    
    df["day_of_week"] = df["date_parsed"].dt.weekday  # 0=Monday, 6=Sunday
    df["month"] = df["date_parsed"].dt.month
    df["year"] = df["date_parsed"].dt.year
    df["day_of_year"] = df["date_parsed"].dt.dayofyear
    df["is_weekend"] = df["day_of_week"].apply(lambda x: 1 if x >= 5 else 0)
    
    # Season mapping
    # 1=Winter, 2=Spring, 3=Summer, 4=Autumn
    df["season"] = df["month"].apply(lambda m: 1 if m in [12, 1, 2] else (2 if m in [3, 4, 5] else (3 if m in [6, 7, 8] else 4)))
    
    df.drop(columns=["date_parsed"], inplace=True)
    return df

def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Manually applies consistent one-hot encoding for weather and events
    to prevent shape mismatches during inference.
    """
    df = df.copy()
    
    # Weather One-Hot
    for w in WEATHER_CATEGORIES:
        col_name = f"weather_{w.lower()}"
        df[col_name] = (df["weather"] == w).astype(int)
        
    # Event One-Hot
    for e in EVENT_CATEGORIES:
        col_name = f"event_{e.lower().replace(' ', '_')}"
        df[col_name] = (df["event"] == e).astype(int)
        
    # Drop source categoricals to avoid feeding text to models
    cols_to_drop = ["weather", "event"]
    for c in cols_to_drop:
        if c in df.columns:
            df.drop(columns=[c], inplace=True)
            
    return df

def compute_historical_features(df: pd.DataFrame, consumption_col: str = "actual_consumption") -> pd.DataFrame:
    """
    Calculates essential ML lag and rolling statistics on historical consumption.
    Assumes dataframe is sorted chronologically.
    """
    df = df.copy()
    
    # 1. Lag Features (demand from prior days)
    df["lag_1"] = df[consumption_col].shift(1)
    df["lag_2"] = df[consumption_col].shift(2)
    df["lag_7"] = df[consumption_col].shift(7)
    
    # 2. Rolling Averages
    df["rolling_mean_3"] = df[consumption_col].shift(1).rolling(window=3, min_periods=1).mean()
    df["rolling_mean_7"] = df[consumption_col].shift(1).rolling(window=7, min_periods=1).mean()
    df["rolling_std_7"] = df[consumption_col].shift(1).rolling(window=7, min_periods=1).std().fillna(0)
    
    return df

def prepare_training_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Executes full feature pipeline for model training.
    """
    # Make sure we sort chronologically
    df_sorted = df.sort_values(by="date").reset_index(drop=True)
    
    # 1. Create Lag & Rolling features
    df_features = compute_historical_features(df_sorted, "actual_consumption")
    
    # 2. Extract Datetime details
    df_features = extract_datetime_features(df_features)
    
    # 3. One-hot Encode categoricals
    df_features = encode_categoricals(df_features)
    
    # Drop rows that don't have sufficient history for lags (first 7 rows)
    df_features = df_features.dropna(subset=["lag_7"]).reset_index(drop=True)
    
    # Define columns to exclude from training features
    exclude_cols = ["date", "day_of_week_str", "cooked_quantity", "visitors", "actual_consumption", "waste_generated"]
    
    # Target
    y = df_features["actual_consumption"]
    
    # Features
    X = df_features.drop(columns=[col for col in exclude_cols if col in df_features.columns])
    
    return X, y

def prepare_inference_features(
    prediction_record: Dict[str, Any], 
    historical_records: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Engineers inference features for a future record by joining it with 
    the last 10 days of historical records to compute lags & rolling stats.
    """
    # 1. Build a chronological DataFrame of historical data + prediction day
    df_history = pd.DataFrame(historical_records)
    df_history = df_history.sort_values(by="date").reset_index(drop=True)
    
    # Add target slot
    pred_row = {
        "date": prediction_record["date"],
        "weather": prediction_record["weather"],
        "temperature": prediction_record["temperature"],
        "is_holiday": prediction_record["is_holiday"],
        "event": prediction_record["event"],
        "actual_consumption": 0 # Placeholder to calculate lag/rolling on preceding days
    }
    
    df_full = pd.concat([df_history, pd.DataFrame([pred_row])], ignore_index=True)
    
    # 2. Compute lag & rolling
    df_full = compute_historical_features(df_full, "actual_consumption")
    
    # 3. Extract Datetime & One-hot encoding
    df_full = extract_datetime_features(df_full)
    df_full = encode_categoricals(df_full)
    
    # 4. Extract only the prediction row (the last row)
    inference_row = df_full.iloc[[-1]].copy()
    
    # Ensure correct columns match exactly what was trained
    exclude_cols = ["date", "cooked_quantity", "visitors", "actual_consumption", "waste_generated"]
    inference_features = inference_row.drop(columns=[col for col in exclude_cols if col in inference_row.columns])
    
    return inference_features
