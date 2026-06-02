import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path
from backend.app.config import logger

DATA_DIR = Path(__file__).resolve().parent
CSV_PATH = DATA_DIR / "sample_food_consumption.csv"

def generate_synthetic_data(num_days: int = 500) -> pd.DataFrame:
    """
    Generates a highly realistic time-series dataset simulating canteen/mess
    food consumption and waste over a specified number of days.
    """
    logger.info(f"Generating synthetic food waste dataset for {num_days} days...")
    
    # Anchor date: 1.5 years ago from today
    start_date = datetime.now() - timedelta(days=num_days)
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    
    data = []
    
    # Weather distribution parameters
    weathers = ["Sunny", "Cloudy", "Rainy", "Snowy"]
    weather_probs = [0.5, 0.3, 0.15, 0.05]
    
    # Event list
    events = ["None", "College Fest", "Sports Meet", "Corporate Conference", "Festive Celebrations"]
    event_probs = [0.92, 0.02, 0.02, 0.02, 0.02]
    
    for i, dt in enumerate(dates):
        # 1. Day of Week
        day_of_week = dt.weekday() # 0 = Monday, 6 = Sunday
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # 2. Seasonality / Month
        month = dt.month
        # Canteens in college/offices experience dips in Summer (June, July) and Winter (December)
        seasonal_factor = 1.0
        if month in [6, 7]:
            seasonal_factor = 0.75 # Summer drop
        elif month == 12:
            seasonal_factor = 0.80 # Winter holiday drop
            
        # 3. Holiday (National/Custom holidays)
        is_holiday = 0
        # Simple rule-based holiday assignment (e.g. Christmas, New Year, Thanksgiving, etc.)
        if (month == 1 and dt.day == 1) or \
           (month == 12 and dt.day in [24, 25, 31]) or \
           (month == 7 and dt.day == 4) or \
           (month == 11 and dt.day in [24, 25]) or \
           (random.random() < 0.02): # 2% chance of minor local holiday
            is_holiday = 1
            
        # 4. Weather & Temp
        weather = np.random.choice(weathers, p=weather_probs)
        # Seasonal temperature
        if month in [12, 1, 2]: # Winter
            temp = random.uniform(2.0, 12.0)
        elif month in [6, 7, 8]: # Summer
            temp = random.uniform(28.0, 38.0)
        else: # Spring / Autumn
            temp = random.uniform(15.0, 25.0)
            
        # 5. Event
        event = np.random.choice(events, p=event_probs)
        
        # 6. Visitor and Food Demand Simulation (The Ground Truth)
        # Baseline visitors
        base_visitors = 320.0
        
        # Apply day-of-week factor: higher Mon-Thu (350), slightly lower Fri (300), very low weekend (100)
        if day_of_week in [0, 1, 2, 3]:
            weekday_mult = 1.1
        elif day_of_week == 4:
            weekday_mult = 0.95
        else:
            weekday_mult = 0.35 # Canteen is partially closed on weekends
            
        # Compile visitor count
        visitors = base_visitors * weekday_mult * seasonal_factor
        
        # Adjust for Holiday
        if is_holiday:
            visitors = visitors * 0.15 # 85% drop on holidays
            
        # Adjust for Weather
        if weather == "Rainy":
            visitors = visitors * 0.85 # 15% drop due to rain
        elif weather == "Snowy":
            visitors = visitors * 0.70 # 30% drop due to snow
            
        # Adjust for Events
        event_impact = 0.0
        if event != "None":
            if event == "College Fest":
                visitors = visitors * 1.50
                event_impact = 100.0
            elif event == "Sports Meet":
                visitors = visitors * 1.35
                event_impact = 70.0
            elif event == "Corporate Conference":
                visitors = visitors * 1.25
                event_impact = 50.0
            elif event == "Festive Celebrations":
                visitors = visitors * 1.40
                event_impact = 80.0
                
        # Add random noise to visitors
        visitors = max(10.0, int(visitors + np.random.normal(0, 15)))
        
        # Actual meal demand/plates consumed is directly related to visitors (approx 90-95% conversion)
        actual_plates_consumed = max(5, int(visitors * random.uniform(0.88, 0.96)))
        
        # 7. Simulated historical cooked quantity (Cafeteria Manager heuristic before AI system)
        # Typically managers over-cook, relying on the average weekday.
        # This leads to heavy food waste!
        avg_cooked_heuristic = base_visitors * weekday_mult * 1.05 # Add 5% safety buffer
        # In historical manual operation, they didn't adjust properly for rain, summer breaks, or holidays
        if is_holiday:
            cooked_quantity = max(40, int(avg_cooked_heuristic * 0.5)) # Reduced but still way too much!
        elif weather in ["Rainy", "Snowy"]:
            cooked_quantity = int(avg_cooked_heuristic * 0.95) # Barely adjusted
        else:
            cooked_quantity = int(avg_cooked_heuristic + np.random.normal(0, 10))
            
        # Cooked quantity cannot be less than actual consumed plates
        cooked_quantity = max(actual_plates_consumed, cooked_quantity)
        
        # 8. Waste calculation
        # Extra plates wasted
        plates_wasted = cooked_quantity - actual_plates_consumed
        # Approx 0.45 kg of raw + prepared waste per meal plate
        waste_generated_kg = round(plates_wasted * 0.45 + max(0.0, np.random.normal(1.5, 0.5)), 2)
        
        data.append({
            "date": dt.strftime("%Y-%m-%d"),
            "day_of_week": dt.strftime("%A"),
            "temperature": round(temp, 1),
            "weather": weather,
            "is_holiday": is_holiday,
            "event": event,
            "visitors": visitors,
            "cooked_quantity": cooked_quantity,
            "actual_consumption": actual_plates_consumed,
            "waste_generated": waste_generated_kg
        })
        
    df = pd.DataFrame(data)
    return df

def save_synthetic_dataset(num_days: int = 500) -> str:
    """
    Generates and saves the synthetic dataset to CSV if it doesn't already exist.
    """
    if CSV_PATH.exists():
        logger.info(f"Synthetic dataset already exists at: {CSV_PATH}")
        return str(CSV_PATH)
        
    df = generate_synthetic_data(num_days)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    logger.info(f"Synthetic dataset successfully written to: {CSV_PATH}")
    return str(CSV_PATH)

if __name__ == "__main__":
    save_synthetic_dataset()
