from fastapi import FastAPI, BackgroundTasks,HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys
import logging
from datetime import datetime
from event_dispatch_functions import trigger_health_alert,trigger_email_alert,send_email,prepare_template,send_slack_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

event_dispatcher = FastAPI(title="Event Dispatcher Service")
router = APIRouter()

# CORS
event_dispatcher.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class HealthAlertRequest(BaseModel):
    issues: List[str]
    channels: Optional[List[str]] = ["email"]
    channel: Optional[str] = None

class EmailAlertRequest(BaseModel):
    stock_list: List[Dict[str, Any]]
    channels: Optional[List[str]] = ["email"]
    channel: Optional[str] = None

class SlackAlertRequest(BaseModel):
    message: str
    channel: str

# Endpoints
@router.get("/health")
def health_check():
    return JSONResponse({"status": "OK", "timestamp": str(datetime.now())})

@router.post("/api/v1/health-alert")
def send_health_alert(request: HealthAlertRequest, background_tasks: BackgroundTasks):
    logger.info(f"Received health alert request for issues: {request.issues}")
    current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
    try:
        background_tasks.add_task(trigger_health_alert, logger, request.issues, current_datetime, request.channels, request.channel)
    except Exception as e:
        logger.error(f"Failed to send health alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse({"status": "Health alert process initiated", "channels": request.channels})

@router.post("/api/v1/email-alert")
def send_email_alert(request: EmailAlertRequest, background_tasks: BackgroundTasks):
    logger.info(f"Received email alert request for stockflow")
    current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
    try:
        background_tasks.add_task(trigger_email_alert, logger, request.stock_list, current_datetime, request.channels, request.channel)
    except Exception as e:
        logger.error(f"Failed to send email alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse({"status": "Email alert process initiated", "channels": request.channels})

@router.post("/api/v1/slack-alert")
def send_slack_alert(request: SlackAlertRequest, background_tasks: BackgroundTasks):
    logger.info(f"Received generic Slack alert request")
    try:
        background_tasks.add_task(send_slack_message, logger, request.message, request.channel)
    except Exception as e:
        logger.error(f"Failed to send slack alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse({"status": "Slack alert process initiated"})

event_dispatcher.include_router(router)

if __name__ == "__main__":
    logger.info("Starting Event Dispatcher Service")
    uvicorn.run("main:event_dispatcher", host="0.0.0.0", port=8000, log_level="info", reload=True)

