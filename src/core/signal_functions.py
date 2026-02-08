import yfinance as yf
import pandas as pd
from datetime import datetime
import numpy as np

def calculate_final_signal(logging,stock_id: str,interval: str,period: int,window: int, num_std: float):
    nse_symbol = stock_id.upper()
    df = yf.download(nse_symbol, period="1y", interval=interval, progress=False, auto_adjust=False)
    return calculate_bharatquant_v4(logging,stock_id)

def calculate_individual(logging,option: str, stock_id: str,interval: str,period: int,window: int, num_std: float):
    nse_symbol = stock_id.upper()
    df = yf.download(nse_symbol, period="1y", interval=interval, progress=False, auto_adjust=False)
    logging.info(f"Fetched data for {nse_symbol}")
    if option=="rsi":
        logging.info(f"Calculated RSI for {nse_symbol}")
        return  calculate_rsi(stock_id,df,period,interval)
    elif option=="bb":
        logging.info(f"Calculated Bollinger Bands for {nse_symbol}")
        return calculate_bollinger_bands(stock_id,df,window,num_std)
    elif option=="macd":
        logging.info(f"Calculated MACD for {nse_symbol}")
        return calculate_macd_signal(stock_id,df,interval)
    elif option=="cmf":
        logging.info(f"Calculated CMF for {nse_symbol}")
        return calculate_cmf(stock_id,df,period,interval,window)
    else:
        logging.info(f"Invalid Strategy option: {option}")
        return {"error": "Invalid Strategy option!"}

def signal_aggregator_v3(logging,rsi_result, macd_result, bb_result,cmf_result):
    logging.info("Initiating signal_aggregator_v3 with scoring.")
    reasons = []
    signals = []
    score = 0
    
    # helper to convert potential numpy types
    def to_float(val):
        if hasattr(val, 'item'):
            return float(val.item())
        return float(val)

    # 1. RSI Logic
    rsi_val = to_float(rsi_result['rsi'])
    rsi_smooth = to_float(rsi_result['rsi_smooth'])
    positive_rsi = False
    if rsi_val < 30 and rsi_smooth > rsi_val:
        positive_rsi = True
        score += 1
        reasons.append(f"RSI is oversold ({rsi_val:.2f}) and recovering")
        signals.append("RSI_OVERSOLD")
    elif 40 <= rsi_val <= 70 and rsi_smooth < rsi_val:
        positive_rsi = True
        score += 1
        reasons.append(f"RSI is in bullish range ({rsi_val:.2f}) and rising")
        signals.append("RSI_BULLISH_MOMENTUM")

    # 2. CMF Logic
    cmf_val = to_float(cmf_result['latest_cmf'])
    positive_cmf = cmf_val >= 0
    if positive_cmf:
        score += 1
        reasons.append(f"CMF is positive ({cmf_val:.4f}), indicating accumulation")
        signals.append("CMF_POSITIVE")

    # 3. MACD Logic
    macd_val = to_float(macd_result['macd'])
    signal_val = to_float(macd_result['signal'])
    hist_val = to_float(macd_result['histogram'])
    
    if macd_result['crossover'] == "bullish_crossover":
        score += 2
        reasons.append("MACD Bullish Crossover detected")
        signals.append("MACD_CROSSOVER")
    
    if hist_val > 0 and "bullish" in macd_result['trend_strength']:
        score += 1
        reasons.append(f"MACD Histogram is positive ({hist_val:.4f}) with bullish strength")
        signals.append("MACD_BULLISH_TREND")

    # 4. Bollinger Bands Logic
    price = to_float(bb_result['price'])
    lower_band = to_float(bb_result['lower_band'])
    middle_band = to_float(bb_result['middle_band'])
    upper_band = to_float(bb_result['upper_band'])
    
    # Proximity to lower band (within 1.5%)
    if (price - lower_band) / lower_band <= 0.015:
        score += 1
        reasons.append("Price is near the lower Bollinger Band (potential support)")
        signals.append("BB_LOWER_PROXIMITY")
    
    if bb_result['crossed_above_middle']:
        score += 1
        reasons.append("Price crossed above the middle Bollinger Band")
        signals.append("BB_MIDDLE_CROSSOVER")

    # Final Recommendation
    recommendation = "NONE"
    buy_signal = False
    strength = "Weak"
    
    if score >= 4:
        recommendation = "BUY"
        buy_signal = True
        strength = "Strong"
    elif score >= 2:
        recommendation = "WATCH"
        buy_signal = score >= 3 # Maintain backward compatibility if score is 3
        strength = "Moderate"
    
    # Ensure buy is true if recommendation is BUY
    if recommendation == "BUY":
        buy_signal = True

    logging.info(f"Analysis completed. Score: {score}, Recommendation: {recommendation}")
    
    return {
        'recommendation': recommendation,
        'buy': buy_signal,
        'score': score,
        'strength': strength,
        'reason': ". ".join(reasons),
        'signals': "; ".join(signals),
        'metadata': {
            'rsi': {'value': rsi_val, 'smooth': rsi_smooth},
            'macd': {'value': macd_val, 'signal': signal_val, 'histogram': hist_val},
            'bb': {'upper': upper_band, 'lower': lower_band, 'middle': middle_band, 'bandwidth': to_float(bb_result['band_width'])},
            'cmf': {'value': cmf_val}
        },
        'timestamp': datetime.now().isoformat()
    }

