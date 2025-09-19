import os
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
import time

def check_service_health(url, retries=3, timeout=20):
    for attempt in range(retries):
        output = os.popen(f"curl -s --max-time {timeout} {url} | jq -r .").read().strip()
        print(f"output for {url}: {output} : attempt: {attempt}")
        print("*****************")
        status = os.popen(f"echo '{output}' | jq -r .status").read().strip()
        if status == "OK":
            return True
        time.sleep(1)  # Wait 1 second before retrying
    return False

def health_check():
    issues = []
    is_healthy = True
    se_healthy = check_service_health("https://tekpeek.duckdns.org/api/health")
    sc_healthy = check_service_health("https://tekpeek.duckdns.org/api/admin/health")
    mie_healthy = check_service_health("http://market-intel-engine-service:8000/health")

    if not se_healthy:
        is_healthy = False
        issues.append("signal-engine")
    if not sc_healthy:
        is_healthy = False
        issues.append("stockflow-controller")
    if not mie_healthy:
        is_healthy = False
        issues.append("market-intel-engine")

    return [is_healthy, issues]

if __name__ == "__main__":
    health_status = health_check()
    print(f"health_status: {health_status}")
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
            reciever = "kingaiva@icloud.com"
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = formataddr(("Stockflow Health Check", sender_addr))
            msg['To'] = reciever
            msg.set_content(body)
            server = smtplib.SMTP(smtp_host,smtp_port)    
            server.starttls()
            server.login(smtp_user,smtp_password)
            server.send_message(msg)