import sys
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

def send_email(stock_list,error_list):
    subject = "Daily Stock Alert: Buy Signal Detected"
    sender_addr = "noreply.avinash.s@gmail.com"
    smtp_host = os.getenv("SMTP_HOST")
    body = f"""
    Hello,

    Your stock analyzer has identified new buy signals based on today's market data.

    Highlighted Stock(s): {stock_list}

    Errored Stock(s): {error_list}

    Thank you,
    Market Tracker

    ---

    This is an automated message. Please do not reply.
    """
    smtp_user = "noreply.avinash.s@gmail.com"
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_port = os.getenv("SMTP_PORT")
    reciever = "avinashsubhash19@gmail.com"
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr(("Market Monitor", sender_addr))
    msg['To'] = reciever
    msg.set_content(body)
    server = smtplib.SMTP(smtp_host,smtp_port)    
    server.starttls()
    server.login(smtp_user,smtp_password)
    server.send_message(msg)