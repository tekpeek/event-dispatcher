import os
import logging
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from email_handler import *

def trigger_health_alert(logger,issues,current_datetime):
    subject = f"Stockflow Alert: Health Check Failed - {current_datetime}"
    body = f"""
Hello,

Stockflow has identified failed health check during routine checks.

Errored Services: {issues}

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