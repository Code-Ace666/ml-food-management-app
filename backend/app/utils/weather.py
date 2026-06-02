import requests
import random
from typing import Dict, Any
from backend.app.config import settings, logger

def get_weather_forecast(date_str: str) -> Dict[str, Any]:
    """
    Retrieves weather forecast. If an OpenWeatherMap API key is supplied,
    calls the live API; otherwise, generates highly realistic simulated seasonal weather.
    """
    api_key = settings.OPENWEATHERMAP_API_KEY
    city = settings.DEFAULT_CITY
    
    if api_key:
        try:
            # Note: For portfolio demonstrations, OpenWeatherMap 5-day forecast
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Parse forecast matching date_str if available, or return first entry
                logger.info(f"Successfully fetched live weather from OpenWeatherMap API for {city}")
                
                # Default parse
                first_forecast = data["list"][0]
                temp = first_forecast["main"]["temp"]
                weather_main = first_forecast["weather"][0]["main"]
                
                # Map to project categories: Sunny, Cloudy, Rainy, Snowy
                weather_map = {
                    "Clear": "Sunny",
                    "Clouds": "Cloudy",
                    "Rain": "Rainy",
                    "Drizzle": "Rainy",
                    "Thunderstorm": "Rainy",
                    "Snow": "Snowy"
                }
                mapped_weather = weather_map.get(weather_main, "Sunny")
                
                return {
                    "temperature": round(temp, 1),
                    "weather": mapped_weather,
                    "source": "OpenWeatherMap API"
                }
        except Exception as e:
            logger.error(f"Live Weather API lookup failed: {e}. Falling back to simulation.")
            
    # Premium Simulation Mode (Fully free, zero latency)
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month = dt.month
    except Exception:
        month = 5 # Default to May
        
    # Season-based temp and weather probabilities
    if month in [12, 1, 2]: # Winter
        temp = random.uniform(3.0, 14.0)
        weather = random.choices(["Sunny", "Cloudy", "Rainy", "Snowy"], weights=[0.25, 0.45, 0.15, 0.15])[0]
    elif month in [6, 7, 8]: # Summer
        temp = random.uniform(27.0, 37.0)
        weather = random.choices(["Sunny", "Cloudy", "Rainy"], weights=[0.65, 0.25, 0.10])[0]
    else: # Spring / Autumn
        temp = random.uniform(16.0, 24.0)
        weather = random.choices(["Sunny", "Cloudy", "Rainy"], weights=[0.55, 0.35, 0.10])[0]
        
    return {
        "temperature": round(temp, 1),
        "weather": weather,
        "source": "Local Weather Simulator"
    }
