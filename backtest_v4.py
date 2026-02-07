import pandas as pd
import yfinance as yf
import logging
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path to import signal functions
sys.path.append(os.getcwd())

from src.core.signal_functions import calculate_bharatquant_v4
from src.core.top_500_nse_tickers import top_500_nse_tickers
top_500_nse_tickers=top_500_nse_tickers[:50]

# Setup basic logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("backtester")

class TradeManager:
    def __init__(self, initial_capital=100000):
        self.active_trade = None
        self.trades = []
        self.capital = initial_capital
        self.slippage = 0.0005 # 0.05%

    def execute_buy(self, symbol, price, tp, sl, time, atr):
        if self.active_trade:
            return False
            
        self.active_trade = {
            "symbol": symbol,
            "entry_price": price,
            "entry_time": time,
            "tp": tp, # Original TP for reference, though we use trailing now
            "sl": sl,
            "atr": atr,
            "highest_high": price,
            "trailing_active": False,
            "max_age": time + timedelta(days=5)
        }
        return True

    def update(self, current_time, high, low, close):
        if not self.active_trade:
            return None

        trade = self.active_trade
        exit_price = None
        exit_reason = None

        # Update high for trailing
        if high > trade['highest_high']:
            trade['highest_high'] = high
            
        # Activate trailing once price hits 1.0x ATR profit
        if not trade['trailing_active'] and trade['highest_high'] >= trade['entry_price'] + trade['atr']:
            trade['trailing_active'] = True
            
        # If trailing is active, move SL up (1.5x ATR below highest high)
        if trade['trailing_active']:
            new_sl = trade['highest_high'] - (1.5 * trade['atr'])
            if new_sl > trade['sl']:
                trade['sl'] = new_sl

        # 1. Check SL (which might be the trailing SL)
        if low <= trade['sl']:
            exit_price = trade['sl']
            exit_reason = "STOP_LOSS" if not trade['trailing_active'] else "TRAILING_STOP"
        # 2. Check Timeout (5 days)
        elif current_time >= trade['max_age']:
            exit_price = close
            exit_reason = "TIMEOUT"

        if exit_price:
            pnl_perc = (exit_price - trade['entry_price']) / trade['entry_price']
            # Apply slippage on both entry and exit
            pnl_perc -= (self.slippage * 2)
            
            trade_result = {
                "symbol": trade['symbol'],
                "entry_time": trade['entry_time'],
                "exit_time": current_time,
                "entry_price": trade['entry_price'],
                "exit_price": exit_price,
                "pnl_perc": round(pnl_perc * 100, 2),
                "reason": exit_reason
            }
            self.trades.append(trade_result)
            self.active_trade = None
            return trade_result
        
        return None

    def get_summary(self):
        if not self.trades:
            return "No trades executed."
        
        df = pd.DataFrame(self.trades)
        win_rate = (df['pnl_perc'] > 0).mean() * 100
        total_pnl = df['pnl_perc'].sum()
        profit_factor = df[df['pnl_perc'] > 0]['pnl_perc'].sum() / abs(df[df['pnl_perc'] < 0]['pnl_perc'].sum()) if any(df['pnl_perc'] < 0) else float('inf')
        
        return {
            "total_trades": len(self.trades),
            "win_rate": f"{win_rate:.2f}%" if not df.empty else "0.00%",
            "total_pnl": f"{total_pnl:.2f}%" if not df.empty else "0.00%",
            "profit_factor": f"{profit_factor:.2f}" if not df.empty else "0.00",
            "avg_pnl": f"{df['pnl_perc'].mean():.2f}%" if not df.empty else "0.00%"
        }

