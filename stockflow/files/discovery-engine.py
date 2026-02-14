import os
import pandas as pd
import yfinance as yf
import requests
import logging
import sys
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

import time
STOCKFLOW_CONTROLLER_URL = os.getenv("STOCKFLOW_CONTROLLER")
SF_API_KEY = os.getenv("SF_API_KEY")
DEPLOY_TYPE = os.getenv("DEPLOY_TYPE", "default")

def get_top_500_stocks_by_volume(csv_file_path: str = "EQUITY_L.csv") -> List[str]:
    try:
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found: {csv_file_path}")
            return []

        logger.info(f"Reading stock symbols from {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        symbols = df.iloc[:, 0].tolist()
        nse_symbols = [f"{symbol}.NS" for symbol in symbols]
        
        logger.info(f"Fetching volume data for {len(nse_symbols)} stocks individually...")
        
        volume_data = {}
        for i, symbol in enumerate(nse_symbols):
            try:
                # Add small delay to avoid rate limiting
                if i % 10 == 0 and i > 0:
                    time.sleep(1)
                
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                
                if not hist.empty and 'Volume' in hist.columns:
                    volume = hist['Volume'].iloc[-1]
                    if volume > 0:
                        volume_data[symbol] = volume
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(nse_symbols)} stocks")
                    
            except Exception as e:
                # Log specific errors but continue
                if "delisted" not in str(e).lower():
                    logger.warning(f"Error fetching data for {symbol}: {str(e)}")
                continue

        logger.info(f"Successfully fetched volume data for {len(volume_data)} stocks")
        
        # Sort by volume descending
        sorted_stocks = sorted(volume_data.items(), key=lambda x: x[1], reverse=True)
        top_500_stocks = [stock[0] for stock in sorted_stocks[:900]]
        
        return top_500_stocks
        
    except Exception as e:
        logger.error(f"Error in get_top_500_stocks_by_volume: {str(e)}")
        return []

def post_to_controller(tickers: List[str]):
    if not tickers:
        logger.warning("No tickers to post.")
        return

    # User changed endpoint to /api/admin/top-stocks
    # Ensure DEPLOY_TYPE prefix is handled if needed (controller handles it via router prefix)
    url = f"{STOCKFLOW_CONTROLLER_URL}/api/admin/top-stocks"
    headers = {"X-API-Key": SF_API_KEY}
    payload = {"tickers": tickers}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully posted {len(tickers)} tickers to controller.")
    except Exception as e:
        logger.error(f"Failed to post tickers to controller: {str(e)}")

if __name__ == "__main__":
    # Base path for CSV might vary depending on env
    csv_path = os.getenv("EQUITY_CSV_PATH", "EQUITY_L.csv")
    
    top_stocks = get_top_500_stocks_by_volume(csv_path)
    if top_stocks:
        post_to_controller(top_stocks)
    else:
        logger.error("Failed to identify top stocks.")
