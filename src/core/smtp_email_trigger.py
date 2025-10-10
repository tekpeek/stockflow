import sys
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def prepare_template():
    #with open("email-template.mjml") as f:
    #    template = f.read()
    #compiled_html = MJML(template).render()
    with open("email-template.html") as f:
        html = f.read()
    compiled_html = html
    return compiled_html

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
    body=prepare_template()
    smtp_user = "noreply.avinash.s@gmail.com"
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_port = os.getenv("SMTP_PORT")
    reciever = "kingaiva@icloud.com"
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

send_email([],[])