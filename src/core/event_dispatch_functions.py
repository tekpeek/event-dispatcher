import os
import requests
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
SLACK_SECRETS_PATH = os.getenv("SLACK_SECRETS_PATH", "/app/secrets/slack")

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

def get_slack_webhook(channel_name: str):
    if not channel_name:
        raise ValueError("Slack channel name is mandatory")
    
    # Strictly check for file-based secret (K8s mounted volume)
    secret_file = os.path.join(SLACK_SECRETS_PATH, channel_name)
    if not os.path.exists(secret_file):
        raise FileNotFoundError(f"Slack secret file not found for channel: {channel_name}")
    
    try:
        with open(secret_file, 'r') as f:
            webhook = f.read().strip()
            if not webhook:
                raise ValueError(f"Slack secret file for channel '{channel_name}' is empty")
            return webhook
    except Exception as e:
        raise Exception(f"Failed to read Slack secret for channel '{channel_name}': {str(e)}")

def send_slack_message(logger, message: str, channel: str):
    try:
        url = get_slack_webhook(channel)
        logger.info(f"Sending Slack message to channel: {channel}...")
        response = requests.post(url, json={"text": message})
        response.raise_for_status()
        logger.info("Slack message sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send Slack message: {str(e)}")
        return False

def trigger_health_alert(logger, issues: List[str], current_datetime: str, channels: List[str] = ["email"], channel: str = None):
    results = {}
    
    if "email" in channels:
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
            send_email(logger, subject, body, receiver, is_html=False)
            results["email"] = "sent"
        except Exception as e:
            logger.error(f"Failed to send health alert email: {str(e)}")
            results["email"] = f"failed: {str(e)}"

    if "slack" in channels:
        slack_msg = f"*Stockflow Alert: Health Check Failed*\n*Time:* {current_datetime}\n*Errored Services:* {', '.join(issues)}"
        if send_slack_message(logger, slack_msg, channel):
            results["slack"] = "sent"
        else:
            results["slack"] = "failed"

    return results

def trigger_email_alert(logger, stock_list, current_datetime: str, channels: List[str] = ["email"], channel: str = None):
    results = {}
    
    if "email" in channels:
        current_datetime_str = datetime.now().strftime("%B %d %Y - %I:%M %p")
        subject = f"Stockflow Alert: Buy Signal Detected - {current_datetime_str}"
        sender_addr = "noreply.avinash.s@gmail.com"
        smtp_host = os.getenv("SMTP_HOST")
        
        # Format stock details
        body = prepare_template(stock_list)
        smtp_user = "noreply.avinash.s@gmail.com"
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_port = os.getenv("SMTP_PORT")
        receiver = "avinashsubhash19@outlook.com"
        
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = formataddr(("Market Monitor", sender_addr))
        msg['To'] = receiver
        msg.attach(MIMEText(body, "html"))
        
        try:
            with smtplib.SMTP(smtp_host, int(smtp_port or 587)) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            logger.info(f"Email alert sent successfully")
            results["email"] = "sent"
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            results["email"] = f"failed: {str(e)}"

    if "slack" in channels:
        stock_summary = "\n".join([f"• *{s['symbol']}*: {s['buy_rating']} ({s['overall_sentiment']})" for s in stock_list])
        slack_msg = f"*Stockflow Alert: Buy Signal Detected*\n*Time:* {current_datetime}\n*Summary:*\n{stock_summary}"
        if send_slack_message(logger, slack_msg, channel):
            results["slack"] = "sent"
        else:
            results["slack"] = "failed"
            
    return results

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