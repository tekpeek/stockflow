import smtp_email_trigger as email_trigger
import os
import json
import requests
import pandas as pd
import yfinance as yf
import time
import sys
from typing import List, Tuple
import logging

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
except Exception as e:
    logger.error(f"Error loading environment variables: {str(e)}")


def save_list_to_file(stock_list: List[str], filename: str) -> None:
    try:
        with open(filename, 'w') as f:
            f.write("top_500_nse_tickers = [\n")
            
            # Write each stock ticker with proper formatting
            for i, stock in enumerate(stock_list):
                if i == len(stock_list) - 1:  # Last item
                    f.write(f'    "{stock}"\n')
                else:
                    f.write(f'    "{stock}",\n')
            f.write("]\n\n")
        
        logger.info(f"Successfully saved {len(stock_list)} stocks to {filename}")
        
    except Exception as e:
        logger.error(f"Error saving list to file {filename}: {str(e)}")


def get_top_500_stocks_from_mount() -> List[str]:
    mount_path = "/app/data/tickers"
    try:
        logger.info(f"Reading top stocks from mount: {mount_path}")
        if not os.path.exists(mount_path):
            logger.warning(f"Mount point {mount_path} does not exist. Falling back to local import.")
            return []
        
        with open(mount_path, 'r') as f:
            tickers_str = f.read().strip()
            tickers = tickers_str.split(",") if tickers_str else []
            logger.info(f"Successfully read {len(tickers)} stocks from mount")
            return tickers
    except Exception as e:
        logger.error(f"Error reading stocks from mount: {str(e)}")
        return []

def fetch_openai_analysis(url, prompt, retries=3, timeout=240):
    for attempt in range(retries):
        try:
            response = requests.post(url,json={"prompt":prompt},timeout=timeout)
            parsed_response = response.json()
            keys = list(parsed_response.keys())
            if "mie_analysis" not in keys:
                parsed_response = json.loads(parsed_response[keys[0]])
            print(parsed_response)
            status = parsed_response["mie_analysis"]
            status = status["status"]
        except Exception as e:
            print(f"Error parsing output from openai. Error : {e}")
            raise
        print(f"output for {url}: {parsed_response} : attempt: {attempt}")
        print("*****************")
        if status == "failed":
            continue
        else:
            return parsed_response # Wait 1 second before retrying
    if status == "failed":
        raise Exception(f"Analysis failed. Response : {parsed_response}")
    return parsed_response

def identify_stocks():
    final_buy_list = []
    error_list = []
    ticker_list= []
    for ticker in top_500_nse_tickers.top_500_nse_tickers:
        output=os.popen(f"curl -s {SIGNAL_ENGINE_URL}/api/{ticker} | jq -r .").read().strip()
        signals = os.popen(f"echo '{output}' | jq -r .signals").read().strip()
        strength = os.popen(f"echo '{output}' | jq -r .strength").read().strip()
        reasons = os.popen(f"echo '{output}' | jq -r .reason").read().strip()
        
        if "true" not in output and "false" not in output:
            error_list.append(ticker)
        if "true" in output:
            print(f"{ticker}")
            ticker_list.append(ticker)
            final_buy_list.append([ticker, signals, strength, reasons])

def identify_v4_stocks():
    logger.info("Initiating BharatQuant v4 Scanning...")
    final_buy_list = []
    error_list = []
    ticker_list = []
    
    # Fetch tickers from Mount (ConfigMap)
    tickers = get_top_500_stocks_from_mount()
    
    if not tickers:
        logger.error("No tickers found to scan.")
        return [[], [], []]

    for i, ticker in enumerate(tickers):
        try:
            # v4.3 Optimization: Score >= 6 for high-probability swing
            res = requests.get(f"{SIGNAL_ENGINE_URL}/api/{ticker}")
            res = res.json()
            if res.get('buy') and res.get('score', 0) >= 6:
                logger.info(f"V4 BUY DETECTED: {ticker} | Score: {res['score']}")
                ticker_list.append(ticker)
                # Format to match identifying_stocks output: [ticker, signals, strength, reasons]
                final_buy_list.append([
                    ticker, 
                    res.get('signals', ''), 
                    res.get('strength', ''), 
                    res.get('reason', '')
                ])
                
            if (i + 1) % 50 == 0:
                logger.info(f"V4 Scan Progress: {i + 1}/{len(tickers)}")
                
        except Exception as e:
            logger.error(f"Error in v4 analysis for {ticker}: {str(e)}")
            error_list.append(ticker)
            continue

    return [final_buy_list, error_list, ticker_list]

def perform_market_sentiment_analysis(ticker_list):
    prompt=""
    with open("/app/market_analysis_prompt.txt") as file:
        prompt = file.read()
        prompt = prompt.replace("__TICKER_LIST__",str(ticker_list))
    file.close()
    mie_analysis = fetch_openai_analysis(f"{MARKET_INTEL_ENGINE_URL}/chat",prompt)
    final_list=[]
    for i in range(len(mie_analysis["mie_analysis"]["results"])):
        if mie_analysis["mie_analysis"]["results"][i]["buy_rating"] >=5:
            final_list.append(mie_analysis["mie_analysis"]["results"][i])
    return final_list

if __name__ == "__main__":
    # 1. Fetch BharatQuant v4 Signals (Local Engine) - ONLY V4
    logger.info("Starting BharatQuant v4 Signal Identification...")
    v4_results = identify_v4_stocks()
    v4_payload = v4_results[0]
    unique_tickers = v4_results[2]
    
    logger.info(f"Total Unique Stocks identified by V4: {len(unique_tickers)}")
    
    if len(v4_payload) > 0:
        # 2. Perform AI Sentiment Analysis
        final_list = perform_market_sentiment_analysis(v4_payload)
        if len(final_list) > 0:
            # 3. Send Email Alert
            email_trigger.send_email(logger, EVENT_DISPATCHER_URL, final_list)
            logger.info("Email Sent successfully with BharatQuant v4 signals.")
        else:
            logger.info("No stocks passed the AI Sentiment filter (Score >= 5).")
    else:
        logger.info("No BUY signals detected by BharatQuant v4 engine.")