def run_backtest(symbol, period_h="60d", silent=False):
    if not silent: print(f"📊 Running BharatQuant v4 Backtest for {symbol} (Period: {period_h})...")
    
    # Calculate daily period to ensure EMA200 has 1 year of lookback BEFORE the start of hourly data
    # yfinance period format is usually like '2y', '60d'
    # We'll pull 3y daily to be safe for a 2y hourly backtest
    period_d = "3y" if "2y" in period_h else "1y"
    if "1y" in period_h and period_d == "1y": period_d = "2y"

    # 1. Fetch Data
    df_h = yf.download(symbol, period=period_h, interval="1h", progress=False, auto_adjust=False)
    df_d = yf.download(symbol, period=period_d, interval="1d", progress=False, auto_adjust=False)
    
    if df_h.empty or df_d.empty:
        print("❌ Error: Could not fetch data.")
        return

    # Flatten columns
    if isinstance(df_h.columns, pd.MultiIndex): df_h.columns = df_h.columns.get_level_values(0)
    if isinstance(df_d.columns, pd.MultiIndex): df_d.columns = df_d.columns.get_level_values(0)

    # Normalize timezones
    if df_h.index.tz is not None:
        df_h.index = df_h.index.tz_convert(None)
    if df_d.index.tz is not None:
        df_d.index = df_d.index.tz_convert(None)

    tm = TradeManager()
    
    # Loop through hourly data (starting with enough lookback)
    start_idx = 50 
    for i in range(start_idx, len(df_h)):
        current_time = df_h.index[i]
        
        # Slice Hour data up to current_time
        slice_h = df_h.iloc[:i+1]
        
        # Slice Daily data up to current day
        current_day = current_time.floor('D')
        # We need to ensure the Daily slice doesn't include the "current" day's close if the hour is middle of the day
        # But for Macro trend (200 EMA), it's usually fine to use up to the previous day
        slice_d = df_d[df_d.index < current_day]
        
        # If we have an active trade, update it
        if tm.active_trade:
            row = df_h.iloc[i]
            res = tm.update(current_time, row['High'], row['Low'], row['Close'])
            if res:
                if not silent: print(f"📉 EXIT: {res['reason']} at {res['exit_price']} | PnL: {res['pnl_perc']}%")
        else:
            # Check for BUY signal
            result = calculate_bharatquant_v4(logger, symbol, df_daily_input=slice_d, df_hourly_input=slice_h)
            
            if result.get('recommendation') == "BUY" and result.get('score') >= 6:
                if not silent: print(f"🚀 BUY: {symbol} at {result['entry_price']} | Score: {result['score']} | {current_time}")
                # Extract ATR from metadata
                atr = result.get('metadata', {}).get('rsi', {}).get('atr', 0)
                tm.execute_buy(symbol, result['entry_price'], result['take_profit'], result['stop_loss'], current_time, atr)

    if not silent:
        print("\n" + "="*30)
        print(f"BACKTEST SUMMARY: {symbol}")
        print("="*30)
        summary = tm.get_summary()
        if isinstance(summary, dict):
            for k, v in summary.items():
                print(f"{k.replace('_', ' ').title()}: {v}")
        else:
            print(summary)
        print("="*30 + "\n")
    
    return tm.trades

def run_bulk_backtest(period="60d"):
    all_trades = []
    tickers = top_500_nse_tickers
    total = len(tickers)
    
    print(f"🚀 Starting Bulk Backtest for {total} tickers (Period: {period})...")
    
    for i, symbol in enumerate(tickers, 1):
        if i % 10 == 0 or i == 1:
            print(f"[{i}/{total}] Backtesting {symbol}...")
        try:
            trades = run_backtest(symbol, period_h=period, silent=True)
            all_trades.extend(trades)
        except Exception as e:
            continue
            
    # Final Portfolio Summary
    print("\n" + "="*50)
    print(f"GLOBAL PORTFOLIO SUMMARY (PERIOD: {period})")
    print("="*50)
    
    if not all_trades:
        print("No trades executed across the portfolio.")
        return

    df = pd.DataFrame(all_trades)
    win_rate = (df['pnl_perc'] > 0).mean() * 100
    total_pnl = df['pnl_perc'].sum()
    profit_factor = df[df['pnl_perc'] > 0]['pnl_perc'].sum() / abs(df[df['pnl_perc'] < 0]['pnl_perc'].sum()) if any(df['pnl_perc'] < 0) else float('inf')
    
    print(f"Total Symbols Scanned: {total}")
    print(f"Total Trades Executed: {len(all_trades)}")
    print(f"Avg Trades Per Stock: {len(all_trades)/total:.2f}")
    print(f"Combined Win Rate   : {win_rate:.2f}%")
    print(f"Combined PnL        : {total_pnl:.2f}%")
    print(f"Combine Profit Factor: {profit_factor:.2f}")
    print(f"Average PnL/Trade   : {df['pnl_perc'].mean():.2f}%")
    print("="*50 + "\n")

if __name__ == "__main__":
    # Get period from args if present e.g. --period 2y
    period = "60d"
    if "--period" in sys.argv:
        p_idx = sys.argv.index("--period")
        if p_idx + 1 < len(sys.argv):
            period = sys.argv[p_idx + 1]

    if "--bulk" in sys.argv:
        run_bulk_backtest(period=period)
    else:
        # Ticker is first arg that isn't a flag
        args = [a for a in sys.argv[1:] if not a.startswith("--") and a != period]
        ticker = args[0] if args else "RELIANCE.NS"
        run_backtest(ticker, period_h=period)
