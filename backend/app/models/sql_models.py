from sqlalchemy import Column, Integer, Float, String, Date, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class ConsumptionRecord(Base):
    """
    SQLAlchemy model representing daily food preparation, actual consumption,
    weather parameters, calendar conditions, and waste outputs.
    """
    __tablename__ = "consumption_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    day_of_week = Column(String(15), nullable=False)
    temperature = Column(Float, nullable=False)
    weather = Column(String(30), nullable=False)
    is_holiday = Column(Integer, default=0, nullable=False)
    event = Column(String(50), default="None", nullable=False)
    visitors = Column(Integer, nullable=False)
    cooked_quantity = Column(Integer, nullable=False) # meals prepared
    actual_consumption = Column(Integer, nullable=False) # meals eaten
    waste_generated = Column(Float, nullable=False) # waste in kilograms

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d") if self.date else None,
            "day_of_week": self.day_of_week,
            "temperature": self.temperature,
            "weather": self.weather,
            "is_holiday": self.is_holiday,
            "event": self.event,
            "visitors": self.visitors,
            "cooked_quantity": self.cooked_quantity,
            "actual_consumption": self.actual_consumption,
            "waste_generated": self.waste_generated
        }

class DonationRecord(Base):
    """
    SQLAlchemy model tracking food surpluses dispatched to external NGOs
    via the webhook simulation system.
    """
    __tablename__ = "donation_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    quantity_kg = Column(Float, nullable=False)
    ngo_name = Column(String(100), nullable=False)
    status = Column(String(30), default="Pending", nullable=False) # Pending, Dispatched, Delivered, Failed
    dispatch_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    response_payload = Column(Text, nullable=True) # Response JSON from simulated webhook

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d") if self.date else None,
            "quantity_kg": self.quantity_kg,
            "ngo_name": self.ngo_name,
            "status": self.status,
            "dispatch_time": self.dispatch_time.isoformat() if self.dispatch_time else None,
            "response_payload": self.response_payload
        }