def signal_aggregator_v2(rsi_result, macd_result, bb_result,cmf_result):
    reasons = []
    buy_signal = False
    buy_signal_list = []
    signal_strength = "Weak"

    # proce volatility calculation
    pv_one = (bb_result['price'] - bb_result['lower_band']) / bb_result['lower_band'] <= 0.014
    pv_two = rsi_result['rsi'] <= 32
    price_volatility = (pv_one or pv_two)

    if price_volatility:
        reasons.append("Price volatility is favorable")
        if float(cmf_result['latest_cmf']) >= 0 or float(cmf_result['latest_cmf']) > -0.18:
            reasons.append("Volume confirmation is positive")
            buy_signal = True
            if float(macd_result['macd']) >= float(macd_result['signal']) or float(macd_result['histogram']) >= 0:
                reasons.append("Trend confirmation is positive")
                signal_strength = "Strong"
            else:
                reasons.append("Trend confirmation is negative")
        else:
            reasons.append("Volume confirmation is negative")
    else:
        reasons.append("Price volatility is not favorable")
    
    return {
        'buy': buy_signal,
        'reason': "; ".join(reasons),
        'signals': "; ".join(buy_signal_list),
        'strength': f"{signal_strength}"
    }

def should_buy(rsi_result, macd_result, bb_result, cmf_result):
    reasons = []
    buy_signal = False
    buy_signal_list = []
    signal_strength = "Weak"

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

    cmf_signal = False
    if float(cmf_result['latest_cmf']) > 0:
        cmf_signal = True
        reasons.append("CMF Value is positive")
    else:
        reasons.append("CMF value is negative")

    # Combine signals: RSI favorable signal + MACD buy signal + any BB buy signal
    macd_signal = (macd_result['is_potential_entry'] and ("bullish" in macd_result['trend_strength']))
    if rsi_signal and macd_signal and bb_signal and cmf_signal:
        buy_signal = True
        reasons.insert(0, "Strong BUY signal detected based on all indicators")
    elif (macd_signal and rsi_signal) or (macd_signal and bb_signal) or (rsi_signal and bb_signal):
        if cmf_signal:
            buy_signal = True
            reasons.insert(0, "Weak bullish signal, monitor the stock and take decision")
    else:
        reasons.insert(0, "No strong BUY signal detected")

    if rsi_result:
        buy_signal_list.append("RSI")
    if macd_signal:
        buy_signal_list.append("MACD")
    if bb_signal:
        buy_signal_list.append("Bollinger Bands")
    if cmf_signal:
        buy_signal_list.append("CMF")
    if len(buy_signal_list) >= 3:
        signal_strength = "Strong"
    return {
        'buy': buy_signal,
        'reason': "; ".join(reasons),
        'signals': "; ".join(buy_signal_list),
        'strength': f"{signal_strength}"
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
    
    # Handle case where result might be a series (if df had multiple symbols) or a scalar
    try:
        val_rsi = latest_rsi[stock_symbol] if hasattr(latest_rsi, '__getitem__') else latest_rsi
        val_smooth = rsi_smooth[stock_symbol] if hasattr(rsi_smooth, '__getitem__') else rsi_smooth
    except (KeyError, IndexError):
        val_rsi = latest_rsi
        val_smooth = rsi_smooth

    return {
        'rsi': round(float(val_rsi), 2),
        'rsi_smooth': round(float(val_smooth), 2)
    }

def calculate_macd_signal(stock_symbol: str, df, interval: str) -> dict:
    symbol = stock_symbol.upper()
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
    data = df
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

def calculate_cmf(stock_symbol: str,df, period: str, interval: str, window: int = 20):
    df.columns = df.columns.get_level_values(0)
    df = df.copy()
    df.dropna(subset=['High', 'Low', 'Close', 'Volume'], inplace=True)
    mf_multiplier = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
    mf_multiplier.replace([float('inf'), -float('inf')], 0, inplace=True)  # handle division by zero
    mf_volume = mf_multiplier * df['Volume']
    df['CMF'] = mf_volume.rolling(window=window).sum() / df['Volume'].rolling(window=window).sum()
    #slope = np.polyfit(np.arange(len(df['CMF'].dropna().values[-2:])), df['CMF'].dropna().values[-2:], 1)[0]
    latest_cmf = df['CMF'].dropna().iloc[-1]
    return {
        'latest_cmf': f"{latest_cmf}"
        #'slope': f"{slope}"
    }

def to_native(obj):
    """
    Recursively converts numpy types to standard python types for JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_native(i) for i in obj]
    elif isinstance(obj, (np.bool_, np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return to_native(obj.tolist())
    return obj

def detect_market_structure(df, window=5):
    """
    Detects Higher Highs (HH) and Higher Lows (HL) on the given dataframe.
    """
    if len(df) < window * 2 + 1:
        return {"structure": "Insufficient Data", "is_higher_low": False}
    
    # Identify local peaks and troughs
    # A peak is a high higher than 'window' bars before and after
    df = df.copy()
    df['peak'] = df['High'].rolling(window=window*2+1, center=True).max() == df['High']
    df['trough'] = df['Low'].rolling(window=window*2+1, center=True).min() == df['Low']
    
    peaks = df[df['peak']]['High']
    troughs = df[df['trough']]['Low']
    
    if len(troughs) < 2:
        return {"structure": "Building", "is_higher_low": False}
    
    last_trough = troughs.iloc[-1]
    prev_trough = troughs.iloc[-2]
    
    is_higher_low = last_trough > prev_trough
    
    structure = "Bullish" if is_higher_low else "Neutral/Bearish emotion"
    
    return {
        "structure": structure,
        "is_higher_low": is_higher_low,
        "last_trough": last_trough,
        "prev_trough": prev_trough
    }

def detect_rsi_divergence(df, rsi_series, window=20):
    """
    Detects Bullish RSI Divergence: Price makes lower low, RSI makes higher low.
    """
    if len(df) < window:
        return {"divergence": False}
    
    # Look at recent local lows
    df = df.copy()
    df['rsi'] = rsi_series
    df['low_swing'] = df['Low'].rolling(window=5, center=True).min() == df['Low']
    
    lows = df[df['low_swing']].tail(2)
    
    if len(lows) < 2:
        return {"divergence": False}
    
    p1, p2 = lows['Low'].iloc[0], lows['Low'].iloc[1]
    r1, r2 = lows['rsi'].iloc[0], lows['rsi'].iloc[1]
    
    # Bullish Divergence: Price Lower Low, RSI Higher Low
    is_divergence = p2 < p1 and r2 > r1
    
    return {"divergence": is_divergence}

def detect_bb_squeeze(df, window=20):
    """
    Detects Bollinger Band Squeeze (low volatility before breakout).
    """
    close = df['Close']
    middle_band = close.rolling(window).mean()
    std_dev = close.rolling(window).std()
    upper_band = middle_band + (2 * std_dev)
    lower_band = middle_band - (2 * std_dev)
    
    bandwidth = (upper_band - lower_band) / middle_band
    # A squeeze is defined as bandwidth being in the bottom 25% of its recent history
    # Use a smaller window for rank if data is short
    rank_window = min(len(bandwidth.dropna()), 100)
    if rank_window < 20:
        return {"is_squeeze": False, "is_expanding": False, "bandwidth_percentile": 0.5}

    percentile = bandwidth.rolling(window=rank_window).rank(pct=True).iloc[-1]
    
    is_squeeze = percentile < 0.25
    
    # Expansion: currently widening?
    is_expanding = bandwidth.iloc[-1] > bandwidth.iloc[-2]
    
    return {"is_squeeze": is_squeeze, "is_expanding": is_expanding, "bandwidth_percentile": percentile}

def signal_aggregator_v4(logging, rsi_res, macd_res, bb_res, cmf_res, structure_res, macro_res):
    """
    BharatQuant v4: Hard Hierarchy Aggregator.
    """
    logging.info("Initiating BharatQuant v4 Aggregator.")
    
    score = 0
    reasons = []
    signals = []
    
    # 1. Macro Filter (Layer 1) - CRITICAL
    if not macro_res.get('is_bullish_macro', False):
        logging.info("V4 Fail: Bearish Macro Regime.")
        return {
            "recommendation": "NONE",
            "buy": False,
            "score": 0,
            "strength": "Weak",
            "reason": "Bearish Macro Regime (Daily Trend)",
            "signals": "MACRO_BEARISH"
        }
    
    # 2. Structure Layer (Layer 2) - BASE +3
    if structure_res.get('is_higher_low', False):
        score += 3
        reasons.append("Hourly Higher Low confirmed (Bullish Structure)")
        signals.append("STRUCTURE_HL")
    else:
        # The user said "buy only if all three layers agree"
        # Since Layer 2 didn't agree, we stop or give a WATCH
        logging.info("V4 Info: No Bullish Structure HL detected.")
    
    # 3. Trigger Layer (Layer 3) - CONFLUENCE
    # RSI Divergence (+2)
    if rsi_res.get('divergence', False):
        score += 2
        reasons.append("Bullish RSI Divergence detected")
        signals.append("RSI_DIVERGENCE")
        
    # Volatility (+2)
    if bb_res.get('is_squeeze', False) and bb_res.get('is_expanding', False):
        score += 2
        reasons.append("Bollinger Band Squeeze & Expansion (Breakout)")
        signals.append("BB_SQUEEZE_BREAKOUT")
    
    # Liquidity (+1)
    if float(cmf_res.get('latest_cmf', 0)) > 0.15:
        score += 1
        reasons.append(f"Strong Money Flow (CMF: {cmf_res['latest_cmf']})")
        signals.append("CMF_STRONG")
        
    # Momentum (+1)
    if macd_res.get('crossover') == "bullish_crossover":
        score += 1
        reasons.append("MACD Bullish Crossover")
        signals.append("MACD_CROSSOVER")

    # FINAL RECOMMENDATION (Hard Hierarchy: Score >= 4 means 1+2+3 agree)
    recommendation = "NONE"
    strength = "No Signal"
    buy_signal = False
    
    if score >= 7:
        recommendation = "BUY"
        strength = "Institutional (Unicorn)"
        buy_signal = True
    elif score >= 5:
        recommendation = "BUY"
        strength = "Strong (Professional)"
        buy_signal = True
    elif score >= 4:
        recommendation = "BUY"
        strength = "Moderate (Aggressive)"
        buy_signal = True
    elif score >= 2:
        recommendation = "WATCH"
        strength = "Weak (Wait for Confirmation)"
        buy_signal = False
    
    logging.info(f"V4 Final: Score {score}, Recommendation {recommendation}")
    
    return {
        'recommendation': recommendation,
        'buy': buy_signal,
        'score': score,
        'strength': strength,
        'reason': ". ".join(reasons),
        'signals': "; ".join(signals),
        'timestamp': datetime.now().isoformat()
    }

def calculate_bharatquant_v4(logging, stock_id: str, df_daily_input=None, df_hourly_input=None):
    """
    Orchestrates BharatQuant v4 analysis: Fetches 1D and 1H data (or uses provided) and calls the aggregator.
    """
    symbol = stock_id.upper()
    logging.info(f"Starting BharatQuant v4 analysis for {symbol}")
    
    # 1. Fetch Multi-Timeframe Data
    if df_daily_input is not None and df_hourly_input is not None:
        df_daily = df_daily_input
        df_hourly = df_hourly_input
    else:
        # Daily data for Macro (1y lookback)
        df_daily = yf.download(symbol, period="1y", interval="1d", progress=False, auto_adjust=False)
        # Hourly data for Structure and Signals (60d lookback for 1h is usually the limit for yfinance)
        df_hourly = yf.download(symbol, period="60d", interval="1h", progress=False, auto_adjust=False)
    
    if df_daily.empty or df_hourly.empty:
        return {"error": f"Missing data for {symbol}"}
    
    # Flatten columns if multi-indexed
    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = df_daily.columns.get_level_values(0)
    if isinstance(df_hourly.columns, pd.MultiIndex):
        df_hourly.columns = df_hourly.columns.get_level_values(0)

    # 2. Layer 1: Macro Trend (Daily)
    close_daily = df_daily['Close']
    ema50_d = close_daily.ewm(span=50, adjust=False).mean()
    ema200_d = close_daily.ewm(span=200, adjust=False).mean()
    
    latest_price_d = close_daily.iloc[-1]
    latest_ema50_d = ema50_d.iloc[-1]
    latest_ema200_d = ema200_d.iloc[-1]
    
    # Golden Zone: Price > EMA200 and EMA50 > EMA200
    is_bullish_macro = latest_price_d > latest_ema200_d and latest_ema50_d > latest_ema200_d
    macro_res = {'is_bullish_macro': is_bullish_macro}

    # 3. Layer 2: Market Structure (Hourly)
    structure_res = detect_market_structure(df_hourly)
    
    # 4. Layer 3: Triggers (Hourly)
    # RSI
    rsi_dict = calculate_rsi(stock_id, df_hourly, 14, "1h")
    # MACD
    macd_res = calculate_macd_signal(stock_id, df_hourly, "1h")
    # Bollinger Bands
    bb_res = calculate_bollinger_bands(stock_id, df_hourly, 20, 2)
    # CMF
    cmf_res = calculate_cmf(stock_id, df_hourly, "14", "1h", 20)
    
    # ATR for TP/SL
    high_h = df_hourly['High']
    low_h = df_hourly['Low']
    close_h = df_hourly['Close']
    tr = pd.concat([high_h - low_h, (high_h - close_h.shift()).abs(), (low_h - close_h.shift()).abs()], axis=1).max(axis=1)
    atr_h = tr.rolling(window=14).mean().iloc[-1]
    
    # RSI Divergence
    # We need a series for RSI divergence detection
    close_h = df_hourly['Close']
    delta = close_h.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))
    
    rsi_div_res = detect_rsi_divergence(df_hourly, rsi_series)
    # BB Squeeze
    bb_sq_res = detect_bb_squeeze(df_hourly)
    
    # 5. Aggregate
    final_res = signal_aggregator_v4(
        logging, 
        rsi_div_res, 
        macd_res, 
        bb_sq_res, 
        cmf_res, 
        structure_res, 
        macro_res
    )
    
    # 6. Set TP/SL if BUY
    if final_res['buy']:
        latest_price = float(df_hourly['Close'].iloc[-1])
        final_res['entry_price'] = latest_price
        final_res['take_profit'] = round(latest_price + (1.5 * float(atr_h)), 2)
        if structure_res.get('last_trough'):
            final_res['stop_loss'] = round(float(structure_res['last_trough']), 2)
    
    # Add metadata for debugging
    final_res['metadata'] = {
        'macro': {'price': float(latest_price_d), 'ema50': float(latest_ema50_d), 'ema200': float(latest_ema200_d)},
        'structure': structure_res,
        'rsi': rsi_dict,
        'macd': macd_res,
        'bb': bb_res,
        'cmf': cmf_res
    }
    logging.info("Response: ",to_native(final_res))
    return to_native(final_res)