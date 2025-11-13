import sys
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def prepare_template(stock_list=None):
    with open("/home/ubuntu/app/email-template.html") as f:
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

def send_email(stock_list,error_list):
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