import yfinance as yf
import pandas as pd

def calculate_final_signal(stock_id: str,interval: str,period: int,window: int, num_std: float):
    nse_symbol = stock_id.upper()
    df = yf.download(nse_symbol, period="3mo", interval=interval, progress=False, auto_adjust=False) 
    rsi = calculate_rsi(stock_id,df,period,interval)
    macd = calculate_macd_signal(stock_id,df,interval)
    bb = calculate_bollinger_bands(stock_id,df,window,num_std)
    return should_buy(rsi, macd, bb)

def calculate_individual(option: str, stock_id: str,interval: str,period: int,window: int, num_std: float):
    nse_symbol = stock_id.upper()
    df = yf.download(nse_symbol, period="3mo", interval=interval, progress=False, auto_adjust=False)
    if option=="rsi":
        return  calculate_rsi(stock_id,df,period,interval)
    elif option=="bb":
        return calculate_bollinger_bands(stock_id,df,window,num_std)
    elif option=="macd":
        return calculate_macd_signal(stock_id,df,interval)
    else:
        return {"error": "Invalid Strategy option!"}

def should_buy(rsi_result, macd_result, bb_result):
    reasons = []
    buy_signal = False

    # RSI condition: oversold or recovering
    rsi_signal = False
    if rsi_result['rsi'] < 30 and rsi_result['rsi_smooth'] > rsi_result['rsi']:
        rsi_signal = True
    elif rsi_result['rsi'] >= 40 and rsi_result['rsi'] <= 70 and rsi_result['rsi_smooth'] < rsi_result['rsi']:
        rsi_signal = True
        reasons.append(f"RSI is low or recovering: RSI={rsi_result['rsi']:.2f}")
    else:
        reasons.append(f"RSI not favorable: RSI={rsi_result['rsi']:.2f}")

    # MACD condition: bullish crossover and rising momentum
    if macd_result['crossover']!= "none" and macd_result['momentum_up']:
        reasons.append("MACD bullish crossover with rising momentum")
    else:
        reasons.append("MACD not indicating bullish momentum")

    # Bollinger Bands condition: price crossed above middle, squeeze or oversold
    bb_signal = False
    if bb_result['crossed_above_middle']:
        bb_signal = True
        reasons.append("Price crossed above Bollinger middle band")
    if bb_result['is_squeeze']:
        bb_signal = True
        reasons.append("Bollinger Bands in squeeze, potential breakout")
    if bb_result['is_oversold']:
        bb_signal = True
        reasons.append("Price near or below lower Bollinger Band (oversold)")

    if not bb_signal:
        reasons.append("Bollinger Bands not indicating buy")

    # Combine signals: RSI favorable signal + MACD buy signal + any BB buy signal
    macd_signal = (macd_result['is_potential_entry'] and ("bullish" in macd_result['trend_strength']))
    if rsi_signal and macd_signal and bb_signal:
        buy_signal = True
        reasons.insert(0, "Strong BUY signal detected based on all indicators")
    elif (macd_signal and rsi_signal) or (macd_signal and bb_signal) or (rsi_signal and bb_signal):
        buy_signal = True
        reasons.insert(0, "Weak bullish signal, monitor the stock and take decision")
    else:
        reasons.insert(0, "No strong BUY signal detected")

    return {
        'buy': buy_signal,
        'reason': "; ".join(reasons)
    }

def calculate_rsi(stock_symbol: str, df, period: int, interval: str) -> float:

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
    
    return {
        'rsi': round(float(latest_rsi[stock_symbol]), 2),
        'rsi_smooth': round(float(rsi_smooth[stock_symbol]), 2)
    }

