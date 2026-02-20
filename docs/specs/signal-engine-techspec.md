# Technical Specification: Signal Engine

This document details the technical implementation of the BharatQuant v4 signal generation logic.

## Signal Generation Logic (BharatQuant v4)

The engine implements a hierarchical scoring system implemented in `src/core/signal_functions.py`.

### Scoring Weights
| Indicator | Condition | Score |
|-----------|-----------|-------|
| **Market Structure** | Hourly Higher Low (HL) | +3 |
| **Logic Scaffolding** | Base confirmation | Required |
| **RSI** | Bullish Divergence | +2 |
| **Bollinger Bands** | Squeeze + Expansion | +2 |
| **CMF** | Positive Money Flow (> 0.15) | +1 |
| **MACD** | Bullish Crossover | +1 |

### Logic Hierarchy Process
1. **Daily Filter**: Verify Price > EMA200 and EMA50 > EMA200. If fail, return `NONE`.
2. **Hourly Analysis**: Detect local peaks/troughs using a sliding window.
3. **Trigger Calculation**: Run RSI, MACD, BB, and CMF concurrently on 1H data.
4. **Aggregation**: Sum scores. 
    - `>= 7`: Institutional
    - `>= 5`: Strong
    - `>= 4`: Moderate

## API Endpoint: Detailed Reference

### `GET /api/{stock_id}/{indicator}`
Extracts raw calculation results for a specific indicator.
- **Indicators**: `rsi`, `macd`, `bb`, `cmf`.
- **Logic**: Returns raw values (e.g., RSI value, smooth RSI) without the V4 aggregator logic. Used for UI graphing and debugging.

## Parameter Handling
The engine respects externalized strategy parameters injected from the `strategy-config` Secret:
- `INTERVAL`: Default `1d`
- `PERIOD`: Default `14`
- `WINDOW`: Default `20`
- `NUM_STD`: Default `2`

## Error State Handling
- **Missing Data**: Returns a JSON structure with an `error` key if Yahoo Finance returns empty DataFrames.
- **Invalid Format**: Validates `.NS` suffix via regex before initiating download.
