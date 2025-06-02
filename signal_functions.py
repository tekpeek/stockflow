import yfinance as yf
import pandas as pd

def calculate_final_signal(stock_id: str):
    print(calculate_rsi(stock_id))

def calculate_rsi(stock_symbol: str, period: int = 14, interval: str = '1d') -> float:
    nse_symbol = stock_symbol.upper()
    df = yf.download(nse_symbol, period="3mo", interval=interval)

    if df.empty or 'Close' not in df.columns:
        return {"error": "Could not fetch data for {stock_symbol}."}

    close = df['Close']
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing (using EMA)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Drop NaNs and get latest value
    latest_rsi = rsi.dropna().iloc[-1]
    rsi_smooth = rsi.ewm(span=5, adjust=False).mean().iloc[-1]
    #return round(latest_rsi, 2)
    return {
        'rsi': round(float(latest_rsi[stock_symbol]), 2),
        'rsi_smooth': round(float(rsi_smooth[stock_symbol]), 2)
    }

calculate_final_signal("RELIANCE.NS")