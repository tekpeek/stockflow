import logging
import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from src.core.signal_functions import calculate_bharatquant_v4
from src.core.top_500_nse_tickers import top_500_nse_tickers

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_v4_bulk():
    buy_stocks = []
    total = len(top_500_nse_tickers)
    
    print(f"🚀 Starting BharatQuant v4 Bulk Analysis for {total} tickers...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    for i, symbol in enumerate(top_500_nse_tickers, 1):
        if i % 10 == 0 or i == 1:
            print(f"[{i}/{total}] Processing {symbol}...")
            
        try:
            # We pass a silent logger to avoid flooding the console
            silent_logger = logging.getLogger("silent")
            silent_logger.setLevel(logging.CRITICAL)
            
            result = calculate_bharatquant_v4(silent_logger, symbol)
            
            if result.get('recommendation') == "BUY" and result.get('score') >= 5:
                buy_stocks.append({
                    "symbol": symbol,
                    "score": result.get('score'),
                    "strength": result.get('strength'),
                    "reason": result.get('reason'),
                    "tp": result.get('take_profit'),
                    "sl": result.get('stop_loss')
                })
                print(f"✅ BUY SIGNAL FOUND: {symbol} (Score: {result.get('score')})")
                
        except Exception as e:
            # Silently continue on errors for specific tickers
            pass
            
    print("-" * 50)
    print(f"✅ Analysis Complete. Scanned {total} stocks.")
    print(f"💰 Found {len(buy_stocks)} BUY opportunities.")
    print("-" * 50)
    
    if buy_stocks:
        print("\n--- BHARATQUANT V4 BUY LIST ---")
        for stock in buy_stocks:
            print(f"Ticker: {stock['symbol']}")
            print(f"  Score: {stock['score']} ({stock['strength']})")
            print(f"  Target: {stock['tp']} | Stop: {stock['sl']}")
            print(f"  Reason: {stock['reason']}")
            print("-" * 20)
    else:
        print("\nNo BUY signals found in the top 500 tickers at this moment.")

if __name__ == "__main__":
    test_v4_bulk()
