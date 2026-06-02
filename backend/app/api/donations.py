from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import requests
import json
from typing import List, Dict, Any

from backend.app.database import get_db
from backend.app.models.sql_models import DonationRecord
from backend.app.models.schemas import DonationRequest, DonationResponse, NGOAlertTrigger
from backend.app.config import settings, logger
from backend.app.utils.alerts import assess_surplus_and_alert

router = APIRouter(prefix="/api/donations", tags=["Donations"])

@router.get("/alert", response_model=NGOAlertTrigger)
def check_donation_alert(date: str, predicted_waste_kg: float):
    """
    Checks if a predicted waste quantity exceeds thresholds, triggering
    an automated recommendation for NGO donation.
    """
    alert_info = assess_surplus_and_alert(date, predicted_waste_kg)
    return NGOAlertTrigger(**alert_info)

@router.post("/webhook-simulator")
def ngo_webhook_simulator(payload: Dict[str, Any]):
    """
    A simulated external NGO API endpoint. Log details of incoming donation
    payloads and outputs a mock dispatch acceptance response.
    """
    logger.info(f"[NGO WEBHOOK SIMULATOR] Received donation payload: {json.dumps(payload, indent=2)}")
    
    ngo_name = payload.get("ngo_name", "Local Rescue NGO")
    quantity_kg = payload.get("quantity_kg", 0.0)
    
    # Mock dispatch details
    drivers = ["Sarah Jenkins", "Robert Chen", "Elena Rostova", "Marcus Vance"]
    assigned_driver = drivers[int(quantity_kg) % len(drivers)]
    eta = random_eta = int((quantity_kg * 1.5) % 30) + 20 # 20-50 min
    verification_code = f"DONATE-{int(datetime.now().timestamp()) % 10000:04d}"
    
    response = {
        "status": "success",
        "message": "Donation dispatch accepted",
        "ngo_partner": ngo_name,
        "quantity_accepted_kg": quantity_kg,
        "assigned_driver": assigned_driver,
        "eta_minutes": eta,
        "security_verification_code": verification_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"[NGO WEBHOOK SIMULATOR] Responding with dispatch status: {json.dumps(response, indent=2)}")
    return response

@router.post("/dispatch", response_model=DonationResponse)
def dispatch_surplus_to_ngo(request: DonationRequest, db: Session = Depends(get_db)):
    """
    Dispatches surplus food to the selected NGO by making an HTTP call to the
    simulated webhook endpoint, logging response payloads, and saving details in DB.
    """
    target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
    
    # Payload for the webhook
    payload = {
        "date": request.date,
        "quantity_kg": request.quantity_kg,
        "ngo_name": request.ngo_name,
        "request_origin": "Smart Food Waste Management System API",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Trigger webhook
    webhook_url = settings.NGO_WEBHOOK_URL
    logger.info(f"Triggering simulated NGO webhook at: {webhook_url}")
    
    try:
        # Call the webhook simulator (which is hosted locally)
        # Note: If calling our own API synchronously, uvicorn single-threaded can deadlock
        # if not handled properly. To make it bulletproof and offline-safe without actual
        # network deadlock, we will call our simulation handler function directly if
        # it is a local URL, or fall back to requests.post.
        if "127.0.0.1" in webhook_url or "localhost" in webhook_url:
            # Direct python call to prevent local HTTP deadlocks in single-worker mode!
            response_json = ngo_webhook_simulator(payload)
            status_code = 200
        else:
            response = requests.post(webhook_url, json=payload, timeout=5)
            status_code = response.status_code
            response_json = response.json()
            
        if status_code != 200:
            raise Exception(f"Webhook returned status code {status_code}")
            
    except Exception as e:
        logger.error(f"Simulated Webhook Dispatch Failed: {e}")
        # Log failure but still save in DB with "Failed" status
        response_json = {"status": "failed", "error": str(e)}
        
    # Save record in database
    status = "Dispatched" if response_json.get("status") == "success" else "Failed"
    
    donation_record = DonationRecord(
        date=target_date,
        quantity_kg=request.quantity_kg,
        ngo_name=request.ngo_name,
        status=status,
        dispatch_time=datetime.utcnow(),
        response_payload=json.dumps(response_json)
    )
    
    db.add(donation_record)
    db.commit()
    db.refresh(donation_record)
    
    # Format response
    return DonationResponse(
        id=donation_record.id,
        date=donation_record.date.strftime("%Y-%m-%d"),
        quantity_kg=donation_record.quantity_kg,
        ngo_name=donation_record.ngo_name,
        status=donation_record.status,
        dispatch_time=donation_record.dispatch_time.isoformat(),
        response_payload=donation_record.response_payload
    )

@router.get("/history", response_model=List[DonationResponse])
def get_donation_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Retrieves previous NGO donation records.
    """
    records = db.query(DonationRecord).order_by(DonationRecord.dispatch_time.desc()).limit(limit).all()
    
    response_list = []
    for r in records:
        response_list.append(
            DonationResponse(
                id=r.id,
                date=r.date.strftime("%Y-%m-%d"),
                quantity_kg=r.quantity_kg,
                ngo_name=r.ngo_name,
                status=r.status,
                dispatch_time=r.dispatch_time.isoformat(),
                response_payload=r.response_payload
            )
        )
    return response_list
