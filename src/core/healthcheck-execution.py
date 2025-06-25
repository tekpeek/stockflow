import os
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime

def health_check():
    issues=[]
    is_healthy = True
    output=os.popen(f"curl -s https://tekpeek.duckdns.org/health | jq -r .").read().strip()
    se_status = os.popen(f"echo '{output}' | jq -r .status").read().strip()

    output=os.popen(f"curl -s https://tekpeek.duckdns.org/admin/health | jq -r .").read().strip()
    sc_status = os.popen(f"echo '{output}' | jq -r .status").read().strip()

    if str(se_status) != "OK":
        is_healthy = False
        issues.append("signal-engine")
    if str(sc_status) != "OK":
        is_healthy = False
        issues.append("stockflow-controller")



    return [is_healthy, issues]

if __name__ == "__main__":
    health_status = health_check()
    if not health_status[0]:
            current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
            subject = f"Stockflow Alert: Health Check Failed - {current_datetime}"
            sender_addr = "noreply.avinash.s@gmail.com"
            smtp_host = os.getenv("SMTP_HOST")
            body = f"""
Hello,

Stockflow has identified failed health check during routine checks.

Errored Services: {health_status[1]}

Thank you,
Stockflow

---

This is an automated message. Please do not reply.
            """
            smtp_user = "noreply.avinash.s@gmail.com"
            smtp_password = os.getenv("SMTP_PASSWORD")
            smtp_port = os.getenv("SMTP_PORT")
            reciever = "avinashsubhash19@gmail.com"
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = formataddr(("Stockflow Health Check", sender_addr))
            msg['To'] = reciever
            msg.set_content(body)
            server = smtplib.SMTP(smtp_host,smtp_port)    
            server.starttls()
            server.login(smtp_user,smtp_password)
            server.send_message(msg)