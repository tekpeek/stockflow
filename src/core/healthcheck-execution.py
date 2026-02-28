import os
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
import time
import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

try:
    STOCKFLOW_CONTROLLER_URL = os.getenv("STOCKFLOW_CONTROLLER")
    SIGNAL_ENGINE_URL = os.getenv("SIGNAL_ENGINE")
    MARKET_INTEL_ENGINE_URL = os.getenv("MARKET_INTEL_ENGINE")
    EVENT_DISPATCHER_URL = os.getenv("EVENT_DISPATCHER")
    KUBESNAP_URL = os.getenv("KUBESNAP")
    DEPLOY_TYPE = os.getenv("DEPLOY_TYPE")
    API_KEY = os.getenv("API_KEY")
except Exception as e:
    logger.error(f"Error loading environment variables: {str(e)}")

def check_service_health(url, retries=3, timeout=20):
    for attempt in range(retries):
        output = os.popen(f"curl -s --max-time {timeout} {url} | jq -r .").read().strip()
        logger.info(f"output for {url}: {output} : attempt: {attempt}")
        status = os.popen(f"echo '{output}' | jq -r .status").read().strip()
        if status == "OK":
            logger.info(f"Service {url} is healthy")
            return True
        time.sleep(1)
    logger.error(f"Service {url} is not healthy")
    return False

def health_check():
    issues = []
    is_healthy = True
    se_healthy = check_service_health(f"{SIGNAL_ENGINE_URL}/api/health")
    sc_healthy = check_service_health(f"{STOCKFLOW_CONTROLLER_URL}/api/admin/health")
    mie_healthy = check_service_health(f"{MARKET_INTEL_ENGINE_URL}/health")

    if not se_healthy:
        is_healthy = False
        issues.append("signal-engine")
    if not sc_healthy:
        is_healthy = False
        issues.append("stockflow-controller")
    if not mie_healthy:
        is_healthy = False
        issues.append("market-intel-engine")
    logger.info(f"health_status: {is_healthy}, issues: {issues}")
    return [is_healthy, issues]

def trigger_failure_api(issues):
    url = f"{KUBESNAP_URL}/api/kubesnap/{DEPLOY_TYPE}"
    if not API_KEY:
        logger.error("API_KEY environment variable not set. Skipping API call.")
        return

    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        logger.info(f"Triggering API for issues: {issues}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("Successfully triggered failure API")
        else:
            logger.error(f"Failed to trigger failure API. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logger.error(f"Error triggering failure API: {e}")

def send_email(issues,retries=3,timeout=20):
    url = f"{EVENT_DISPATCHER_URL}/api/v1/health-alert"
    headers = {"Content-Type": "application/json"}
    payload = {"issues": issues, "channels": ["email", "slack"], "channel": "stockflow"}

    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            logger.info(f"Response for {url}: {response.text} : attempt: {attempt}")
            logger.info(f"Response status for {url}: {response.status_code}")
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    status = response_json.get("status")
                    if status == "Health alert process initiated":
                        return True
                except ValueError:
                    logger.error("Invalid JSON response")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

        time.sleep(1)
    return False

if __name__ == "__main__":
    health_status = health_check()
    logger.info(f"health_status: {health_status}")
    if not health_status[0]:
            trigger_failure_api(health_status[1])
            current_datetime = datetime.now().strftime("%B %d %Y - %I:%M %p")
            status = send_email(health_status[1])
            if not status:
                logger.error(f"Failed to send email for issues: {health_status[1]}")