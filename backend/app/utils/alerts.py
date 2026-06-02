import logging
from backend.app.config import settings

logger = logging.getLogger("alerts")

def assess_surplus_and_alert(date_str: str, predicted_waste_kg: float) -> dict:
    """
    Evaluates whether the predicted waste exceeds the allowed threshold
    and triggers standard console alerts or NGO recommendations.
    """
    threshold = settings.DONATION_THRESHOLD_KG
    triggered = predicted_waste_kg >= threshold
    
    suggested_ngos = [
        "Robin Hood Army (Local Canteen Chapter)",
        "Feeding America / Local Mess Rescue",
        "Zero Waste Alliance",
        "Community Bread Basket"
    ]
    
    if triggered:
        msg = f"[ALERT] Excess food surplus predicted for {date_str}! Predicted waste is {predicted_waste_kg:.2f} kg, crossing the threshold of {threshold:.2f} kg. Food Donation Recommended."
        logger.warning(msg)
        return {
            "date": date_str,
            "predicted_waste_kg": predicted_waste_kg,
            "is_triggered": True,
            "message": msg,
            "suggested_ngos": suggested_ngos
        }
    else:
        msg = f"[INFO] Food waste levels for {date_str} are estimated at {predicted_waste_kg:.2f} kg, which is within the safe threshold limit ({threshold:.2f} kg)."
        logger.info(msg)
        return {
            "date": date_str,
            "predicted_waste_kg": predicted_waste_kg,
            "is_triggered": False,
            "message": msg,
            "suggested_ngos": []
        }
