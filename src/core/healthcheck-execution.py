import os
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
import time
import requests
import json

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

def trigger_failure_api(issues):
    url = "https://tekpeek.duckdns.org/api/kubesnap/default"
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("API_KEY environment variable not set. Skipping API call.")
        return

    headers = {
        "X-API-Key": api_key
    }
    
    try:
        print(f"Triggering API for issues: {issues}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("Successfully triggered failure API")
            print(f"Failed to trigger failure API. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error triggering failure API: {e}")

def send_email(issues,retries=3,timeout=20):
    url = "http://event-dispatcher-service:8000/api/v1/health-alert"
    headers = {"Content-Type": "application/json"}
    payload = {"issues": issues}

    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            print(f"Response for {url}: {response.text} : attempt: {attempt}")
            print("*****************")
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    status = response_json.get("status")
                    if status == "Health alert email sent":
                        return True
                except ValueError:
                    print("Invalid JSON response")
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

        time.sleep(1)  # Wait 1 second before retrying
    return False

if __name__ == "__main__":
    health_status = health_check()
    print(f"health_status: {health_status}")
    if not health_status[0]:
            trigger_failure_api(health_status[1])
            current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
            status = send_email(health_status[1])
            if not status:
                print(f"Failed to send email for issues: {health_status[1]}")