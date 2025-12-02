import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import logging
from typing import List, Any

logger = logging.getLogger(__name__)

# Environment variables
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER", "noreply.avinash.s@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_ADDR = os.getenv("SENDER_ADDR", "noreply.avinash.s@gmail.com")
TEMPLATE_PATH = os.getenv("TEMPLATE_PATH", "templates/email-template.html")

def send_email(subject: str, body: str, to_email: str, is_html: bool = False):
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

def prepare_stock_template(stock_list: List[Any]) -> str:
    try:
        # Resolve template path
        template_file = os.path.abspath(TEMPLATE_PATH)
        if not os.path.exists(template_file):
             # Try relative to current working directory if absolute fails
             possible_path = os.path.join(os.getcwd(), TEMPLATE_PATH)
             if os.path.exists(possible_path):
                 template_file = possible_path
             else:
                 logger.warning(f"Template file not found at {TEMPLATE_PATH} or {possible_path}")
                 return "<html><body><h1>Stock Alert</h1><p>Template not found.</p></body></html>"

        with open(template_file, "r") as f:
            html = f.read()

        rows_html = ""
        for stock in stock_list:
            # Handle both dict and object access if necessary, but Pydantic models use dot notation
            # The input here comes from the API model, so it should be objects
            symbol = getattr(stock, 'symbol', stock.get('symbol') if isinstance(stock, dict) else '')
            buy_rating = getattr(stock, 'buy_rating', stock.get('buy_rating') if isinstance(stock, dict) else '')
            overall_sentiment = getattr(stock, 'overall_sentiment', stock.get('overall_sentiment') if isinstance(stock, dict) else '')
            key_drivers = getattr(stock, 'key_drivers', stock.get('key_drivers') if isinstance(stock, dict) else '')
            confidence = getattr(stock, 'confidence', stock.get('confidence') if isinstance(stock, dict) else '')
            summary = getattr(stock, 'summary', stock.get('summary') if isinstance(stock, dict) else '')

            rows_html += f"""
            <tr>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{symbol}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{buy_rating}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{overall_sentiment}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{key_drivers}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{confidence}</td>
                <td style="padding:10px; border-bottom:1px solid #eaeaea;">{summary}</td>
            </tr>"""
        
        return html.replace("{{STOCK_ROWS}}", rows_html)
    except Exception as e:
        logger.error(f"Error preparing template: {str(e)}")
        raise e
