import yfinance as yf
import pandas as pd
import numpy as np
from top_500_nse_tickers import top_500_nse_tickers, top_10_nse_tickers, top_300_nse_tickers, top_50_nse_tickers
import os
from signal_functions import calculate_bollinger_bands, calculate_cmf, calculate_macd_signal, calculate_rsi, signal_aggregator_v3, signal_aggregator_v2, should_buy

def calculate_bulk_backtest(option: str):
    final_count = 0
    final_num = 0
    for ticker in top_500_nse_tickers:
        output=os.popen(f"curl -s http://127.0.0.1:8001/backtest/{ticker}/{option} | jq -r .").read().strip()
        total_signals = os.popen(f"echo '{output}' | jq -r .total_signals").read().strip()
        try:
            count = int(total_signals)
            accuracy = float(os.popen(f"echo '{output}' | jq -r .accuracy").read().strip())
            if count!= "'null'" and count!=None and count>0:
                final_count += count
                final_num += (count*accuracy)
        except:
            print(f"Calculation failed for {ticker}")
            continue
    result = float(float(final_num)/final_count)
    return {
        'final_accuracy': f"{result}",
        'total_signals': f"{final_count}"
    }

def calculate_bulk_backtest_overall():
    final_count = 0
    final_num = 0
    for ticker in top_50_nse_tickers:
        output=os.popen(f"curl -s http://127.0.0.1:8001/backtest/{ticker} | jq -r .").read().strip()
        total_signals = os.popen(f"echo '{output}' | jq -r .total_signals").read().strip()
        try:
            count = int(total_signals)
            accuracy = float(os.popen(f"echo '{output}' | jq -r .accuracy").read().strip())
            if count!= "'null'" and count!=None and count>0:
                final_count += count
                final_num += (count*accuracy)
        except:
            print(f"Calculation failed for {ticker}")
            continue
    if final_count > 0:
        result = float(float(final_num)/final_count)
    else:
        result = 0
    return {
        'final_accuracy': f"{result}",
        'total_signals': f"{final_count}"
    }

def backtest_prediction_single_accuracy(option: str,stock_id: str, interval: str, period: int, window: int, num_std: float, growth_threshold: float = 0.005, lookahead: int = 4):
    nse_symbol = stock_id.upper()
    df = yf.download(nse_symbol, period="2y", interval=interval, progress=False, auto_adjust=False)
    results = []
    min_lookback = max(period, window, 14)
    correct = 0
    total_signals = 0
    for i in range(min_lookback, len(df) - lookahead):
        df_slice = df.iloc[:i+1]
        signal=False
        if option=="rsi":
            rsi_result = calculate_rsi(stock_id, df_slice, period, interval)
            rsi_signal = False
            if rsi_result['rsi'] < 30 and rsi_result['rsi_smooth'] > rsi_result['rsi']:
                rsi_signal = True
            elif rsi_result['rsi'] >= 40 and rsi_result['rsi'] <= 70 and rsi_result['rsi_smooth'] < rsi_result['rsi']:
                rsi_signal = True
            signal = rsi_result
        elif option=="macd":
            macd_result = calculate_macd_signal(stock_id, df_slice, interval)
            macd_signal = (macd_result['is_potential_entry'] and ("bullish" in macd_result['trend_strength']))
            signal=macd_signal
        elif option=="bb":
            bb_result = calculate_bollinger_bands(stock_id, df_slice, window, num_std)
            bb_signal = False
            if bb_result['crossed_above_middle']:
                bb_signal = True
            if bb_result['is_squeeze']:
                bb_signal = True
            if bb_result['is_oversold']:
                bb_signal = True
            signal=bb_signal
        elif option=="cmf":
            cmf_result = calculate_cmf(stock_id,df_slice,period,interval,window)
            cmf_signal=False
            print(float(cmf_result['latest_cmf']))
            if float(cmf_result['latest_cmf']) > 0:
                cmf_signal=True
            signal=cmf_signal
        #signal = should_buy(rsi, macd, bb)
        signal={
        'buy': signal,
        'reason': ";",
        'signals': ";",
        'strength': ";"
        }
        print(f"Signal is {signal}")
        if signal['buy']:
            print("Entered condition")
            total_signals += 1
            buy_price = df['Close'].iloc[i]
            future_prices = df['Close'].iloc[i+1:i+1+lookahead]
            max_future_price = future_prices.max()
            max_future_price=max_future_price[stock_id]
            buy_price = buy_price[stock_id]
            growth = (max_future_price - buy_price) / buy_price
            print(f"Growth: {growth}")
            success = growth >= growth_threshold
            print(success)
            if success:
                print("Entered condition 2")
                print(df.index[i])
                print(max_future_price)
                print(buy_price)
                correct += 1
            results.append({
                'date': str(df.index[i]),
                'buy_price': buy_price,
                'max_future_price': max_future_price,
                'growth': growth,
                'success': str(success),
                'reason': signal['reason'],
                'strength': signal['strength'],
                'signals': signal['signals']
            })
    accuracy = correct / total_signals if total_signals > 0 else 0
    summary = {
        'total_signals': total_signals,
        'correct_predictions': correct,
        'accuracy': accuracy,
        'details': results
    }
    return summary

def backtest_prediction_accuracy(stock_id: str, interval: str, period: int, window: int, num_std: float, growth_threshold: float = 0.005, lookahead: int = 7):
    nse_symbol = stock_id.upper()
    df = yf.download(nse_symbol, period="2y", interval=interval, progress=False, auto_adjust=False)
    results = []
    min_lookback = max(period, window, 14)
    correct = 0
    total_signals = 0
    for i in range(min_lookback, len(df) - lookahead):
        df_slice = df.iloc[:i+1]
        rsi = calculate_rsi(stock_id, df_slice, period, interval)
        macd = calculate_macd_signal(stock_id, df_slice, interval)
        bb = calculate_bollinger_bands(stock_id, df_slice, window, num_std)
        cmf = calculate_cmf(stock_id,df_slice,period,interval,window)
        #signal = should_buy(rsi, macd, bb, cmf)
        #signal = signal_aggregator_v2(rsi, macd, bb, cmf)
        signal = signal_aggregator_v3(rsi, macd, bb, cmf)
        print(signal)
        if signal['buy']:
            print("Entered condition")
            total_signals += 1
            buy_price = df['Close'].iloc[i]
            future_prices = df['Close'].iloc[i+1:i+1+lookahead]
            max_future_price = future_prices.max()
            max_future_price=max_future_price[stock_id]
            buy_price = buy_price[stock_id]
            growth = (max_future_price - buy_price) / buy_price
            print(f"Growth: {growth}")
            success = growth >= growth_threshold
            print(success)
            if success:
                print("Entered condition 2")
                print(df.index[i])
                print(max_future_price)
                print(buy_price)
                correct += 1
            results.append({
                'date': str(df.index[i]),
                'buy_price': buy_price,
                'max_future_price': max_future_price,
                'growth': growth,
                'success': str(success),
                'reason': signal['reason'],
                'strength': signal['strength'],
                'signals': signal['signals']
            })
    accuracy = correct / total_signals if total_signals > 0 else 0
    summary = {
        'total_signals': total_signals,
        'correct_predictions': correct,
        'accuracy': accuracy,
        'details': results
    }
    return summary