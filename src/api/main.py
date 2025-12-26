from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys
import logging
from datetime import datetime
from email_handler import send_email, prepare_stock_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Event Dispatcher Service")
router = APIRouter()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class StockItem(BaseModel):
    symbol: str
    buy_rating: float
    overall_sentiment: str
    key_drivers: Any
    confidence: str
    summary: str

class StockAlertRequest(BaseModel):
    stocks: List[StockItem]
    error_list: List[str] = []

class HealthAlertRequest(BaseModel):
    issues: List[str]

class GenericEmailRequest(BaseModel):
    subject: str
    body: str
    to_email: Optional[str] = None

# Endpoints
@router.get("/health")
def health_check():
    return JSONResponse({"status": "OK", "timestamp": str(datetime.now())})

@router.post("/api/v1/stock-alert")
def send_stock_alert(request: StockAlertRequest):
    logger.info(f"Received stock alert request for {len(request.stocks)} stocks")
    
    current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
    subject = f"Stockflow Alert: Buy Signal Detected - {current_datetime}"
    
    try:
        body = prepare_stock_template(request.stocks)
        # Default receiver for stock alerts
        receiver = os.getenv("STOCK_ALERT_RECEIVER", "avinashsubhash19@outlook.com")
        send_email(subject, body, receiver, is_html=True)
        return JSONResponse({"status": "Email sent", "count": len(request.stocks)})
    except Exception as e:
        logger.error(f"Failed to send stock alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/health-alert")
def send_health_alert(request: HealthAlertRequest):
    logger.info(f"Received health alert request for issues: {request.issues}")
    
    current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
    subject = f"Stockflow Alert: Health Check Failed - {current_datetime}"
    
    body = f"""
Hello,

Stockflow has identified failed health check during routine checks.

Errored Services: {request.issues}

Thank you,
Stockflow

---

This is an automated message. Please do not reply.
    """
    
    # Default receiver for health alerts
    receiver = os.getenv("HEALTH_ALERT_RECEIVER", "kingaiva@icloud.com")
    
    try:
        send_email(subject, body, receiver, is_html=False)
        return JSONResponse({"status": "Health alert email sent"})
    except Exception as e:
        logger.error(f"Failed to send health alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/send-email")
def send_generic_email(request: GenericEmailRequest):
    logger.info(f"Received generic email request: {request.subject}")
    receiver = request.to_email or os.getenv("DEFAULT_RECEIVER", "avinashsubhash19@outlook.com")
    try:
        send_email(request.subject, request.body, receiver, is_html=False)
        return JSONResponse({"status": "Email sent"})
    except Exception as e:
        logger.error(f"Failed to send generic email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)

if __name__ == "__main__":
    logger.info("Starting Event Dispatcher Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info", reload=True)

