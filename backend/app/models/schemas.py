from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date as date_type, datetime

class ConsumptionRecordBase(BaseModel):
    date: date_type
    day_of_week: str
    temperature: float
    weather: str
    is_holiday: int
    event: str
    visitors: int
    cooked_quantity: int
    actual_consumption: int
    waste_generated: float

class ConsumptionRecordCreate(ConsumptionRecordBase):
    pass

class ConsumptionRecordResponse(ConsumptionRecordBase):
    id: int

    class Config:
        from_attributes = True

class PredictionRequest(BaseModel):
    date: str = Field(..., description="Date for forecast in YYYY-MM-DD format")
    temperature: float = Field(22.0, description="Forecasted daily high temperature in Celsius")
    weather: str = Field("Sunny", description="Forecasted weather condition (Sunny, Cloudy, Rainy, Snowy)")
    is_holiday: int = Field(0, description="1 if the day is a calendar holiday, 0 otherwise")
    event: str = Field("None", description="Ongoing event on this day (None, College Fest, Sports Meet, Corporate Conference, Festive Celebrations)")

class IngredientEstimate(BaseModel):
    name: str
    amount: float
    unit: str

class PredictionResponse(BaseModel):
    predicted_consumption_plates: int
    estimated_waste_kg: float
    suggested_cooking_plates: int
    model_used: str
    active_portions: Dict[str, Any]
    ingredient_estimates: List[IngredientEstimate]

class NGOAlertTrigger(BaseModel):
    date: str
    predicted_waste_kg: float
    is_triggered: bool
    message: str
    suggested_ngos: List[str]

class DonationRequest(BaseModel):
    date: str
    quantity_kg: float
    ngo_name: str

class DonationResponse(BaseModel):
    id: int
    date: str
    quantity_kg: float
    ngo_name: str
    status: str
    dispatch_time: str
    response_payload: Optional[str] = None

    class Config:
        from_attributes = True

class ModelMetric(BaseModel):
    rmse: float
    mae: float
    r2: float

class TrainingResponse(BaseModel):
    status: str
    message: str
    best_model: str
    num_samples_trained: int
    metrics: Dict[str, ModelMetric]

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    intent: str
    data: Optional[Dict[str, Any]] = None
