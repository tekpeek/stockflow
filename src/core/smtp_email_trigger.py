import requests
import time

def send_email(logger,EVENT_DISPATCHER_URL,stock_list,retries=3,timeout=20):
    url = f"{EVENT_DISPATCHER_URL}/api/v1/email-alert"
    headers = {"Content-Type": "application/json"}
    payload = {"stock_list": stock_list, "channels": ["email", "slack"], "channel": "stockflow"}

    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            logger.info(f"Response for {url}: {response.text} : attempt: {attempt}")
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    status = response_json.get("status")
                    if status == "Email alert process initiated":
                        return True
                except ValueError:
                    logger.error("Invalid JSON response")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

        time.sleep(1)
    return False