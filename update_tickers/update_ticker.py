import pandas as pd
import yfinance as yf
import time
from typing import List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_list_to_file(stock_list: List[str], filename: str) -> None:
    try:
        with open(filename, 'w') as f:
            f.write("TOP_500_STOCKS_BY_VOLUME = [\n")
            
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


def get_top_500_stocks_by_volume(csv_file_path: str = "EQUITY_L.csv") -> List[str]:
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
        save_list_to_file(top_500_stocks, "top_500_nse_tickers.py")
        
        return top_500_stocks
        
    except Exception as e:
        logger.error(f"Error in get_top_500_stocks_by_volume: {str(e)}")
        return []


def get_top_500_stocks_by_volume_with_volume_data(csv_file_path: str = "EQUITY_L.csv") -> List[Tuple[str, float]]:
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


if __name__ == "__main__":
    # Example usage
    print("Fetching top 500 stocks by volume...")
    top_stocks = get_top_500_stocks_by_volume()
    print(f"Top 10 stocks: {top_stocks[:10]}")
    print(f"Total stocks returned: {len(top_stocks)}")
