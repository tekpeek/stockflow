import sys
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime

def send_email(stock_list,error_list):
    current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
    subject = f"Stockflow Alert: Buy Signal Detected - {current_datetime}"
    sender_addr = "noreply.avinash.s@gmail.com"
    smtp_host = os.getenv("SMTP_HOST")
    
    # Format stock details
    stock_details = ""
    for stock in stock_list:
        ticker, signals, strength, reasons = stock
        stock_details += f"""
Stock: {ticker}
Signals: {signals}
Strength: {strength}
Reasons: {reasons}
{'-' * 30}
        """
    
    body = f"""
Hello,

Your stock analyzer has identified new buy signals based on today's market data.

Buy Signals Detected:
{stock_details}

Errored Stock(s): {error_list}

Thank you,
Market Tracker

---

This is an automated message. Please do not reply.
    """
    smtp_user = "noreply.avinash.s@gmail.com"
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_port = os.getenv("SMTP_PORT")
    reciever = "kingaiva@icloud.com"
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr(("Market Monitor", sender_addr))
    msg['To'] = reciever
    msg.set_content(body)
    server = smtplib.SMTP(smtp_host,smtp_port)    
    server.starttls()
    server.login(smtp_user,smtp_password)
    server.send_message(msg)