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
        symbol, buy_rating, overall_sentiment, key_drivers, confidence, summary = stock["symbol"], stock["buy_rating"], stock["overall_sentiment"], str(stock["key_drivers"]), stock["confidence"], stock["summary"] 
        stock_details += f"""
Stock: {symbol}
Buy Rating: {buy_rating}
Overall Sentiment: {overall_sentiment}
Key Drivers: {key_drivers}
Confidence: {confidence}
Summary: {summary}
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