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


def get_top_500_stocks_by_volume(csv_file_path: str = "/home/ubuntu/app/EQUITY_L.csv") -> List[str]:
    try:
        # Read the CSV file
        logger.info(f"Reading stock symbols from {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        # Extract symbols from the first column
        symbols = df.iloc[:, 0].tolist()  # First column contains SYMBOL
        logger.info(f"Found {len(symbols)} stock symbols")
        
        # Add .ns suffix for NSE stocks
        nse_symbols = [f"{symbol}.NS" for symbol in symbols]
        
        # Dictionary to store volume data
        volume_data = {}
        
        # Fetch volume data for each stock
        logger.info("Fetching volume data from yfinance...")
        for i, symbol in enumerate(nse_symbols):
            try:
                # Add small delay to avoid rate limiting
                if i % 10 == 0 and i > 0:
                    time.sleep(1)
                # Fetch stock data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                
                if not hist.empty and 'Volume' in hist.columns:
                    volume = hist['Volume'].iloc[-1]  # Get latest volume
                    if volume > 0:  # Only include stocks with positive volume
                        volume_data[symbol] = volume
                
                # Log progress every 100 stocks
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(nse_symbols)} stocks")
                    
            except Exception as e:
                logger.warning(f"Error fetching data for {symbol}: {str(e)}")
                continue
        
        logger.info(f"Successfully fetched volume data for {len(volume_data)} stocks")
        
        # Sort by volume in descending order
        sorted_stocks = sorted(volume_data.items(), key=lambda x: x[1], reverse=True)
        
        # Extract top 500 stock symbols
        top_500_stocks = [stock[0] for stock in sorted_stocks[:500]]
        
        logger.info(f"Returning top {len(top_500_stocks)} stocks by volume")
        
        # Save the list to a new Python file
        save_list_to_file(top_500_stocks, "/home/ubuntu/app/top_500_nse_tickers.py")
        
        return top_500_stocks
        
    except Exception as e:
        logger.error(f"Error in get_top_500_stocks_by_volume: {str(e)}")
        return []


def get_top_500_stocks_by_volume_with_volume_data(csv_file_path: str = "/home/ubuntu/app/EQUITY_L.csv") -> List[Tuple[str, float]]:
    try:
        # Read the CSV file
        logger.info(f"Reading stock symbols from {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        # Extract symbols from the first column
        symbols = df.iloc[:, 0].tolist()  # First column contains SYMBOL
        logger.info(f"Found {len(symbols)} stock symbols")
        
        # Add .ns suffix for NSE stocks
        nse_symbols = [f"{symbol}.NS" for symbol in symbols]
        
        # Dictionary to store volume data
        volume_data = {}
        
        # Fetch volume data for each stock
        logger.info("Fetching volume data from yfinance...")
        for i, symbol in enumerate(nse_symbols):
            try:
                # Add small delay to avoid rate limiting
                if i % 10 == 0 and i > 0:
                    time.sleep(1)
                
                # Fetch stock data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                
                if not hist.empty and 'Volume' in hist.columns:
                    volume = hist['Volume'].iloc[-1]  # Get latest volume
                    if volume > 0:  # Only include stocks with positive volume
                        volume_data[symbol] = volume
                
                # Log progress every 100 stocks
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(nse_symbols)} stocks")
                    
            except Exception as e:
                logger.warning(f"Error fetching data for {symbol}: {str(e)}")
                continue
        
        logger.info(f"Successfully fetched volume data for {len(volume_data)} stocks")
        
        # Sort by volume in descending order
        sorted_stocks = sorted(volume_data.items(), key=lambda x: x[1], reverse=True)
        
        # Extract top 500 stock symbols with volume data
        top_500_stocks = sorted_stocks[:500]
        
        logger.info(f"Returning top {len(top_500_stocks)} stocks by volume with volume data")
        return top_500_stocks
        
    except Exception as e:
        logger.error(f"Error in get_top_500_stocks_by_volume_with_volume_data: {str(e)}")
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

    return [final_buy_list, error_list, ticker_list]

def perform_market_sentiment_analysis(ticker_list):
    prompt=""
    with open("/home/ubuntu/app/market_analysis_prompt.txt") as file:
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
    _ = get_top_500_stocks_by_volume()
    import top_500_nse_tickers
    list_data = identify_stocks()
    final_list = perform_market_sentiment_analysis(list_data[0])
    if len(final_list)>0:
        email_trigger.send_email(final_list,[])
        print("Email Sent")