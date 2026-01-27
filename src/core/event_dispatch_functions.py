import os
import logging
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Any
import sys
from datetime import datetime

# Environment variables
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER", "noreply.avinash.s@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_ADDR = os.getenv("SENDER_ADDR", "noreply.avinash.s@gmail.com")
TEMPLATE_PATH = os.getenv("TEMPLATE_PATH", "templates/email-template.html")

def send_email(logger,subject: str, body: str, to_email: str, is_html: bool = False):
    if not SMTP_HOST or not SMTP_PASSWORD:
        logger.error("SMTP credentials not set")
        raise Exception("SMTP configuration missing")

    try:
        msg = MIMEMultipart("alternative") if is_html else EmailMessage()
        msg['Subject'] = subject
        msg['From'] = formataddr(("Stockflow Notification", SENDER_ADDR))
        msg['To'] = to_email

        if is_html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.set_content(body)

        logger.info(f"Connecting to SMTP server: {SMTP_HOST}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT or 587)) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise e

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
        send_email(logger,subject, body, receiver, is_html=False)
        return JSONResponse({"status": "Health alert email sent"})
    except Exception as e:
        logger.error(f"Failed to send health alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def trigger_email_alert(logger,stock_list,current_datetime):
    current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
    subject = f"Stockflow Alert: Buy Signal Detected - {current_datetime}"
    sender_addr = "noreply.avinash.s@gmail.com"
    smtp_host = os.getenv("SMTP_HOST")
    
    # Format stock details
    body=prepare_template(stock_list)
    smtp_user = "noreply.avinash.s@gmail.com"
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_port = os.getenv("SMTP_PORT")
    reciever = "avinashsubhash19@outlook.com"
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = formataddr(("Market Monitor", sender_addr))
    msg['To'] = reciever
    msg.attach(MIMEText(body, "html"))
    #msg.set_content(body)
    server = smtplib.SMTP(smtp_host,smtp_port)    
    server.starttls()
    server.login(smtp_user,smtp_password)
    server.send_message(msg)

def prepare_template(stock_list=None):
    with open("email-template.html") as f:
        html = f.read()
    
    if stock_list:
        # Generate table rows from stock_list
        rows_html = ""
        for stock in stock_list:
            symbol, buy_rating, overall_sentiment, key_drivers, confidence, summary = stock["symbol"], stock["buy_rating"], stock["overall_sentiment"], str(stock["key_drivers"]), stock["confidence"], stock["summary"] 
            
            rows_html += f"""
            <tr>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{symbol}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{buy_rating}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{overall_sentiment}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{key_drivers}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{confidence}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{summary}</td>
            </tr>"""
        
        # Replace placeholder with generated rows
        html = html.replace("{{STOCK_ROWS}}", rows_html)
    
    return html