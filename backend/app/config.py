import os
import json
import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("config")

# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
INGREDIENTS_FILE = BASE_DIR / "backend" / "app" / "data" / "ingredients.json"
MODELS_DIR = BASE_DIR / "backend" / "models_store"

# Ensure models directory exists
MODELS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./food_waste.db"
    APP_ENV: str = "development"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    SECRET_KEY: str = "dev_secret_key"
    
    # Webhook
    NGO_WEBHOOK_URL: str = "http://127.0.0.1:8000/api/donations/webhook-simulator"
    DONATION_THRESHOLD_KG: float = 15.0
    
    # Optional weather integration
    OPENWEATHERMAP_API_KEY: str = ""
    DEFAULT_CITY: str = "New Delhi"
    
    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()

def get_ingredients_config() -> Dict[str, Any]:
    """
    Dynamically loads current ingredient portion config.
    Fallback values are used if the JSON file is missing.
    """
    if INGREDIENTS_FILE.exists():
        try:
            with open(INGREDIENTS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ingredients configuration: {e}")
            
    # Default Portion Fallbacks
    return {
        "rice": {"name": "Rice", "portion_size": 100.0, "unit": "g"},
        "vegetables": {"name": "Vegetables", "portion_size": 150.0, "unit": "g"},
        "oil": {"name": "Cooking Oil", "portion_size": 15.0, "unit": "ml"},
        "flour": {"name": "Flour (Atta)", "portion_size": 80.0, "unit": "g"},
        "milk": {"name": "Milk", "portion_size": 50.0, "unit": "ml"},
        "pulses": {"name": "Pulses & Lentils", "portion_size": 40.0, "unit": "g"}
    }

def update_ingredients_config(portions: Dict[str, Any]) -> bool:
    """
    Updates portion size configurations in ingredients.json.
    """
    try:
        INGREDIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INGREDIENTS_FILE, "w") as f:
            json.dump(portions, f, indent=2)
        logger.info("Successfully updated ingredients configuration.")
        return True
    except Exception as e:
        logger.error(f"Failed to save portion sizes to config file: {e}")
        return False