def calculate_macd_signal(stock_symbol: str, df, interval: str) -> dict:
    symbol = stock_symbol.upper()
    df = yf.download(symbol, period="3mo", interval=interval, progress=False, auto_adjust=False)
    if df.empty or 'Close' not in df.columns:
        raise ValueError(f"Could not fetch data for {stock_symbol}.")

    close = df['Close']
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    macd = (ema12 - ema26).squeeze()
    signal = macd.ewm(span=9, adjust=False).mean().squeeze()
    hist = (macd - signal).squeeze()

    m0 = macd.iloc[-1].item() if isinstance(macd.iloc[-1], pd.Series) else macd.iloc[-1]
    m1 = macd.iloc[-2].item() if isinstance(macd.iloc[-2], pd.Series) else macd.iloc[-2]
    m2 = macd.iloc[-3].item() if isinstance(macd.iloc[-3], pd.Series) else macd.iloc[-3]
    m3 = macd.iloc[-4].item() if isinstance(macd.iloc[-4], pd.Series) else macd.iloc[-4]
    s0 = signal.iloc[-1].item() if isinstance(signal.iloc[-1], pd.Series) else signal.iloc[-1]
    s1 = signal.iloc[-2].item() if isinstance(signal.iloc[-2], pd.Series) else signal.iloc[-2]
    s2 = signal.iloc[-3].item() if isinstance(signal.iloc[-3], pd.Series) else signal.iloc[-3]
    s3 = signal.iloc[-4].item() if isinstance(signal.iloc[-4], pd.Series) else signal.iloc[-4]
    h0 = hist.iloc[-1].item() if isinstance(hist.iloc[-1], pd.Series) else hist.iloc[-1]

    # crossover detection
    prev_above = m1 > s1 and m2 > s2 and m3 > s3
    now_above  = m0 > s0
    if not prev_above and now_above:
        crossover = "bullish_crossover"
    elif prev_above and not now_above:
        crossover = "bearish_crossover"
    else:
        crossover = "none"

    # momentum direction: are both rising?
    momentum_up = (m0 > m1) and (s0 > s1)

    # which line is lower now, and is it rising?
    lower_line_rising = (m0 < s0 and m0 > m1) or (s0 <= m0 and s0 > s1)

    # potential entry: bullish crossover + lower line rising
    is_entry = (crossover == "bullish_crossover") and lower_line_rising

    # trend strength from histogram
    if h0 > 0.5:
        strength = "strong_bullish"
    elif h0 > 0:
        strength = "moderate_bullish"
    elif h0 > -0.5:
        strength = "weak_bearish"
    else:
        strength = "strong_bearish"

    return {
        "macd": round(m0, 4),
        "signal": round(s0, 4),
        "histogram": round(h0, 4),
        "crossover": crossover,
        "trend_strength": strength,
        "momentum_up": momentum_up,
        "is_potential_entry": is_entry
    }

def calculate_bollinger_bands(stock_symbol: str, df, window: int, num_std: float):
    data = yf.download(stock_symbol, period="3mo", interval="1d", progress=False, auto_adjust=False)
    close = data['Close']
    middle_band = close.rolling(window).mean()
    std_dev = close.rolling(window).std()

    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)

    # Drop NaNs at start to get valid indices
    valid_idx = middle_band.dropna().index
    if len(valid_idx) < 2:
        raise ValueError("Not enough data points after rolling window to compute Bollinger Bands")

    last_idx = valid_idx[-1]
    prev_idx = valid_idx[-2]

    price = close.loc[last_idx]
    price_prev = close.loc[prev_idx]
    mb_latest = middle_band.loc[last_idx]
    mb_prev = middle_band.loc[prev_idx]
    ub_latest = upper_band.loc[last_idx]
    lb_latest = lower_band.loc[last_idx]

    # Convert to scalars if they are pandas Series with single values
    def to_scalar(val, name):
        if isinstance(val, pd.Series) and len(val) == 1:
            #print(f"Converting {name} from Series to scalar")
            return val.iloc[0]
        elif isinstance(val, pd.Series):
            #print(f"Warning: {name} is Series with length > 1")
            raise ValueError(f"{name} is Series with multiple values: {val}")
        return val

    price = to_scalar(price, "price")
    price_prev = to_scalar(price_prev, "price_prev")
    mb_latest = to_scalar(mb_latest, "mb_latest")
    mb_prev = to_scalar(mb_prev, "mb_prev")
    ub_latest = to_scalar(ub_latest, "ub_latest")
    lb_latest = to_scalar(lb_latest, "lb_latest")

    band_width = (ub_latest - lb_latest) / mb_latest if mb_latest != 0 else 0

    overbought_threshold = 0.98
    oversold_threshold = 1.02

    is_overbought = price >= ub_latest * overbought_threshold
    is_oversold = price <= lb_latest * oversold_threshold

    bandwidth_series = (upper_band - lower_band) / middle_band
    avg_bandwidth = bandwidth_series.rolling(window).mean()
    avg_bandwidth_latest = avg_bandwidth.loc[last_idx]
    avg_bandwidth_latest = to_scalar(avg_bandwidth_latest, "avg_bandwidth_latest")

    is_squeeze = False
    if pd.notna(avg_bandwidth_latest):
        is_squeeze = band_width < avg_bandwidth_latest * 0.5

    crossed_above_middle = (price_prev < mb_prev) and (price > mb_latest)
    crossed_below_middle = (price_prev > mb_prev) and (price < mb_latest)

    return {
        'middle_band': mb_latest,
        'upper_band': ub_latest,
        'lower_band': lb_latest,
        'is_overbought': is_overbought,
        'is_oversold': is_oversold,
        'is_squeeze': is_squeeze,
        'band_width': band_width,
        'price': price,
        'crossed_above_middle': crossed_above_middle,
        'crossed_below_middle': crossed_below_middle,
    }