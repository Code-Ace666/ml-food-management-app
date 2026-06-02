from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.app.config import get_ingredients_config, update_ingredients_config, logger

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

@router.get("/portions")
def get_portions():
    """
    Retrieves the active canteen portion configuration sizes.
    """
    return get_ingredients_config()

@router.post("/portions/update")
def update_portions(portions: Dict[str, Any]):
    """
    Updates the portion configuration sizes. Allows modification
    of existing values or dynamic addition of new raw ingredients.
    """
    # Validation: Ensure each ingredient has a portion size and unit
    for key, value in portions.items():
        if "name" not in value or "portion_size" not in value or "unit" not in value:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format for ingredient '{key}'. Must include 'name', 'portion_size', and 'unit'."
            )
        try:
            value["portion_size"] = float(value["portion_size"])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Portion size for '{key}' must be a numeric value."
            )
            
    success = update_ingredients_config(portions)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to persist portion configurations to ingredients.json."
        )
        
    return {"status": "success", "message": "Portion configuration updated successfully.", "portions": portions}

@router.post("/estimate")
def estimate_ingredients(plates: int):
    """
    Dynamically computes raw ingredient portion sizes for a given number of meals/plates.
    """
    if plates <= 0:
        raise HTTPException(status_code=400, detail="Plate quantity must be positive.")
        
    portions_config = get_ingredients_config()
    estimates = {}
    
    for key, item in portions_config.items():
        total_amount = plates * item["portion_size"]
        
        # Format display conversion
        if item["unit"] == "g" and total_amount >= 1000:
            display_val = round(total_amount / 1000.0, 2)
            display_unit = "kg"
        elif item["unit"] == "ml" and total_amount >= 1000:
            display_val = round(total_amount / 1000.0, 2)
            display_unit = "L"
        else:
            display_val = round(total_amount, 2)
            display_unit = item["unit"]
            
        estimates[key] = {
            "name": item["name"],
            "raw_amount": total_amount,
            "display_amount": display_val,
            "display_unit": display_unit
        }
        
    return {"plates": plates, "estimates": estimates}
